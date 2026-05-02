# DM Toolkit

A suite of AI-powered tools to help with learning to DM, running sessions, and building campaigns in D&D 5e (2024 rules).

## Project Status

**Phase 1 — In Progress:** Core session tools
- NPC Forge — built, deployed to Pi
- Combat Companion — built, deployed to Pi
- Scene Painter, Session Companion — planned

## Tools

| Tool | Status | Purpose |
|------|--------|---------|
| DM Learning Guide | Done | Curated HTML reference: mindset, skills, tools, resources, checklists |
| NPC Forge | Done | Build distinct NPCs with voice, quirks, motivations, sample dialogue |
| Combat Companion | Done | Live combat tracker + monster reference + AI assist |
| Scene Painter | Planned | Generate atmospheric read-aloud descriptions from location/mood inputs |
| Session Companion | Planned | Pre-session prep workflow with AI batch generation; in-session one-click reference |
| Campaign Wiki | Planned | Track NPCs, locations, factions, session notes |
| Encounter Builder | Future | Design balanced encounters with narrative hooks |

## Tech Stack

- **Backend:** FastAPI (Python) — serves tools as static HTML, handles Claude API calls
- **Frontend:** HTML/React per tool — generated via Claude Design, adapted for local API
- **AI:** Claude API (Anthropic SDK) — Haiku for generation tools, Sonnet for campaign companion
- **Campaign data:** Markdown knowledge base (one file per NPC/location/session — human-editable, selectively loaded into AI context)
- **VTT:** Roll20 (current) → Foundry VTT (planned migration when DM role begins)
- **Character sheets:** D&D Beyond

## Running Locally

```bash
source .venv/bin/activate
uvicorn server:app --reload
```

- NPC Forge → `http://localhost:8000/tools/npc_forge.html`
- Combat Companion → `http://localhost:8000/tools/combat_companion.html`

## Pi Deployment (always-on)

The tools run permanently on the home Pi server as a systemd service — no startup needed.

**Pi:** `bgmaddox@rachett.local` | Tailscale `100.80.40.124` | Port `8502`

| Tool | Home Network | Anywhere (Tailscale) |
|------|-------------|----------------------|
| NPC Forge | [rachett.local:8502/tools/npc_forge.html](http://rachett.local:8502/tools/npc_forge.html) | [100.80.40.124:8502/tools/npc_forge.html](http://100.80.40.124:8502/tools/npc_forge.html) |
| Combat Companion | [rachett.local:8502/tools/combat_companion.html](http://rachett.local:8502/tools/combat_companion.html) | [100.80.40.124:8502/tools/combat_companion.html](http://100.80.40.124:8502/tools/combat_companion.html) |

### Deploying updates

After making changes locally, push to the Pi and restart the service:

```bash
./deploy_pi.sh
```

That script rsyncs all files (excluding `.venv` and `.env`) and runs `sudo systemctl restart dnd-toolkit`.

### First-time Pi setup (already done — for reference)

```bash
# 1. On the Pi: create dir and venv
ssh bgmaddox@rachett.local
mkdir -p ~/dnd && python3 -m venv ~/dnd/.venv && exit

# 2. From Mac: push files + API key
rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='.env' \
  . bgmaddox@rachett.local:~/dnd/
scp .env bgmaddox@rachett.local:~/dnd/.env

# 3. On the Pi: install deps and register service
ssh bgmaddox@rachett.local
cd ~/dnd && .venv/bin/pip install -r requirements.txt
sudo cp dnd-toolkit.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable dnd-toolkit && sudo systemctl start dnd-toolkit
```

### Service management

```bash
ssh bgmaddox@rachett.local
sudo systemctl status dnd-toolkit    # check it's running
sudo systemctl restart dnd-toolkit   # restart after manual changes
sudo journalctl -u dnd-toolkit -f    # tail logs
```

## Campaign Knowledge Base

```
campaign/
├── templates/          # Copy these when creating new entities
│   ├── npc_template.md
│   ├── location_template.md
│   └── session_template.md
└── LMoP/
    ├── WORLD.md        # Setting, party, tone — always loaded
    ├── FACTIONS.md     # Factions and relationships
    ├── npcs/           # One file per NPC
    ├── locations/      # One file per location
    └── sessions/       # One file per session
```

## Campaign

Currently playing: Lost Mines of Phandelver (as player, level 3)
Next: Taking over as DM for the same group (4-5 players, mix of new and experienced)
System: D&D 5e 2024 (5.5e)
Platform: Virtual — Roll20 + D&D Beyond
