# File: src/db.py
# Description: Handles DB connection and migration execution.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-10-20
# Revisions:
#   2025-10-22 - Added run_migrations()
# Preconditions: SQLite3 installed; migration file exists.
# Postconditions: Database schema ready.

import sqlite3
from pathlib import Path

DB_PATH = Path("scheduler.db")


def get_connection():
    """Return a SQLite3 connection object."""
    return sqlite3.connect(DB_PATH)


def run_migrations():
    """Run initial SQL migration to create tables if needed."""
    migration = Path("db/migrate_001_init.sql")
    if not migration.exists():
        raise FileNotFoundError(
            "Migration file not found at db/migrate_001_init.sql"
        )
    with get_connection() as conn:
        # run migration if any required table is missing
        sql = migration.read_text(encoding="utf-8")
        conn.executescript(sql)

        # verify tables created
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cur.fetchall()}

        #  Ensure 'location' column exists on tasks table for travel-time logic
        cur = conn.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cur.fetchall()]
        if "location" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN location TEXT")

        # Ensure default user exists for Sprint 1 simplicity
        cur = conn.execute(
            "SELECT id FROM users WHERE username=?", ("default",)
        )
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO users (username) VALUES (?)", ("default",)
            )

        # default categories
        cur = conn.execute(
            "SELECT COUNT(*) FROM categories WHERE user_id = "
            "(SELECT id FROM users WHERE username='default')"
        )
        if cur.fetchone()[0] == 0:
            default_categories = [
                "Work",
                "Personal",
                "Health",
                "Chores",
                "Meals",
                "Leisure",
            ]
            for category in default_categories:
                conn.execute(
                    "INSERT OR IGNORE INTO categories (user_id, name) "
                    "VALUES ((SELECT id FROM users WHERE username='default'), ?)",
                    (category,),
                )

        # default tasks
        cur = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id = "
            "(SELECT id FROM users WHERE username='default')"
        )
        if cur.fetchone()[0] == 0:
            # get default category IDs
            cur = conn.execute(
                "SELECT id, name FROM categories WHERE user_id = "
                "(SELECT id FROM users WHERE username='default')"
            )
            category_map = {name: id for id, name in cur.fetchall()}

            conn.execute(
                "INSERT INTO tasks (user_id, name, duration_minutes, "
                "selected, category_id) "
                "VALUES ((SELECT id FROM users WHERE username='default'), "
                "?, ?, 1, ?)",
                ("Break", 15, "Personal"),
            )

            default_tasks = [
                ("Breakfast", 45, "Meals"),
                ("Lunch", 45, "Meals"),
                ("Dinner", 45, "Meals"),
                ("Exercise", 45, "Health"),
                ("Laundry", 20, "Chores"),
                ("Study", 60, "Personal"),
                ("Team Meeting", 60, "Work"),
                ("Reading", 30, "Leisure"),
                ("Email Management", 30, "Work"),
                ("Work", 90, "Work"),
                ("Go on a Walk", 20, "Health"),
                ("Nap", 20, "Personal"),
                ("Shower", 20, "Personal"),
                ("Clean", 90, "Chores"),
            ]
            for name, duration, category_name in default_tasks:
                category_id = category_map.get(category_name)
                conn.execute(
                    "INSERT INTO tasks (user_id, name, duration_minutes, "
                    "selected, category_id) "
                    "VALUES ((SELECT id FROM users WHERE username='default'), "
                    "?, ?, 0, ?)",
                    (name, duration, category_id),
                )
        conn.commit()
