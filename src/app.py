# File: src/app.py
# Description: Simple CLI to interact with the scheduler DB.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-10-21

from src.db import run_migrations, get_connection
from src.task_repo import TaskRepo
from src.manual_scheduler import run_manual_scheduler
from src.manual_scheduler import ManualScheduler
from src.automatic_scheduler import AutomaticScheduler
from datetime import datetime, time, timedelta
from src.categories import CategoryRepo
from src.location_input import LocationRepo, display_location
from src.places_api import PlacesAPI, display_places, suggest_categories_from_places
from src.auto_suggest import generate_suggestions, insert_suggestions, display_suggestions
from src.export_data import export_tasks, export_auto_schedule, export_manual_schedule
from src.weather_api import get_weather_sync
import re


def _get_default_user_id() -> int:
    with get_connection() as conn:
        cur = conn.execute("SELECT id FROM users WHERE username=?", ("default",))
        row = cur.fetchone()
        return row[0]


def main():
    run_migrations()
    user_id = _get_default_user_id()
    repo = TaskRepo(user_id=user_id)
    # Tracks most recent schedule and retains last schedule for export.
    most_recent = None
    saved_schedule = None
    saved_scheduler = None
    saved_schedule_list = []

    while True:
        # print main menu after each option
        print("Welcome to Schedule Builder!\n")
        print("="*50)
        print("                     MAIN MENU")
        print("="*50)
        print("1. Manage Tasks")
        print("2. Manual Scheduler")
        print("3. Automatic Scheduler")
        print("4. Settings")
        print("5. Export Most Recent Schedule")
        print("6. Quit")
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        print()

        # ================= MANAGE TASKS MENU =================
        if cmd == "1":
            while True:
                print("\n" + "="*50)
                print("                   MANAGE TASKS")
                print("="*50)
                print("1. Add a new task")
                print("2. Delete a task")
                print("3. List all tasks")
                print("4. Select a task by ID")
                print("5. Set task as flexible/fixed")
                print("6. Export task info")
                print("7. Back to Main Menu")
                sub = input("> ").strip().lower()
                print()

                # 1. Add a new task
                if sub == "1":
                    print("\n" + "="*50)
                    print("                    ADD A NEW TASK")
                    print("="*50)
                    name = input("Task name: ").strip()
                    duration_str = input(
                        "Duration (min, integer > 0): "
                    ).strip()
                    location = (
                        input(
                            "Location (e.g., Home, Gym, Library) (optional): "
                        )
                        .strip()
                        or None
                    )
                    
                    try:
                        cost_unstripped = (
                        input(
                            "Cost of activity (e.g. 15.00) (optional):"
                        )
                        or None
                        )
                        cost = re.sub('[^0-9,.]', '', cost_unstripped)
                        duration = int(duration_str)

                        # show categories to assign
                        category_repo = CategoryRepo(user_id)
                        categories = category_repo.list_categories()

                        category_id = None
                        if categories:
                            print("\nAvailable Categories:")
                            category_repo.display_categories(categories)
                            cat_id_str = input(
                                "Enter category ID to assign (or leave blank for none): "
                            ).strip()

                            if cat_id_str.isdigit() and int(cat_id_str) != 0:
                                category_id = int(cat_id_str)
                                # verify category exists
                                if not any(cat[0] == category_id for cat in categories):
                                    print("Category ID does not exist.")
                                    category_id = None

                        # add task with category (if any) and location
                        task_id = repo.add_task(
                            name, duration, category_id=category_id, location=location, cost=cost
                        )

                        if category_id:
                            category_name = next(
                                (cat[1] for cat in categories if cat[0] == category_id),
                                "Unknown",
                            )
                            print(f"Task added under category '{category_name}'.")
                        else:
                            print("Task added.")
                    except Exception as e:
                        print("Error:", e)

                # 2. Delete a task
                elif sub == "2":
                    print("\n" + "="*50)
                    print("                   DELETE A TASK")
                    print("="*50)
                    repo.list_tasks()  # list tasks
                    task_id_str = input("Task ID to delete: ").strip()
                    try:
                        task_id = int(task_id_str)
                        deleted = repo.delete_task(task_id)  # returns True/False
                        if deleted:
                            print("Task deleted.")
                        else:
                            print("No task with that ID for this user.")
                    except Exception as e:
                        print("Error:", e)

                # 3. List all tasks
                elif sub == "3":
                    print("\n" + "="*50)
                    print("                     TASKS")
                    print("="*50)
                    rows = repo.list_tasks()
                    if not rows:
                        print("(no tasks yet)")
                    for t in rows:
                        task_id, name, duration, selected, task_type, fixed_time, cost = t
                        status = "✓" if selected else "✗"
                        print(
                            f"{task_id}. {name} | {duration} minutes | "
                            f"type:{task_type} | fixed_time:{fixed_time} | cost:${cost} | [{status}]"
                        )

                # 4. Select a task
                elif sub == "4":
                    # display tasks
                    print("\n" + "="*50)
                    print("                     TASKS")
                    print("="*50)
                    rows = repo.list_tasks()
                    if not rows:
                        print("(no tasks yet)")
                        return
                    for t in rows:
                        task_id, name, duration, selected, task_type, fixed_time, cost = t
                        status = "✓" if selected else "✗"
                        print(
                            f"{task_id}. {name} | {duration} minutes | "
                            f"type:{task_type} | fixed_time:{fixed_time} | cost:${cost} | [{status}]"
                        )

                    tid_str = input("Task ID: ").strip()
                    try:
                        tid = int(tid_str)
                        new_val = repo.toggle_select(tid)
                        status = "✓" if new_val else "✗"
                        print(f"Selection toggled. [{status}]")
                    except Exception as e:
                        print("Error:", e)

                # 5. Set task as flexible/fixed
                elif sub == "5":
                    # display tasks
                    print("\n" + "="*50)
                    print("                     TASKS")
                    print("="*50)
                    rows = repo.list_tasks()
                    if not rows:
                        print("(no tasks yet)")
                        return
                    for t in rows:
                        task_id, name, duration, selected, task_type, fixed_time, cost = t
                        status = "✓" if selected else "✗"
                        print(
                            f"{task_id}. {name} | {duration} minutes | "
                            f"type:{task_type} | fixed_time:{fixed_time} | cost:${cost} | [{status}]"
                        )

                    task_id_str = input("Enter task ID to modify: ").strip()
                    try:
                        task_id = int(task_id_str)

                        # get current task details
                        tasks = repo.list_tasks()
                        task = next((t for t in tasks if t[0] == task_id), None)

                        if not task:
                            print("Task not found.")
                            continue

                        task_id, name, duration, selected, task_type, fixed_time, cost = task

                        print(f"\nCurrent: {name} - Type: {task_type or 'flexible'}")
                        if fixed_time:
                            # convert 24-hour back to 12-hour for display
                            time_obj = datetime.strptime(fixed_time, "%H:%M")
                            print(f"Fixed Time: {time_obj.strftime('%I:%M %p')}")

                        print("\nSet task type:")
                        print("1. Flexible\n2. Fixed Time")

                        type_choice = input("> ").strip()

                        # set as flexible
                        if type_choice == "1":
                            repo.set_task_type(task_id, "flexible")
                            print(f"Task '{name}' set as flexible.")
                        # set as fixed
                        elif type_choice == "2":
                            fixed_time_input = input(
                                "Enter fixed time (HH:MM AM/PM): "
                            ).strip()
                            try:
                                repo.set_task_type(
                                    task_id, "fixed", fixed_time_input
                                )
                                # convert for display
                                time_obj = datetime.strptime(
                                    fixed_time_input, "%I:%M %p"
                                )
                                print(
                                    f"Task '{name}' set as fixed at "
                                    f"{time_obj.strftime('%I:%M %p')}."
                                )
                            except ValueError as e:
                                print(f"Error: {e}")
                        else:
                            print("Invalid choice.")
                    except Exception as e:
                        print("Error:", e)

                # 6. Export task info
                elif sub == "6":
                    print("\n" + "="*50)
                    print("                  EXPORT TASK INFO")
                    print("="*50)
                    export_tasks(repo)

                # Back to main menu
                elif sub == "7":
                    break
                else:
                    print("Invalid choice.")

        # ================= MANUAL SCHEDULER =================
        elif cmd == "2":
            scheduler = run_manual_scheduler(user_id)
            if scheduler:
                saved_schedule_list = getattr(scheduler, "schedule_list", None)
                most_recent = "manual"

        # ================= AUTOMATIC SCHEDULER =================
        elif cmd == "3":
            while True:
                print("\n" + "="*50)
                print("               AUTOMATIC SCHEDULER")
                print("="*50)
                print("1. Build New Schedule")
                print("2. Clear All Selections")
                print("3. View Current Schedule")
                print("4. View Weather Forecast")
                print("5. Back to Main Menu")
                sub_cmd = input("> ").strip().lower()
                print()

                # ---- Build new schedule ----
                if sub_cmd == "1":
                    scheduler = AutomaticScheduler(user_id)

                    # Optionally set time boundaries
                    print(
                        "\nWould you like to set custom time boundaries? "
                        "(default: 08:00 AM - 10:00 PM)"
                    )
                    if input(
                        "Enter 'y' for custom times: "
                    ).strip().lower() == "y":
                        print(
                            "\nEnter times in HH:MM AM/PM format (e.g., 08:00 AM)"
                        )
                        start = input("Start time: ").strip()
                        end = input("End time: ").strip()
                        if not scheduler.set_time_boundaries(start, end):
                            print("Using default time boundaries.")
                    
                    # Optionally set budget for time period
                    print("\nWould you like to set a budget? ")
                    if input(
                        "Enter 'y' to input budget: "
                    ).strip().lower() == "y":
                        user_budget = input("\nEnter budget (e.g. 230.00): ")
                        scheduler.set_budget(user_budget)

                    # Build and display schedule
                    schedule = scheduler.build_schedule()
                    if schedule:
                        scheduler.display_schedule(schedule)
                        
                        # Saves the schedule to be able to export if wanted later. 
                        saved_scheduler = scheduler
                        saved_schedule = schedule
                        most_recent = "auto"
                        
                        # Offer to generate suggestions for open time slots
                        print("\nWould you like to generate suggestions for open time slots?")
                        if input("Enter 'y' to generate suggestions: ").strip().lower() == "y":
                            location = input("Enter location (e.g., Seattle, WA): ").strip()
                            
                            if location:
                                print("\nGenerating suggestions...")
                                suggestions = generate_suggestions(
                                    schedule=schedule,
                                    location=location,
                                    schedule_start=scheduler.schedule_start,
                                    schedule_end=scheduler.schedule_end,
                                    time_slot_duration=scheduler.time_slot_duration
                                )
                                
                                if suggestions:
                                    display_suggestions(suggestions)
                                    
                                    # Review and approve suggestions
                                    print("Review suggestions above. Enter the numbers of suggestions to approve")
                                    print("(e.g., '1 3 5' to approve suggestions 1, 3, and 5, or 'all' for all)")
                                    approval_input = input("> ").strip().lower()
                                    
                                    approved_indices = []
                                    if approval_input == "all":
                                        approved_indices = list(range(len(suggestions)))
                                    else:
                                        try:
                                            approved_indices = [
                                                int(x.strip()) - 1  # Convert to 0-based index
                                                for x in approval_input.split()
                                                if x.strip().isdigit()
                                            ]
                                            # Filter valid indices
                                            approved_indices = [
                                                idx for idx in approved_indices
                                                if 0 <= idx < len(suggestions)
                                            ]
                                        except ValueError:
                                            print("Invalid input. No suggestions approved.")
                                    
                                    if approved_indices:
                                        task_ids = insert_suggestions(user_id, suggestions, approved_indices)
                                        if task_ids:
                                            print(f"\n✓ {len(task_ids)} suggestion(s) added to your tasks!")
                                            print("These tasks are marked as '[Suggested]' and are automatically selected.")
                                            print("\nYou can rebuild your schedule to include these new tasks.")
                                        else:
                                            print("\nNo suggestions were added.")
                                    else:
                                        print("\nNo suggestions approved.")
                                else:
                                    print("No suggestions could be generated.")
                            else:
                                print("Location is required to generate suggestions.")
                
                # ---- Clear schedule ----
                elif sub_cmd == "2":
                    print("\nClear all task selections? This will unselect ALL tasks.")
                    confirm = input("Enter 'y' to confirm: ").strip().lower()
                    if confirm == "y":
                        repo = TaskRepo(user_id)
                        # get all selected tasks and unselect them
                        tasks = repo.list_tasks()
                        for task in tasks:
                            task_id = task[0]
                            if task[3]:  # if selected
                                repo.toggle_select(task_id)
                        print("✓ All task selections cleared.")
                        saved_scheduler = None
                        saved_schedule = None
                        most_recent = None

                # ---- View current schedule ----
                elif sub_cmd == "3":
                    if saved_schedule:
                        saved_scheduler.display_schedule(saved_schedule)
                    else:
                        print("No schedule available. Please build a new schedule first.")

                # ---- View weather forecast ----
                elif sub_cmd == "4":
                    location = input(
                        "Enter location for weather forecast (e.g., Seattle, WA): "
                    ).strip()
                    if not location:
                        print("Location cannot be empty.")
                        continue
                    try:
                        weather_data = get_weather_sync(location)
                        if weather_data:
                            print(f"\nWeather Forecast for {location}:")
                            for entry in weather_data:
                                dt = entry['datetime'].strftime("%Y-%m-%d %I:%M %p")
                                temp = entry['temperature']
                                desc = entry['description']
                                print(f"{dt} | {temp}°F | {desc}")
                        else:
                            print("No weather data available.")
                    except Exception as e:
                        print(f"Error retrieving weather data: {e}")

                # ---- Back to main menu ----
                elif sub_cmd == "5":
                    break

                else:
                    print("Invalid choice.")
            

        # ================= SETTINGS MENU =================
        elif cmd == "4":
            while True:
                
                print("\n" + "="*50)
                print("                     SETTINGS")
                print("="*50)
                print("1. Manage categories")
                print("2. Break settings")
                print("3. Vacation settings")
                print("4. Back to Main Menu")
                sub = input("> ").strip()
                print()

                # ---- Category management ----
                if sub == "1":
                    category_repo = CategoryRepo(user_id)

                    while True:
                        print("\n" + "="*50)
                        print("                 CATEGORY MANAGEMENT")
                        print("="*50)
                        print("1. List Categories")
                        print("2. Add Category")
                        print("3. Delete Category")
                        print("4. Back")
                        cat_choice = input("> ").strip()

                        # list
                        if cat_choice == "1":
                            categories = category_repo.list_categories()
                            category_repo.display_categories(categories)

                        # add
                        elif cat_choice == "2":
                            name = input("Enter category name: ").strip()
                            try:
                                category_id = category_repo.create_category(name)
                                print(f"Category '{name}' created successfully!")
                            except Exception as e:
                                print(f"Error: {e}")

                        # delete
                        elif cat_choice == "3":
                            categories = category_repo.list_categories()
                            category_repo.display_categories(categories)
                            cat_id = input(
                                "Enter category ID to delete: "
                            ).strip()
                            if cat_id.isdigit():
                                confirm = input(
                                    "This will unlink the category from all tasks. "
                                    "Continue? (y/n): "
                                ).strip().lower()
                                if confirm == "y":
                                    category_repo.delete_category(int(cat_id))
                                    print("Category deleted successfully!")

                        # exit
                        elif cat_choice == "4":
                            break
                        else:
                            print("Invalid choice!")

                # ---- Break settings ----
                elif sub == "2":
                    print("\n" + "="*50)
                    print("                  BREAK SETTINGS")
                    print("="*50)
                    if (
                        input(
                            "Enable automatic breaks (Y/N):  "
                        ).strip().lower()
                        == "y"
                    ):
                        try:
                            break_id = 1
                            repo.toggle_select(break_id)
                        except Exception as e:
                            print("Error:", e)
                    else:
                        print("Invalid choice")

                # ---- Vacation settings ----
                elif sub == "3":
                    location_repo = LocationRepo(user_id)

                    while True:
                        print("\n" + "="*50)
                        print("                  VACATION SETTINGS")
                        print("="*50)
                        print("1. Save location")
                        print("2. Display locations")
                        print("3. Delete location")
                        print("4. Back to Main Menu")
                        vac_choice = input("> ").strip()

                        # ---- Save location ----
                        if vac_choice == "1":
                            try:
                                location = input("Enter location (e.g., Seattle, WA): ").strip()
                                if not location:
                                    print("Location cannot be empty.")
                                    continue

                                start_str = input("Enter start date (YYYY-MM-DD): ").strip()
                                end_str = input("Enter end date (YYYY-MM-DD): ").strip()

                                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                                end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

                                location_id = location_repo.save_location(location, start_date, end_date)
                                print(f"Location '{location}' saved.")
                            
                            except ValueError as e:
                                print(f"Error: {e}")
                            except Exception as e:
                                print(f"Error: {e}")

                        # ---- Display locations ----
                        elif vac_choice == "2":
                            locations = location_repo.get_saved_locations()
                            display_location(locations)

                        # ---- Delete location ----
                        elif vac_choice == "3":
                            locations = location_repo.get_saved_locations()
                            if not locations:
                                print("No saved locations to delete.")
                                continue

                            display_location(locations)
                            loc_id_str = input("Enter location ID to delete: ").strip()
                            if loc_id_str.isdigit():
                                confirm = input("Are you sure? (y/n): ").strip().lower()
                                if confirm == "y":
                                    loc_id = int(loc_id_str)
                                    deleted = location_repo.delete_location(loc_id)
                                    print("Location deleted.")
                                else:
                                    print("Deletion cancelled.")
                            else:
                                print("Invalid ID.")

                        # ---- Back to main menu ----
                        elif vac_choice == "4":
                            break
                # ---- Back to main menu ----
                elif sub == "4":
                    break
                else:
                    print("Invalid choice.")

        # ================= EXPORT SCHEDULE =================
        elif cmd == "5":
            # Checks the most recent type of schedule and calls that function.
            if most_recent == None:
                print("You must create a schedule first!")
            elif most_recent == "manual":
                export_manual_schedule(saved_schedule_list)
            elif most_recent == "auto":
                export_auto_schedule(saved_scheduler, saved_schedule)
                
        # ================= QUIT =================
        elif cmd == "6":
            print("Goodbye!")
            break

        else:
            print("Unknown command. Please enter a valid number.")

        print()


if __name__ == "__main__":
    main()
