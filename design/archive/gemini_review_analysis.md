# Gemini Branch Review — Analysis & Planning Notes

**Branch:** `gemini-review`  
**Date reviewed:** 2026-05-05  
**Files changed:** 20 (5 modified, 15 new)

---

## Overview

Gemini's work can be summarized in three big bets:

1. **Session Companion** — a new fourth tool (AI chat assistant) with a full backend lifecycle
2. **Portable Launcher** — scripts and a setup wizard to run the toolkit without terminal knowledge
3. **NPC Forge upgrades** — AI portrait generation, new filter fields, and a hand-off bus between tools

The backend (`server.py`, `campaign_loader.py`) was significantly expanded to support all three, and a new `utils/` module adds BM25 semantic search for campaign files.

The design doc in `design/session_companion_plan.md` is thorough and worth reading — it was clearly written first and then implemented against, which is a good sign for coherence.

---

## 1. Session Companion (`tools/session_companion.html` + new server endpoints)

### What it is
A 645-line Alpine.js chat interface that acts as an AI co-pilot during a session. You pick a campaign and session number, then ask questions in natural language. The backend loads layered campaign context (world docs, lean PC stats, BM25-matched NPC/location files, and recent session summaries) and routes queries to Claude.

### Backend additions (`server.py`)
| Endpoint | Purpose |
|----------|---------|
| `POST /api/ai/chat` | Main chat — builds tiered context and sends to Claude Sonnet |
| `POST /api/session/start` | Returns a summary of available context for the chosen campaign/session |
| `POST /api/session/notes/append` | Appends timestamped text to a raw notes file |
| `POST /api/session/finalize` | Reads raw notes → sends to Claude → writes a structured session summary `.md` |
| `GET /api/version` | Returns toolkit version |
| `GET /api/updates/check` | Polls GitHub releases API for a newer version |

### Honest assessment

**Strong:**
- The layered context design (Tiers 1–4) is well-thought-out and cost-conscious. Lean PC stats instead of full character sheets is smart.
- The finalize/summarize loop (raw notes → structured session log → future context) is exactly the right approach for keeping API costs low over a campaign.
- BM25 keyword search is a pragmatic choice — no ML model download, zero startup cost, good enough for a campaign-scale corpus of markdown files.
- Alpine.js is the right call; keeps it consistent with no build step.

**Concerns:**
- The root route was changed to point at `session_companion.html` instead of `npc_forge.html`. This would break the existing Pi deployment if merged as-is.
- The `client` (Anthropic) is set to `None` if the key is missing, but `POST /api/ai/chat` and `POST /api/session/finalize` don't check for `None` before calling `client.messages.create()` — those endpoints would throw a `NoneType` error if run without a key.
- The chat model is hardcoded to `claude-3-5-sonnet-20241022` (a specific snapshot). This works today but will drift. Should pull from a config or use the latest alias.
- `POST /api/updates/check` makes a network request to GitHub on every call. Fine for an on-demand check, but it was placed in `server.py` startup-adjacent code. If GitHub is slow it adds latency.
- The `history` normalization in `POST /api/ai/chat` has a `# Simplified for now` comment where role alternation should be enforced. Anthropic's API will reject non-alternating message lists — this is a latent bug.

**Overall verdict:** Worth keeping — the concept is solid and the bones are good. Needs the `None` guard fixed and role alternation enforced before it's stable.

---

## 2. Campaign Loader Upgrades (`campaign_loader.py`)

### What changed
- Token budget raised from 2,000 → 4,000
- Two new helper functions: `_get_lean_pc_stats()` and `_get_recent_summaries()`
- BM25 index integration via `utils/bm25_index.py` — if a `query` is passed, it pulls the top 2 matching entity files
- The old `_matching_files()` hint system is still supported in parallel
- `DM_REFERENCE.md` added to the base layer (this file doesn't exist in the repo yet)
- Context header now includes a token count: `[Campaign context: lmop | Tokens: ~1240]`

### Concerns
- There's a circular import bug: inside `load_campaign_context()`, the `hints` branch does `from campaign_loader import _matching_files` — importing from yourself. This will either throw an `ImportError` or silently shadow the local name. The function is already in scope; just call `_matching_files()` directly.
- `DM_REFERENCE.md` is referenced but doesn't exist anywhere in the repo. The `_read()` call will silently return `""` (which is safe), but it's a missing piece.
- The `_get_lean_pc_stats()` function uses a very specific regex pattern (`\*\*Class:\*\*`) that assumes a particular markdown format for PC sheets. If your character files don't match that format, it returns silent blanks.

**Overall verdict:** The tiered context approach is a genuine improvement over the flat hint system. Fix the circular import before use. Consider creating `DM_REFERENCE.md` as a real file.

---

## 3. BM25 Search (`utils/bm25_index.py`)

A clean, small module (~60 lines). Builds a BM25 index over all `.md` files in a campaign's `npcs/` and `locations/` folders. Called on demand from `campaign_loader.py`.

### Concerns
- The index is rebuilt from disk every time a new `BM25Index` object is created, but the module-level `_indices` dict caches one instance per campaign name. If you add a new NPC file mid-session, the index won't update without a server restart.
- `rank-bm25` is a new dependency (added to `requirements.txt`). Lightweight and fine.
- Score threshold is `0.1` — hardcoded. May need tuning once you have real campaign files to test against.

**Overall verdict:** Keep it. It's small, dependency-light, and solves a real problem (finding the right NPC file without loading everything).

---

## 4. NPC Forge Upgrades (`tools/npc_forge.html`)

### What changed (+515 lines net)
- **Portrait generation**: A new portrait frame UI slot with a `Generate` button. Triggers the existing Gemini image endpoint. Includes regenerate, loading shimmer, and error states.
- **New filter fields**: Class, Level Tier (Minor/Seasoned/Legendary), Disposition (Friendly/Neutral/Hostile/Cautious), and Story Role (Villain/Ally/Rival/Quest Giver/Wild Card). These fields feed into a richer prompt template.
- **Prompt builder refactor**: `buildPrompt()` now assembles a more structured prompt from all the new fields.
- **Sticky Forge button**: The generate button is now `position: sticky; bottom: 0` so it's always visible when scrolling the left panel.
- **Saved NPC list**: Scrollable list capped at 160px with a thin custom scrollbar, rather than unbounded.
- **Tool hand-off bus**: Reads `localStorage['dm_toolkit_handoff']` on load — the Session Companion can pre-fill NPC Forge fields by writing to this key.
- **AI provider toggle**: A Claude/Gemini toggle button in the header (wired to new state but Gemini path implementation is partial).
- **Compact mode**: Portrait scales down to 80px in compact view.

### Concerns
- The `buildPrompt()` function is quite long and assembles a raw string inside the component body. It works but will be hard to maintain as fields grow.
- The Gemini provider toggle is wired in the UI but the actual routing logic in `generateNPC()` doesn't appear fully implemented — selecting Gemini may silently fall back to Claude or throw.
- Portrait generation will hit rate limits quickly if a DM is building a roster of NPCs back-to-back (Gemini image is 3 RPM on free tier).
- The `lore-hint` block at the bottom of the left panel was removed. That was the "Tip of the day" text — not critical, but worth knowing it's gone.

**Overall verdict:** The new fields meaningfully improve NPC generation quality. The portrait feature is nice-to-have but adds complexity and rate limit exposure. Worth keeping the fields; the portrait feature needs rate limit UX (cooldown indicator) before it's stable.

---

## 5. Scene Painter (`tools/scene_painter.html`)

Minimal change — adds a `useEffect` on mount that reads `localStorage['dm_toolkit_handoff']`. If the Session Companion or another tool writes a `{type: 'SCENE', location, mood, keyFeature}` payload, Scene Painter auto-fills its fields.

**Assessment:** Small, clean, correct. Keep it.

---

## 6. Portable Launcher (`run_toolkit.command`, `run_toolkit.bat`, `setup_wizard.py`)

### What it does
- `run_toolkit.command` (macOS) and `run_toolkit.bat` (Windows): shell scripts that check for Python, create a `.venv`, install requirements, and run `server.py`. No terminal knowledge required.
- `setup_wizard.py`: a `tkinter` GUI dialog that runs at startup if `.env` is missing API keys. Prompts for Anthropic key (required) and Gemini key (optional). Validates key format and writes to `.env` via `python-dotenv`.

### Concerns
- `setup_wizard()` is called at the module level in `server.py` (runs on import). This means the GUI dialog pops before FastAPI even starts. On the Pi (headless), this will fail — the `except` branch handles it, but it's fragile. The Pi doesn't need a wizard at all.
- The launcher scripts assume `server.py` is in the same directory as the script. This is true for the local setup but breaks if someone moves the `.command` file.
- `run_toolkit.command` needs execute permissions (`chmod +x`) — Git tracked it with the right mode (`100755`), so this should be fine as long as it's cloned correctly.
- The macOS app packaging pieces (`tools/build_macos_app.sh`, `tools/generate_icon.py`, icon files) are present but incomplete — `build_macos_app.sh` presumably wraps PyInstaller or py2app, but that's not in `requirements.txt`.

**Overall verdict:** The launcher scripts are genuinely useful for a portable/shareable version. The setup wizard is a good idea but needs to be conditional on environment (skip entirely on Linux/Pi). The macOS app packaging is aspirational and not ready.

---

## 7. User Guides (`USER_GUIDE.md`, `USER_GUIDE_PORTABLE.md`)

End-user documentation written for a non-technical audience. Covers setup, API key acquisition, tool descriptions, quitting, and basic troubleshooting.

- `USER_GUIDE.md` is clean and well-written.
- `USER_GUIDE_PORTABLE.md` appears to be a variant for the portable/packaged version.

These are fine to keep, but are probably not needed in the repo root for day-to-day development — they'd make more sense bundled with a release artifact.

---

## 8. Design Documents (`design/packaging_plan.md`, `design/session_companion_plan.md`)

Planning documents Gemini wrote. The session companion plan is genuinely useful and detailed. The packaging plan covers PyInstaller-based distribution, code signing, etc. — aspirational for now.

These are fine to keep in `design/` as references.

---

## Summary Table

| Change | Quality | Recommendation |
|--------|---------|----------------|
| Session Companion UI | Good concept, partially implemented | Keep — fix `None` guard + role alternation |
| Tiered context loader | Solid improvement | Keep — fix circular import + add `DM_REFERENCE.md` |
| BM25 search module | Clean and useful | Keep as-is |
| NPC Forge new fields | Meaningful improvement | Keep |
| NPC Forge portrait generation | Nice-to-have, rate limit risk | Keep — add cooldown UX |
| NPC Forge AI provider toggle | Partially wired | Decide: complete or remove |
| Scene Painter hand-off | Small and correct | Keep |
| Setup wizard | Good idea, wrong scope | Keep — make Pi-conditional |
| Launcher scripts | Useful for portable mode | Keep — separate from Pi workflow |
| Packaging / app icons | Not ready | Skip for now |
| Root route change | Breaking change for Pi | Revert or make configurable |
| `client = None` when no API key | Latent crash risk | Fix before merging |
| Model hardcoded to snapshot | Will drift | Move to config or use latest alias |

---

## Suggested Merge Strategy

Rather than merging the whole branch, cherry-pick in phases:

**Phase 1 — Safe wins (merge now):**
- BM25 module (`utils/`)
- Campaign loader tiers (`campaign_loader.py`) — after fixing the circular import
- Scene Painter hand-off (`tools/scene_painter.html`)
- NPC Forge new filter fields + sticky button (isolated CSS/UI changes)

**Phase 2 — Session Companion (needs work before merge):**
- Fix `client is None` guard in chat and finalize endpoints
- Fix role alternation in chat history normalization
- Revert root route change (keep `npc_forge.html` as default on Pi)
- Make setup wizard conditional on platform/environment
- Then merge the backend endpoints and Session Companion UI

**Phase 3 — Decide together:**
- NPC portrait generation (rate limit UX needed)
- AI provider toggle (complete or cut)
- Launcher scripts (useful but separate concern from Pi deploy)

**Phase 4 — Defer:**
- macOS app packaging
- Update checker endpoint
- User guides (bundle with release artifacts, not repo root)
