from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys, os, tempfile
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db import db  # the actual singleton instance, matches app.py's import
from src.fusion import predict_price, get_real_condition_score
from src.explainability import load_model_and_features, build_row_from_car_details, prepare_for_model, explain

estimation_bp = Blueprint("estimation", __name__)

LUXURY_BRANDS = {"bmw", "audi", "mercedes-benz", "mercedes", "jaguar", "land rover",
                  "porsche", "volvo", "lexus"}
PREMIUM_BRANDS = {"toyota", "honda", "hyundai", "skoda", "volkswagen", "kia", "ford"}

# Friendly display names for the SHAP breakdown -- falls back to the raw
# column name for anything not listed here.
FEATURE_LABELS = {
    "brand": "Brand",
    "brand_tier": "Brand Tier",
    "year": "Manufacture Year",
    "car_age": "Vehicle Age",
    "age_squared": "Age (non-linear effect)",
    "km_driven": "Kilometers Driven",
    "km_per_year": "Usage Rate (km/year)",
    "fuel_type": "Fuel Type",
    "transmission": "Transmission",
    "city": "City",
    "body_type": "Body Type",
    "owner_count": "Number of Owners",
    "is_new_ish": "Recency Bonus (<=3 yrs)",
    "condition_score": "Condition Score",
}

# Cap how many factors the UI shows -- explain() already sorts by
# importance, so this keeps only the most impactful ones.
MAX_BREAKDOWN_ITEMS = 8


def build_car_details(form):
    """
    Replicates the exact feature-engineering logic from fusion.py's main()
    CLI branch, so the API path produces identical features to the CLI path.
    """
    brand = str(form.get("brand", "")).strip().lower()
    fuel_type = str(form.get("fuel", "")).strip().lower()
    transmission = str(form.get("transmission", "")).strip().lower()
    city = str(form.get("city", "")).strip().lower()
    body_type = str(form.get("bodyType", "")).strip().lower()

    year = int(form.get("year")) if form.get("year") else None
    km_driven = float(form.get("km")) if form.get("km") else None

    current_year = 2026
    car_age = current_year - year if year else np.nan
    km_per_year = km_driven / car_age if km_driven and car_age else np.nan

    brand_tier = "luxury" if brand in LUXURY_BRANDS else ("premium" if brand in PREMIUM_BRANDS else "economy")

    return {
        "brand": brand,
        "year": year,
        "km_driven": km_driven,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "city": city,
        "body_type": body_type,
        "car_age": car_age,
        "km_per_year": km_per_year,
        "brand_tier": brand_tier,
        "age_squared": car_age ** 2 if not np.isnan(car_age) else np.nan,
        "is_new_ish": int(car_age <= 3) if not np.isnan(car_age) else 0,
        "owner_count": int(form.get("owners", 1)),
    }


def get_shap_breakdown(car_details, photo_paths):
    """
    Runs the real SHAP explainer (src/explainability.py) against the same
    fusion model used for the price prediction, and converts the result
    into the {factor, impact} shape the React PriceBreakdown component
    expects. Returns an empty list if anything goes wrong -- this must
    never break the core price prediction, which is already proven working.
    """
    try:
        model, feature_cols = load_model_and_features()
        X_row, _ = build_row_from_car_details(car_details, photo_paths, feature_cols)
        X_row = prepare_for_model(X_row)
        explanation = explain(model, X_row)

        breakdown = []
        for item in explanation["breakdown"][:MAX_BREAKDOWN_ITEMS]:
            factor_name = FEATURE_LABELS.get(item["feature"], item["feature"])
            breakdown.append({
                "factor": factor_name,
                "impact": float(item["rupee_impact"]),
            })
        return breakdown
    except Exception as e:
        print(f"[WARN] SHAP explanation failed, returning empty breakdown: {e}")
        return []


@estimation_bp.route("/analyze", methods=["POST"])
@jwt_required()
def analyze():
    user_id = int(get_jwt_identity())
    form = request.form

    # Save any uploaded photos to a temp dir; fusion.py expects a list of paths
    photo_paths = []
    for key in request.files:
        file = request.files[key]
        tmp_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(tmp_path)
        photo_paths.append(tmp_path)

    car_details = build_car_details(form)

    # predict_price internally re-runs condition scoring; call it separately
    # too so we can surface damage_types/damage_count in the API response.
    condition_result = get_real_condition_score(photo_paths) if photo_paths else {
        "condition_score": 1.0, "damage_types": []
    }

    pred_price, condition_score = predict_price(car_details, photo_paths)
    pred_price = float(pred_price)
    condition_score = float(condition_score)

    # SHAP breakdown -- reuses the same car_details/photo_paths, runs the
    # real explainer, wrapped so a failure here never breaks the price result.
    breakdown = get_shap_breakdown(car_details, photo_paths)

    # "If in perfect condition" price -- a second, cheap real prediction
    # with an empty photo list, which makes get_real_condition_score default
    # to condition_score=1.0. No extra YOLO inference needed for this call.
    try:
        perfect_price, _ = predict_price(car_details, [])
        perfect_condition_price = float(perfect_price)
    except Exception as e:
        print(f"[WARN] perfect-condition prediction failed: {e}")
        perfect_condition_price = None

    # --- Persist to DB, matching AutoGaugeDB.save_estimation's real signature ---
    estimation_data = {
        "brand": car_details["brand"],
        "model": form.get("model"),
        "year": car_details["year"],
        "km_driven": car_details["km_driven"],
        "fuel_type": car_details["fuel_type"],
        "transmission": car_details["transmission"],
        "city": car_details["city"],
        "body_type": car_details["body_type"],
        "owner_count": car_details["owner_count"],
        "condition": form.get("condition", ""),
        "predicted_price": pred_price,
        "condition_score": condition_score,
        "damage_detected": condition_result.get("damage_types", []),
        "base_price": pred_price,
    }

    success, estimation_id = db.save_estimation(user_id, estimation_data)
    if not success:
        print(f"[WARN] db.save_estimation() failed for user {user_id}")

    return jsonify({
        "estimation_id": estimation_id if success else None,
        "price": pred_price,
        "condition": condition_score,
        "damage": condition_result.get("damage_types", []),
        "breakdown": breakdown,
        "perfect_condition_price": perfect_condition_price,
    })


@estimation_bp.route("", methods=["GET"])
@jwt_required()
def list_estimations():
    user_id = int(get_jwt_identity())
    limit = int(request.args.get("limit", 50))
    history = db.get_estimation_history(user_id, limit=limit)
    return jsonify({"items": history, "hasMore": False, "page": 0})


@estimation_bp.route("/<int:est_id>", methods=["DELETE"])
@jwt_required()
def delete_estimation(est_id):
    user_id = int(get_jwt_identity())
    success, message = db.delete_estimation(est_id, user_id)
    return jsonify({"success": success, "message": message})


@estimation_bp.route("/statistics", methods=["GET"])
@jwt_required()
def statistics():
    user_id = int(get_jwt_identity())
    count = db.get_estimation_count(user_id)
    saved_count = len(db.get_saved_vehicles(user_id))
    return jsonify({
        "total_estimations": count,
        "saved_vehicles": saved_count,
    })