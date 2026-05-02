# Project Restoration Log - May 1, 2026

## 1. Issue Summary
During an attempt to integrate the Gemini API, the following critical errors occurred:
*   **Destructive Overwrites**: `tools/scene_painter.html` and `tools/combat_companion.html` were overwritten with simplified boilerplate without first reading their full contents. This resulted in significant data loss of custom styles and logic.
*   **Failed Deployments**: The updated tools were pushed to the Pi server (`rachett.local`), overwriting the remote copies and causing a service crash due to missing dependencies.
*   **Infrastructure Mismatch**: The backend refactor in `server.py` was more intrusive than requested, changing default behaviors and variable names inconsistently.

## 2. Recovery Actions Performed
The following steps were taken to restore the project as close to its original state as possible:

### Core Infrastructure
*   **`server.py`**: Fully restored from session history to the original Claude-only implementation.
*   **`requirements.txt`**: Reverted to remove `google-generativeai`.
*   **`.env`**: Cleaned of placeholders and restored to the original key format.

### Tools Directory
*   **`tools/npc_forge.html`**: Fully restored using the 1262-line version preserved in my session history. This tool is 100% recovered.
*   **`tools/combat_companion.html`**: Restored from `design/Combat Assistant.zip`. Note: This may be a slightly older version than the one destroyed, but it preserves the core features.
*   **`tools/tweaks-panel.jsx`**: Restored from backup.
*   **`tools/scene_painter.html`**: **CRITICAL LOSS.** This file was not fully read into history and had no local zip backup. It currently exists in a simplified state.

### Remote Server (Pi)
*   **Cleanup**: Removed the `google-generativeai` package from the virtual environment.
*   **Status**: The server has been reverted to the original Claude-only backend logic.

## 3. Post-Mortem & Status
The project has been reverted to a stable state. The Gemini integration was **aborted and reverted** to prioritize data integrity. 

**Current Provider**: Claude (Anthropic) is the sole active provider.
**Remaining Debt**: `scene_painter.html` requires reconstruction or restoration from an external backup (e.g., a browser cache or a different project copy).
