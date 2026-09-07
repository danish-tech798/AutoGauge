"""
data_preprocessing.py
----------------------
Loads the used-vehicle dataset, cleans it, and engineers features
for the price-prediction model.

Supports THREE schemas (auto-detected):
  1. "used_vehicles.csv" (your uploaded file) -> columns:
     vehicle_type, brand, model, year, kms_driven, fuel_type,
     transmission, engine_cc, owner, city, body_type, selling_price
  2. "Vehicle dataset from cardekho" (nehalbirla) -> columns:
     name, year, selling_price, km_driven, fuel, seller_type,
     transmission, owner
  3. "CarDekho Used Car Data" (manishkr1754) -> columns:
     car_name, brand, model, vehicle_age, km_driven, transmission_type,
     fuel_type, seller_type, mileage, engine, max_power, seats,
     selling_price

The script auto-detects which schema you have and normalizes it into
one clean, consistent output file: data/processed_cars.csv

Usage:
    python data_preprocessing.py --input data/raw_cars.csv --output data/processed_cars.csv
"""

import argparse
import re
import numpy as np
import pandas as pd

CURRENT_YEAR = 2026

# ---------------------------------------------------------------------
# Brand tiering — used to engineer a "brand_tier" feature since luxury
# and economy brands depreciate at very different rates.
# ---------------------------------------------------------------------
LUXURY_BRANDS = {
    "bmw", "audi", "mercedes-benz", "mercedes", "jaguar", "land rover",
    "porsche", "volvo", "lexus", "mini", "bentley", "rolls-royce",
    "ferrari", "lamborghini", "maserati"
}
PREMIUM_BRANDS = {
    "toyota", "honda", "hyundai", "skoda", "volkswagen", "kia",
    "jeep", "mg", "ford"
}
# Everything else falls into "economy" (maruti, tata, renault, datsun,
# chevrolet, fiat, nissan, mahindra, etc.)


def detect_schema(df: pd.DataFrame) -> str:
    """Return 'v1', 'v2', or 'v3' depending on which schema is present."""
    if "kms_driven" in df.columns and "engine_cc" in df.columns:
        return "v3"
    if "vehicle_age" in df.columns or "car_name" in df.columns:
        return "v2"
    return "v1"


def extract_brand_model(name: str):
    """Split a full car name like 'Maruti Swift Dzire VDI' into
    brand='Maruti', model='Swift Dzire VDI'."""
    if not isinstance(name, str) or not name.strip():
        return "unknown", "unknown"
    parts = name.strip().split(" ", 1)
    brand = parts[0].strip().lower()
    model = parts[1].strip() if len(parts) > 1 else "unknown"
    return brand, model


def parse_numeric_with_unit(series: pd.Series) -> pd.Series:
    """Strip units like 'kmpl', 'CC', 'bhp' and convert to float.
    e.g. '23.4 kmpl' -> 23.4, '1248 CC' -> 1248.0"""
    def _parse(val):
        if pd.isna(val):
            return np.nan
        if isinstance(val, (int, float)):
            return float(val)
        match = re.search(r"[-+]?\d*\.?\d+", str(val))
        return float(match.group()) if match else np.nan
    return series.apply(_parse)


def brand_tier(brand: str) -> str:
    b = str(brand).lower()
    if b in LUXURY_BRANDS:
        return "luxury"
    if b in PREMIUM_BRANDS:
        return "premium"
    return "economy"


def normalize_schema_v1(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["brand"], df["model"] = zip(*df["name"].map(extract_brand_model))
    df["car_age"] = CURRENT_YEAR - df["year"]
    df = df.rename(columns={
        "selling_price": "price",
        "km_driven": "km_driven",
        "fuel": "fuel_type",
        "transmission": "transmission_type",
    })
    # v1 has no mileage/engine/power columns in the basic version
    for col in ["mileage", "engine", "max_power", "seats"]:
        if col not in df.columns:
            df[col] = np.nan
    return df


def normalize_schema_v2(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "brand" not in df.columns:
        df["brand"], df["model"] = zip(*df["car_name"].map(extract_brand_model))
    df["brand"] = df["brand"].astype(str).str.lower()
    df["car_age"] = df["vehicle_age"] if "vehicle_age" in df.columns else CURRENT_YEAR - df.get("year", CURRENT_YEAR)
    df = df.rename(columns={
        "fuel_type": "fuel_type",
        "transmission_type": "transmission_type",
        "selling_price": "price",
    })
    return df


def normalize_schema_v3(df: pd.DataFrame) -> pd.DataFrame:
    """Handles the 'used_vehicles.csv' schema:
    vehicle_type, brand, model, year, kms_driven, fuel_type,
    transmission, engine_cc, owner, city, body_type, selling_price
    """
    df = df.copy()

    # This file mixes cars AND two-wheelers (bikes). Since this project
    # is about CAR price prediction, drop the bikes.
    if "body_type" in df.columns:
        before = len(df)
        df = df[df["body_type"].str.lower() != "bike"]
        dropped = before - len(df)
        if dropped:
            print(f"Dropped {dropped} two-wheeler rows (body_type == 'bike')")

    # 'vehicle_type' column is entirely empty in this file -> drop it
    if "vehicle_type" in df.columns and df["vehicle_type"].notna().sum() == 0:
        df = df.drop(columns=["vehicle_type"])

    df["brand"] = df["brand"].astype(str).str.strip().str.lower()
    df["car_age"] = CURRENT_YEAR - df["year"]

    df = df.rename(columns={
        "kms_driven": "km_driven",
        "engine_cc": "engine",
        "selling_price": "price",
    })

    # owner column mixes numbers ("1","2"...) and text ("first owner", etc)
    owner_text_map = {
        "first owner": 1, "second owner": 2, "third owner": 3,
        "fourth owner or more": 4,
    }
    def _owner_to_num(val):
        val = str(val).strip().lower()
        if val in owner_text_map:
            return owner_text_map[val]
        try:
            return int(float(val))
        except ValueError:
            return np.nan
    if "owner" in df.columns:
        df["owner_raw"] = df["owner"].apply(_owner_to_num)

    # this schema has no mileage/max_power/seats -> fill placeholders
    for col in ["mileage", "max_power", "seats"]:
        if col not in df.columns:
            df[col] = np.nan

    return df


def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- numeric coercion for columns that often come with units ---
    for col in ["mileage", "engine", "max_power"]:
        if col in df.columns:
            df[col] = parse_numeric_with_unit(df[col])

    df["km_driven"] = pd.to_numeric(df["km_driven"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["car_age"] = pd.to_numeric(df["car_age"], errors="coerce")

    # --- drop rows with no target or obviously broken rows ---
    df = df.dropna(subset=["price"])
    df = df[df["price"] > 0]
    df = df[df["car_age"] >= 0]

    # --- fix impossible / placeholder values ---
    df.loc[df["car_age"] > 40, "car_age"] = np.nan
    df.loc[df["km_driven"] <= 0, "km_driven"] = np.nan
    df.loc[df["km_driven"] > 500000, "km_driven"] = np.nan  # odometer outlier

    # --- impute remaining numeric NaNs with median (robust to outliers) ---
    for col in ["km_driven", "mileage", "engine", "max_power", "seats", "car_age"]:
        if col in df.columns and df[col].notna().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    # --- categorical cleanup ---
    for col in ["fuel_type", "transmission_type", "seller_type", "owner", "brand"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    # ===================== FEATURE ENGINEERING =====================

    # km driven per year of ownership — flags odometer inconsistencies
    df["km_per_year"] = df["km_driven"] / df["car_age"].replace(0, 1)

    # brand resale tier
    df["brand_tier"] = df["brand"].apply(brand_tier)

    # non-linear depreciation signal: cars lose value fastest in yrs 1-3
    df["age_squared"] = df["car_age"] ** 2
    df["is_new_ish"] = (df["car_age"] <= 3).astype(int)

    # power-to-engine ratio (performance proxy), guard against div-by-zero
    if "engine" in df.columns and "max_power" in df.columns:
        df["power_per_cc"] = df["max_power"] / df["engine"].replace(0, np.nan)
        df["power_per_cc"] = df["power_per_cc"].fillna(df["power_per_cc"].median())

    # owner count as an ordinal number instead of free text
    owner_map = {
        "first owner": 1, "1st owner": 1,
        "second owner": 2, "2nd owner": 2,
        "third owner": 3, "3rd owner": 3,
        "fourth & above owner": 4, "4th & above owner": 4,
        "test drive car": 0,
    }
    if "owner_raw" in df.columns:
        # already numeric, from schema v3
        df["owner_count"] = pd.to_numeric(df["owner_raw"], errors="coerce")
        df["owner_count"] = df["owner_count"].fillna(df["owner_count"].median())
    elif "owner" in df.columns:
        df["owner_count"] = df["owner"].map(owner_map)
        df["owner_count"] = df["owner_count"].fillna(df["owner_count"].median())

    # city / body_type are useful categorical signals when present (v3)
    for col in ["city", "body_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    # log-transform target — car prices are right-skewed, this
    # stabilizes variance and usually improves regression performance
    df["price_log"] = np.log1p(df["price"])

    # --- drop columns that ended up 100% empty (no real signal at all) ---
    fully_empty = [c for c in df.columns if df[c].isna().all()]
    if fully_empty:
        print(f"Dropping fully-empty columns (no data available): {fully_empty}")
        df = df.drop(columns=fully_empty)
        # power_per_cc depends on engine/max_power - recompute guard
        if "power_per_cc" in df.columns and df["power_per_cc"].isna().all():
            df = df.drop(columns=["power_per_cc"])

    # --- drop obvious duplicates and reset index ---
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    return df


def load_and_process(input_path: str) -> pd.DataFrame:
    raw = pd.read_csv(input_path)
    raw.columns = [c.strip().lower().replace(" ", "_") for c in raw.columns]

    schema = detect_schema(raw)
    print(f"Detected schema: {schema}")

    if schema == "v1":
        norm = normalize_schema_v1(raw)
    elif schema == "v3":
        norm = normalize_schema_v3(raw)
    else:
        norm = normalize_schema_v2(raw)

    processed = clean_and_engineer(norm)
    return processed


def main():
    parser = argparse.ArgumentParser(description="Preprocess CarDekho used-car dataset")
    parser.add_argument("--input", type=str, default="data/raw_cars.csv",
                         help="Path to raw downloaded CSV")
    parser.add_argument("--output", type=str, default="data/processed_cars.csv",
                         help="Path to save the cleaned/engineered CSV")
    args = parser.parse_args()

    processed = load_and_process(args.input)
    processed.to_csv(args.output, index=False)

    print(f"\nSaved cleaned dataset -> {args.output}")
    print(f"Shape: {processed.shape}")
    print("\nColumns:", list(processed.columns))
    print("\nSample rows:")
    print(processed.head())


if __name__ == "__main__":
    main()