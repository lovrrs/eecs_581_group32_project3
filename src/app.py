# File: src/app.py
# Description: Simple CLI to interact with the scheduler DB.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-10-21

from src.db import run_migrations, get_connection
from src.task_repo import TaskRepo
from src.manual_scheduler import run_manual_scheduler
from src.automatic_scheduler import AutomaticScheduler
from datetime import datetime, time, timedelta
from src.categories import CategoryRepo
from src.location_input import LocationRepo, display_location
from src.places_api import PlacesAPI, display_places, suggest_categories_from_places


def _get_default_user_id() -> int:
    with get_connection() as conn:
        cur = conn.execute("SELECT id FROM users WHERE username=?", ("default",))
        row = cur.fetchone()
        return row[0]

def main():
    run_migrations()
    user_id = _get_default_user_id()
    repo = TaskRepo(user_id=user_id)
    
    while True:
        # print main menu after each option
        print("Welcome to Schedule Builder!\n")
        print("MAIN MENU\n",
          "1. Add a new task\n",
          "2. Delete a task\n",
          "3. List all tasks\n",
          "4. Select a task by ID\n",
          "5. Set task as flexible/fixed\n",
          "6. Export task info\n",
          "7. Manual Scheduler\n",
          "8. Automatic Scheduler\n",
          "9. Break Settings\n",
          "10. Manage Categories\n",
          "11. Vacation Settings\n", # add budget, location, date
          "12. Quit")
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        print()
        # add a new task
        if cmd == "1":
            name = input("Task name: ").strip()
            duration_str = input("Duration (min, integer > 0): ").strip()
            try:
                duration = int(duration_str)

                # show categories to assign
                category_repo = CategoryRepo(user_id)
                categories = category_repo.list_categories()
                if categories:
                    print("\nAvailable Categories:")
                    category_repo.display_categories(categories)
                    cat_id_str = input("Enter category ID to assign (or leave blank for none): ").strip()

                    category_id = None # default
                    if cat_id_str.isdigit() and int(cat_id_str) != 0:
                        category_id = int(cat_id_str)
                        # verify category exists
                        if not any(cat[0] == category_id for cat in categories):
                            print("Category ID does not exist.")
                            category_id = None
                else:
                    category_id = None

                # add task w/ category
                task_id = repo.add_task(name, duration)
                if category_id:
                    repo.set_task_category(task_id, category_id)
                    # create readable name
                    category_name = next((cat[1] for cat in categories if cat[0] == category_id), "Unknown")
                    print(f"Task added under category '{category_name}'.")
                else:
                    print("Task added.")
            except Exception as e:
                print("Error:", e)
        # delete a task
        elif cmd == "2":
            repo.list_tasks() # list taks
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
        # list all tasks
        elif cmd == "3":
            rows = repo.list_tasks()
            if not rows:
                print("(no tasks yet)")
            for t in rows:
                task_id, name, duration, selected, task_type, fixed_time = t
                status = "✓" if selected else "✗"
                print(f"{task_id}. {name} | {duration} minutes | type:{task_type} | fixed_time:{fixed_time} | [{status}]")
        # select a task
        elif cmd == "4":
            repo.list_tasks() # list tasks
            tid_str = input("Task ID: ").strip()
            try:
                tid = int(tid_str)
                new_val = repo.toggle_select(tid)
                print(f"Selection toggled. [{status}]")
            except Exception as e:
                print("Error:", e)
        # set task type
        elif cmd == "5":
            repo.list_tasks() # list tasks
            task_id_str = input("Enter task ID to modify: ").strip()
            try:
                task_id = int(task_id_str)
                
                # get current task details
                tasks = repo.list_tasks()
                task = next((t for t in tasks if t[0] == task_id), None)

                if not task:
                    print("Task not found.")
                    continue

                task_id, name, duration, selected, task_type, fixed_time = task

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
                    repo.set_task_type(task_id, 'flexible')
                    print("Task '{name}' set as flexible.")
                # set as fixed
                elif type_choice == "2":
                    fixed_time_input = input("Enter fixed time (HH:MM AM/PM): ").strip()
                    try:
                        repo.set_task_type(task_id, 'fixed', fixed_time_input)
                        # convert for display
                        time_obj = datetime.strptime(fixed_time_input, "%I:%M %p")
                        print(f"Task '{name}' set as fixed at {time_obj.strftime('%I:%M %p')}.")
                    except ValueError as e:
                        print(f"Error: {e}")
                else:
                    print("Invalid choice.")
            except Exception as e:
                print("Error:", e)

        
        # export task info
        elif cmd == "6":
            rows = repo.list_tasks()
            with open("tasks_output.txt", "w", encoding="utf-8") as f:
                if not rows:
                    f.write("(no tasks yet)\n")
                else:
                    for t in rows:
                        line = f"{t[0]}. {t[1]} - {t[2]} min - selected={bool(t[3])}\n"
                        f.write(line)
        # manual scheduler
        elif cmd == "7":
            run_manual_scheduler(user_id)
        # automatic scheduler
        elif cmd == "8":
            scheduler = AutomaticScheduler(user_id)

            print("\nAutomatic Schedule Builder")
            print("-------------------------")
            
            # Optionally set time boundaries
            print("\nWould you like to set custom time boundaries? (default: 8:00 AM - 10:00 PM)")
            if input("Enter 'y' for custom times: ").strip().lower() == 'y':
                print("\nEnter times in HH:MM AM/PM format (e.g., 8:00 AM)")
                start = input("Start time: ").strip()
                end = input("End time: ").strip()
                if not scheduler.set_time_boundaries(start, end):
                    print("Using default time boundaries.")

            # Build and display schedule
            schedule = scheduler.build_schedule()
            if schedule:
                scheduler.display_schedule(schedule)
                
        # break settings
        elif cmd == '9':
            if  input("Enable automatic breaks (Y/N):  ").strip().lower() == 'y':
                #duration_str = input("Duration (min, integer > 0): ").strip()
                try:
                    #duration = int(duration_str)
                    break_id = 1
                    new_val = repo.toggle_select(break_id)
                except Exception as e:
                    print("Error:", e)
            else:
                print('Invalid choice')

        # categories
        elif cmd == '10':
            category_repo = CategoryRepo(user_id)

            while True:
                print("\n CATEGORY MANAGEMENT")
                print("1. List Categories")
                print("2. Add Category")
                print("3. Delete Category")
                print("4. Return to Main Menu")
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
                        print(f'Category {name} created successfully!')
                    except Exception as e:
                        print(f'Error: {e}')

                # delete
                elif cat_choice == "3":
                    categories = category_repo.list_categories()
                    category_repo.display_categories(categories)
                    cat_id = input("Enter category ID to delete: ").strip()
                    if cat_id.isdigit():
                        confirm = input("This will unlink the category from all tasks. Continue? (y/n): ").strip().lower()
                        if confirm == 'y':
                            category_repo.delete_category(int(cat_id))
                            print("Category deleted successfully!")
                
                # exit
                elif cat_choice == "4":
                    break
                else:
                    print("Invalid choice!")

                    

        # exit
        elif cmd == "12":
            print("Goodbye!")
            break
        else:
            print("Unknown command. Select a command from the main menu.")
        
        print()

if __name__ == "__main__":
    main()
