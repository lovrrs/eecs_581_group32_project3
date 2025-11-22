# File: src/travel_time.py
# Description: Helper to estimate travel time between two locations.
#
# Supports:
#   - Manual overrides via TRAVEL_TIMES dict
#   - Live Google Maps–style times via Distance Matrix API (if API key set)

import os
import math
from typing import Optional

import requests  # requires "pip install requests"


TRAVEL_TIMES = {
    ("Home", "Gym"): 10,
    ("Gym", "Library"): 7,
    ("Library", "Home"): 12,
    # Add more as needed...
}

# Read Google Maps Distance Matrix API key from env 
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


def _distance_matrix_minutes(loc1: str, loc2: str) -> Optional[int]:
    """
    Use Google Distance Matrix API to get driving time between two locations.
    Returns minutes (rounded up) or None on any error / missing API key.
    """
    if not GOOGLE_MAPS_API_KEY:
        return None

    try:
        params = {
            "origins": loc1,
            "destinations": loc2,
            "mode": "driving",
            "units": "imperial",
            "key": GOOGLE_MAPS_API_KEY,
        }
        resp = requests.get(DISTANCE_MATRIX_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "OK":
            return None

        rows = data.get("rows", [])
        if not rows or not rows[0].get("elements"):
            return None

        element = rows[0]["elements"][0]
        if element.get("status") != "OK":
            return None

        duration = element.get("duration")
        if not duration or "value" not in duration:
            return None

        seconds = duration["value"]
        minutes = math.ceil(seconds / 60)
        return minutes
    except Exception:
        # Any error -> let caller fall back to default
        return None


def get_travel_time(loc1: Optional[str], loc2: Optional[str], default: int = 15) -> int:
    """
    Return estimated travel time in minutes between two locations.

    Priority:
      1) If locations are missing or equal -> 0
      2) If pair is found in TRAVEL_TIMES (either direction) -> use that
      3) If Google Maps API key is set and call succeeds -> use live result
      4) Else -> use default fallback.
    """
    if not loc1 or not loc2:
        return 0
    if loc1 == loc2:
        return 0

    # 1) Manual overrides first (exact string match)
    if (loc1, loc2) in TRAVEL_TIMES:
        return TRAVEL_TIMES[(loc1, loc2)]
    if (loc2, loc1) in TRAVEL_TIMES:
        return TRAVEL_TIMES[(loc2, loc1)]

    # 2) Try live Google Distance Matrix
    live_minutes = _distance_matrix_minutes(loc1, loc2)
    if live_minutes is not None:
        return live_minutes

    # 3) Fallback
    return default
