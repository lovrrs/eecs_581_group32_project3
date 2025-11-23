# File: src/auto_suggest.py
# Description: Auto-suggest points of interest to fill open time slots in schedule
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-20

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
from src.places_api import PlacesAPI, suggest_categories_from_places
from src.task_repo import TaskRepo
from src.categories import CategoryRepo
from src.db import get_connection


def generate_suggestions(
    schedule: List[Dict],
    location: str,
    schedule_start: time,
    schedule_end: time,
    time_slot_duration: int = 30,
    min_slot_duration: int = 30
) -> List[Dict]:
    """
    Generate suggestions for points of interest to fill open time slots.
    
    Args:
        schedule: List of scheduled time slots (from AutomaticScheduler.build_schedule())
        location: Location string (e.g., "Seattle, WA")
        schedule_start: Start time of the schedule
        schedule_end: End time of the schedule
        time_slot_duration: Duration of each time slot in minutes (default: 30)
        min_slot_duration: Minimum duration for a suggestion slot in minutes (default: 30)
        
    Returns:
        List of suggested activities with time slots and place information
    """
    if not location or not location.strip():
        print("Error: Location is required to generate suggestions.")
        return []
    
    # Find open time slots
    open_slots = _find_open_slots(
        schedule, schedule_start, schedule_end, time_slot_duration, min_slot_duration
    )
    
    if not open_slots:
        print("No open time slots found in the schedule.")
        return []
    
    # Initialize Places API
    try:
        places_api = PlacesAPI()
    except Exception as e:
        print(f"Error initializing Places API: {e}")
        return []
    
    suggestions = []
    
    # Generate suggestions for each open slot
    for slot in open_slots:
        slot_duration = slot['duration_minutes']
        
        # Determine activity type based on time of day
        period = _determine_period(slot['start_time'])
        activity_query = _get_activity_query(period, slot_duration)
        
        try:
            # Search for places
            places = places_api.search_places(activity_query, location)
            
            if places:
                # Select the best place (highest rated)
                best_place = max(places, key=lambda p: p.get('rating', 0) if isinstance(p.get('rating'), (int, float)) else 0)
                
                # Suggest appropriate duration (round to nearest 30 minutes, minimum 30)
                suggested_duration = max(min_slot_duration, (slot_duration // 30) * 30)
                
                suggestion = {
                    'start_time': slot['start_time'],
                    'end_time': slot['end_time'],
                    'duration_minutes': suggested_duration,
                    'name': best_place['name'],
                    'address': best_place.get('address', 'Address not available'),
                    'rating': best_place.get('rating', 'N/A'),
                    'place_types': best_place.get('types', []),
                    'place_id': best_place.get('place_id'),
                }
                suggestions.append(suggestion)
        except Exception as e:
            print(f"Error searching for places: {e}")
            continue
    
    return suggestions


def insert_suggestions(
    user_id: int,
    suggestions: List[Dict],
    approved_indices: List[int]
) -> List[int]:
    """
    Insert approved suggestions into the schedule as tasks marked as "Suggested".
    
    Args:
        user_id: User ID
        suggestions: List of suggestion dictionaries from generate_suggestions()
        approved_indices: List of indices (0-based) of suggestions to approve
        
    Returns:
        List of task IDs that were created
    """
    if not suggestions or not approved_indices:
        return []
    
    repo = TaskRepo(user_id=user_id)
    category_repo = CategoryRepo(user_id=user_id)
    
    created_task_ids = []
    
    for idx in approved_indices:
        if idx < 0 or idx >= len(suggestions):
            continue
        
        suggestion = suggestions[idx]
        
        # Mark task name with [Suggested] prefix
        task_name = f"[Suggested] {suggestion['name']}"
        
        # Determine category from place types
        category_name = suggest_categories_from_places(suggestion.get('place_types', []))
        category_id = None
        
        # Try to find or create the category
        try:
            categories = category_repo.list_categories()
            category = next((cat for cat in categories if cat[1].lower() == category_name.lower()), None)
            if category:
                category_id = category[0]
        except Exception:
            pass
        
        # Add task with location from address
        try:
            task_id = repo.add_task(
                name=task_name,
                duration=suggestion['duration_minutes'],
                category_id=category_id,
                location=suggestion.get('address', None)
            )
            
            # Set as flexible task (suggestions are flexible by default)
            repo.set_task_type(task_id, "flexible")
            
            # Auto-select the suggested task
            repo.toggle_select(task_id)
            
            created_task_ids.append(task_id)
        except Exception as e:
            print(f"Error creating task for suggestion '{suggestion['name']}': {e}")
            continue
    
    return created_task_ids


def _find_open_slots(
    schedule: List[Dict],
    schedule_start: time,
    schedule_end: time,
    time_slot_duration: int,
    min_slot_duration: int
) -> List[Dict]:
    """
    Find open time slots in the schedule.
    
    Returns:
        List of open slot dictionaries with start_time, end_time, and duration_minutes
    """
    # Create a set of occupied time ranges
    occupied_ranges = []
    for slot in schedule:
        if slot.get('task_id') is not None:
            occupied_ranges.append({
                'start': slot['start'],
                'end': slot['end']
            })
    
    # Generate all possible time slots
    all_slots = []
    curr_time = datetime.combine(datetime.today(), schedule_start)
    end_datetime = datetime.combine(datetime.today(), schedule_end)
    
    while curr_time < end_datetime:
        slot_end = curr_time + timedelta(minutes=time_slot_duration)
        if slot_end > end_datetime:
            break
        all_slots.append({
            'start': curr_time.time(),
            'end': slot_end.time()
        })
        curr_time = slot_end
    
    # Find consecutive open slots
    open_slots = []
    i = 0
    while i < len(all_slots):
        if _is_slot_occupied(all_slots[i], occupied_ranges):
            i += 1
            continue
        
        # Find consecutive open slots
        open_start = all_slots[i]['start']
        open_count = 0
        j = i
        while j < len(all_slots) and not _is_slot_occupied(all_slots[j], occupied_ranges):
            open_count += 1
            j += 1
        
        # Calculate duration
        duration_minutes = open_count * time_slot_duration
        
        if duration_minutes >= min_slot_duration:
            open_end = all_slots[j - 1]['end']
            open_slots.append({
                'start_time': open_start,
                'end_time': open_end,
                'duration_minutes': duration_minutes
            })
        
        i = j
    
    return open_slots


def _is_slot_occupied(slot: Dict, occupied_ranges: List[Dict]) -> bool:
    """Check if a time slot overlaps with any occupied range."""
    slot_start = datetime.combine(datetime.today(), slot['start'])
    slot_end = datetime.combine(datetime.today(), slot['end'])
    
    for occupied in occupied_ranges:
        occ_start = datetime.combine(datetime.today(), occupied['start'])
        occ_end = datetime.combine(datetime.today(), occupied['end'])
        
        # Check for overlap
        if not (slot_end <= occ_start or slot_start >= occ_end):
            return True
    
    return False


def _determine_period(time_obj: time) -> str:
    """Determine time period (morning, afternoon, evening, night) from time."""
    hour = time_obj.hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def _get_activity_query(period: str, duration_minutes: int) -> str:
    """
    Get activity search query based on time period and duration.
    
    Args:
        period: Time period (morning, afternoon, evening, night)
        duration_minutes: Duration of the time slot
        
    Returns:
        Search query string for Places API
    """
    # Activity suggestions based on time of day
    if period == "morning":
        if duration_minutes >= 120:
            return "parks"
        elif duration_minutes >= 60:
            return "cafes"
        else:
            return "coffee shops"
    elif period == "afternoon":
        if duration_minutes >= 120:
            return "museums"
        elif duration_minutes >= 60:
            return "restaurants"
        else:
            return "shopping"
    elif period == "evening":
        if duration_minutes >= 120:
            return "restaurants"
        elif duration_minutes >= 60:
            return "movie theaters"
        else:
            return "bars"
    else:  # night
        if duration_minutes >= 60:
            return "restaurants"
        else:
            return "bars"


def display_suggestions(suggestions: List[Dict]) -> None:
    """
    Display suggestions in a formatted review list.
    
    Args:
        suggestions: List of suggestion dictionaries
    """
    if not suggestions:
        print("No suggestions to display.")
        return
    
    print("\n" + "="*70)
    print("                    SUGGESTED POINTS OF INTEREST")
    print("="*70 + "\n")
    
    for idx, suggestion in enumerate(suggestions, 1):
        start_time = suggestion['start_time'].strftime("%I:%M %p")
        end_time = suggestion['end_time'].strftime("%I:%M %p")
        rating = suggestion.get('rating', 'N/A')
        if isinstance(rating, (int, float)):
            rating = f"{rating:.1f}"
        
        print(f"{idx:2d}. {suggestion['name']}")
        print(f"     Time: {start_time} - {end_time} ({suggestion['duration_minutes']} min)")
        print(f"     Address: {suggestion.get('address', 'Address not available')}")
        print(f"     Rating: {rating}")
        print()
    
    print("="*70 + "\n")

