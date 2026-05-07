## Status — All Priority 1, 2, & 3 tasks completed.

---

## Current State — What Is Done and Working

### Tools (all in `tools/`)
| File | Status |
|------|--------|
| `npc_forge.html` | ✅ Complete |
| `combat_companion.html` | ✅ Complete |
| `scene_painter.html` | ✅ Complete |
| `session_companion.html` | ✅ Complete |
| `dm_learning_guide.html` | ✅ Complete |

### Packaging & Distribution (Priority 3)
- `scripts/package.py` — ✅ Complete. Generates a clean distribution ZIP in `dist/`.
- `tools/build_macos_app.sh` — ✅ Complete. Creates a native macOS `.app` wrapper.
- `scripts/generate_icons.py` — ✅ Complete. Generates `.ico` for Windows.
- `campaign/Example/` — ✅ Complete. A full "Oakhaven" example campaign.
- `run_toolkit.command` / `.bat` — ✅ Complete. Portable launchers.

### Backend (`server.py`)
- `POST /api/session/prep/{campaign}/{n}` — Added for Prep history persistence.
- `GET /api/updates/check` — GitHub release version check implemented.
- `BM25Plus` — Switched to `BM25Plus` for better keyword relevance with low-density files.
- `PORTABLE` mode verified (tkinter wizard + fixed ports on Pi).

### Campaign Context
- **Flexible PC Parsing:** Regex updated in `campaign_loader.py` to handle various markdown styles (e.g., fairy bard sheets).
- **DM Reference:** `campaign/lmop/DM_REFERENCE.md` created with House Rules and Player Info sections.
- **BM25 Tuning:** Verified baseline threshold of `0.1` for `BM25Plus` matches.

---

## Deploy to Pi

When changes are ready:
```bash
git push origin main
ssh rachett 'bash ~/deploy.sh dnd'
```

The Pi pulls from `origin/main`, restarts the `dnd-toolkit.service`, and serves on port 8502.

---

## Important Constraints

- **Never change the root route** (`@app.get("/")` in `server.py`) away from `npc_forge.html`. The Pi navigates to `rachett.local:8502` which hits `/` — it must serve NPC Forge.
- **The Pi is headless** — no tkinter, no webbrowser, no display. `PORTABLE` env var must remain unset on the Pi. The `_is_headless()` check in `setup_wizard.py` guards this.
- **Port 8502** is the Pi's fixed port. On the Pi, uvicorn is launched by systemd directly (not `__main__`), so the `__main__` block only matters for local dev and the portable launcher.
- **Anthropic API:** Use `claude-sonnet-4-6` for reasoning tasks (chat, finalize). Use `claude-haiku-4-5-20251001` for fast/cheap tasks (NPC generation, tactics). Do not use hardcoded model snapshots.
- **Gemini free tier:** The rate limiter in `server.py` (`_gemini_text_limiter`, 14 RPM) must not be removed. Gemini is optional — all Claude paths must work without a Gemini key.
- **Campaign loader:** The loader is called with `query=` from the chat endpoint. Do not add blocking I/O — it's called synchronously inside an async FastAPI route.
- **`requests` library is in `requirements.txt`** — safe to use. `Pillow` is also in requirements.

---

## Key File Map

```
server.py               — FastAPI backend, all API endpoints
campaign_loader.py      — Tiered campaign context builder
utils/bm25_index.py     — BM25 keyword search over campaign files
setup_wizard.py         — Desktop first-run API key wizard
run_toolkit.command     — macOS portable launcher
run_toolkit.bat         — Windows portable launcher

tools/
  npc_forge.html        — NPC generator (React/JSX-in-HTML)
  combat_companion.html — Combat tracker (React/JSX-in-HTML)
  scene_painter.html    — Scene description generator (Alpine.js)
  session_companion.html— AI session chat (Alpine.js)
  dm_learning_guide.html— Static DM reference (plain JS)
  DnDIcon-Small.png     — Red dragon tab icon
  DnDIcon-Green.png     — Green dragon tab icon
  DnDIcon-Blue.png      — Blue dragon tab icon
  DnDIcon-Computer.png  — Desktop app icon (tome + d20 + dragon)

campaign/
  lmop/
    WORLD.md            — Campaign world lore (base context layer 1)
    FACTIONS.md         — Faction relationships (base context layer 1)
    DM_REFERENCE.md     — ⚠️ Does not exist yet — needs to be created
    pcs/                — Player character markdown sheets
    npcs/               — NPC markdown files (indexed by BM25)
    locations/          — Location markdown files (indexed by BM25)
    sessions/
      session_N.md      — Finalized session summaries (context layer 4)
      chat_N.json       — Persisted chat history per session (new)
      transcripts/
        raw_YYYY-MM-DD.txt — Raw session notes

design/
  gemini_review_analysis.md  — Full review of Gemini's original branch
  session_companion_plan.md  — Session Companion design doc
  packaging_plan.md          — Portable/macOS packaging plan
  gemini_handoff.md          — This file
```

---

## Deploy to Pi

When changes are ready:
```bash
git push origin main
ssh rachett 'bash ~/deploy.sh dnd'
```

The Pi pulls from `origin/main`, restarts the `dnd-toolkit.service`, and serves on port 8502.
