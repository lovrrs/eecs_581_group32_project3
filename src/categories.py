# File: src/categories.py
# Description: Category management for task organization.
# Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
# Created: 2025-11-19

from src.db import get_connection
from typing import List, Tuple
from src.task_repo import TaskRepo
import sqlite3

class CategoryRepo:
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    def create_category(self, name: str) -> int:
        """create a new category"""
        if not name.strip():
            raise ValueError("Category name cannot be empty")
        
        with get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO categories (user_id, name) VALUES (?, ?)",
                    (self.user_id, name.strip())
                )
                conn.commit()
                return conn.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError(f"Category '{name}' already exists")

    def list_categories(self) -> List[Tuple]:
        """list all categories for the user"""
        with get_connection() as conn:
            cursor = conn.execute(
                """SELECT id, name, (SELECT COUNT(*) FROM tasks WHERE category_id = categories.id) as task_count
                  FROM categories WHERE user_id = ?""",
                (self.user_id,)
            )
            return cursor.fetchall()
        
    def delete_category(self, category_id: int):
        """delete a category by id"""
        with get_connection() as conn:
            # remove category association from tasks
            conn.execute(
                "UPDATE tasks SET category_id = NULL WHERE category_id = ? AND user_id = ?",
                (category_id, self.user_id)
            )

            # delete the category
            conn.execute(
                "DELETE FROM categories WHERE id = ? AND user_id = ?",
                (category_id, self.user_id)
            )
            conn.commit()

    def display_categories(self, categories):
        """display categories in formatted list"""
        if not categories:
            print("No categories found.")
            return

        # sort categories by id
        categories.sort(key=lambda x: x[0])

        print("\n" + "="*50)
        print("CATEGORIES")
        print("="*50)
        for cat_id, name, task_count in categories:
            print(f"{cat_id:2d}. {name} ({task_count} tasks):")
            print("-"*50)
            tasks = TaskRepo(self.user_id).get_tasks_by_category(cat_id)

            if not tasks:
                print("    No tasks in this category.")
            else:
                for task in tasks:
                    task_id, task_name, duration, selected, task_type, fixed_time = task
                    status = "✓" if selected else "✗"
                    print(f"    - {task_name} ({duration} mins) [{task_type}]")
            print()
        print("="*50)    
            