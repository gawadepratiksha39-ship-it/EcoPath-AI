"""
map_service.py — Routing (OSRM) and route planning within India.

Geocoding is handled by services/geocoder.py unless coordinates are
already provided from autocomplete selection.
"""

from typing import List, Optional, Tuple

import requests

from services.carbon_service import calculate_emissions
from services.geocoder import (
    GeocoderError,
    MSG_INVALID_INDIAN,
    check_route_distance_sanity,
    geocode_location,
    geocode_pair,
    validate_stored_place,
)

OSRM_URL = "https://router.project-osrm.org/route/v1"
USER_AGENT = "EcoPathAI/0.1 (ecopath-ai climate app)"

OSRM_PROFILES = {
    "car": "driving",
    "bus": "driving",
    "train": "driving",
    "bicycle": "cycling",
    "bike": "cycling",
    "walking": "foot",
}

REQUEST_TIMEOUT = 15


class MapServiceError(Exception):
    """Raised when geocoding or routing fails."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _headers() -> dict:
    return {"User-Agent": USER_AGENT}


def _fetch_osrm_route(
    source: dict, destination: dict, profile: str
) -> Tuple[float, float, List]:
    """Fetch route from OSRM. Returns (distance_km, duration_min, geometry)."""
    coords = f"{source['lon']},{source['lat']};{destination['lon']},{destination['lat']}"

    try:
        response = requests.get(
            f"{OSRM_URL}/{profile}/{coords}",
            params={"overview": "full", "geometries": "geojson"},
            headers=_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise MapServiceError(
            f"Routing service unavailable: {exc}", status_code=503
        ) from exc

    if data.get("code") != "Ok" or not data.get("routes"):
        message = data.get("message", "No route found between these locations.")
        raise MapServiceError(message)

    route = data["routes"][0]
    distance_km = round(route["distance"] / 1000, 2)
    duration_min = round(route["duration"] / 60, 1)

    raw_coords = route["geometry"]["coordinates"]
    geometry = [[coord[1], coord[0]] for coord in raw_coords]

    return distance_km, duration_min, geometry


def _resolve_place(
    text: str,
    stored: Optional[dict],
) -> dict:
    """Use stored coordinates when available; otherwise geocode in India."""
    if stored and stored.get("lat") is not None and stored.get("lon") is not None:
        try:
            return validate_stored_place(stored)
        except GeocoderError as exc:
            raise MapServiceError(exc.message, status_code=exc.status_code) from exc
    return None


def plan_route(
    source: str,
    destination: str,
    transport_mode: str = "car",
    source_place: Optional[dict] = None,
    dest_place: Optional[dict] = None,
    country_code: str = None,
    country_name: str = None,
) -> dict:
    """
    Plan a route between two Indian locations.

    If source_place / dest_place include lat/lon from autocomplete,
    geocoding is skipped for those points.
    """
    source = (source or "").strip()
    destination = (destination or "").strip()
    transport_mode = (transport_mode or "car").lower()

    if not source or not destination:
        raise MapServiceError(MSG_INVALID_INDIAN)

    if source.lower() == destination.lower():
        raise MapServiceError("Source and destination must be different.")

    profile = OSRM_PROFILES.get(transport_mode)
    if not profile:
        raise MapServiceError(f"Unsupported transport mode: {transport_mode}")

    try:
        source_coords = _resolve_place(source, source_place)
        dest_coords = _resolve_place(destination, dest_place)

        if source_coords and dest_coords:
            pass
        elif source_coords:
            dest_coords = geocode_location(destination)
        elif dest_coords:
            source_coords = geocode_location(source)
        else:
            source_coords, dest_coords = geocode_pair(source, destination)
    except GeocoderError as exc:
        raise MapServiceError(exc.message, status_code=exc.status_code) from exc

    distance_km, duration_min, geometry = _fetch_osrm_route(
        source_coords, dest_coords, profile
    )

    try:
        check_route_distance_sanity(distance_km, transport_mode)
    except GeocoderError as exc:
        raise MapServiceError(exc.message, status_code=exc.status_code) from exc

    carbon_kg = calculate_emissions(distance_km, transport_mode)

    print(
        f"[Route] {source_coords.get('short_name', source_coords['display_name'])} -> "
        f"{dest_coords.get('short_name', dest_coords['display_name'])} | "
        f"{distance_km} km | {duration_min} min | {carbon_kg} kg CO2 | mode={transport_mode}"
    )

    return {
        "source": source_coords,
        "destination": dest_coords,
        "transport_mode": transport_mode,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "carbon_kg": carbon_kg,
        "geometry": geometry,
    }
