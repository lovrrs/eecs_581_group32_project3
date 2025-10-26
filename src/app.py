# File: src/app.py
# Description: Simple CLI to interact with the scheduler DB.
# Programmer(s): K. Li
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
    print("Welcome to Sprint 1 Scheduler! Type 'help' for commands.")
    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if cmd == "help":
            print("Commands: add, list, select, quit")
            print("  add    -> create a new task")
            print("  list   -> list all tasks")
            print("  select -> toggle selection by id")
            print("  quit   -> exit program")
        elif cmd == "add":
            name = input("Task name: ").strip()
            duration_str = input("Duration (min, integer > 0): ").strip()
            try:
                duration = int(duration_str)
                repo.add_task(name, duration)
                print("Task added.")
            except Exception as e:
                print("Error:", e)
        elif cmd == "list":
            rows = repo.list_tasks()
            if not rows:
                print("(no tasks yet)")
            for t in rows:
                print(f"{t[0]}. {t[1]} - {t[2]} min - selected={bool(t[3])}")
        elif cmd == "select":
            tid_str = input("Task ID: ").strip()
            try:
                tid = int(tid_str)
                new_val = repo.toggle_select(tid)
                print(f"Selection toggled. selected={bool(new_val)}")
            except Exception as e:
                print("Error:", e)
        elif cmd == "quit":
            print("Goodbye!")
            break
        else:
            print("Unknown command. Type 'help'.")

if __name__ == "__main__":
    main()
