# Roadmap

## Phase 1 — Core Session Tools (Current Focus)

These address the DM's stated pain points: scene descriptions and NPC differentiation.
All Phase 1 tools are Streamlit pages in a single local app.

### 1.1 Scene Painter
**Goal:** Generate a read-aloud scene description from minimal input.
**Inputs:**
- Location type (e.g. "dungeon corridor", "forest clearing", "tavern common room")
- Mood/tone (e.g. "tense and foreboding", "warm and lively", "eerie and abandoned")
- Time of day / lighting
- Scale (small room / medium hall / vast cavern / open exterior)
- Key object or feature (e.g. "a cracked altar", "a locked cage", "a roaring fire") — provides the "unexpected detail"
- Occupants/activity (e.g. "empty", "two guards playing cards", "a robed figure with their back turned")
- Weather/environmental effect (optional — rain, fog, magical aura, extreme heat)
- Campaign location link (optional — pull existing details from campaign context)

**Outputs:**
- 3-5 sentence read-aloud description (sensory, atmospheric, ends on a hook)
- 3 bullet points: things players might notice on closer investigation
- DM-only note: what's actually happening beneath the surface of this scene

**AI role:** Claude generates based on D&D 5e fiction conventions and sensory detail formula.

### 1.2 NPC Forge
**Goal:** Generate a distinct, playable NPC from a concept.
**Inputs:** Role/concept (e.g. "nervous blacksmith", "smug noble guard captain"), optional name, optional faction/affiliation
**Outputs:**
- Name + brief physical description (2 sentences)
- Voice quirk (one specific verbal habit)
- Physical tell (one mannerism)
- Want (immediate desire — what do they want right now, in this interaction?)
- Secret (one thing they're not saying)
- Faction/affiliation (who do they answer to, or who do they hate?)
- Stat block hint (one-word tag: Commoner / Guard / Veteran / Bandit / Spy / etc.)
- Sample dialogue (2-3 lines as this NPC would actually speak)

**AI role:** Claude generates. Output should be immediately usable, not a writing prompt.

### 1.3 Session Companion
**Goal:** Persistent AI chat with campaign context loaded for live in-session use.
**Features:**
- Campaign context file (NPCs, locations, current plot threads) pre-loaded into system prompt
- Simple chat interface — ask anything, get fast answer
- "Quick prompts" panel: one-click buttons for common asks
  (Name an NPC, Describe this room, What does [NPC] say, Give me a complication)
- Campaign context editor (add/update NPC/location info between sessions)

**AI role:** Claude as DM copilot with full campaign context.

### 1.4 Combat Companion
**Goal:** A live combat tool that complements Roll20 (which handles initiative/HP/conditions visually)
by providing the DM with monster intelligence, condition duration tracking, and AI-assisted narration.

**What Roll20 already handles (don't rebuild):** Initiative order, token HP bars, condition icons, dice rolling.

**Three-panel layout:**

**Left — Active Encounter**
- Encounter name + terrain/setup notes
- Combatant list: name, type (PC/Monster/NPC), HP bar (current/max), active conditions
- Active combatant highlighted; "Next Turn" button advances the tracker
- Per-combatant condition tracker: add condition → set duration type (rounds / concentration / until save) → auto-counts down on Next Turn
- Concentration spell tracker: which PC has concentration on what, auto-prompts Con save when they take damage

**Center — Monster Reference** *(main panel)*
- Search any SRD monster by name — instant display, no API call
- Data sourced from static local JSON (Open5e SRD data — free, complete, accurate)
- Displays: AC, HP, Speed, ability scores, Actions, Bonus Actions, Reactions, Special Abilities, CR
- **Tactics panel** beneath stat block: how this monster fights intelligently (pre-written per monster, based on "Monsters Know What They're Doing" principles — goblins flee, wolves trip, hobgoblins use Martial Advantage)

**Right — AI Assist** *(used sparingly, Haiku model)*
- Three one-click quick prompts:
  - "Describe this hit" (inputs: attacker, damage, HP threshold of target)
  - "Would it flee or surrender?" (inputs: monster type, HP %, situation)
  - "What's the smart move?" (inputs: monster, party state, terrain)
- Free text input for anything else
- Output displayed inline — no page change

**Static vs. AI:**
- Monster stat blocks, condition rules, tactics guidance → static JSON/text (instant, free, always accurate)
- Hit narration, flee/surrender judgment, tactical advice → Claude Haiku (fast, cheap, context-aware)

---

## Phase 2 — Campaign Management

*Begin when Phase 1 tools are built and validated in sessions.*

### 2.1 Campaign Wiki
- NPC roster with full NPC Forge profiles
- Location registry with scene descriptions
- Faction tracker (relationships, goals, current status)
- Session log (brief notes per session, searchable)
- Quest board (active/completed/abandoned)

### 2.2 Session Planner
- Template-driven session outline
- Expected scenes, key NPCs, loot planned
- Pre-session NPC/scene banking
- Post-session: quick notes → auto-generate session recap

---

## Phase 3 — Encounter & Adventure Tools

*Begin when entering homebrew territory.*

### 3.1 Encounter Builder
- Party-level-aware difficulty calculator (XP budget method)
- Monster selector with stat block preview
- Narrative hook generator per encounter
- Environmental hazard suggestions

### 3.2 Adventure Ideation
- Plot hook generator from keywords
- Three-act structure scaffolding
- Villain motivation builder
- Location + conflict + NPC combinator

---

## Knowledge Base Architecture (Karpathy Pattern)

Campaign knowledge lives as **human-readable markdown files**, not JSON. Files are the source of truth — you write them like prep notes; the AI reads them as context. One file per entity. Short, structured, consistent.

### Why markdown over JSON
- You edit these files between sessions as natural prep notes
- No schema errors or syntax mistakes to debug
- The AI reads them directly without parsing
- Each file is independently loadable — only load what's relevant

### Knowledge Hierarchy
| Layer | File(s) | Load when |
|-------|---------|-----------|
| Rules | `DM_REFERENCE.md` | Always |
| World/Setting | `WORLD.md` | Always |
| Factions | `FACTIONS.md` | When NPCs interact or politics matter |
| NPC profile | `npcs/[name].md` | When that NPC appears by name in query |
| Location | `locations/[name].md` | When that location appears in query |
| Session log | `sessions/session_N.md` | When querying recent events |

### Selective Loading (campaign_loader.py)
Do NOT load the entire campaign into every prompt. Instead:
1. Parse the query for named NPCs and locations
2. Load only the matching entity files
3. Always include `WORLD.md` + `DM_REFERENCE.md` as the base layer
4. Fall back to `FACTIONS.md` if no specific entity match found

This keeps every API call small, fast, and cheap.

---

## Tech Stack

**Why FastAPI + HTML over Streamlit:**
The Claude Design export gave us a production-quality React frontend for NPC Forge — fully styled, animated, and functional. Rebuilding that in Streamlit would produce an inferior result. FastAPI serves the HTML files statically and handles Claude API calls in ~20 lines of Python. Each tool is a browser tab, perfect for the 3-monitor setup. Streamlit is not used — the right tool won.

```
DnD/
├── server.py                       # FastAPI app — all API endpoints + static file serving
├── tools/                          # HTML/React tool files (one per tool)
│   ├── npc_forge.html              # Adapted from Claude Design export
│   ├── scene_painter.html
│   └── session_companion.html
├── campaign/
│   ├── templates/                  # Starter templates for new entities
│   │   ├── npc_template.md
│   │   ├── location_template.md
│   │   └── session_template.md
│   └── LMoP/                       # One subdirectory per campaign
│       ├── WORLD.md                # Setting, tone, party info — always loaded
│       ├── FACTIONS.md             # Factions, relationships — loaded for social queries
│       ├── npcs/                   # One .md file per NPC
│       │   └── [name].md
│       ├── locations/              # One .md file per location
│       │   └── [name].md
│       └── sessions/               # One .md file per session
│           └── session_N.md
├── utils/
│   ├── claude_client.py            # Anthropic SDK wrapper with error handling + retry
│   ├── prompts.py                  # System prompts per tool
│   └── campaign_loader.py          # Selective context loading by entity name match
├── design/                         # Claude Design exports + visual specs
│   ├── npc_forge_spec.md
│   └── npc_forge_export/
├── config.py                       # Model, temperature, max tokens, file paths
├── .env                            # ANTHROPIC_API_KEY (never commit)
├── .gitignore                      # Must include .env
├── DM_REFERENCE.md                 # Rules reference — always loaded
├── VISION.md
├── ROADMAP.md
└── README.md
```

**Dependencies:**
- `fastapi`
- `uvicorn`
- `anthropic`
- `python-dotenv`

**Environment:**
- `ANTHROPIC_API_KEY` in `.env`
- Python 3.11+ venv

**Running locally:**
```bash
uvicorn server:app --reload
# NPC Forge → http://localhost:8000/tools/npc_forge.html
# Scene Painter → http://localhost:8000/tools/scene_painter.html
```

**Model selection:**
- NPC Forge, Scene Painter: `claude-haiku-4-5-20251001` — fast, cheap, excellent for creative text
- Session Companion: `claude-sonnet-4-6` — more reasoning needed for campaign-aware responses

---

## VTT Migration (Parallel Track)

**Current:** Roll20 + D&D Beyond
**Target (when DM role begins):** Foundry VTT

Foundry advantages for this DM:
- Local hosting on desktop (3 monitors — one for Foundry GM view, one for DM toolkit, one for notes)
- `dnd5e` system module handles automation (attacks, damage, conditions, death saves)
- `D&D Beyond Importer` module syncs character sheets automatically
- One-time $50 cost vs Roll20 subscription for equivalent features

Action: Research Foundry setup guide before taking over as DM.
