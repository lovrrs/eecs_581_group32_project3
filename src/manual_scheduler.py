# File: src/manual_scheduler.py
# Description: The user is able to manually create their own schedule
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-05

import sys
from datetime import datetime, time, timedelta
from src.db import get_connection
from src.task_repo import TaskRepo

class ManualScheduler:
    def __init__(self, user_id:int):
        self.user_id = user_id
        self.repo = TaskRepo(user_id=user_id)
        self.schedule_start = time(8, 0)    # default: 8:00 AM
        self.schedule_end = time(22, 0)     # default: 10:00 PM
        self.time_slot_duration = 30        # 30 min intervals

    def set_time_boundaries(self, start_time:str, end_time:str):
        """Set custom schedule boundaries"""
        try:
            self.schedule_start = datetime.strptime(start_time, '%H:%M').time()
            self.schedule_end = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            print('Invalid time format. Use HH:MM (24-hour format)')
            return False
        return True
    
    def generate_time_slots(self):
        """Generate time slots from start to end time"""
        slots = []
        # create datetime object using today's date and the schedule start/end time -- needed to do time arithmetic
        curr_time = datetime.combine(datetime.today(), self.schedule_start)
        end_datetime = datetime.combine(datetime.today(), self.schedule_end)

        while curr_time < end_datetime:
            slot_end = curr_time + timedelta(minutes=self.time_slot_duration) # add time slot duration to the current time
            # prevents creating partial slots & breaks out of loop
            if slot_end > end_datetime:
                break
            # append slot data
            slots.append({
                'start': curr_time.time(),
                'end': slot_end.time(),
                'task_id': None,
                'task_name': None
            })
            curr_time = slot_end # make curr_time the slot_end to move forward
        return slots
    
    def display_schedule_grid(self, time_slots, available_tasks):
        """Display schedule grid with current assignments"""
        print("\n" + "="*70)
        print("                      MANUAL SCHEDULE BUILDER")
        print("="*70)

        selected_tasks = [t for t in available_tasks if t[3]] # t[3] is selected flag
        
        if not selected_tasks:
            print("No tasks selected! Use command '4' in main menu to select tasks first.")
            return
        
        # display selected tasks
        for task in selected_tasks:
            task_id, name, duration, selected = task
            print(f'{task_id:2d}. {name} ({duration} minutes)')

        print("-"*70)

def run_manual_scheduler(user_id:int):
    """Main function to run the manual scheduler"""
    scheduler = ManualScheduler(user_id)

    print("\n" + "="*60)
    print("               MANUAL SCHEDULE BUILDER")
    print("="*60)
    print("Build your schedule by assigning tasks to specific time slots!")
    print("------------------------------------------------------------")

    # Get available tasks from DB
    available_tasks = scheduler.repo.list_tasks()
    if not available_tasks:
        print("No tasks found. Add tasks first!")
        return

    # Generate empty time slots
    time_slots = scheduler.generate_time_slots()

    # Menu loop
    while True:
        print("\nOptions:")
        print("1. View tasks")
        print("2. View schedule grid")
        print("3. Assign a task to a time slot")
        print("4. Change schedule time boundaries")
        print("5. Exit\n")

        choice = input("Enter choice (1-5): ").strip()

        if choice == '1':
            print("\nAvailable Tasks:")
            for t in available_tasks:
                task_id, name, duration, *_ = t
                print(f"{task_id:2d}. {name} ({duration} minutes)")

        elif choice == '2':
            print("\nCurrent Schedule:")
            for i, slot in enumerate(time_slots, start=1):
                start = slot['start'].strftime("%H:%M")
                end = slot['end'].strftime("%H:%M")
                task_name = slot['task_name'] or "-"
                print(f"{i:2d}. {start} - {end}: {task_name}")

        elif choice == '3':
            print()
            print("\nAssign a task to a time slot")

            print("\nCurrent Schedule:")
            for i, slot in enumerate(time_slots, start=1):
                start = slot['start'].strftime("%H:%M")
                end = slot['end'].strftime("%H:%M")
                task_name = slot['task_name'] or "-"
                print(f"{i:2d}. {start} - {end}: {task_name}")

            slot_num = input("Enter time slot number: ").strip()

            print("\nAvailable Tasks:")
            for t in available_tasks:
                task_id, name, duration, *_ = t
                print(f"{task_id:2d}. {name} ({duration} minutes)")

            task_num = input("Enter task ID to assign: ").strip()

            if not (slot_num.isdigit() and task_num.isdigit()):
                print("Invalid input. Enter numeric values.")
                continue

            slot_idx = int(slot_num) - 1
            task_id = int(task_num)

            if slot_idx < 0 or slot_idx >= len(time_slots):
                print("Invalid slot number.")
                continue

            task = next((t for t in available_tasks if t[0] == task_id), None)
            if not task:
                print("Invalid task ID.")
                continue

            task_id, name, duration, *_ = task
            time_slots[slot_idx]['task_id'] = task_id
            time_slots[slot_idx]['task_name'] = name

            print(f"Assigned '{name}' to {time_slots[slot_idx]['start'].strftime('%H:%M')} - {time_slots[slot_idx]['end'].strftime('%H:%M')}")

        elif choice == '4':
            start = input("Enter new start time (HH:MM): ")
            end = input("Enter new end time (HH:MM): ")
            if scheduler.set_time_boundaries(start, end):
                time_slots = scheduler.generate_time_slots()
                print("Updated schedule boundaries!")

        elif choice == '5':
            print("Exiting manual scheduler...")
            break

        else:
            print("Invalid option. Try again.")

        

