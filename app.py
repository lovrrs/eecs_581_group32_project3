# File: src/app.py
# Description: Simple CLI to interact with the scheduler DB.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-10-21

from src.db import run_migrations, get_connection
from src.task_repo import TaskRepo

def _get_default_user_id() -> int:
    with get_connection() as conn:
        cur = conn.execute("SELECT id FROM users WHERE username=?", ("default",))
        row = cur.fetchone()
        return row[0]

def main():
    run_migrations()
    user_id = _get_default_user_id()
    repo = TaskRepo(user_id=user_id)
    print("Welcome to Sprint 1 Scheduler!\n")
    print("MAIN MENU\n",
          "1. Add a new task\n",
          "2. Delete a task\n",
          "3. List all tasks\n",
          "4. Select a task by ID\n",
          "5. Export task info\n",
          "6. Quit")
    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if cmd == "1":
            name = input("Task name: ").strip()
            duration_str = input("Duration (min, integer > 0): ").strip()
            try:
                duration = int(duration_str)
                repo.add_task(name, duration)
                print("Task added.")
            except Exception as e:
                print("Error:", e)
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
        elif cmd == "3":
            rows = repo.list_tasks()
            if not rows:
                print("(no tasks yet)")
            for t in rows:
                print(f"{t[0]}. {t[1]} ({t[2]} minutes) - selected={bool(t[3])}")
        elif cmd == "4":
            tid_str = input("Task ID: ").strip()
            try:
                tid = int(tid_str)
                new_val = repo.toggle_select(tid)
                print(f"Selection toggled. selected={bool(new_val)}")
            except Exception as e:
                print("Error:", e)
        elif cmd == "5":
            rows = repo.list_tasks()
            with open("tasks_output.txt", "w", encoding="utf-8") as f:
                if not rows:
                    f.write("(no tasks yet)\n")
                else:
                    for t in rows:
                        line = f"{t[0]}. {t[1]} - {t[2]} min - selected={bool(t[3])}\n"
                        f.write(line)
        elif cmd == "6":
            print("Goodbye!")
            break
        else:
            print("Unknown command. Select a command from the main menu.")

if __name__ == "__main__":
    main()
