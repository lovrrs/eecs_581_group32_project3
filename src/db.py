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
        raise FileNotFoundError("Migration file not found at db/migrate_001_init.sql")
    with get_connection() as conn:
        sql = migration.read_text(encoding="utf-8")
        conn.executescript(sql)
        # Ensure default user exists for Sprint 1 simplicity
        cur = conn.execute("SELECT id FROM users WHERE username=?", ("default",))
        if not cur.fetchone():
            conn.execute("INSERT INTO users (username) VALUES (?)", ("default",))
