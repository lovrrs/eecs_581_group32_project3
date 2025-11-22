# File: src/travel_time.py
# Description: Simple helper to estimate travel time between two locations.

# Travel time table (in minutes) between known locations.
# You can customize this for your demo.
TRAVEL_TIMES = {
    ("Home", "Gym"): 10,
    ("Gym", "Library"): 7,
    ("Library", "Home"): 12,
    # Add more as needed...
}

def get_travel_time(loc1, loc2, default=15):
    """
    Return estimated travel time in minutes between two locations.
    - If locations are the same or missing -> 0
    - If pair is found in TRAVEL_TIMES (either direction) -> use that
    - Else -> use default fallback.
    """
    if not loc1 or not loc2:
        return 0
    if loc1 == loc2:
        return 0

    if (loc1, loc2) in TRAVEL_TIMES:
        return TRAVEL_TIMES[(loc1, loc2)]
    if (loc2, loc1) in TRAVEL_TIMES:
        return TRAVEL_TIMES[(loc2, loc1)]

    return default
