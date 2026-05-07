# Project Instructions: DnD Toolkit

## Architecture & Workflow
- **Branching Mandate:** Before starting any implementation task, create a new feature branch from `main`. Use a descriptive name like `feat-feature-name` or `fix-bug-name`.
- **Validation:** Always verify changes by running the server locally before committing.

## Deployment
- **Pi Service:** The app runs as `dnd-toolkit.service` on the Pi.
- **Pi Path:** `/home/bgmaddox/dnd`
- **Deploy Script:** `ssh rachett 'bash ~/deploy.sh dnd'`

## Local Development
- **Run Command:** `./run_toolkit.command` or `python server.py`
- **Environment:** Requires a `.venv` with dependencies from `requirements.txt`.
