# File: src/app.py
# Description: Simple CLI to interact with the scheduler DB.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-10-21

from src.db import run_migrations, get_connection
from src.task_repo import TaskRepo
from src.manual_scheduler import run_manual_scheduler

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
          "5. Export task info\n",
          "6. Manual Scheduler\n",
          "7. Automatic Scheduler\n",
          "8. Quit")
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
                repo.add_task(name, duration)
                print("Task added.")
            except Exception as e:
                print("Error:", e)
        # delete a task
        elif cmd == "2":
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
                task_id, name, duration, selected = t
                status = "✓" if selected else "✗"
                print(f"{task_id}. {name} ({duration} minutes) [{status}]")
        # select a task
        elif cmd == "4":
            tid_str = input("Task ID: ").strip()
            try:
                tid = int(tid_str)
                new_val = repo.toggle_select(tid)
                print(f"Selection toggled. [{status}]")
            except Exception as e:
                print("Error:", e)
        # export task info
        elif cmd == "5":
            rows = repo.list_tasks()
            with open("tasks_output.txt", "w", encoding="utf-8") as f:
                if not rows:
                    f.write("(no tasks yet)\n")
                else:
                    for t in rows:
                        line = f"{t[0]}. {t[1]} - {t[2]} min - selected={bool(t[3])}\n"
                        f.write(line)
        # manual scheduler
        elif cmd == "6":
            run_manual_scheduler(user_id)
        # automatic scheduler
        elif cmd == "7":
            continue
        # exit
        elif cmd == "8":
            print("Goodbye!")
            break
        else:
            print("Unknown command. Select a command from the main menu.")
        
        print()

if __name__ == "__main__":
    main()
