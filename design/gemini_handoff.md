# Gemini Handoff — DM Toolkit

**Prepared by:** Claude Sonnet 4.6  
**Date:** 2026-05-05  
**Branch to work on:** `main` (or a new feature branch off main)

---

## Project Overview

This is a personal D&D Dungeon Master toolkit running as a FastAPI server with plain HTML/JS frontends. It is deployed on a **Raspberry Pi** at `rachett.local:8502` (always-on, headless, systemd service) and is also distributed as a **portable desktop launcher** (`run_toolkit.command` / `run_toolkit.bat`) for a friend's Mac/Windows machine.

**The two deployment modes are controlled by a single env var:**
- Pi: `PORTABLE` is never set → uses `PORT=8502`, no setup wizard, no browser auto-open
- Desktop: launcher sets `PORTABLE=1` → dynamic port, tkinter setup wizard, browser auto-opens

**Tech stack:** FastAPI · Python 3.13 · Alpine.js (Session Companion) · React/JSX-in-HTML (NPC Forge, Combat Companion) · plain JS (Scene Painter, DM Learning Guide) · Anthropic Claude API · optional Gemini free tier

---

## Current State — What Is Done and Working

### Tools (all in `tools/`)
| File | Status |
|------|--------|
| `npc_forge.html` | ✅ Complete — Class, Level Tier, Disposition, Story Role fields; portrait generation (Pollinations.ai) with server-side persistence; two-tier NPC library; tool hand-off bus |
| `combat_companion.html` | ✅ Working — HP tracking, initiative, encounter management |
| `scene_painter.html` | ✅ Working — reads `localStorage['dm_toolkit_handoff']` on mount for auto-fill |
| `session_companion.html` | ✅ Complete — AI chat with tiered campaign context, raw notes, session finalize/summarize, past sessions list, resume conversation |
| `dm_learning_guide.html` | ✅ Static reference tool |

### Backend (`server.py`)
All endpoints working. Key additions from this cycle:
- `POST /api/ai/chat` — Session Companion chat with role-alternation enforcement
- `POST /api/session/start|notes/append|finalize` — session lifecycle
- `GET /api/session/summaries/{campaign}` — lists finalized session `.md` files
- `GET/POST /api/session/chat/{campaign}/{n}` — persists chat history per session
- `POST /api/npcs/{id}/portrait` — downloads portrait from Pollinations and saves locally
- `PORTABLE`/`PORT` env var separation
- All `client.messages.create()` calls guarded against `None` client
- Model updated from hardcoded `claude-3-5-sonnet-20241022` → `claude-sonnet-4-6`

### Icons
All 5 tools have tab favicons. Assets in `tools/`:
- `DnDIcon-Small.png` — red dragon (NPC Forge, Session Companion)
- `DnDIcon-Green.png` — green dragon (Scene Painter, DM Learning Guide)
- `DnDIcon-Blue.png` — blue dragon (Combat Companion)
- `DnDIcon-Computer.png` — open tome app icon (setup wizard window, future .app packaging)
- `DnDIconSet.png` — source file with all 3 badges side-by-side

### Campaign Loader (`campaign_loader.py`)
Tiered context system:
1. `WORLD.md` + `FACTIONS.md` + `DM_REFERENCE.md` (base layer)
2. Lean PC stats from `pcs/*.md`
3. BM25-matched NPC/location files (`utils/bm25_index.py`) — top 2 matches per query
4. Recent session summaries (`sessions/session_N.md`)

Token budget: 4,000. Context header includes token count.

### Portable Launcher
- `run_toolkit.command` (macOS) / `run_toolkit.bat` (Windows) — sets up `.venv`, installs deps, runs server with `PORTABLE=1`
- `setup_wizard.py` — tkinter GUI for first-time API key entry, uses `DnDIcon-Computer.png` as window icon, fully headless-safe (skips silently on Pi)

---

## Pending Work

### Priority 1 — Small, clearly-scoped fixes

**1. Prep Mode Save (Session Companion)**  
`finalizeSession()` in `tools/session_companion.html` line ~745 currently just alerts "Prep notes saved." with no actual persistence. Should save `prepHistory` to `campaign/{name}/sessions/chat_{sessionNumber}_prep.json` using the existing `/api/session/chat/{campaign}/{session_number}` endpoint pattern (or a new `/api/session/prep/{campaign}/{n}` endpoint).

**2. `DM_REFERENCE.md` creation**  
`campaign_loader.py` loads `campaign/{campaign}/DM_REFERENCE.md` as part of the base layer. This file does not exist yet. Create a template at `campaign/lmop/DM_REFERENCE.md` with sections for:
- House Rules
- Session Schedule / Player Info
- Campaign Tone & Themes
- Important Decisions Made

**3. PC sheet regex fragility (`_get_lean_pc_stats` in `campaign_loader.py`)**  
The lean PC stats function uses `\*\*Class:\*\*` patterns to extract info. This silently returns empty if the PC markdown files use different formatting. Check the actual format of the PC files in `campaign/lmop/pcs/` and update the regex (or make it more flexible) to match them correctly.

---

### Priority 2 — Feature completions

**4. NPC Forge header provider toggle — cleanup**  
There are two AI provider toggles in NPC Forge: one in the Tweaks panel (right side) and a duplicate pill in the header. Both are wired to the same `tweaks.aiProvider` state and work correctly. The header one is more visible and convenient; remove the one from the Tweaks panel to eliminate the duplicate. In `tools/npc_forge.html`, find `TweakRadio label="AI Provider"` and remove it.

**5. Portrait generation — cooldown UX**  
Portrait generation hits Pollinations.ai (free, no key needed). No hard rate limit, but back-to-back requests for a full NPC roster can be slow. Add a brief cooldown state after generation: disable the Generate button for ~5 seconds and show "Cooling down..." to prevent rapid-fire requests. In `tools/npc_forge.html`, the `generatePortrait` function at line ~1200 sets `setPortraitLoading`. After the `img.onload` callback, add a short `setTimeout` before re-enabling.

**6. BM25 score threshold tuning**  
`utils/bm25_index.py` uses a hardcoded threshold of `0.1`. This has never been tested against real campaign files. Once actual NPC/location markdown files exist in `campaign/lmop/`, run test queries and adjust the threshold. It may need to be lower (more permissive) or higher (more selective) depending on file density. The threshold is at line ~47 of `utils/bm25_index.py`.

---

### Priority 3 — macOS app packaging (aspirational)

**7. macOS `.app` bundle**  
`design/packaging_plan.md` describes this in detail. The goal is a double-clickable `.app` for macOS using PyInstaller. The `DnDIcon-Computer.png` is the intended icon — convert it to `.icns` format first:
```bash
# macOS icon conversion:
mkdir MyIcon.iconset
sips -z 1024 1024 tools/DnDIcon-Computer.png --out MyIcon.iconset/icon_512x2.png
iconutil -c icns MyIcon.iconset
```
Then reference the `.icns` in the PyInstaller spec. See `design/packaging_plan.md` for the full spec.

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
