"""
carbon_service.py — CO₂ emission calculations for travel routes.

Uses per-mode emission factors (kg CO₂ per km) to estimate footprint.
"""

# kg CO₂ per kilometer by transport mode
EMISSION_FACTORS = {
    "car": 0.21,
    "bus": 0.10,
    "bicycle": 0.0,
    "bike": 0.0,
    "walking": 0.0,
    "train": 0.05,  # rail; OSRM uses road distance as approximation
}

MODE_LABELS = {
    "car": "Car",
    "bus": "Bus",
    "train": "Train",
    "bicycle": "Bicycle",
    "bike": "Bicycle",
    "walking": "Walking",
}


def calculate_emissions(distance_km: float, transport_mode: str) -> float:
    """
    Calculate estimated CO₂ emissions in kg for a given distance and mode.

    Args:
        distance_km: Route distance in kilometers.
        transport_mode: One of car, bus, train, bicycle, walking.

    Returns:
        Carbon footprint in kg CO₂ (rounded to 2 decimal places).
    """
    factor = EMISSION_FACTORS.get(transport_mode.lower(), EMISSION_FACTORS["car"])
    return round(distance_km * factor, 2)
