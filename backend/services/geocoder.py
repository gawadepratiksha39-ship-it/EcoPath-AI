"""
geocoder.py — Robust Nominatim geocoding with validation and fallbacks.

Resolves place names to coordinates using structured Nominatim queries,
country-aware fallbacks, coordinate validation, and pair sanity checks.

Configure optional regional bias via environment variables:
  GEOCODE_DEFAULT_COUNTRY_CODE=in   (ISO 3166-1 alpha-2 for countrycodes param)
  GEOCODE_DEFAULT_COUNTRY_NAME=India  (appended on fallback query)
"""

import logging
import math
import os
import time
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "EcoPathAI/0.1 (ecopath-ai climate app)"
REQUEST_TIMEOUT = 15
NOMINATIM_DELAY = 1.1  # Nominatim usage policy: max 1 req/sec

# India-only platform
INDIA_COUNTRY_CODE = "in"
INDIA_COUNTRY_NAME = "India"
INDIA_LAT_MIN, INDIA_LAT_MAX = 6.5, 37.5
INDIA_LON_MIN, INDIA_LON_MAX = 68.0, 97.5
MAX_INDIA_ROUTE_KM = 3500
MSG_INVALID_INDIAN = "Please enter a valid Indian location."
MSG_LOCATIONS_INCORRECT = "Locations seem incorrect."

# Major Indian cities for reliable prefix autocomplete (name, state, lat, lon)
MAJOR_INDIAN_CITIES: List[Tuple[str, str, float, float]] = [
    ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    ("Delhi", "Delhi", 28.6139, 77.2090),
    ("New Delhi", "Delhi", 28.6139, 77.2090),
    ("Bengaluru", "Karnataka", 12.9716, 77.5946),
    ("Bangalore", "Karnataka", 12.9716, 77.5946),
    ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Kolkata", "West Bengal", 22.5726, 88.3639),
    ("Pune", "Maharashtra", 18.5204, 73.8567),
    ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("Surat", "Gujarat", 21.1702, 72.8311),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Kanpur", "Uttar Pradesh", 26.4499, 80.3319),
    ("Nagpur", "Maharashtra", 21.1458, 79.0882),
    ("Indore", "Madhya Pradesh", 22.7196, 75.8577),
    ("Thane", "Maharashtra", 19.2183, 72.9781),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    ("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185),
    ("Patna", "Bihar", 25.5941, 85.1376),
    ("Vadodara", "Gujarat", 22.3072, 73.1812),
    ("Ghaziabad", "Uttar Pradesh", 28.6692, 77.4538),
    ("Ludhiana", "Punjab", 30.9010, 75.8573),
    ("Agra", "Uttar Pradesh", 27.1767, 78.0081),
    ("Nashik", "Maharashtra", 19.9975, 73.7898),
    ("Goa", "Goa", 15.2993, 74.1240),
    ("Panaji", "Goa", 15.4909, 73.8278),
    ("Kochi", "Kerala", 9.9312, 76.2673),
    ("Coimbatore", "Tamil Nadu", 11.0168, 76.9558),
    ("Chandigarh", "Chandigarh", 30.7333, 76.7794),
    ("Guwahati", "Assam", 26.1445, 91.7362),
    ("Varanasi", "Uttar Pradesh", 25.3176, 82.9739),
    ("Amritsar", "Punjab", 31.6340, 74.8723),
    ("Srinagar", "Jammu and Kashmir", 34.0837, 74.7973),
    ("Mysuru", "Karnataka", 12.2958, 76.6394),
    ("Mysore", "Karnataka", 12.2958, 76.6394),
    ("Kolhapur", "Maharashtra", 16.7050, 74.2433),
    ("Sawantwadi", "Maharashtra", 15.9050, 73.8200),
    ("Mapusa", "Goa", 15.5900, 73.8100),
    ("Margao", "Goa", 15.2832, 73.9581),
]

DEFAULT_COUNTRY_CODE = INDIA_COUNTRY_CODE
DEFAULT_COUNTRY_NAME = INDIA_COUNTRY_NAME

# Country name → ISO 3166-1 alpha-2 (for countrycodes param)
COUNTRY_NAME_TO_ISO: Dict[str, str] = {
    "india": "in",
    "united states": "us",
    "usa": "us",
    "us": "us",
    "united kingdom": "gb",
    "uk": "gb",
    "england": "gb",
    "france": "fr",
    "germany": "de",
    "spain": "es",
    "italy": "it",
    "canada": "ca",
    "australia": "au",
    "japan": "jp",
    "china": "cn",
    "brazil": "br",
    "mexico": "mx",
    "netherlands": "nl",
    "belgium": "be",
    "switzerland": "ch",
    "sweden": "se",
    "norway": "no",
    "poland": "pl",
    "russia": "ru",
    "south africa": "za",
    "uae": "ae",
    "united arab emirates": "ae",
    "singapore": "sg",
    "pakistan": "pk",
    "bangladesh": "bd",
    "indonesia": "id",
    "thailand": "th",
    "vietnam": "vn",
    "south korea": "kr",
    "new zealand": "nz",
    "ireland": "ie",
    "portugal": "pt",
    "austria": "at",
    "greece": "gr",
    "turkey": "tr",
    "argentina": "ar",
    "philippines": "ph",
    "malaysia": "my",
    "saudi arabia": "sa",
    "israel": "il",
    "kenya": "ke",
    "nigeria": "ng",
    "egypt": "eg",
}

_last_nominatim_call = 0.0

# Structured place types we trust
PREFERRED_ADDRESSTYPES = {
    "city",
    "town",
    "village",
    "hamlet",
    "suburb",
    "municipality",
    "county",
    "state",
    "administrative",
    "locality",
    "neighbourhood",
    "residential",
}

WATER_CLASSES = {"natural", "waterway", "water"}
WATER_TYPES = {
    "ocean",
    "sea",
    "water",
    "bay",
    "strait",
    "channel",
    "reef",
    "lagoon",
    "reservoir",
    "dock",
}

ADDRESS_KEYS = ("city", "town", "village", "hamlet", "suburb", "state", "country")

# ISO country code → continent (for pair validation)
COUNTRY_CONTINENT: Dict[str, str] = {
    "in": "asia",
    "cn": "asia",
    "jp": "asia",
    "kr": "asia",
    "pk": "asia",
    "bd": "asia",
    "np": "asia",
    "lk": "asia",
    "th": "asia",
    "vn": "asia",
    "id": "asia",
    "my": "asia",
    "sg": "asia",
    "ph": "asia",
    "ae": "asia",
    "sa": "asia",
    "il": "asia",
    "tr": "asia",
    "ru": "europe_asia",
    "us": "north_america",
    "ca": "north_america",
    "mx": "north_america",
    "gb": "europe",
    "de": "europe",
    "fr": "europe",
    "it": "europe",
    "es": "europe",
    "pt": "europe",
    "nl": "europe",
    "be": "europe",
    "ch": "europe",
    "at": "europe",
    "pl": "europe",
    "se": "europe",
    "no": "europe",
    "dk": "europe",
    "fi": "europe",
    "ie": "europe",
    "gr": "europe",
    "au": "oceania",
    "nz": "oceania",
    "br": "south_america",
    "ar": "south_america",
    "cl": "south_america",
    "co": "south_america",
    "za": "africa",
    "ng": "africa",
    "eg": "africa",
    "ke": "africa",
}

MAX_PAIR_DISTANCE_RETRY_KM = MAX_INDIA_ROUTE_KM
SANITY_MODES = {"car", "bus", "bicycle", "bike", "train", "walking"}


class GeocoderError(Exception):
    """Raised when geocoding fails validation or lookup."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _headers() -> dict:
    return {"User-Agent": USER_AGENT}


def is_within_india_bounds(lat: float, lon: float) -> bool:
    """True if coordinates fall inside India's approximate bounding box."""
    return (
        INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX
        and INDIA_LON_MIN <= lon <= INDIA_LON_MAX
    )


def _reject_non_india_input(query: str) -> None:
    """Reject queries that explicitly name a country other than India."""
    parsed = parse_location_input(query)
    if not parsed["has_country"]:
        return
    country = parsed["country"].lower()
    if country in ("india", "in", "bharat", "hindustan"):
        return
    iso = country_name_to_iso(parsed["country"])
    if iso and iso != INDIA_COUNTRY_CODE:
        raise GeocoderError(MSG_INVALID_INDIAN)
    if iso is None and "india" not in country:
        raise GeocoderError(MSG_INVALID_INDIAN)


def _is_indian_result(result: dict) -> bool:
    """Validate Nominatim result is in India with in-bounds coordinates."""
    address = result.get("address") or {}
    code = (address.get("country_code") or "").lower()
    if code != INDIA_COUNTRY_CODE:
        return False
    lat = float(result.get("lat", 0))
    lon = float(result.get("lon", 0))
    return is_within_india_bounds(lat, lon)


def format_short_display_name(result: dict) -> str:
    """
    Short label without country: e.g. 'Mumbai, Maharashtra' or 'Panaji, Goa'.
    """
    address = result.get("address") or {}
    parts: List[str] = []
    for key in ("city", "town", "village", "hamlet", "suburb"):
        val = address.get(key)
        if val and val not in parts:
            parts.append(val)
    state = address.get("state")
    if state and state not in parts:
        parts.append(state)
    if not parts and state:
        parts.append(state)
    if parts:
        return ", ".join(parts)
    display = result.get("display_name", "")
    return display.replace(", India", "").strip()


def place_from_coords(
    lat: float,
    lon: float,
    display_name: str,
    short_name: str = "",
    original_query: str = "",
) -> dict:
    """Build a place dict from stored coordinates (skip re-geocoding)."""
    if not is_within_india_bounds(lat, lon):
        raise GeocoderError(MSG_INVALID_INDIAN)
    return {
        "name": original_query or display_name,
        "lat": float(lat),
        "lon": float(lon),
        "display_name": display_name,
        "short_name": short_name or display_name,
        "country": INDIA_COUNTRY_NAME,
        "country_code": INDIA_COUNTRY_CODE,
        "continent": "asia",
    }


def validate_stored_place(place: dict) -> dict:
    """Validate a client-supplied place payload before routing."""
    if not place:
        raise GeocoderError(MSG_INVALID_INDIAN)
    lat = place.get("lat")
    lon = place.get("lon")
    if lat is None or lon is None:
        raise GeocoderError(MSG_INVALID_INDIAN)
    if (place.get("country_code") or INDIA_COUNTRY_CODE).lower() != INDIA_COUNTRY_CODE:
        raise GeocoderError(MSG_INVALID_INDIAN)
    return place_from_coords(
        lat,
        lon,
        place.get("display_name") or place.get("short_name") or "",
        place.get("short_name") or "",
        place.get("name") or "",
    )


def country_name_to_iso(name: Optional[str]) -> Optional[str]:
    """Convert a country name or 2-letter code to ISO alpha-2."""
    if not name:
        return None
    key = name.strip().lower()
    if len(key) == 2 and key.isalpha():
        return key
    return COUNTRY_NAME_TO_ISO.get(key)


def parse_location_input(text: str) -> dict:
    """
    Parse user input into structured parts.

    "Mumbai, India"       → city, country
    "Austin, Texas, USA"  → city, state, country
    "London"              → city only
    """
    text = (text or "").strip()
    parts = [p.strip() for p in text.split(",") if p.strip()]

    if len(parts) >= 3:
        return {
            "original": text,
            "city": parts[0],
            "state": ", ".join(parts[1:-1]),
            "country": parts[-1],
            "has_country": True,
        }
    if len(parts) == 2:
        return {
            "original": text,
            "city": parts[0],
            "state": None,
            "country": parts[1],
            "has_country": True,
        }
    return {
        "original": text,
        "city": text,
        "state": None,
        "country": None,
        "has_country": False,
    }


def _has_country_hint(query: str) -> bool:
    return parse_location_input(query)["has_country"]


def _primary_name(query: str) -> str:
    return parse_location_input(query)["city"]


def _rate_limit() -> None:
    """Enforce Nominatim 1 req/sec policy across all calls."""
    global _last_nominatim_call
    elapsed = time.time() - _last_nominatim_call
    if elapsed < NOMINATIM_DELAY:
        time.sleep(NOMINATIM_DELAY - elapsed)
    _last_nominatim_call = time.time()


def _nominatim_search(params: dict) -> List[dict]:
    """Execute a Nominatim search with required parameters."""
    _rate_limit()

    search_params = {
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "countrycodes": INDIA_COUNTRY_CODE,
        **params,
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=search_params,
            headers=_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status == 429:
            raise GeocoderError(
                "Location search is busy. Please wait a moment and try again.",
                status_code=503,
            ) from exc
        raise GeocoderError(
            f"Geocoding service unavailable: {exc}", status_code=503
        ) from exc


def _is_water_or_ocean(result: dict) -> bool:
    """Detect ocean, sea, or other water features."""
    osm_class = (result.get("class") or "").lower()
    osm_type = (result.get("type") or "").lower()
    addresstype = (result.get("addresstype") or "").lower()

    if osm_type in WATER_TYPES or addresstype in WATER_TYPES:
        return True
    if osm_class in WATER_CLASSES and osm_type in WATER_TYPES:
        return True
    if osm_class == "natural" and osm_type == "water":
        return True
    return False


def _has_structured_place(result: dict) -> bool:
    """Prefer results with city/town/village/state/country in address."""
    address = result.get("address") or {}
    addresstype = (result.get("addresstype") or "").lower()

    if addresstype in PREFERRED_ADDRESSTYPES:
        return True
    if any(key in address for key in ("city", "town", "village", "hamlet")):
        return True
    if "state" in address and "country" in address:
        return True
    return False


def _place_names_from_result(result: dict) -> List[str]:
    """Collect place names from a Nominatim result (city, town, village, state, etc.)."""
    address = result.get("address") or {}
    names: List[str] = []
    for key in (
        "city", "town", "village", "hamlet", "municipality", "suburb",
        "county", "state_district", "state", "district",
    ):
        val = address.get(key)
        if val:
            names.append(val.lower())
    display_first = (result.get("display_name") or "").split(",")[0].strip().lower()
    if display_first:
        names.append(display_first)
    return names


def _matches_query_intent(query: str, result: dict) -> bool:
    """
    Ensure the geocoded place matches user input (flexible for partial names).
    """
    parsed = parse_location_input(query)
    primary = parsed["city"].lower().strip()
    if not primary:
        return False

    address = result.get("address") or {}

    if parsed["has_country"]:
        result_country = (address.get("country") or "").lower()
        expected = parsed["country"].lower()
        country_ok = (
            expected in result_country
            or result_country in expected
            or country_name_to_iso(expected) == (address.get("country_code") or "").lower()
        )
        if country_ok:
            return True

    for name in _place_names_from_result(result):
        if primary == name or primary in name or name in primary:
            return True
        if name.startswith(primary) or primary.startswith(name):
            return True

    display = (result.get("display_name") or "").lower()
    if primary in display:
        return True

    return False


def _score_geocode_match(query: str, result: dict) -> float:
    """Rank Nominatim candidates — higher is a better match."""
    primary = _primary_name(query).lower()
    score = float(result.get("importance", 0)) * 10

    if _matches_query_intent(query, result):
        score += 50

    for name in _place_names_from_result(result):
        if name == primary:
            score += 30
        elif name.startswith(primary) or primary.startswith(name):
            score += 20
        elif primary in name or name in primary:
            score += 10

    return score


def _nominatim_search_ranked(query: str, limit: int = 5) -> Optional[dict]:
    """Search Nominatim and return the best-ranked Indian match."""
    _rate_limit()
    search_params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
        "countrycodes": INDIA_COUNTRY_CODE,
    }
    try:
        response = requests.get(
            NOMINATIM_URL,
            params=search_params,
            headers=_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
    except requests.RequestException:
        return None

    ranked: List[tuple] = []
    for raw in results:
        if not raw:
            continue
        if _is_water_or_ocean(raw):
            continue
        if not _has_structured_place(raw):
            continue
        if not _is_indian_result(raw):
            continue
        match_score = _score_geocode_match(query, raw)
        if match_score >= 10:
            ranked.append((match_score, raw))

    if not ranked:
        return None

    ranked.sort(key=lambda x: x[0], reverse=True)
    return _parse_result(ranked[0][1], query, "ranked")


def _is_valid_result(result: dict, query: str = "") -> bool:
    """Validate a single Nominatim result."""
    if not result:
        return False
    if _is_water_or_ocean(result):
        return False

    lat = float(result.get("lat", 0))
    lon = float(result.get("lon", 0))

    if abs(lat) < 0.01 and abs(lon) < 0.01:
        return False
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return False

    if not _has_structured_place(result):
        return False

    if query and not _matches_query_intent(query, result):
        return False

    if not _is_indian_result(result):
        return False

    return True


def _format_display_name(result: dict) -> str:
    """Build a clean display name from structured address fields."""
    address = result.get("address") or {}
    parts: List[str] = []

    for key in ADDRESS_KEYS:
        value = address.get(key)
        if value and value not in parts:
            parts.append(value)

    if parts:
        return ", ".join(parts)
    return result.get("display_name", "Unknown location")


def _parse_result(raw: dict, original_query: str, query_used: str = "") -> dict:
    """Normalize a Nominatim result into our geocode payload."""
    address = raw.get("address") or {}
    return {
        "name": original_query,
        "lat": float(raw["lat"]),
        "lon": float(raw["lon"]),
        "display_name": _format_display_name(raw),
        "short_name": format_short_display_name(raw),
        "country": address.get("country", INDIA_COUNTRY_NAME),
        "country_code": (address.get("country_code") or INDIA_COUNTRY_CODE).lower(),
        "continent": _continent_for_result(raw),
        "addresstype": raw.get("addresstype", ""),
        "osm_type": raw.get("type", ""),
        "importance": float(raw.get("importance", 0)),
        "query_used": query_used,
    }


def _continent_for_result(result: dict) -> str:
    address = result.get("address") or {}
    code = (address.get("country_code") or "").lower()
    return COUNTRY_CONTINENT.get(code, "unknown")


def _log_resolved(label: str, place: dict) -> None:
    """Debug output for resolved geocoding."""
    msg = (
        f"[Geocoder] {label}: input={place.get('name', '?')!r} -> "
        f'resolved="{place["display_name"]}" '
        f"coords=({place['lat']:.5f}, {place['lon']:.5f}) "
        f"country={place.get('country') or '?'} "
        f"[{place.get('country_code', '?')} / {place.get('continent', '?')}] "
        f"query={place.get('query_used', '?')!r}"
    )
    logger.info(msg)
    print(msg)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in km."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _continents_compatible(a: dict, b: dict) -> bool:
    """Check if two places are on compatible continents."""
    ca, cb = a.get("continent"), b.get("continent")
    if ca == "unknown" or cb == "unknown":
        return True
    if ca == cb:
        return True
    # Russia spans Europe/Asia — allow cross with asia/europe
    cross_ok = {("europe", "asia"), ("asia", "europe"), ("europe", "europe_asia"),
                ("europe_asia", "europe"), ("europe_asia", "asia"), ("asia", "europe_asia")}
    return (ca, cb) in cross_ok or (cb, ca) in cross_ok


def _pair_needs_retry(
    source: dict,
    destination: dict,
    source_had_country: bool,
    dest_had_country: bool,
) -> bool:
    """Decide if geocoding pair should be retried with country bias."""
    dist = haversine_km(source["lat"], source["lon"], destination["lat"], destination["lon"])

    if dist > MAX_PAIR_DISTANCE_RETRY_KM and not (source_had_country and dest_had_country):
        return True

    if not _continents_compatible(source, destination):
        if not source_had_country or not dest_had_country:
            return True

    return False


def _structured_search(
    city: str,
    state: Optional[str] = None,
    country: Optional[str] = None,
    country_code: Optional[str] = None,
    label: str = "",
) -> Optional[dict]:
    """Structured Nominatim search preferring city/town/village/hamlet fields."""
    for place_key in ("city", "town", "village", "hamlet", "municipality"):
        params: dict = {place_key: city}
        if state:
            params["state"] = state
        if country:
            params["country"] = country
        if country_code:
            params["countrycodes"] = country_code

        results = _nominatim_search(params)
        if results and _is_valid_result(results[0], city):
            return _parse_result(results[0], city, label or f"structured:{place_key}")

    return None


def _geocode_known_place(query: str) -> Optional[dict]:
    """Instant geocode for curated Indian places (no API call)."""
    q = _primary_name(query).strip().lower()
    for name, state, lat, lon in MAJOR_INDIAN_CITIES:
        if name.lower() == q:
            short = f"{name}, {state}"
            place = place_from_coords(lat, lon, f"{short}, India", short, query)
            place["query_used"] = "known_place"
            return place
    return None


def _run_query_strategies(
    query: str,
    country_code: Optional[str],
    country_name: Optional[str],
) -> Optional[dict]:
    """
    Fallback geocoding:
      1. Structured city/town/village (when country is in input or as hint)
      2. Free-text city name (with countrycodes if available)
      3. "City, Country" text fallback
    """
    query = query.strip()
    parsed = parse_location_input(query)
    has_country = parsed["has_country"]
    primary = parsed["city"]
    cc = country_code or (country_name_to_iso(parsed["country"]) if parsed["country"] else None)

    known = _geocode_known_place(query)
    if known:
        return known

    strategies: List[Tuple[str, dict]] = []

    # Ranked multi-result search (best for towns, villages, landmarks)
    ranked = _nominatim_search_ranked(primary if not has_country else query)
    if ranked:
        ranked["name"] = query
        return ranked

    # Always try "Place, India" for bare names
    if not has_country:
        ranked_india = _nominatim_search_ranked(f"{primary}, India")
        if ranked_india:
            ranked_india["name"] = query
            return ranked_india

    # Structured search when country is in user input
    if has_country:
        strategies.append((
            f"structured:{primary},{parsed['country']}",
            {"_structured": True, "city": primary, "state": parsed.get("state"),
             "country": parsed["country"], "country_code": cc},
        ))
        strategies.append((f"text:{query}", {"q": query}))

    # Query 1: bare city name, optionally biased with countrycodes
    params1: dict = {"q": primary}
    if cc and not has_country:
        params1["countrycodes"] = cc
    strategies.append((f"text:{primary}", params1))

    # Query 2: structured + text with country hint
    if country_name and not has_country:
        strategies.append((
            f"structured:{primary},{country_name}",
            {"_structured": True, "city": primary, "country": country_name,
             "country_code": country_code or country_name_to_iso(country_name)},
        ))
        strategies.append((f"text:{primary},{country_name}", {"q": f"{primary}, {country_name}"}))
        hint_cc = country_code or country_name_to_iso(country_name)
        if hint_cc:
            strategies.append((
                f"text+cc:{primary},{country_name}",
                {"q": f"{primary}, {country_name}", "countrycodes": hint_cc},
            ))

    seen: set = set()
    for label, params in strategies:
        if params.get("_structured"):
            key = ("structured", primary, parsed.get("state"), params.get("country"), cc)
            if key in seen:
                continue
            seen.add(key)
            result = _structured_search(
                city=primary,
                state=params.get("state"),
                country=params.get("country"),
                country_code=params.get("country_code"),
                label=label,
            )
            if result:
                result["name"] = query
                result["query_used"] = label
                return result
            continue

        key = tuple(sorted((k, str(v)) for k, v in params.items()))
        if key in seen:
            continue
        seen.add(key)

        results = _nominatim_search(params)
        if results and _is_valid_result(results[0], query):
            return _parse_result(results[0], query, label)

    return None


def geocode_location(
    query: str,
    country_code: Optional[str] = None,
    country_name: Optional[str] = None,
) -> dict:
    """
    Geocode a single place name with fallback strategies.

    Args:
        query: User-entered location (e.g. "Mumbai" or "Paris, France").
        country_code: Optional ISO country code bias (e.g. "in").
        country_name: Optional country name for fallback query (e.g. "India").

    Returns:
        Dict with lat, lon, display_name, country_code, continent.
    """
    query = (query or "").strip()
    if not query:
        raise GeocoderError(MSG_INVALID_INDIAN)

    _reject_non_india_input(query)

    cc = INDIA_COUNTRY_CODE
    cn = INDIA_COUNTRY_NAME

    result = _run_query_strategies(query, cc, cn)
    if result:
        return result

    raise GeocoderError(MSG_INVALID_INDIAN)


def geocode_pair(
    source: str,
    destination: str,
    country_code: Optional[str] = None,
    country_name: Optional[str] = None,
) -> Tuple[dict, dict]:
    """
    Geocode source and destination with cross-validation and retry.

    Uses resolved source country to narrow ambiguous destination (and vice versa).
    Retries when results are on wrong continents or implausibly far apart.
    """
    cc = country_code or country_name_to_iso(country_name) or DEFAULT_COUNTRY_CODE or None
    cn = country_name or DEFAULT_COUNTRY_NAME or None

    source_parsed = parse_location_input(source)
    dest_parsed = parse_location_input(destination)

    if source_parsed["original"].lower() == dest_parsed["original"].lower():
        raise GeocoderError("Source and destination must be different.")

    # Geocode source with input country or API/env hints
    src_cc = country_name_to_iso(source_parsed["country"]) if source_parsed["country"] else cc
    src_cn = source_parsed["country"] or cn
    source_place = geocode_location(source, src_cc, src_cn)

    # Cross-hint: use resolved source country for ambiguous destination
    dest_cc = (
        country_name_to_iso(dest_parsed["country"])
        if dest_parsed["country"]
        else source_place.get("country_code") or cc
    )
    dest_cn = dest_parsed["country"] or source_place.get("country") or cn
    dest_place = geocode_location(destination, dest_cc, dest_cn)

    source_had = source_parsed["has_country"]
    dest_had = dest_parsed["has_country"]

    if _pair_needs_retry(source_place, dest_place, source_had, dest_had):
        print("[Geocoder] Pair validation failed - retrying with enhanced queries")

        retry_cn = cn or source_place.get("country") or dest_place.get("country")
        retry_cc = cc or source_place.get("country_code") or dest_place.get("country_code")

        if not source_had and retry_cn:
            source_place = geocode_location(
                f"{source_parsed['city']}, {retry_cn}", retry_cc, retry_cn
            )
        if not dest_had and retry_cn:
            dest_place = geocode_location(
                f"{dest_parsed['city']}, {retry_cn}", retry_cc, retry_cn
            )

        # Cross-retry: destination using source's resolved country
        if not dest_had and source_place.get("country"):
            dest_place = geocode_location(
                destination,
                source_place["country_code"],
                source_place["country"],
            )

        dist = haversine_km(
            source_place["lat"], source_place["lon"],
            dest_place["lat"], dest_place["lon"],
        )

        if dist > MAX_PAIR_DISTANCE_RETRY_KM:
            raise GeocoderError(MSG_LOCATIONS_INCORRECT)

        if not _continents_compatible(source_place, dest_place) and not (
            source_had and dest_had
        ):
            raise GeocoderError(MSG_LOCATIONS_INCORRECT)

    _validate_pair_intent(source, destination, source_place, dest_place)

    _log_resolved("Source", source_place)
    _log_resolved("Destination", dest_place)

    return source_place, dest_place


def _validate_pair_intent(
    source_q: str,
    dest_q: str,
    source_place: dict,
    dest_place: dict,
) -> None:
    """
    Reject pairs where different city names resolved suspiciously close
    (e.g. Paris + Tokyo both mapped to Paris).
    """
    s_city = parse_location_input(source_q)["city"].lower()
    d_city = parse_location_input(dest_q)["city"].lower()

    if s_city == d_city:
        return

    dist = haversine_km(
        source_place["lat"], source_place["lon"],
        dest_place["lat"], dest_place["lon"],
    )

    if dist < 80:
        s_ok = s_city in source_place["display_name"].lower()
        d_ok = d_city in dest_place["display_name"].lower()
        if not s_ok or not d_ok:
            raise GeocoderError(MSG_LOCATIONS_INCORRECT)


def _suggest_matches_query(query: str, result: dict) -> bool:
    """Loose prefix match for autocomplete (e.g. 'Mum' matches Mumbai)."""
    q = query.lower().strip()
    for name in _place_names_from_result(result):
        if name.startswith(q) or q in name:
            return True
    first_part = (result.get("display_name") or "").split(",")[0].strip().lower()
    return first_part.startswith(q) or q in first_part


def _major_city_suggestions(query: str) -> List[dict]:
    """Prefix-match against curated major Indian cities."""
    q = query.lower().strip()
    matches: List[dict] = []
    seen: set = set()

    for name, state, lat, lon in MAJOR_INDIAN_CITIES:
        if not name.lower().startswith(q):
            continue
        key = (round(lat, 3), round(lon, 3))
        if key in seen:
            continue
        seen.add(key)
        short = f"{name}, {state}"
        matches.append({
            "label": short,
            "display_name": f"{short}, India",
            "short_name": short,
            "lat": lat,
            "lon": lon,
            "country_code": INDIA_COUNTRY_CODE,
            "_priority": 2.0,
        })

    return matches


def suggest_places(query: str, limit: int = 5) -> List[dict]:
    """
    Autocomplete Indian cities via major-city list + Nominatim (countrycodes=in).
    """
    query = (query or "").strip()
    if len(query) < 2:
        return []

    seen_coords: set = set()
    ranked: List[tuple] = []

    for item in _major_city_suggestions(query):
        coord_key = (round(item["lat"], 4), round(item["lon"], 4))
        seen_coords.add(coord_key)
        ranked.append((item.pop("_priority", 2.0), item))

    search_terms = [query]
    if not _has_country_hint(query):
        search_terms.append(f"{query}, India")

    for term in search_terms:
        _rate_limit()
        results = _nominatim_search({"q": term, "limit": 10})
        for raw in results:
            if not _is_indian_result(raw):
                continue
            if not _has_structured_place(raw):
                continue
            if not _suggest_matches_query(query, raw):
                continue

            coord_key = (round(float(raw["lat"]), 4), round(float(raw["lon"]), 4))
            if coord_key in seen_coords:
                continue
            seen_coords.add(coord_key)

            importance = float(raw.get("importance", 0))
            parsed = _parse_result(raw, query, f"suggest:{term}")
            item = {
                "label": parsed["short_name"],
                "display_name": parsed["display_name"],
                "short_name": parsed["short_name"],
                "lat": parsed["lat"],
                "lon": parsed["lon"],
                "country_code": parsed["country_code"],
            }
            ranked.append((importance, item))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in ranked[:limit]]


# Alias for callers expecting geocode_place
geocode_place = geocode_location


def check_route_distance_sanity(distance_km: float, transport_mode: str) -> None:
    """Reject routes that exceed reasonable distance within India."""
    if distance_km > MAX_INDIA_ROUTE_KM:
        raise GeocoderError(MSG_LOCATIONS_INCORRECT)
