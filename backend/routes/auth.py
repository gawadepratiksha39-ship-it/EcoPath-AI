"""
auth.py — Registration, login, and profile API routes.
"""

from flask import Blueprint, jsonify, request

from services.auth_service import (
    AuthError,
    get_current_user_id,
    get_user_stats,
    login_user,
    register_user,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    try:
        result = register_user(
            data.get("name", ""),
            data.get("email", ""),
            data.get("password", ""),
        )
        return jsonify(result), 201
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    try:
        result = login_user(data.get("email", ""), data.get("password", ""))
        return jsonify(result), 200
    except AuthError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated."}), 401

    from models.database import get_db_connection

    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found."}), 404

    stats = get_user_stats(user_id)
    return jsonify({
        "user": dict(row),
        "stats": stats,
    }), 200
