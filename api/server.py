"""
AutoGauge Flask API Server
Bridges the React frontend to the existing ML pipeline + SQLite database
"""
import sys
import os

# Two path insertions needed, matching app.py's approach:
#
# 1. Project root — so "from src.db import db" and "from src.fusion import ..."
#    work correctly as package-qualified imports.
#
# 2. src/ itself — because fusion.py internally does a BARE import
#    ("from condition_scorer import load_model, score_image", no "src."
#    prefix). That only resolves if src/ is directly on sys.path, which is
#    what happens automatically when running "python src/fusion.py" from
#    the CLI, but NOT when fusion.py is imported from elsewhere (like here).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, SRC_DIR)

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from routes.auth_routes import auth_bp
from routes.estimation_routes import estimation_bp
from routes.market_routes import market_bp
from routes.saved_vehicles_routes import saved_vehicles_bp

app = Flask(__name__)

# Allow the Next.js dev server to call this API
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# JWT config — CHANGE THIS SECRET before any real deployment
app.config["JWT_SECRET_KEY"] = "autogauge-dev-secret-change-me"
jwt = JWTManager(app)

# Register route blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(estimation_bp, url_prefix="/api/estimations")
app.register_blueprint(market_bp, url_prefix="/api/market")
app.register_blueprint(saved_vehicles_bp, url_prefix="/api/saved-vehicles")

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "AutoGauge API"})

if __name__ == "__main__":
    # debug=False confirmed necessary — the debug reloader was killing
    # the worker process mid-request during model loading (YOLO/XGBoost).
    app.run(debug=False, port=5000)