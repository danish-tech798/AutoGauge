"""
fusion.py
----------
Combines the image-based condition score with the tabular price model.

IMPORTANT CONTEXT (explain this in your report/viva):
Your tabular dataset (CarDekho-style listings) and your image dataset
(CarDD damage photos) come from different sources - none of the 7,396
historical car listings have matching photos. So we can't look up a
"real" condition score for each historical training row.

Solution: we SIMULATE a condition_score for training, correlated with
car_age, km driven, and owner count (older/higher-mileage/more-owned
cars are statistically more likely to be damaged, plus some randomness
to mimic real-world variation). This teaches the model the *relationship*
between condition and price - i.e. "a lower condition score should pull
the price down" - without needing real matched photos for every row.

At ACTUAL prediction time (predict_price function below), we use the
REAL image model (condition_scorer.py) on the user's uploaded photos to
get a real condition score, then feed that real score into this trained
model to get a photo-informed price prediction.

This is a standard technique called "weak supervision" / proxy-label
training, used when you don't have a perfectly matched dataset.

Usage:
    # Step 1: retrain the model with the condition_score feature
    python src/fusion.py --train

    # Step 2: predict price for a single car using its real photos
    python src/fusion.py --predict --photos path/to/photo1.jpg path/to/photo2.jpg \
        --brand maruti --model_name swift --year 2018 --km_driven 45000 \
        --fuel_type petrol --transmission manual --city pune --body_type hatchback \
        --owner_count 1
"""

import argparse
import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

DATA_PATH = "data/processed_cars.csv"
MODEL_OUT_PATH = "models/fusion_model.pkl"
FEATURES_OUT_PATH = "models/fusion_feature_columns.pkl"
DAMAGE_MODEL_PATH = "models/damage_detector/run/weights/best.pt"

DROP_COLS = ["price", "price_log", "price_adjusted", "owner", "owner_raw", "model"]
CATEGORICAL_COLS = ["brand", "fuel_type", "transmission", "city",
                     "body_type", "brand_tier"]


# =====================================================================
# STEP 1: Simulate condition_score for historical training data
# =====================================================================
def simulate_condition_score(df: pd.DataFrame, seed: int = 42) -> pd.Series:
    """Creates a realistic-looking condition_score (0=badly damaged,
    1=pristine) for historical training rows, since we don't have real
    photos matched to these listings.

    IMPORTANT design choice: the score is only WEAKLY tied to age/
    mileage (older cars are somewhat more likely to show wear), and
    MOSTLY driven by independent randomness. This reflects reality -
    a car's cosmetic condition (a scratch from a parking lot, a dent
    from someone else's door) is largely NOT predictable from its age
    or mileage alone. That's exactly why photos add real value beyond
    what the tabular features already know: they capture damage that
    specs cannot predict.
    """
    rng = np.random.default_rng(seed)

    age = df["car_age"].fillna(df["car_age"].median())
    age_wear = np.clip(age / 20, 0, 1)  # mild age-related baseline wear

    # Most of the variation is independent random "accident/incident"
    # noise - this is the part a photo reveals that specs alone cannot.
    independent_wear = rng.beta(1.5, 3, size=len(df))  # skewed toward "less wear"

    total_wear = 0.25 * age_wear + 0.75 * independent_wear
    condition_score = 1 - total_wear

    return pd.Series(np.clip(condition_score, 0, 1), index=df.index)


# =====================================================================
# STEP 2: Train the fusion model (tabular features + condition_score)
# =====================================================================
def prepare_features(df: pd.DataFrame):
    df = df.copy()
    y = df["price_log"] if "price_log" in df.columns else np.log1p(df["price"])

    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    X = df[feature_cols].copy()

    for col in CATEGORICAL_COLS:
        if col in X.columns:
            X[col] = X[col].astype("category")

    return X, y


def train_fusion_model():
    os.makedirs("models", exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows from {DATA_PATH}")

    df["condition_score"] = simulate_condition_score(df)
    print("Added simulated condition_score feature "
          f"(mean={df['condition_score'].mean():.3f}, "
          f"std={df['condition_score'].std():.3f})")

    # ---- simulate condition's EFFECT on price ----
    # We don't have real photos matched to real sale prices, so there's
    # no ground truth for "how much does visible damage actually reduce
    # resale price". We simulate a modest, realistic effect: a car in
    # the worst visible condition (score=0) sells for ~15% less than an
    # identical car in perfect condition (score=1). This creates a
    # genuine training signal so the model learns to actually USE the
    # condition_score, not just see it as a redundant/ignored feature.
    # (This assumption should be stated clearly in your report - it's
    # a reasonable estimate, not measured from real transaction data.)
    price_multiplier = 0.80 + 0.20 * df["condition_score"]
    df["price_adjusted"] = df["price"] * price_multiplier
    df["price_log"] = np.log1p(df["price_adjusted"])

    X, y = prepare_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = xgb.XGBRegressor(
        n_estimators=400, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        enable_categorical=True, tree_method="hist",
    )
    model.fit(X_train, y_train)

    pred_log = model.predict(X_test)
    pred_price = np.expm1(pred_log)
    true_price = np.expm1(y_test)

    mae = mean_absolute_error(true_price, pred_price)
    rmse = np.sqrt(mean_squared_error(true_price, pred_price))
    r2 = r2_score(y_test, pred_log)
    mape = np.mean(np.abs((true_price - pred_price) / true_price)) * 100

    print("\n" + "=" * 50)
    print("FUSION MODEL PERFORMANCE (tabular + condition_score)")
    print("=" * 50)
    print(f"R² Score:            {r2:.4f}")
    print(f"Mean Absolute Error:  Rs {mae:,.0f}")
    print(f"RMSE:                 Rs {rmse:,.0f}")
    print(f"MAPE:                 {mape:.2f}%")
    print("=" * 50)

    importance = pd.Series(model.feature_importances_, index=X.columns) \
        .sort_values(ascending=False)
    print("\nTop features (note where condition_score ranks):")
    for feat, score in importance.head(10).items():
        marker = "  <-- image-derived feature" if feat == "condition_score" else ""
        print(f"  {feat:20s} {score:.3f}{marker}")

    joblib.dump(model, MODEL_OUT_PATH)
    joblib.dump(list(X.columns), FEATURES_OUT_PATH)
    print(f"\nFusion model saved -> {MODEL_OUT_PATH}")


# =====================================================================
# STEP 3: Predict price for a NEW car using its REAL photos
# =====================================================================
def get_real_condition_score(photo_paths: list) -> dict:
    """Runs the trained YOLOv8 damage detector on real photos to get a
    real condition_score, instead of the simulated one used in training.
    Accepts a list of individual photo file paths (one or more angles
    of the same car) and combines them using the worst (lowest) score,
    since one bad photo reveals real damage even if others look clean."""
    from condition_scorer import load_model, score_image

    if not photo_paths:
        print("WARNING: no photos provided. Using a neutral condition_score of 1.0.")
        return {"condition_score": 1.0, "damage_types": []}

    if not os.path.exists(DAMAGE_MODEL_PATH):
        print(f"WARNING: no trained damage model found at {DAMAGE_MODEL_PATH}")
        print("Using a neutral condition_score of 1.0 (assume good condition).")
        return {"condition_score": 1.0, "damage_types": []}

    model = load_model(DAMAGE_MODEL_PATH)
    per_photo_results = [score_image(model, p) for p in photo_paths]

    overall_score = min(r["condition_score"] for r in per_photo_results)
    all_damage_types = sorted({
        t for r in per_photo_results for t in r["damage_types"]
    })

    return {"condition_score": overall_score, "damage_types": all_damage_types}


def predict_price(car_details: dict, photo_paths: list):
    if not os.path.exists(MODEL_OUT_PATH):
        raise FileNotFoundError(
            f"No trained fusion model found at {MODEL_OUT_PATH}. "
            "Run `python src/fusion.py --train` first."
        )

    model = joblib.load(MODEL_OUT_PATH)
    feature_cols = joblib.load(FEATURES_OUT_PATH)

    condition_result = get_real_condition_score(photo_paths)
    condition_score = condition_result["condition_score"]

    row = {col: car_details.get(col, np.nan) for col in feature_cols}
    row["condition_score"] = condition_score

    X_new = pd.DataFrame([row])
    for col in CATEGORICAL_COLS:
        if col in X_new.columns:
            X_new[col] = X_new[col].astype("category")
    X_new = X_new[feature_cols]

    pred_log = model.predict(X_new)[0]
    pred_price = np.expm1(pred_log)

    print("\n" + "=" * 50)
    print("FUSION PRICE PREDICTION")
    print("=" * 50)
    print(f"Condition score (from photos): {condition_score:.3f} / 1.0")
    print(f"Damage detected:                {condition_result.get('damage_types', [])}")
    print(f"Predicted price:                Rs {pred_price:,.0f}")
    print("=" * 50)

    return pred_price, condition_score


def main():
    parser = argparse.ArgumentParser(description="Fusion: tabular + image condition score")
    parser.add_argument("--train", action="store_true", help="Retrain model with condition_score")
    parser.add_argument("--predict", action="store_true", help="Predict price for a single car")
    parser.add_argument("--photos", nargs="+", default=[], help="Paths to car photos")
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

    if args.train:
        train_fusion_model()
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
            "brand": args.brand,
            "year": args.year,
            "km_driven": args.km_driven,
            "fuel_type": args.fuel_type,
            "transmission": args.transmission,
            "city": args.city,
            "body_type": args.body_type,
            "car_age": car_age,
            "km_per_year": km_per_year,
            "brand_tier": brand_tier,
            "age_squared": car_age ** 2 if car_age is not None else np.nan,
            "is_new_ish": int(car_age <= 3) if car_age is not None else 0,
            "owner_count": args.owner_count,
        }
        predict_price(car_details, args.photos)
    else:
        print("Specify --train or --predict. See file docstring for usage examples.")


if __name__ == "__main__":
    main()
