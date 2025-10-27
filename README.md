# Sprint 1 Release - Smart Scheduler (Python)

Team: Group 32  
Members: Jace Keagy, K Li, Lan Lim, Jenna Luong, Kit Magar, Bryce Martin
Sprint Duration: Oct 12 - Oct 26, 2025  
Release: v0.1.1

## Features Implemented (Sprint 1)
- US-01: Basic interface shell (CLI)
- US-02: Add task (name, duration)
- US-03: View tasks
- US-04: Select/unselect task
- US-14: SQLite persistence (migrations)
- US-16: Export list to file
- US-21: Delete task

## How to Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m src.app
```

## Demo Script
1. 1 -> name=Study, duration=60
2. 3
3. 4 -> id=1
4. 3
5. 6

## Acceptance Test Checklist
- Start app -> help text visible
- Add valid/invalid tasks -> correct messages
- List tasks -> correct rows
- Toggle selection -> persists after restart


## License
MIT
