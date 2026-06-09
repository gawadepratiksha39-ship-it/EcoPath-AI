"""
routes.py — Route planning API endpoints (India only).
"""

from flask import Blueprint, jsonify, request

from models.database import get_db_connection
from services.auth_service import get_current_user_id
from services.geocoder import GeocoderError, suggest_places
from services.ai_service import analyze_route
from services.map_service import MapServiceError, plan_route

routes_bp = Blueprint("routes", __name__, url_prefix="/api/routes")


@routes_bp.route("/suggest", methods=["GET"])
def suggest_locations():
    """
    Autocomplete Indian places while user types.

    Query params:
        q (str): partial place name (min 2 chars)
    """
    query = request.args.get("q", "")
    try:
        suggestions = suggest_places(query)
        return jsonify({"suggestions": suggestions}), 200
    except GeocoderError as exc:
        return jsonify({"error": exc.message, "suggestions": []}), exc.status_code
    except Exception:
        return jsonify({"error": "Suggestion lookup failed.", "suggestions": []}), 500


@routes_bp.route("/plan", methods=["POST"])
def plan_route_endpoint():
    """
    Plan an eco-friendly route between two Indian locations.

    Request body:
        source, destination (str)
        transport_mode (str)
        source_place, destination_place (optional) — pre-resolved from autocomplete:
            { lat, lon, short_name, display_name }
    """
    data = request.get_json(silent=True) or {}
    source = data.get("source", "")
    destination = data.get("destination", "")
    transport_mode = data.get("transport_mode", "car")
    source_place = data.get("source_place") or _place_from_flat(data, "source")
    dest_place = data.get("destination_place") or data.get("dest_place") or _place_from_flat(data, "destination")

    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Please log in to plan routes."}), 401

    try:
        result = plan_route(
            source,
            destination,
            transport_mode,
            source_place=source_place,
            dest_place=dest_place,
        )

        _save_to_history(result, user_id)

        result["ai_insights"] = analyze_route(result, user_id)

        return jsonify(result), 200

    except MapServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except Exception:
        return jsonify({"error": "An unexpected error occurred."}), 500


def _place_from_flat(data: dict, prefix: str):
    """Build place dict from flat lat/lon fields (source_lat, etc.)."""
    lat = data.get(f"{prefix}_lat")
    lon = data.get(f"{prefix}_lon")
    if lat is None or lon is None:
        return None
    return {
        "lat": lat,
        "lon": lon,
        "short_name": data.get(f"{prefix}_short_name") or data.get(f"{prefix}_display_name"),
        "display_name": data.get(f"{prefix}_display_name") or data.get(f"{prefix}_short_name"),
        "name": data.get(prefix, ""),
        "country_code": "in",
    }


def _save_to_history(route_result: dict, user_id: int) -> None:
    """Save completed route to SQLite carbon_history table."""
    try:
        conn = get_db_connection()
        src = route_result["source"].get("short_name") or route_result["source"]["display_name"]
        dst = route_result["destination"].get("short_name") or route_result["destination"]["display_name"]
        conn.execute(
            """
            INSERT INTO carbon_history
                (user_id, source, destination, distance_km, carbon_kg, transport_mode)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                src,
                dst,
                route_result["distance_km"],
                route_result["carbon_kg"],
                route_result["transport_mode"],
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
