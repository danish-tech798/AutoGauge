"""
tabular_model.py
------------------
Trains a price-prediction model on the cleaned car dataset
(data/processed_cars.csv, produced by data_preprocessing.py).

What it does:
  1. Loads the cleaned data
  2. Picks the useful features, encodes categories
  3. Splits into train/test sets
  4. Trains an XGBoost regression model
  5. Prints accuracy metrics (how good the model is)
  6. Shows which features matter most for price
  7. Saves the trained model to models/xgboost_model.pkl

Usage:
    python src/tabular_model.py
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

DATA_PATH = "data/processed_cars.csv"
MODEL_OUT_PATH = "models/xgboost_model.pkl"
FEATURES_OUT_PATH = "models/feature_columns.pkl"

# Columns we DON'T want to feed into the model
# (either identifiers, text duplicates of numeric columns, or leakage)
DROP_COLS = ["price", "price_log", "owner", "owner_raw", "model"]

# Columns the model should treat as categories (text groups),
# not as continuous numbers
CATEGORICAL_COLS = ["brand", "fuel_type", "transmission", "city",
                     "body_type", "brand_tier"]


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns from {path}")
    return df


def prepare_features(df: pd.DataFrame):
    """Splits the dataframe into X (features) and y (target price),
    and converts text columns into a format XGBoost understands."""
    df = df.copy()

    # target: predict log(price) - this smooths out the fact that
    # car prices vary hugely (a 50,000 rupee car and a 30 lakh car)
    y = df["price_log"] if "price_log" in df.columns else np.log1p(df["price"])

    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    X = df[feature_cols].copy()

    # convert categorical text columns to pandas 'category' dtype -
    # XGBoost can use these directly without manual one-hot encoding
    for col in CATEGORICAL_COLS:
        if col in X.columns:
            X[col] = X[col].astype("category")

    return X, y


def train_model(X_train, y_train):
    model = xgb.XGBRegressor(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        enable_categorical=True,   # lets XGBoost handle text categories directly
        tree_method="hist",
    )
    model.fit(X_train, y_train)
    return model


def evaluate(model, X_test, y_test):
    """Prints how accurate the model is, in terms a non-ML person
    can understand (actual rupee error, not just abstract scores)."""
    pred_log = model.predict(X_test)

    # convert predictions and true values back from log scale to real prices
    pred_price = np.expm1(pred_log)
    true_price = np.expm1(y_test)

    mae = mean_absolute_error(true_price, pred_price)
    rmse = np.sqrt(mean_squared_error(true_price, pred_price))
    r2 = r2_score(y_test, pred_log)
    mape = np.mean(np.abs((true_price - pred_price) / true_price)) * 100

    print("\n" + "=" * 50)
    print("MODEL PERFORMANCE")
    print("=" * 50)
    print(f"R² Score:            {r2:.4f}  (closer to 1.0 = better)")
    print(f"Mean Absolute Error:  Rs {mae:,.0f}  (average price prediction error)")
    print(f"RMSE:                 Rs {rmse:,.0f}")
    print(f"MAPE:                 {mape:.2f}%  (average % error)")
    print("=" * 50)

    return {"r2": r2, "mae": mae, "rmse": rmse, "mape": mape}


def show_feature_importance(model, X):
    importance = model.feature_importances_
    feat_imp = pd.Series(importance, index=X.columns).sort_values(ascending=False)

    print("\nTop features driving price predictions:")
    print("-" * 50)
    for feat, score in feat_imp.head(10).items():
        bar = "█" * int(score * 50)
        print(f"{feat:20s} {bar} {score:.3f}")


def main():
    os.makedirs("models", exist_ok=True)

    df = load_data(DATA_PATH)
    X, y = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\nTrain size: {len(X_train)}  |  Test size: {len(X_test)}")

    print("\nTraining XGBoost model...")
    model = train_model(X_train, y_train)

    evaluate(model, X_test, y_test)
    show_feature_importance(model, X)

    joblib.dump(model, MODEL_OUT_PATH)
    joblib.dump(list(X.columns), FEATURES_OUT_PATH)
    print(f"\nModel saved -> {MODEL_OUT_PATH}")
    print(f"Feature list saved -> {FEATURES_OUT_PATH}")


if __name__ == "__main__":
    main()
