"""
explainability.py
-------------------
Generates a human-readable "why this price?" report for a single car
prediction, using SHAP (SHapley Additive exPlanations).

WHAT SHAP DOES, IN PLAIN TERMS:
Your model looks at ~15 features and spits out one number. SHAP opens
up that black box and tells you, for ONE specific prediction, how much
each individual feature pushed the price UP or DOWN compared to the
"average" car. For example:
    Base price (average car):     Rs 4,50,000
    car_age = 8 years         ->  -Rs 1,20,000
    brand = maruti (economy)  ->  -Rs   30,000
    condition_score = 0.87    ->  +Rs   18,000
    -----------------------------------------
    Final predicted price:        Rs 3,18,000

This is exactly the "report" your project needs - it doesn't just give
a number, it explains WHY.

Usage:
    # Explain a car already in your dataset (quick test, no photo needed)
    python src/explainability.py --index 42

    # Explain a brand new car with a real photo (full pipeline)
    python src/explainability.py --predict --photos path/to/photo.jpg \
        --brand maruti --model_name swift --year 2018 --km_driven 45000 \
        --fuel_type petrol --transmission manual --city pune \
        --body_type hatchback --owner_count 1
"""

import argparse
import os
import numpy as np
import pandas as pd
import joblib
import shap
import matplotlib
matplotlib.use("Agg")  # no GUI needed, just save to file
import matplotlib.pyplot as plt

DATA_PATH = "data/processed_cars.csv"
MODEL_PATH = "models/fusion_model.pkl"
FEATURES_PATH = "models/fusion_feature_columns.pkl"
REPORT_IMG_PATH = "report/price_explanation.png"

CATEGORICAL_COLS = ["brand", "fuel_type", "transmission", "city",
                     "body_type", "brand_tier"]


def load_model_and_features():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"No trained model found at {MODEL_PATH}. "
            "Run `python src/fusion.py --train` first."
        )
    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURES_PATH)
    return model, feature_cols


def build_row_from_index(index: int, feature_cols: list):
    """Pull one existing car from the processed dataset (useful for
    quick testing without needing a real photo)."""
    df = pd.read_csv(DATA_PATH)
    if "condition_score" not in df.columns:
        # match how fusion.py simulates it, so the explainer has
        # something to work with when testing on historical rows
        from fusion import simulate_condition_score
        df["condition_score"] = simulate_condition_score(df)

    row = df.iloc[[index]].copy()
    actual_price = row["price"].values[0] if "price" in row.columns else None
    X_row = row[feature_cols].copy()
    return X_row, actual_price


def build_row_from_car_details(car_details: dict, photo_paths: list, feature_cols: list):
    """Build a feature row for a brand-new car + real photo, reusing
    fusion.py's real image-scoring pipeline."""
    from fusion import get_real_condition_score

    condition_result = get_real_condition_score(photo_paths)
    row = {col: car_details.get(col, np.nan) for col in feature_cols}
    row["condition_score"] = condition_result["condition_score"]

    X_row = pd.DataFrame([row])[feature_cols]
    return X_row, condition_result


def prepare_for_model(X_row: pd.DataFrame):
    X_row = X_row.copy()
    for col in CATEGORICAL_COLS:
        if col in X_row.columns:
            X_row[col] = X_row[col].astype("category")
    return X_row


def explain(model, X_row: pd.DataFrame):
    """Runs SHAP and converts the log-scale contributions into actual
    rupee amounts, so the report is human-readable."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_row)[0]  # one row
    base_log = explainer.expected_value

    feature_names = X_row.columns.tolist()
    feature_values = X_row.iloc[0].to_dict()

    # sort features by how much they matter for THIS prediction
    order = np.argsort(-np.abs(shap_values))

    # walk from the base value, adding one feature's effect at a time,
    # converting log-space cumulative totals into real rupees at each
    # step -> gives a rupee amount for each feature that sums exactly
    # to the final predicted price
    running_log = base_log
    base_price = np.expm1(base_log)
    breakdown = []
    for idx in order:
        fname = feature_names[idx]
        prev_price = np.expm1(running_log)
        running_log += shap_values[idx]
        new_price = np.expm1(running_log)
        rupee_impact = new_price - prev_price
        breakdown.append({
            "feature": fname,
            "value": feature_values[fname],
            "rupee_impact": rupee_impact,
        })

    final_price = np.expm1(running_log)

    return {
        "base_price": base_price,
        "final_price": final_price,
        "breakdown": breakdown,
    }


def _format_value(val):
    """Rounds numeric feature values to a readable precision for the
    report/chart (e.g. 0.6904192076655887 -> 0.69)."""
    if isinstance(val, float):
        return round(val, 2)
    return val


def print_report(result: dict, actual_price=None):
    print("\n" + "=" * 60)
    print("PRICE EXPLANATION REPORT")
    print("=" * 60)
    print(f"Base price (typical car in dataset): Rs {result['base_price']:,.0f}\n")
    print(f"{'Feature':22s} {'Value':18s} {'Impact':>14s}")
    print("-" * 60)
    for item in result["breakdown"]:
        sign = "+" if item["rupee_impact"] >= 0 else "-"
        val_str = str(_format_value(item["value"]))[:16]
        print(f"{item['feature']:22s} {val_str:18s} {sign}Rs {abs(item['rupee_impact']):>10,.0f}")
    print("-" * 60)
    print(f"{'FINAL PREDICTED PRICE':22s} {'':18s}  Rs {result['final_price']:>10,.0f}")
    if actual_price is not None:
        diff = result["final_price"] - actual_price
        print(f"{'Actual listed price':22s} {'':18s}  Rs {actual_price:>10,.0f}")
        print(f"{'Difference':22s} {'':18s}  Rs {diff:>10,.0f}")
    print("=" * 60)


def save_waterfall_chart(result: dict, out_path: str = REPORT_IMG_PATH):
    """Saves a bar chart showing each feature's rupee impact, sorted
    biggest to smallest - easy to drop straight into your project report."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    items = result["breakdown"][:10]  # top 10 factors, keep it readable
    labels = [f"{it['feature']}\n({_format_value(it['value'])})" for it in items]
    values = [it["rupee_impact"] for it in items]
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in values]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(labels[::-1], values[::-1], color=colors[::-1])
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Impact on predicted price (Rs)")
    ax.set_title(
        f"Why this price? Base Rs {result['base_price']:,.0f} -> "
        f"Final Rs {result['final_price']:,.0f}"
    )
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"\nChart saved -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Explain a single price prediction with SHAP")
    parser.add_argument("--index", type=int, help="Row index from processed_cars.csv to explain")
    parser.add_argument("--predict", action="store_true", help="Explain a brand-new car")
    parser.add_argument("--photos", nargs="+", default=[])
    parser.add_argument("--brand", type=str)
    parser.add_argument("--model_name", type=str, dest="model_name")
    parser.add_argument("--year", type=int)
    parser.add_argument("--km_driven", type=float)
    parser.add_argument("--fuel_type", type=str)
    parser.add_argument("--transmission", type=str)
    parser.add_argument("--city", type=str)
    parser.add_argument("--body_type", type=str)
    parser.add_argument("--owner_count", type=int, default=1)
    args = parser.parse_args()

    model, feature_cols = load_model_and_features()
    actual_price = None

    if args.index is not None:
        X_row, actual_price = build_row_from_index(args.index, feature_cols)
    elif args.predict:
        current_year = 2026
        car_age = current_year - args.year if args.year else np.nan
        km_per_year = args.km_driven / car_age if args.km_driven and car_age else np.nan

        luxury = {"bmw", "audi", "mercedes-benz", "mercedes", "jaguar", "land rover",
                  "porsche", "volvo", "lexus"}
        premium = {"toyota", "honda", "hyundai", "skoda", "volkswagen", "kia", "ford"}
        b = str(args.brand).lower()
        brand_tier = "luxury" if b in luxury else ("premium" if b in premium else "economy")

        car_details = {
            "brand": args.brand, "year": args.year, "km_driven": args.km_driven,
            "fuel_type": args.fuel_type, "transmission": args.transmission,
            "city": args.city, "body_type": args.body_type, "car_age": car_age,
            "km_per_year": km_per_year, "brand_tier": brand_tier,
            "age_squared": car_age ** 2 if car_age is not None else np.nan,
            "is_new_ish": int(car_age <= 3) if car_age is not None else 0,
            "owner_count": args.owner_count,
        }
        X_row, _ = build_row_from_car_details(car_details, args.photos, feature_cols)
    else:
        parser.error("Provide either --index N (test on existing car) or --predict (new car)")

    X_row = prepare_for_model(X_row)
    result = explain(model, X_row)
    print_report(result, actual_price)
    save_waterfall_chart(result)


if __name__ == "__main__":
    main()
