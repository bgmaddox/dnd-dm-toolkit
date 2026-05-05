
# Packaging Plan: DM Toolkit Portable

## 1. Goal
Provide a 'zero-configuration' experience for non-technical users on macOS and Windows. The user should be able to double-click an icon and have the toolkit ready to use in their browser.

## 2. Component: The Smart Launchers
Scripts that automate the 'developer' steps (Auto-Venv, API Key Guard, Server Start, Browser Open).

### macOS: `run_toolkit.command`
- Shell script that checks for `.venv`, installs requirements, checks for `.env`, and starts the server.
- Uses `open http://localhost:8000` to launch the browser.

### Windows: `run_toolkit.bat`
- Batch script that performs identical checks.
- Checks for `python` or `py` launcher.
- Uses `start http://localhost:8000` to launch the browser.
- Uses `timeout /t 5` or similar to keep the window open if an error occurs during startup.

## 3. Component: The Setup Wizard (server.py update)
- Add a check in 'server.py' startup logic.
- If 'ANTHROPIC_API_KEY' is not found in environment or .env:
  - Open a simple 'tkinter' popup window or a local "Setup" web page.
  - User pastes key(s) -> Script writes '.env' file -> Server continues.
- **Optimization:** Also prompt for `GEMINI_API_KEY` as an optional secondary key.

## 4. Component: Native App Wrappers
"Double-clickable" icons with custom branding.

### macOS: Automator App
- Use macOS Automator to create an 'Application' that runs the `run_toolkit.command`.
- Allows assigning a custom icon (e.g., a D20 or DM Shield).
- **Update:** Provided `tools/build_macos_app.sh` to automate this.

### Windows: Desktop Shortcut
- A standard Windows Shortcut (`.lnk`) pointing to `run_toolkit.bat`.
- Set "Start in" property to the project root.
- Change icon via Shortcut Properties -> Change Icon (point to a bundled `.ico` file).

## 5. Distribution Strategy
1. Zip the entire `DnD/` directory **EXCEPT** `.git`, `.venv`, and `__pycache__`.
2. **For macOS:** The user unzips and moves the folder to `/Applications` or `Documents`.
3. **For Windows:** The user unzips and moves the folder to `C:\Users\Public` or their `Documents` folder.
4. Double-click the 'DM Toolkit' app icon (Mac) or 'Start Toolkit' shortcut (Win) to start.

## 6. Component: Update Management
- **GitHub Distribution:** Host the project on GitHub.
- **Releases:** Use GitHub Releases to upload the "portable" ZIP files.
- **Auto-Check:** Add an `/api/version-check` endpoint that pings the GitHub API for the latest release tag.
- **UI Indicator:** If a newer version is available, show a subtle "Update Available" button in the tool headers.

## 7. Component: Resilience & Port Handling
- **Port Selection:** Instead of hardcoded 8000, the server should attempt to bind to 8000, and increment if busy.
- **Python Check:** Launchers (`.command` and `.bat`) should verify `python --version` first. If missing, open the browser to `python.org/downloads` and explain requirements.

## 8. Implementation Checklist
- [x] Create `run_toolkit.command` (macOS).
- [x] Create `run_toolkit.bat` (Windows).
- [x] Draft `USER_GUIDE.md` (Non-technical version, platform-specific steps).
- [x] Add `tkinter` API key check snippet to `server.py` (via `setup_wizard.py`).
- [x] Implement "Check for Updates" logic via GitHub API (added to `server.py`).
- [x] Create an Automator/App wrapper script (`tools/build_macos_app.sh`).
- [x] Generate a `.ico` file for Windows (`tools/app_icon.ico`).
- [x] Generate a `.icns` or high-res PNG for macOS (`tools/app_icon.png`).
