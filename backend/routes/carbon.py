"""
carbon.py — Carbon footprint API routes (per-user history).
"""

from flask import Blueprint, jsonify

from models.database import get_db_connection
from services.auth_service import get_current_user_id, get_user_stats

carbon_bp = Blueprint("carbon", __name__, url_prefix="/api/carbon")


@carbon_bp.route("/history", methods=["GET"])
def get_history():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Please log in to view history."}), 401

    try:
        conn = get_db_connection()
        rows = conn.execute(
            """
            SELECT id, source, destination, distance_km, carbon_kg,
                   transport_mode, created_at
            FROM carbon_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (user_id,),
        ).fetchall()
        conn.close()

        records = [dict(row) for row in rows]
        stats = get_user_stats(user_id)
        return jsonify({"records": records, "stats": stats}), 200

    except Exception:
        return jsonify({"error": "Failed to load history."}), 500
