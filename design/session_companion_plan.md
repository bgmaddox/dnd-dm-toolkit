# Technical Specification: 1.3 Session Companion (v2.1 - Advanced DM Support)

## 1. Executive Summary
Build a central DM Copilot dashboard that integrates campaign context into a persistent AI chat. This tool acts as the 'glue' for the DM Toolkit, bridging high-level session management with surgical tools like NPC Forge and Scene Painter. v2.1 features a cost-optimized 'Layered Memory' system, a Pre-Session Prep workflow for banking content before play, semantic context retrieval via BM25, and optional Voice-to-Text note capture as a secondary feature.

**Design principle:** Minimize what the DM has to do *during* play. The dominant workflow is pre-session prep (generate, review, bank); the live chat is a safety net for the unexpected.

## 2. Technical Stack
- Backend: Python (FastAPI)
- Frontend: Alpine.js (via CDN) + Vanilla CSS (Cinzel/Crimson Pro fonts)
- Voice: Browser Web Speech API (Free/Local) — optional, secondary feature
- Models: Claude 3.5 Sonnet (Primary), Gemini 2.0 Flash (Fallback)
- Search: BM25 keyword ranking (`rank-bm25` library — zero ML dependencies, ~10KB)
- Data Store: Markdown (Summaries), JSON (History), Text (Raw Transcripts)

### Why Alpine.js over React
The existing tools (Combat Companion, NPC Forge, Scene Painter) are vanilla HTML/JS. React via CDN requires either a Babel transpilation step (slow, messy) or writing `React.createElement()` calls (verbose). Alpine.js adds reactive components via `x-data` / `x-bind` HTML attributes — no build step, no JSX, consistent with the existing stack, ~15KB.

### Why BM25 over sentence-transformers
Sentence-transformers requires downloading a 400MB+ model and adds significant startup latency. BM25 is a proven keyword-ranking algorithm that handles "which NPC/location file matches this query" well enough for a campaign-scale corpus. Zero model download, fast, and easily replaced later if needed.

## 3. Layered Memory Architecture (Cost & Context Management)
To handle long session recordings without bloating API costs, we use a three-tier storage system:

1. **Layer 1: Raw Transcript (Local/Free)**
   - If voice capture is enabled, streams voice-to-text to `campaign/[campaign]/sessions/transcripts/raw_YYYY-MM-DD.txt`.
   - Also accepts manual typed notes appended via the UI.
   - Cost: $0. Not used in standard AI context.

2. **Layer 2: Structured Session Log (The 'Memories')**
   - Post-session, a 'Finalize Session' command triggers the AI to process the raw transcript into a concise Markdown summary.
   - Extracts: Plot Points, NPCs Met, Loot Found, Outstanding Questions, PC Decisions.
   - Saved as: `campaign/[campaign]/sessions/session_N.md`.
   - Cost: One-time nominal fee per session (~$0.01–0.03 depending on session length).

3. **Layer 3: Active Context (The 'Short-term Memory')**
   - During live play, the Session Companion reads ONLY the Tier 2 summaries — not raw transcripts.
   - Cost: Extremely low token overhead per chat message.

## 4. Cost-Optimization Strategy (Lean Context)
Context is assembled in tiers and only grows on demand:

- **Tier 1 (Constant):** World/Factions/Rules — base layer always injected.
- **Tier 2 (Lean PC Stats):** Compact string of PC Names, Classes, Passive Perception, and Languages. Example: `Tav (Rogue, PP:14, Elvish/Common)`.
- **Tier 3 (On-Demand):** NPC/Location files loaded via BM25 match against the user's query. Only the top 1–2 matching files are injected.
- **Tier 4 (Session Summaries):** Most recent 2–3 session summaries for continuity. DM can override the count.

## 5. File Architecture & Changes

### 5.1 New Files
- `tools/session_companion.html` — Main UI entry point.
- `campaign/[campaign]/sessions/session_N.md` — Per-session structured summaries (Layer 2).
- `campaign/[campaign]/sessions/transcripts/raw_YYYY-MM-DD.txt` — Raw voice/note captures (Layer 1).
- `tools/sessions/chat_[campaign]_session_[N].json` — Chat history, named by campaign + session number for human readability.
- `utils/bm25_index.py` — BM25 wrapper over campaign NPC/location files for on-demand context retrieval.

### 5.2 Modified Files
- `server.py` — Add chat history endpoints, layered memory processing, BM25 context retrieval, and session management endpoints.
- `campaign_loader.py` — Update to support Tier 2 (Lean PC Stats) and Tier 4 (Recent Summaries).

## 6. Backend API Specification (server.py)

### 6.1 Session Lifecycle API
- `POST /api/session/start` — Accepts `{campaign, session_number}`. Returns active context summary (tier counts, estimated token load) for confirmation on the Session Start screen.
- `POST /api/session/finalize` — Reads Layer 1 raw file (or typed notes) → calls AI to summarize → writes Layer 2 Markdown file.
- `POST /api/session/notes/append` — Appends a text chunk to the Layer 1 raw notes file (used by both voice stream and manual note entry).

### 6.2 Chat & Context API
- `POST /api/ai/chat` — Contextual generation with tiered context injection. Runs BM25 match on user query to pull Tier 3 NPC/location files before calling Claude.
- `POST /api/campaign/update-field` — One-click logging for loot/events into Layer 2 session summary or WORLD.md.

### 6.3 Pre-Session Prep API
- `POST /api/prep/generate` — Accepts a prep type (`npc_lines`, `room_descriptions`, `read_aloud`, `encounter_hooks`) and returns batched generated content to bank before the session.

## 7. Frontend Architecture (Alpine.js)

### 7.1 Views / Modes
The UI has two distinct modes toggled at the top level:

**Prep Mode (pre-session):**
- Campaign selector and session number input.
- Prep generator: select type (NPC Lines / Room Descriptions / Read-Aloud / Hooks), adjust parameters, generate a batch, review and save to session notes.
- Session history browser: view/edit past session summaries.

**Live Mode (during session):**
- Session Start screen (see Section 9) shown first.
- 3-column layout: Context Panel | Chat Interface | Quick Log.
- Minimal inputs — prioritize dropdowns, quick prompts, and one-click actions over free text entry.

### 7.2 Component Breakdown
- `SessionStartScreen` — Campaign/session selector with context confirmation (see Section 9).
- `PrepGenerator` — Batch content generation interface for pre-session workflow.
- `ContextPanel` — Displays active context: campaign, session #, loaded summaries, PC list.
- `ChatInterface` — AI chat with `[Forge]`, `[Paint]`, and `[Log]` quick-action buttons.
- `QuickLog` — One-click buttons to log loot, NPCs, plot points directly into the session notes.
- `VoiceConsole` (optional) — Record button + real-time transcription display. Off by default; enable via settings toggle.
- `SessionFinalizer` — End-of-session panel to trigger Layer 2 summary generation.

### 7.3 Inter-Tool Linking (`[Forge]` and `[Paint]` Buttons)
When the DM clicks `[Forge]` or `[Paint]` in the chat, the Session Companion:
1. Serializes the relevant chat context (e.g., the NPC name or location just discussed) into a URL parameter or writes it to `localStorage` under a known key (e.g., `dm_toolkit_handoff`).
2. Opens NPC Forge or Scene Painter in a new tab (or focuses the existing tab if already open).
3. The target tool reads the handoff key on load and pre-populates its inputs.

This requires a small update to NPC Forge and Scene Painter to check for the `dm_toolkit_handoff` key on page load.

## 8. Session Start Screen (Section 9 addition)
Before the live chat activates, the DM sees a confirmation screen:

```
┌─────────────────────────────────────────┐
│  Session Companion — Start Session      │
│                                         │
│  Campaign:   [Lost Mines of Phandelver] │
│  Session #:  [  7  ]                    │
│                                         │
│  Active Context                         │
│  ├─ World file: WORLD.md (412 tokens)   │
│  ├─ PC Stats: 5 characters loaded       │
│  ├─ Summaries: sessions 4, 5, 6         │
│  └─ BM25 index: 14 NPC / 9 location     │
│     files indexed                       │
│                                         │
│       [ Begin Session ]                 │
└─────────────────────────────────────────┘
```

This gives the DM confidence that the right context is loaded before any API calls are made.

## 9. Build Checklist & Verification

### Step 1: Backend Foundation (Session Lifecycle & Layered Memory)
- [ ] Implement `POST /api/session/start` with context summary response.
- [ ] Implement `POST /api/session/notes/append` for raw note capture.
- [ ] Implement `POST /api/session/finalize` summary logic.
- **Verify:** Appending notes for 1 minute creates a raw text file; Finalize produces a clean Markdown summary with the expected sections.

### Step 2: BM25 Context Retrieval
- [ ] Build `utils/bm25_index.py` using `rank-bm25`. Index all NPC/location Markdown files in the campaign folder.
- [ ] Wire into `POST /api/ai/chat` to auto-inject top 1–2 matching files per query.
- [ ] Update `campaign_loader.py` for Lean PC Stats and Recent Summaries.
- **Verify:** Asking "what do we know about Sildar?" retrieves the Sildar NPC file without any manual selection.

### Step 3: Session Start Screen & UI Shell
- [ ] Build `SessionStartScreen` component in Alpine.js.
- [ ] Build mode toggle (Prep / Live).
- [ ] Wire `POST /api/session/start` to populate the context confirmation panel.
- **Verify:** Selecting a campaign and session number shows correct token counts and file counts before starting.

### Step 4: Live Chat Interface
- [ ] Build 3-column live layout: Context Panel | Chat | Quick Log.
- [ ] Implement `[Log]` button → `POST /api/campaign/update-field`.
- **Verify:** AI answers contextual questions using session history; `[Log Loot]` appends correctly.

### Step 5: Inter-Tool Linking
- [ ] Implement `localStorage`-based handoff for `[Forge]` and `[Paint]` buttons.
- [ ] Update NPC Forge and Scene Painter to read `dm_toolkit_handoff` on load.
- **Verify:** Clicking `[Paint]` from a chat message about "the collapsed watchtower" opens Scene Painter with that location pre-filled.

### Step 6: Pre-Session Prep Workflow
- [ ] Implement `POST /api/prep/generate` endpoint.
- [ ] Build `PrepGenerator` UI component.
- **Verify:** Generating "5 read-aloud room descriptions for dungeon rooms" returns a reviewable batch and saves to session notes.

### Step 7: Voice Capture (Optional, Low Priority)
- [ ] Add VoiceConsole component (disabled by default in settings).
- [ ] Wire Web Speech API to `POST /api/session/notes/append`.
- **Verify:** Speaking for 30 seconds appends transcript text to the raw notes file.

## 10. UX Guidelines
- Colors: `--gold: #c9a84c`, `--bg: #111318`, `--teal: #3da894`.
- Feedback: Toast notifications when Loot, NPCs, or Plot Points are logged.
- **Live Mode inputs should be minimal** — dropdowns, single-keyword fields, and quick-prompt buttons over open text entry. The DM should not be typing paragraphs during a session.
- Prep Mode can have richer inputs since it's used before the session starts.
