# File: src/time_periods.py
# Description: Initial code skeleton for time_periods.py (Organizing slots of the day).
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-26

from datetime import datetime, time

# Slots dict for periods with proper time objects
slots = {
    "morning": (time(5, 0), time(12, 0)),    # 5:00 AM - 12:00 PM
    "afternoon": (time(12, 0), time(17, 0)),  # 12:00 PM - 5:00 PM
    "evening": (time(17, 0), time(21, 0)),    # 5:00 PM - 9:00 PM
    "night": (time(21, 0), time(4, 0))        # 9:00 PM - 4:00 AM
}

def determine_period(current_time):
    """Determine which period a given time falls into"""
    if isinstance(current_time, str):
        try:
            # Convert string time (HH:MM) to time object
            current_time = datetime.strptime(current_time, '%H:%M').time()
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
    
    for period, (start, end) in slots.items():
        # Special handling for night period that crosses midnight
        if period == "night":
            if current_time >= start or current_time <= end:
                return period
        else:
            if start <= current_time < end:
                return period
    
    return None

def times_for_slot(period):
    """Get the start and end times for a given period"""
    if period not in slots:
        raise ValueError(f"Invalid period. Must be one of: {', '.join(slots.keys())}")
    return slots[period]

def next_slot(current_slot):
    """Get the next time period in the sequence"""
    sequence = ["morning", "afternoon", "evening", "night"]
    try:
        current_idx = sequence.index(current_slot)
        next_idx = (current_idx + 1) % len(sequence)
        return sequence[next_idx]
    except ValueError:
        raise ValueError(f"Invalid period. Must be one of: {', '.join(sequence)}")

def is_time_in_slot(check_time, period):
    """Check if a given time falls within a specific period"""
    if isinstance(check_time, str):
        check_time = datetime.strptime(check_time, '%H:%M').time()
    
    start, end = slots[period]
    
    # Special handling for night period that crosses midnight
    if period == "night":
        return check_time >= start or check_time <= end
    else:
        return start <= check_time < end
