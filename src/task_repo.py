# File: src/task_repo.py
# Description: Repository layer for CRUD on tasks.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-10-21

from typing import List, Tuple
from datetime import datetime, timedelta
from src.db import get_connection


class TaskRepo:
    """Data access class for the 'tasks' table (US-02, US-03, US-04)."""

    def __init__(self, user_id: int):
        self.user_id = user_id

    # BLOCK: validate_and_insert (US-02)
    # Purpose: Validate name/duration, then insert task in one transaction.
    def add_task(
        self,
        name: str,
        duration: int,
        category_id: int | None = None,
        location: str | None = None,
        cost: float | None = None,
    ) -> int:
        """Add a new task (US-02). Raises ValueError if invalid. Returns task id."""
        if not isinstance(duration, int):
            raise ValueError("Duration must be an integer.")
        if not name or duration <= 0:
            raise ValueError("Invalid name or duration.")
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO tasks "
                "(user_id, name, duration_minutes, selected, "
                "task_type, fixed_time, cost, category_id, location) "
                "VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)",
                (self.user_id, name.strip(), duration, 0, "flexible", cost, category_id, location),
            )
            return cur.lastrowid

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID. Returns True if deleted, False if not found."""
        if not isinstance(task_id, int) or task_id <= 0:
            raise ValueError("Invalid task ID.")
        with get_connection() as conn:
            # Check if exists
            cur = conn.execute(
                "SELECT 1 FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, self.user_id),
            )
            row = cur.fetchone()
            if row is None:
                return False
            # Remove in SQL
            conn.execute(
                "DELETE FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, self.user_id),
            )
            return True

    def list_tasks(self) -> List[Tuple[int, str, int, int, str, str, float]]:
        """Return all tasks for this user (US-03)."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id, name, duration_minutes, selected, task_type, fixed_time, cost "
                "FROM tasks WHERE user_id=? ORDER BY created_at",
                (self.user_id,),
            )
            return cur.fetchall()

    def toggle_select(self, task_id: int) -> int:
        """Toggle task 'selected' flag (US-04). Returns new selected value (0/1)."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT selected FROM tasks WHERE id=? AND user_id=?",
                (task_id, self.user_id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Task not found.")
            new_value = 0 if row[0] else 1
            conn.execute(
                "UPDATE tasks SET selected=? WHERE id=? AND user_id=?",
                (new_value, task_id, self.user_id),
            )
            return new_value

    def set_task_type(
        self,
        task_id: int,
        task_type: str,
        fixed_time: str | None = None,
    ) -> None:
        """Set the task_type field for a task."""
        with get_connection() as conn:
            if task_type == "fixed" and fixed_time:
                # validate fixed_time format HH:MM AM/PM
                try:
                    # convert HH:MM AM/PM to 24-hour HH:MM
                    time_obj = datetime.strptime(fixed_time, "%I:%M %p").time()
                    conn.execute(
                        "UPDATE tasks SET task_type=?, fixed_time=? "
                        "WHERE id=? AND user_id=?",
                        (task_type, time_obj.strftime("%H:%M"), task_id, self.user_id),
                    )
                except ValueError:
                    raise ValueError("Invalid time format. Use HH:MM AM/PM.")
            else:
                # flexible task - clear fixed_time
                conn.execute(
                    "UPDATE tasks SET task_type=?, fixed_time=NULL "
                    "WHERE id=? AND user_id=?",
                    ("flexible", task_id, self.user_id),
                )
            conn.commit()
    
    def edit_duration(
        self,
        task_id: int,
        duration_minutes: int,
    ) -> None:
        """Change duration field for a task."""
        with get_connection() as conn:
            try:
                conn.execute(
                    "UPDATE tasks SET duration_minutes=? "
                    "WHERE id=? AND user_id=?",
                    (duration_minutes, task_id, self.user_id),
                )
            except ValueError:
                    raise ValueError("Invalid duration input.")
            conn.commit()

    def get_fixed_tasks(self):
        """Get all fixed tasks for the user."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id, name, duration_minutes, fixed_time "
                "FROM tasks WHERE user_id=? AND task_type='fixed' "
                "AND selected=1 ORDER BY fixed_time",
                (self.user_id,),
            )
            return cur.fetchall()

    def detect_fixed_task_conflicts(self):
        """Detect time conflicts between fixed tasks."""
        fixed_tasks = self.get_fixed_tasks()
        conflicts = []

        # Check each pair of fixed tasks for overlap
        for i in range(len(fixed_tasks)):
            for j in range(i + 1, len(fixed_tasks)):
                task1_id, task1_name, task1_duration, task1_time = fixed_tasks[i]
                task2_id, task2_name, task2_duration, task2_time = fixed_tasks[j]

                # convert times to datetime for comparison
                time1 = datetime.strptime(task1_time, "%H:%M")
                time2 = datetime.strptime(task2_time, "%H:%M")
                end_time1 = time1 + timedelta(minutes=task1_duration)

                # Check for overlap
                if time2 < end_time1:
                    conflicts.append(
                        {
                            "task1": (
                                task1_id,
                                task1_name,
                                task1_time,
                                task1_duration,
                            ),
                            "task2": (
                                task2_id,
                                task2_name,
                                task2_time,
                                task2_duration,
                            ),
                        }
                    )
        return conflicts

    def get_task_type(self, task_id: int) -> str:
        """Get the type (fixed/flexible) of a task."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT task_type FROM tasks WHERE id=? AND user_id=?",
                (task_id, self.user_id),
            )
            result = cur.fetchone()
            return result[0] if result else "flexible"

    def get_fixed_time(self, task_id: int) -> str | None:
        """Get the fixed time for a task if it exists."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT fixed_time FROM tasks WHERE id=? AND user_id=?",
                (task_id, self.user_id),
            )
            result = cur.fetchone()
            return result[0] if result else None

    def set_task_category(self, task_id: int, category_id: int) -> None:
        """Set the category_id for a task."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id FROM categories WHERE id=? AND user_id=?",
                (category_id, self.user_id),
            )
            if not cur.fetchone():
                raise ValueError("Category not found.")
            conn.execute(
                "UPDATE tasks SET category_id=? WHERE id=? AND user_id=?",
                (category_id, task_id, self.user_id),
            )
            conn.commit()

    def remove_task_category(self, task_id: int) -> None:
        """Remove the category association from a task."""
        with get_connection() as conn:
            conn.execute(
                "UPDATE tasks SET category_id=NULL WHERE id=? AND user_id=?",
                (task_id, self.user_id),
            )
            conn.commit()

    def get_task_location(self, task_id: int) -> str | None:
        """Get the location of a task, or None if not set."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT location FROM tasks WHERE id=? AND user_id=?",
                (task_id, self.user_id),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def get_tasks_by_category(self, category_id: int):
        """Get all tasks for a specific category."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id, name, duration_minutes, selected, task_type, fixed_time "
                "FROM tasks WHERE user_id=? AND category_id=? ORDER BY name",
                (self.user_id, category_id),
            )
            return cur.fetchall()
        

    def get_selected_tasks(self):
        """Get all selected tasks for the user."""
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT id, name, duration_minutes, task_type, fixed_time, cost "
                "FROM tasks WHERE user_id=? AND selected=1 ORDER BY id",
                (self.user_id,),
            )
            return cur.fetchall()
