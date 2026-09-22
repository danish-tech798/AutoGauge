from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.db import db  # the actual singleton instance, matches app.py's import

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")
    phone = data.get("phone", "")

    if not email or not password or not full_name:
        return jsonify({"message": "Missing required fields"}), 400

    success, message = db.signup(email, password, full_name, phone)
    if not success:
        return jsonify({"message": message}), 400

    # signup() doesn't return the user record, so log in immediately
    # to get the user_id needed for the JWT and every other db.py method
    login_success, user_data = db.login(email, password)
    if not login_success:
        # Extremely unlikely (signup just succeeded), but handle it
        return jsonify({"message": "Signup succeeded but auto-login failed"}), 500

    token = create_access_token(identity=str(user_data["id"]))
    return jsonify({
        "token": token,
        "user": {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["full_name"],
            "phone": user_data.get("phone", ""),
        }
    })


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    success, user_data = db.login(email, password)
    if not success:
        return jsonify({"message": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user_data["id"]))
    return jsonify({
        "token": token,
        "user": {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["full_name"],
            "phone": user_data.get("phone", ""),
        }
    })


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = db.get_user(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["full_name"],
            "phone": user.get("phone", ""),
        }
    })


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    full_name = data.get("full_name", "")
    phone = data.get("phone", "")

    success, message = db.update_user_profile(user_id, full_name, phone)
    if not success:
        return jsonify({"message": message}), 400

    user = db.get_user(user_id)
    return jsonify({
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["full_name"],
            "phone": user.get("phone", ""),
        }
    })


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    old_password = data.get("current_password")
    new_password = data.get("new_password")

    success, message = db.change_password(user_id, old_password, new_password)
    if not success:
        return jsonify({"message": message}), 400
    return jsonify({"message": message})
