"""
ai.py — AI sustainability insights API routes.
"""

from flask import Blueprint, jsonify, request

from services.auth_service import get_current_user_id
from services.ai_service import analyze_route, get_personalized_insights

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.route("/analyze", methods=["POST"])
def analyze_trip():
    """
    Analyze a route and return AI eco insights.

    Body: { distance_km, transport_mode, carbon_kg, ... }
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Please log in to access AI insights."}), 401

    data = request.get_json(silent=True) or {}
    if not data.get("distance_km"):
        return jsonify({"error": "Route data is required."}), 400

    insights = analyze_route(data, user_id)
    return jsonify(insights), 200


@ai_bp.route("/insights", methods=["GET"])
def user_insights():
    """Personalized sustainability insights from trip history."""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Please log in to view insights."}), 401

    insights = get_personalized_insights(user_id)
    return jsonify(insights), 200
