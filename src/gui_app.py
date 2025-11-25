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
from src.manage_task_gui import SchedulerGUI
import tkinter as tk
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

    cli_root = tk.Tk()
    cli_root.withdraw()

    while True:
        # print main menu after each option
        print("Welcome to Schedule Builder!\n")
        print("MAIN MENU")
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
            try:
                gui_app = SchedulerGUI(cli_root, user_id=user_id)
                # This line starts the GUI event loop for the pop-up window
                cli_root.wait_window(gui_app.root) 
                print("\nReturned to CLI Main Menu.")
            except Exception as e:
                print(f"An error occurred in the GUI: {e}")

        # ================= MANUAL SCHEDULER =================
        elif cmd == "2":
            scheduler = run_manual_scheduler(user_id)
            if scheduler:
                saved_schedule_list = getattr(scheduler, "schedule_list", None)
                most_recent = "manual"

        # ================= AUTOMATIC SCHEDULER =================
        elif cmd == "3":
            scheduler = AutomaticScheduler(user_id)

            print("\nAutomatic Schedule Builder")
            print("-------------------------")

            # Optionally set time boundaries
            print(
                "\nWould you like to set custom time boundaries? "
                "(default: 8:00 AM - 10:00 PM)"
            )
            if input(
                "Enter 'y' for custom times: "
            ).strip().lower() == "y":
                print(
                    "\nEnter times in HH:MM AM/PM format (e.g., 8:00 AM)"
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

        # ================= SETTINGS MENU =================
        elif cmd == "4":
            while True:
                print("\nSETTINGS")
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
                        print("\nCATEGORY MANAGEMENT")
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
                        print("\nVACATION SETTINGS")
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
