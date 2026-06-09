"""
ai_service.py — Rule-based AI sustainability recommendation engine.

Analyzes routes, transport modes, emissions, and trip history to produce
eco scores, mode comparisons, personalized insights, and natural-language
explanations. No external paid APIs required.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from models.database import get_db_connection
from services.carbon_service import EMISSION_FACTORS, MODE_LABELS, calculate_emissions

ALL_MODES = ["car", "bus", "train", "bicycle", "walking"]

# Distance thresholds (km) for mode recommendations
DIST_SHORT = 3
DIST_MEDIUM = 15
DIST_LONG = 100
DIST_VERY_LONG = 300

# Eco score color bands
SCORE_COLORS = [
    (80, "excellent", "#2d6a4f"),
    (60, "good", "#40916c"),
    (40, "fair", "#e9c46a"),
    (0, "poor", "#e76f51"),
]

BADGES = [
    (80, "Green Champion"),
    (60, "Gold"),
    (40, "Silver"),
    (0, "Bronze"),
]


def _mode_label(mode: str) -> str:
    return MODE_LABELS.get(mode.lower(), mode.title())


def calculate_eco_score(distance_km: float, transport_mode: str) -> dict:
    """
    Eco Score 0–100: compares current mode emissions to car baseline.
    Walking/cycling = 100; car = 0 relative scale.
    """
    mode = transport_mode.lower()
    current = calculate_emissions(distance_km, mode)
    car_baseline = calculate_emissions(distance_km, "car")

    if car_baseline <= 0:
        score = 100
    else:
        reduction_ratio = 1 - (current / car_baseline)
        score = int(round(max(0, min(100, reduction_ratio * 100))))

    label, color = "poor", "#e76f51"
    for threshold, lbl, clr in SCORE_COLORS:
        if score >= threshold:
            label, color = lbl, clr
            break

    explanations = {
        "excellent": "Outstanding choice! Your travel mode has minimal climate impact.",
        "good": "Good sustainable choice with significantly lower emissions than driving.",
        "fair": "Moderate impact. Consider greener alternatives for a higher score.",
        "poor": "High-emission mode. Switching to public transit or rail could help a lot.",
    }

    return {
        "score": score,
        "label": label,
        "color": color,
        "explanation": explanations.get(label, ""),
    }


def get_sustainability_badge(avg_eco_score: float) -> str:
    for threshold, name in BADGES:
        if avg_eco_score >= threshold:
            return name
    return "Bronze"


def _feasible_modes(distance_km: float) -> List[str]:
    """Modes that are realistic for a given distance."""
    if distance_km <= DIST_SHORT:
        return ALL_MODES
    if distance_km <= DIST_MEDIUM:
        return ["walking", "bicycle", "bus", "train", "car"]
    if distance_km <= DIST_LONG:
        return ["bus", "train", "car"]
    return ["train", "bus", "car"]


def compare_route_modes(distance_km: float, current_mode: str) -> dict:
    """Compare emissions across all transport modes for the same distance."""
    feasible = _feasible_modes(distance_km)
    comparisons = []
    best_mode = None
    lowest_carbon = float("inf")

    for mode in ALL_MODES:
        carbon = calculate_emissions(distance_km, mode)
        is_feasible = mode in feasible
        if is_feasible and carbon < lowest_carbon:
            lowest_carbon = carbon
            best_mode = mode
        comparisons.append({
            "mode": mode,
            "label": _mode_label(mode),
            "carbon_kg": carbon,
            "is_current": mode == current_mode.lower(),
            "is_feasible": is_feasible,
        })

    for item in comparisons:
        item["is_best"] = item["mode"] == best_mode and item.get("is_feasible", True)
        car_carbon = calculate_emissions(distance_km, "car")
        if car_carbon > 0:
            item["reduction_vs_car_pct"] = round(
                (1 - item["carbon_kg"] / car_carbon) * 100, 1
            )
        else:
            item["reduction_vs_car_pct"] = 100.0

    current_carbon = calculate_emissions(distance_km, current_mode)
    best_carbon = calculate_emissions(distance_km, best_mode)
    savings_kg = round(current_carbon - best_carbon, 2)
    savings_pct = (
        round((1 - best_carbon / current_carbon) * 100, 1)
        if current_carbon > 0 else 0
    )

    return {
        "modes": comparisons,
        "best_mode": best_mode,
        "best_mode_label": _mode_label(best_mode),
        "current_mode": current_mode.lower(),
        "co2_savings_kg": max(0, savings_kg),
        "co2_reduction_pct": max(0, savings_pct),
    }


def _ideal_mode_for_distance(distance_km: float) -> str:
    if distance_km <= DIST_SHORT:
        return "walking"
    if distance_km <= DIST_MEDIUM:
        return "bicycle"
    if distance_km <= DIST_LONG:
        return "bus"
    if distance_km <= DIST_VERY_LONG:
        return "train"
    return "train"


def _generate_recommendations(
    distance_km: float,
    transport_mode: str,
    carbon_kg: float,
    comparison: dict,
    history: List[dict],
) -> List[dict]:
    """Rule-based recommendation engine."""
    mode = transport_mode.lower()
    ideal = _ideal_mode_for_distance(distance_km)
    recs: List[dict] = []

    def add_rec(title, explanation, priority, alt_mode=None):
        savings_kg = 0.0
        savings_pct = 0.0
        if alt_mode:
            alt_carbon = calculate_emissions(distance_km, alt_mode)
            savings_kg = round(max(0, carbon_kg - alt_carbon), 2)
            if carbon_kg > 0:
                savings_pct = round((1 - alt_carbon / carbon_kg) * 100, 1)
        recs.append({
            "title": title,
            "explanation": explanation,
            "priority": priority,
            "suggested_mode": alt_mode,
            "suggested_mode_label": _mode_label(alt_mode) if alt_mode else None,
            "savings_kg": savings_kg,
            "savings_pct": savings_pct,
        })

    if mode == "car":
        if distance_km > DIST_LONG:
            add_rec(
                "Switch to train for long-distance travel",
                f"For a {distance_km:.0f} km journey, Indian railways produce far less CO₂ per passenger than a private car.",
                "high", "train",
            )
        elif distance_km > DIST_MEDIUM:
            add_rec(
                "Consider bus for medium-distance trips",
                "Inter-city buses in India offer a practical balance of cost and lower emissions compared to driving solo.",
                "high", "bus",
            )
        if distance_km <= DIST_MEDIUM:
            add_rec(
                "Try cycling for this short trip",
                f"At {distance_km:.1f} km, cycling produces zero direct emissions and improves your eco score significantly.",
                "high", "bicycle",
            )
        if distance_km <= DIST_SHORT:
            add_rec(
                "Walking is ideal for very short distances",
                "For trips under 3 km, walking eliminates transport emissions entirely.",
                "high", "walking",
            )

    elif mode == "bus" and distance_km > DIST_VERY_LONG:
        add_rec(
            "Train may be greener for very long routes",
            "For journeys over 300 km, trains typically have lower per-passenger emissions than road buses.",
            "medium", "train",
        )

    elif mode in ("bicycle", "bike", "walking") and distance_km > DIST_LONG:
        add_rec(
            "Consider train for this distance",
            f"At {distance_km:.0f} km, active travel may not be practical. Train is the most sustainable motorized option.",
            "medium", "train",
        )

    if mode != ideal and ideal != mode:
        ideal_label = _mode_label(ideal)
        add_rec(
            f"{ideal_label} is optimal for this distance",
            f"Based on the {distance_km:.1f} km distance, {ideal_label} is the recommended sustainable mode for this trip length.",
            "medium", ideal,
        )

    best = comparison["best_mode"]
    if mode != best:
        best_label = _mode_label(best)
        savings = comparison["co2_savings_kg"]
        pct = comparison["co2_reduction_pct"]
        add_rec(
            f"Switch to {best_label} for maximum savings",
            f"Switching from {_mode_label(mode)} to {best_label} could save {savings:.1f} kg CO₂ ({pct:.0f}% reduction) on this route.",
            "high", best,
        )

    if history:
        modes_used = [r.get("transport_mode", "car") for r in history]
        most_common = Counter(modes_used).most_common(1)[0][0]
        if most_common == "car" and mode == "car":
            add_rec(
                "Break the car habit",
                "Most of your recent trips used a car. Trying bus or train on your next journey could significantly cut your footprint.",
                "medium", "bus",
            )

    if not recs:
        add_rec(
            "Great sustainable choice!",
            f"Your {_mode_label(mode)} trip is already among the best options for this {distance_km:.1f} km route.",
            "low", None,
        )

    return recs[:5]


def _build_explanation(
    distance_km: float,
    transport_mode: str,
    comparison: dict,
    eco_score: dict,
) -> str:
    """Generate a natural-language AI explanation for the trip."""
    mode_label = _mode_label(transport_mode)
    best_label = comparison["best_mode_label"]
    savings_kg = comparison["co2_savings_kg"]
    savings_pct = comparison["co2_reduction_pct"]

    if transport_mode.lower() == comparison["best_mode"]:
        return (
            f"Based on your {distance_km:.0f} km journey by {mode_label}, you are already "
            f"using the most sustainable option available. Your Eco Score of {eco_score['score']}/100 "
            f"reflects excellent climate-conscious travel."
        )

    return (
        f"Based on your {distance_km:.0f} km journey, switching from {mode_label} to {best_label} "
        f"could reduce emissions by {savings_pct:.0f}% and save approximately {savings_kg:.1f} kg of CO₂. "
        f"Your current Eco Score is {eco_score['score']}/100."
    )


def _fetch_user_history(user_id: int, limit: int = 50) -> List[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT distance_km, carbon_kg, transport_mode, created_at
        FROM carbon_history WHERE user_id = ?
        ORDER BY created_at DESC LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def analyze_route(route: dict, user_id: Optional[int] = None) -> dict:
    """
    Full AI analysis for a planned route.
    """
    distance = route.get("distance_km", 0)
    mode = route.get("transport_mode", "car")
    carbon = route.get("carbon_kg", 0)

    history = _fetch_user_history(user_id) if user_id else []
    eco = calculate_eco_score(distance, mode)
    comparison = compare_route_modes(distance, mode)
    recommendations = _generate_recommendations(distance, mode, carbon, comparison, history)
    explanation = _build_explanation(distance, mode, comparison, eco)

    avg_score = eco["score"]
    if history:
        scores = [calculate_eco_score(r["distance_km"], r["transport_mode"])["score"] for r in history]
        avg_score = sum(scores) / len(scores)

    return {
        "eco_score": eco["score"],
        "eco_score_label": eco["label"],
        "eco_score_color": eco["color"],
        "eco_score_explanation": eco["explanation"],
        "badge": get_sustainability_badge(avg_score),
        "recommended_mode": comparison["best_mode"],
        "recommended_mode_label": comparison["best_mode_label"],
        "emissions_saved_kg": comparison["co2_savings_kg"],
        "co2_reduction_pct": comparison["co2_reduction_pct"],
        "explanation": explanation,
        "recommendations": recommendations,
        "route_comparison": comparison["modes"],
    }


def get_personalized_insights(user_id: int) -> dict:
    """Analyze full trip history for dashboard sustainability insights."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT transport_mode, distance_km, carbon_kg, created_at
        FROM carbon_history WHERE user_id = ?
        """,
        (user_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return {
            "total_emissions_saved_kg": 0,
            "most_used_mode": None,
            "most_used_mode_label": "N/A",
            "weekly": {"trips": 0, "carbon_kg": 0, "distance_km": 0, "eco_score": 0},
            "monthly": {"trips": 0, "carbon_kg": 0, "distance_km": 0, "eco_score": 0},
            "overall_eco_score": 0,
            "badge": "Bronze",
            "explanation": "Plan your first route to start receiving personalized sustainability insights.",
            "recommended_mode": "bus",
            "recommended_mode_label": "Bus",
            "emissions_saved_kg": 0,
        }

    records = [dict(r) for r in rows]
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_saved = 0.0
    eco_scores = []
    mode_counts = Counter()

    for r in records:
        dist = r["distance_km"] or 0
        carbon = r["carbon_kg"] or 0
        mode = r.get("transport_mode", "car")
        car_would_be = calculate_emissions(dist, "car")
        total_saved += max(0, car_would_be - carbon)
        eco_scores.append(calculate_eco_score(dist, mode)["score"])
        mode_counts[mode] += 1

    def period_stats(cutoff):
        period = []
        for r in records:
            try:
                created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                continue
            if created >= cutoff:
                period.append(r)
        if not period:
            return {"trips": 0, "carbon_kg": 0, "distance_km": 0, "eco_score": 0}
        scores = [calculate_eco_score(p["distance_km"], p["transport_mode"])["score"] for p in period]
        return {
            "trips": len(period),
            "carbon_kg": round(sum(p["carbon_kg"] or 0 for p in period), 2),
            "distance_km": round(sum(p["distance_km"] or 0 for p in period), 2),
            "eco_score": round(sum(scores) / len(scores)),
        }

    overall_score = round(sum(eco_scores) / len(eco_scores)) if eco_scores else 0
    most_used = mode_counts.most_common(1)[0][0] if mode_counts else "car"
    badge = get_sustainability_badge(overall_score)

    explanation = (
        f"You have saved an estimated {total_saved:.1f} kg CO₂ compared to driving for all your trips. "
        f"Your most-used mode is {_mode_label(most_used)}. "
        f"Overall Eco Score: {overall_score}/100 — {badge} sustainability level."
    )

    return {
        "total_emissions_saved_kg": round(total_saved, 2),
        "most_used_mode": most_used,
        "most_used_mode_label": _mode_label(most_used),
        "weekly": period_stats(week_ago),
        "monthly": period_stats(month_ago),
        "overall_eco_score": overall_score,
        "badge": badge,
        "explanation": explanation,
        "recommended_mode": "train" if overall_score < 60 else "bicycle",
        "recommended_mode_label": _mode_label("train" if overall_score < 60 else "bicycle"),
        "emissions_saved_kg": round(total_saved, 2),
        "eco_score": overall_score,
        "eco_score_label": calculate_eco_score(100, "bus")["label"] if overall_score >= 60 else "fair",
        "eco_score_color": "#40916c" if overall_score >= 60 else "#e9c46a",
        "eco_score_explanation": f"Based on {len(records)} trips analyzed.",
    }
