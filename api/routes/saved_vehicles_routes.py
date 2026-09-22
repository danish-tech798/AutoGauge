from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db import db  # the actual singleton instance, matches app.py's import

saved_vehicles_bp = Blueprint("saved_vehicles", __name__)


@saved_vehicles_bp.route("", methods=["GET"])
@jwt_required()
def list_saved_vehicles():
    user_id = int(get_jwt_identity())
    vehicles = db.get_saved_vehicles(user_id)
    return jsonify({"items": vehicles})


@saved_vehicles_bp.route("", methods=["POST"])
@jwt_required()
def save_vehicle():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    estimation_id = data.get("estimation_id")
    vehicle_name = data.get("vehicle_name", "").strip()
    notes = data.get("notes", "")

    if not estimation_id:
        return jsonify({"message": "estimation_id is required"}), 400
    if not vehicle_name:
        return jsonify({"message": "vehicle_name is required"}), 400

    success, message = db.save_vehicle(user_id, estimation_id, vehicle_name, notes)
    if not success:
        return jsonify({"message": message}), 400

    return jsonify({"message": message})


@saved_vehicles_bp.route("/<int:vehicle_id>", methods=["DELETE"])
@jwt_required()
def delete_saved_vehicle(vehicle_id):
    # NOTE: db.py doesn't currently expose a delete_saved_vehicle method
    # (only delete_estimation exists). Leaving this as a stub that returns
    # a clear error rather than guessing at a method that may not exist --
    # add db.delete_saved_vehicle(user_id, vehicle_id) if this is needed.
    return jsonify({"message": "Deleting saved vehicles isn't wired up on the backend yet"}), 501