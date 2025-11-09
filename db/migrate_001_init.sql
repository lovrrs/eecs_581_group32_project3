/*
File: db/migrate_001_init.sql
Project: EECS 581 - Group 32 - Sprint 1
Description: Initializes SQLite schema for users and tasks
Programmer(s): Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
Created: 2025-10-20
*/
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    selected INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    schedule_type TEXT DEFAULT 'manual',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS schedule_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

-- add task type and fixed time to tasks table
ALTER TABLE tasks ADD COLUMN task_type TEXT CHECK(task_type IN ('flexible', 'fixed')) DEFAULT 'flexible';
ALTER TABLE tasks ADD COLUMN fixed_time TIME;

-- constraint to ensure fixed_time is set for fixed tasks
CREATE TRIGGER validate_fixed_time
BEFORE UPDATE ON tasks FOR EACH ROW
WHEN NEW.task_type = 'fixed' AND NEW.fixed_time IS NULL
BEGIN
    SELECT RAISE(ABORT, 'Fixed tasks must have a fixed_time');
END;