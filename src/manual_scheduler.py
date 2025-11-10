# File: src/manual_scheduler.py
# Description: The user is able to manually create their own schedule
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-05

from datetime import datetime, time, timedelta
from src.db import get_connection
from src.task_repo import TaskRepo

class ManualScheduler:
    def __init__(self, user_id:int):
        self.user_id = user_id
        self.repo = TaskRepo(user_id=user_id)
        self.default_start = time(8, 0)    # default: 8:00 AM
        self.default_end = time(22, 0)     # default: 10:00 PM
        self.time_slot_duration = 30        # 30 min intervals
        # current boundaries start as default
        self.schedule_start = self.default_start
        self.schedule_end = self.default_end

    def set_time_boundaries(self, start_time:str, end_time:str):
        """Set custom schedule boundaries"""
        # if user left either input blank, use original defaults
        if not start_time:
            start_time = self.default_start.strftime('%H:%M')
        if not end_time:
            end_time = self.default_end.strftime('%H:%M')


        try:
            new_start = datetime.strptime(start_time, '%H:%M').time()
            new_end = datetime.strptime(end_time, '%H:%M').time()
        except ValueError:
            print("Invalid time format. Use HH:MM (24-hour format).")
            return False
        
        # start must be before end
        if datetime.combine(datetime.today(), new_start) >= datetime.combine(datetime.today(), new_end):
            print("Start time must be before end time.")
            return False
        
        self.schedule_start = new_start
        self.schedule_end = new_end
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
    
    def assign_task(self, time_slots, slot_idx, task):
        """Assign a task to a specific time slot"""
        task_id, name, duration, *_ = task
        
        # compute new end datetime for task
        slot_start_time = time_slots[slot_idx]['start']
        slot_start_datetime = datetime.combine(datetime.today(), slot_start_time)
        new_end_datetime = slot_start_datetime + timedelta(minutes=duration)
        schedule_end_datetime = datetime.combine(datetime.today(), self.schedule_end)

        # check if task fits in schedule
        if new_end_datetime > schedule_end_datetime:
            print(f"Task '{name}' ({duration} minutes) exceeds schedule end time!")
            return time_slots
        
        new_slots = time_slots[:slot_idx]  # slots before the assigned slot

        # add adjusted slot for task
        new_slots.append({
            'start': slot_start_time,
            'end': new_end_datetime.time(),
            'task_id': task_id,
            'task_name': name
        })

        # notify if this overwrites existing future assignments
        overwritten = [s for s in time_slots[slot_idx+1:] if s.get('task_id')]
        if overwritten:
            print("Warning: This assignment clears later tasks that overlap with the new timing.")

        # generate remaining slots after task assignment
        curr = new_end_datetime
        while curr < schedule_end_datetime:
            slot_end = curr + timedelta(minutes=self.time_slot_duration)
            if slot_end > schedule_end_datetime:
                break
            new_slots.append({
                'start': curr.time(),
                'end': slot_end.time(),
                'task_id': None,
                'task_name': None
            })
            curr = slot_end

        return new_slots
    
    def display_schedule_grid(self, available_tasks):
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
            task_id, name, duration = task
            print(f'{task_id:2d}. {name} ({duration} minutes)')

        print("-"*70)

    def save_schedule(self, time_slots, schedule_name: str = "Manual Schedule"):
        """Save manual schedule to database"""
        try:
                with get_connection() as conn:
                    # create schedule record
                    cur = conn.execute(
                        "INSERT INTO schedules (user_id, name, schedule_type, created_at) VALUES (?, ?, ?, datetime('now'))",
                        (self.user_id, schedule_name, 'manual')
                    )
                    schedule_id = cur.lastrowid
                    
                    # save schedule items
                    for slot in time_slots:
                        if slot['task_id']:
                            conn.execute(
                                """INSERT INTO schedule_items
                                   (schedule_id, task_id, start_time, end_time)
                                   VALUES (?, ?, ?, ?)""",
                                   (schedule_id, slot['task_id'],
                                    slot['start'].strftime('%H:%M'),
                                    slot['end'].strftime('%H:%M'))
                            )
                    conn.commit()
                    print(f"Schedule '{schedule_name}' saved successfully!")
                    return True
        except Exception as e:
            print(f'Error saving schedule: {e}')
            return False

def run_manual_scheduler(user_id:int):
    """Main function to run the manual scheduler"""
    scheduler = ManualScheduler(user_id)

    print("\n" + "="*60)
    print("               MANUAL SCHEDULE BUILDER")
    print("="*60)
    print("Build your schedule by assigning tasks to specific time slots!")
    print("------------------------------------------------------------")

    # Get available tasks from DB - ONLY SELECTED ONES
    available_tasks = [t for t in scheduler.repo.list_tasks() if t[3]] # t[3] is selected flag
    if not available_tasks:
        print("No tasks selected. Select tasks first!")
        return

    # Generate empty time slots
    time_slots = scheduler.generate_time_slots()

    # Menu loop
    while True:
        print("\nOptions:")
        print("1. View tasks")
        print("2. View schedule")
        print("3. Assign a task")
        print("4. Clear a time slot")
        print("5. Save Schedule")
        print("6. Change schedule time boundaries")
        print("7. Insert Breaks")
        print("8. Quit")

        choice = input("> ").strip().lower()

        if choice == '1':
            """View tasks"""

            print("\nAvailable Tasks:")
            for t in available_tasks:
                task_id, name, duration, *_ = t
                print(f"{task_id:2d}. {name} ({duration} minutes)")

        elif choice == '2':
            """View schedule"""

            print("\nCurrent Schedule:")
            for i, slot in enumerate(time_slots, start=1):
                start = slot['start'].strftime("%H:%M")
                end = slot['end'].strftime("%H:%M")
                task_name = slot['task_name'] or "-"
                print(f"{i:2d}. {start} - {end}: {task_name}")

        elif choice == '3':
            """Assign a task to a time slot"""

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
            
            # assign + rebuild slots based on task duration
            time_slots = scheduler.assign_task(time_slots, slot_idx, task)
            assigned = time_slots[slot_idx]
            print(f"Assigned '{assigned['task_name']}' to slot {assigned['start'].strftime('%H:%M')} - {assigned['end'].strftime('%H:%M')}")

        elif choice == '4':
            """Clear a slot on the schedule"""

            # print current schedule
            print("\n Current Schedule:")
            for i, slot in enumerate(time_slots, start=1):
                start = slot['start'].strftime("%H:%M") # start time
                end = slot['end'].strftime("%H:%M") # end time
                task_name = slot['task_name'] or "-" # task name
                print(f"{i:2d}. {start} - {end}: {task_name}")

            slot_num = input("Enter time slot number: ").strip() # user input for slot number

            # checks if slot num is a digit
            if slot_num.isdigit():
                slot_idx = int(slot_num) - 1

                # checks if slot num is a valid time slot
                if 0 <= slot_idx < len(time_slots):

                    # checks if time slot is currently assigned to a task
                    if time_slots[slot_idx]['task_name']:
                        cleared_task = time_slots[slot_idx]['task_name'] # store cleared task for confirmation msg
                        # reset task_id and task_name to None to clear time slot
                        time_slots[slot_idx]['task_id'] = None
                        time_slots[slot_idx]['task_name'] = None
                        print(f"Cleared '{cleared_task}' from slot {slot_num}")
                    else:
                        print("Slot is already empty")

                else:
                    print("Invalid slot number")
            else:
                print("Please enter a valid number")

        elif choice == '5':
            """Save the schedule"""

            # user input to get schedule name
            name = input("Enter schedule name (or press Enter for 'Manual Schedule'): ").strip()
            
            # default name
            if not name:
                name = "Manual Schedule"
            if scheduler.save_schedule(time_slots, name):
                print("Schedule saved!")
            else:
                print("Failed to save schedule.")

        elif choice == '6':
            """Change time boundaries"""

            start = input("Enter new start time (HH:MM): ")
            end = input("Enter new end time (HH:MM): ")
            if scheduler.set_time_boundaries(start, end):
                time_slots = scheduler.generate_time_slots()
                print("Updated schedule boundaries!")
            else:
                print("Failed to update time boundaries. Please use HH:MM format.")
        elif choice == '7':
            """Insert Breaks"""

            for i in range(len(time_slots)-2):
                if (time_slots[i]['task_id'] !=1 and time_slots[i+1]['task_id']!=1):
                        if (time_slots[i]['task_id'] and time_slots[i+1]['task_id']):
                            if (time_slots[i+2]['task_id'] == None):
                                
                                task_id = int(time_slots[i+1]['task_id'])
                                task = next((t for t in available_tasks if t[0] == task_id), None)
                                time_slots[i+1]['task_id'] = None
                                time_slots[i+1]['task_name'] = None
                                break_task = next((t for t in available_tasks if t[0] == 1), None)
                                time_slots=scheduler.assign_task(time_slots,i+1,break_task)
                                time_slots=scheduler.assign_task(time_slots,i+2,task)
                                
                                print("Inserted breaks")
                        


        elif choice == '8':
            """Exit manual scheduler"""
            print("Exiting manual scheduler...")
            break

        else:
            print("Invalid option. Try again.")

        

