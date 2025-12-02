# File: src/location_input.py
# Description: Vacation location and date management
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-20

from src.db import get_connection
from datetime import datetime, date
from typing import List, Tuple, Optional

class LocationRepo:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def save_location(self, location: str, start_date: date, end_date: date) -> int:
        """Save a new vacation location for the user."""
        if not location.strip():
            raise ValueError("Location cannot be empty.")
        
        # Validate dates
        if start_date >= end_date:
            raise ValueError("Start date must be before end date.")
        
        # Ensure start date is not in the past
        if start_date < date.today():
            raise ValueError("Start date cannot be in the past.")
        
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO locations (user_id, location, start_date, end_date) VALUES (?, ?, ?, ?)",
                (self.user_id, location.strip(), start_date.isoformat(), end_date.isoformat())
            )
            conn.commit()
            return cur.lastrowid

    def get_saved_locations(self) -> List[Tuple]:
        """Retrieve all vacation locations for the user."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, location, start_date, end_date, created_at FROM locations WHERE user_id = ? ORDER BY start_date DESC",
                (self.user_id,)
            )
            return cursor.fetchall()
        
    def get_location(self, location_id: int) -> Optional[Tuple]:
        """Retrieve a specific vacation location by ID."""
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, location, start_date, end_date, created_at FROM locations WHERE user_id = ? AND id = ?",
                (self.user_id, location_id)
            )
            return cursor.fetchone()
        
    def delete_location(self, location_id: int):
        """Delete a vacation location by ID."""
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM locations WHERE user_id = ? AND id = ?",
                (self.user_id, location_id)
            )
            conn.commit()

def display_location(locations):
    """Display saved vacation locations in a formatted list."""
    if not locations:
        print("No saved vacation locations.")
        return
    
    print("\n" + "="*50)
    print("            SAVED VACATION LOCATIONS:")
    print("="*50 + "\n")

    for idx, loc, start_date, end_date, created_at in locations:
        start = datetime.strptime(start_date, "%Y-%m-%d").strftime('%b %d, %Y')
        end = datetime.strptime(end_date, "%Y-%m-%d").strftime('%b %d, %Y')
        duration = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days

        print(f"{idx:2d}. {loc}")
        print(f"    {start} to {end} ({duration} days)")
        print(f"    📅 Saved: {datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y')}")
        print()
    print("="*50)