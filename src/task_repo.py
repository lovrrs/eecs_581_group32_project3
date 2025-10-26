# File: src/task_repo.py
# Description: Repository layer for CRUD on tasks.
# Programmer(s): K. Li
# Created: 2025-10-21

from typing import List, Tuple
from src.db import get_connection

class TaskRepo:
    """Data access class for the 'tasks' table (US-02, US-03, US-04)."""

    def __init__(self, user_id:int):
        self.user_id = user_id

    # BLOCK: validate_and_insert (US-02)
    # Purpose: Validate name/duration, then insert task in one transaction.
    def add_task(self, name:str, duration:int) -> int:
        """Add a new task (US-02). Raises ValueError if invalid. Returns task id."""
        if not isinstance(duration, int):
            raise ValueError("Duration must be an integer.")
        if not name or duration <= 0:
            raise ValueError("Invalid name or duration.")
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO tasks (user_id, name, duration_minutes) VALUES (?, ?, ?)",
                (self.user_id, name.strip(), duration),
            )
            return cur.lastrowid

    def list_tasks(self) -> List[Tuple[int, str, int, int]]:
        """Return all tasks for this user (US-03)."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id, name, duration_minutes, selected FROM tasks WHERE user_id=? ORDER BY created_at",
                (self.user_id,)
            )
            return cur.fetchall()

    def toggle_select(self, task_id:int) -> int:
        """Toggle task 'selected' flag (US-04). Returns new selected value (0/1)."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT selected FROM tasks WHERE id=? AND user_id=?",
                (task_id, self.user_id)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Task not found.")
            new_value = 0 if row[0] else 1
            conn.execute(
                "UPDATE tasks SET selected=? WHERE id=? AND user_id=?",
                (new_value, task_id, self.user_id)
            )
            return new_value
