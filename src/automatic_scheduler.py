# File: src/automatic_scheduler.py
# Description: Automatic scheduler that intelligently places tasks in time slots
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-09

from datetime import datetime, time, timedelta
from src.db import get_connection
from src.task_repo import TaskRepo
from src.time_periods import determine_period, times_for_slot, next_slot, is_time_in_slot

class AutomaticScheduler:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.repo = TaskRepo(user_id=user_id)
        self.default_start = time(8, 0)
        self.default_end = time(22, 0)
        self.schedule_start = self.default_start
        self.schedule_end = self.default_end
        self.time_slot_duration = 30

    def set_time_boundaries(self, start_time, end_time):
        """Set custom schedule boundaries"""
        try:
            new_start = datetime.strptime(start_time, '%I:%M %p').time()
            new_end = datetime.strptime(end_time, '%I:%M %p').time()
        except ValueError:
            print("Invalid time format. Use HH:MM AM/PM format.")
            return False

        # Validate schedule duration
        start_dt = datetime.combine(datetime.today(), new_start)
        end_dt = datetime.combine(datetime.today(), new_end)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        duration = (end_dt - start_dt).total_seconds() / 3600
        if duration < 1:
            print("Schedule duration must be at least 1 hour.")
            return False
        if duration > 24:
            print("Schedule duration cannot exceed 24 hours.")
            return False

        self.schedule_start = new_start
        self.schedule_end = new_end
        return True

    def generate_time_slots(self):
        """Generate available time slots between start and end time"""
        slots = []
        curr_time = datetime.combine(datetime.today(), self.schedule_start)
        end_datetime = datetime.combine(datetime.today(), self.schedule_end)

        while curr_time < end_datetime:
            slot_end = curr_time + timedelta(minutes=self.time_slot_duration)
            if slot_end > end_datetime:
                break
            slots.append({
                'start': curr_time.time(),
                'end': slot_end.time(),
                'period': determine_period(curr_time.time().strftime('%H:%M')),
                'task_id': None,
                'task_name': None
            })
            curr_time = slot_end
        return slots

    def build_schedule(self):
        """Automatically build a schedule by intelligently placing tasks in time slots"""
        # Get selected tasks
        tasks = [t for t in self.repo.list_tasks() if t[3]]
        if not tasks:
            print("No tasks selected. Please select tasks first!")
            return None

        time_slots = self.generate_time_slots()
        if not time_slots:
            print("No available time slots in the schedule!")
            return None

        # Sort tasks by duration (longer tasks first)
        tasks.sort(key=lambda x: x[2], reverse=True)

        scheduled_slots = []
        unscheduled_tasks = []

        # Place fixed tasks first.
        for task in (t for t in tasks if self.repo.get_task_type(t[0]) == 'fixed'):
            task_id, name, duration, *_ = task
            slots_needed = -(-duration // self.time_slot_duration)  # Ceiling division
            placed = False
            fixed_time = self.repo.get_fixed_time(task_id)
            if fixed_time:
                # Find slots that match the fixed time
                for i in range(len(time_slots) - slots_needed + 1):
                    if time_slots[i]['start'].strftime('%H:%M') == fixed_time:
                        if self.can_place_task(time_slots, i, slots_needed):
                            self.place_task(time_slots, i, slots_needed, task)
                            placed = True
                            break
            # If can't be placed add to list.
            if not placed:
                unscheduled_tasks.append(task)

        # Place flexible tasks second.
        periods = ["morning", "afternoon", "evening", "night"]
        for task in (t for t in tasks if self.repo.get_task_type(t[0]) != 'fixed'):
            task_id, name, duration, *_ = task
            slots_needed = -(-duration // self.time_slot_duration)  # Ceiling division
            placed = False
            for period in periods:
                if placed:
                    break
                # Find consecutive free slots in the current period.
                for i in range(len(time_slots) - slots_needed + 1):
                    if (time_slots[i]['period'] == period and
                        self.can_place_task(time_slots, i, slots_needed)):
                        self.place_task(time_slots, i, slots_needed, task)
                        placed = True
                        break
            # If can't be placed add to list.
            if not placed:
                unscheduled_tasks.append(task)

        # Create final schedule with only assigned slots
        final_schedule = [slot for slot in time_slots if slot['task_id'] is not None]
        
        # Report unscheduled tasks
        if unscheduled_tasks:
            print("\nWarning: The following tasks could not be scheduled:")
            for task in unscheduled_tasks:
                print(f"- {task[1]} ({task[2]} minutes)")

        return final_schedule

    def can_place_task(self, time_slots, start_idx, slots_needed):
        """Check if a task can be placed in consecutive slots"""
        if start_idx + slots_needed > len(time_slots):
            return False
            
        # Check if all needed slots are free and in the same peroid
        period = time_slots[start_idx]['period']
        for i in range(start_idx, start_idx + slots_needed):
            if (time_slots[i]['task_id'] is not None or 
                time_slots[i]['period'] != period):
                return False
        return True

    def place_task(self, time_slots, start_idx, slots_needed, task):
        """Place a task in consecutive time slots"""
        task_id, name, duration, *_ = task
        
        # Mark all slots for this task
        for i in range(start_idx, start_idx + slots_needed):
            time_slots[i]['task_id'] = task_id
            time_slots[i]['task_name'] = name

    def display_schedule(self, schedule):
        """Display the generated schedule in a readable format"""
        if not schedule:
            print("No schedule to display!")
            return

        print("\n" + "="*70)
        print(f"                   AUTOMATIC SCHEDULE")
        print(f"             {self.schedule_start.strftime('%I:%M %p')} - {self.schedule_end.strftime('%I:%M %p')}")
        print("="*70)

        current_period = None
        for slot in schedule:
            if slot['period'] != current_period:
                current_period = slot['period']
                print(f"\n{current_period.upper()}:")
                print("-" * 50)
            
            start_time = slot['start'].strftime("%I:%M %p")
            end_time = slot['end'].strftime("%I:%M %p")
            print(f"{start_time:>8} - {end_time:<8}: {slot['task_name']}")
