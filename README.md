# Sprint 1 Release - Smart Scheduler (Python)

Team: Group 32  
Members: K Li
Sprint Duration: Oct 12 - Oct 26, 2025  
Release: v0.1.0

## Features Implemented (Sprint 1)
- US-01: Basic interface shell (CLI)
- US-02: Add task (name, duration)
- US-03: View tasks
- US-04: Select/unselect task
- US-14: SQLite persistence (migrations)

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
1. add -> name=Study, duration=60
2. list
3. select -> id=1
4. list
5. quit

## Acceptance Test Checklist
- Start app -> help text visible
- Add valid/invalid tasks -> correct messages
- List tasks -> correct rows
- Toggle selection -> persists after restart


## License
MIT
