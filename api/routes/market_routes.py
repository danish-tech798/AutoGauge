from flask import Blueprint, jsonify
import pandas as pd
import os

market_bp = Blueprint("market", __name__)

@market_bp.route("/statistics", methods=["GET"])
def statistics():
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed_cars.csv')
    df = pd.read_csv(csv_path)
    return jsonify({
        "average_price": float(df["selling_price"].mean()),
        "total_listings": len(df),
        "top_brands": df["brand"].value_counts().head(5).to_dict(),
    })