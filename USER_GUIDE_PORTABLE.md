# DM Toolkit: User Guide (Portable)

Welcome to the DM Toolkit! This guide will help you get started with the portable version of the toolkit on your Mac or Windows computer.

## 1. Installation
1. Download the `dm-toolkit-portable.zip` file.
2. Unzip the folder to a location of your choice (e.g., your Documents folder).
3. (Optional) On Mac, you can drag the folder to your `/Applications` folder.

## 2. Launching the Toolkit

### macOS
1. Open the toolkit folder.
2. Double-click `run_toolkit.command`.
3. If you see a warning about "Unidentified Developer", Right-Click (or Control-Click) the file and select **Open**, then click **Open** again in the popup.
4. A terminal window will open, and your web browser should launch to `http://localhost:8000`.

### Windows
1. Open the toolkit folder.
2. Double-click `run_toolkit.bat`.
3. If you see a "Windows protected your PC" warning, click **More info** and then **Run anyway**.
4. A command prompt will open, and your web browser should launch to `http://localhost:8000`.

## 3. First-Time Setup
On the first launch, a window will pop up asking for your **Anthropic API Key**.
- This key is required for the AI features (like Combat Tactics and NPC generation).
- You can also optionally provide a **Gemini API Key**.
- These keys are stored safely in a `.env` file inside your toolkit folder. They are never shared or sent to anyone except the AI providers.

## 4. Updates
The toolkit will occasionally check for updates from GitHub. If an update is available, you will see an "Update Available" notification in the tool. To update:
1. Download the latest version.
2. Replace your old toolkit folder with the new one (but keep your `campaign/` and `tools/npcs/` folders if you want to keep your data!).

## 5. Troubleshooting
- **Python Missing:** If the launcher says Python is missing, follow the link it provides to install Python 3.
- **Port Busy:** If the server fails to start because a port is busy, try closing other programs or restart the toolkit.
- **Browser doesn't open:** If your browser doesn't open automatically, just go to `http://localhost:8000` manually in Chrome or Firefox.
- **Update Issues:** Check `https://github.com/bgmaddox/dnd-dm-toolkit` for manual downloads and issue reporting.
