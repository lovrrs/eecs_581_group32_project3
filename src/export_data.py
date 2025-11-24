# File: src/export_data.py
# Description: Handles all exporting of tasks and schedules.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-23

# Imports.
from src.automatic_scheduler import AutomaticScheduler
from datetime import datetime
from src.travel_time import get_travel_time
from src.task_repo import TaskRepo
from src.weather_api import get_weather_sync

# Gets the current date for txt naming purpopses.
def get_current_date():
    current_date = datetime.now().strftime("%Y-%m-%d")
    return current_date

# Exports the tasks list.
def export_tasks(repo):
    # Calls from repo similar to how it is viewed in CLI.
    rows = repo.list_tasks()
    output_file = f"MyTasks_{get_current_date()}.txt"
    with open(output_file, "w") as f:
        if not rows:
            f.write("(no tasks yet)\n")
        else:
            for t in rows:
                task_id, name, duration, selected, task_type, fixed_time = t
                status = "Y" if selected else "N"
                line = (
                    f"{task_id}. {name} | {duration} minutes | "
                    f"type:{task_type} | fixed_time:{fixed_time} | [{status}]\n"
                )
                f.write(line)
    print(f"Tasks written to {output_file}")

# Get location for weather API.
def get_location():
    user_location = input("Enter city of plans (Los Angeles, New York) (enter to skip): ").strip()
    return user_location

# Get date for weather API.
def get_date():
    while True:
        user_date = input("Enter date of plans (YYYY-MM-DD) (enter to skip): ").strip()
        # Checks if input skipped or enough characters.
        if len(user_date) == 10 or user_date == "":
            return user_date
        else:
            print("Invalid format. Please use YYYY-MM-DD.")
            continue
        
# Exports the schedule of the auto scheduler.
def export_auto_schedule(scheduler, schedule):
    output_file = f"MySchedule_{get_current_date()}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        if not schedule:
            f.write("No schedule to display!\n")
            return
        f.write("\n" + "="*70 + "\n")
        f.write("                   AUTOMATIC SCHEDULE\n")
        f.write(f"             {scheduler.schedule_start.strftime('%I:%M %p')} - "
                f"{scheduler.schedule_end.strftime('%I:%M %p')}\n")
        f.write("="*70 + "\n")
        # Gets the weather from the API.
        location = get_location()
        date = get_date()
        if date != "" and location != "": 
            f.write(f"\n{get_weather_sync(location, date)}\n")
        current_period = None
        # Schedule similar to the CLI view but written to file.
        for idx, slot in enumerate(schedule):
            if slot['period'] != current_period:
                current_period = slot['period']
                f.write(f"\n{current_period.upper()}:\n")
                f.write("-" * 50 + "\n")
            start_time = slot['start'].strftime("%I:%M %p")
            end_time = slot['end'].strftime("%I:%M %p")
            f.write(f"{start_time:>8} - {end_time:<8}: {slot['task_name']}\n")
            # Travel time to next task
            if idx < len(schedule) - 1:
                current_task_id = slot['task_id']
                next_task_id = schedule[idx + 1]['task_id']
                if current_task_id != next_task_id:
                    try:
                        curr_loc = scheduler.repo.get_task_location(current_task_id)
                        next_loc = scheduler.repo.get_task_location(next_task_id)
                        tt = get_travel_time(curr_loc, next_loc)
                        f.write(
                            f"           -> Travel from {curr_loc or 'Unknown'} "
                            f"to {next_loc or 'Unknown'}: {tt} min\n"
                        )
                    except AttributeError:
                        pass
    print(f"Schedule written to {output_file}")

# Exports the schedule made manually. (NEED TO USE SAVE OPTION TO APPEAR)
def export_manual_schedule(schedule_list):
    output_file = f"MySchedule_{get_current_date()}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Current Schedule:\n")
        # Calls weather information
        location = get_location()
        date = get_date()
        if date != "" and location != "": 
            f.write(f"{get_weather_sync(location, date)}\n\n")
        # Will iterate the schedule list to print like the manual CLI view.
        for i in schedule_list:
            f.write(f"{i}\n")
    print(f"Schedule written to {output_file}")