from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic
import asyncio
import json
import os
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
import re as _re
from campaign_loader import load_campaign_context, list_campaigns

from setup_wizard import setup_wizard

# Versioning
VERSION = "1.1.0"

# PORTABLE=1 activates desktop-launcher mode: dynamic port, browser auto-open, setup wizard.
# On Pi, this env var is never set — server starts on PORT (default 8502) with no wizard.
PORTABLE = os.environ.get("PORTABLE", "").lower() in ("1", "true", "yes")
PORT = int(os.environ.get("PORT", 8502))

load_dotenv()  # always load .env if present; systemd env vars take precedence on Pi

if PORTABLE:
    setup_wizard()

app = FastAPI()

@app.get("/api/version")
async def get_version():
    return {"version": VERSION}

@app.get("/api/updates/check")
async def check_updates():
    repo = "bgmaddox/dnd-dm-toolkit"
    try:
        import requests
        response = await asyncio.to_thread(
            requests.get,
            f"https://api.github.com/repos/{repo}/releases/latest",
            timeout=2,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "").replace("v", "")
            
            # Simple version comparison
            update_available = False
            if latest_version:
                try:
                    curr = [int(x) for x in VERSION.split(".")]
                    late = [int(x) for x in latest_version.split(".")]
                    update_available = late > curr
                except ValueError:
                    update_available = latest_version != VERSION

            return {
                "current_version": VERSION,
                "latest_version": latest_version,
                "update_available": update_available,
                "url": data.get("html_url", f"https://github.com/{repo}/releases")
            }
        else:
            return {
                "current_version": VERSION,
                "update_available": False,
                "error": f"GitHub returned {response.status_code}"
            }
    except Exception as e:
        return {"current_version": VERSION, "update_available": False, "error": str(e)}

# Anthropic Client (Claude)
_anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
client = None
if _anthropic_key:
    client = anthropic.Anthropic(api_key=_anthropic_key)
else:
    print("WARNING: ANTHROPIC_API_KEY not found. AI features using Claude will be disabled.")

# ── Gemini free-tier rate limiter ────────────────────────────────────────────
# Free tier: 15 RPM text, 3 RPM images (Imagen 3).
# We track request timestamps in a rolling 60-second window.
class _RateLimiter:
    def __init__(self, max_rpm: int):
        self._max = max_rpm
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> tuple[bool, float]:
        """Return (allowed, retry_after_seconds). Non-blocking."""
        now = time.monotonic()
        with self._lock:
            cutoff = now - 60.0
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            if len(self._timestamps) >= self._max:
                retry_after = 60.0 - (now - self._timestamps[0])
                return False, max(0.0, retry_after)
            self._timestamps.append(now)
            return True, 0.0

_gemini_text_limiter = _RateLimiter(max_rpm=14)  # stay 1 under 15 RPM free-tier hard limit

# Gemini — optional, only active when GEMINI_API_KEY is set
_gemini_client = None
_gemini_types = None
try:
    from google import genai as _genai_sdk
    from google.genai import types as _gt
    _gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if _gemini_key:
        _gemini_client = _genai_sdk.Client(api_key=_gemini_key)
        _gemini_types = _gt
except ImportError:
    pass


TOOLS_DIR = Path(__file__).parent / "tools"
TACTICS_CACHE = TOOLS_DIR / "tactics_cache.json"
SESSIONS_DIR = TOOLS_DIR / "sessions"
CAMPAIGN_BASE = Path(__file__).parent / "campaign"


@app.get("/api/sessions")
async def list_sessions():
    SESSIONS_DIR.mkdir(exist_ok=True)
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            sessions.append({
                "id": f.stem,
                "name": data.get("name", f.stem),
                "savedAt": data.get("savedAt", ""),
                "combatantCount": len(data.get("combatants", [])),
                "round": data.get("encounter", {}).get("round", 1),
            })
        except Exception:
            pass
    return {"sessions": sessions}


@app.post("/api/sessions")
async def save_session(body: dict):
    SESSIONS_DIR.mkdir(exist_ok=True)
    name = body.get("name", "Unnamed")
    session_id = _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") + "-" + str(int(time.time()))
    body["savedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (SESSIONS_DIR / f"{session_id}.json").write_text(json.dumps(body, indent=2))
    return {"id": session_id}


@app.get("/api/sessions/{session_id}")
async def load_session(session_id: str):
    if not _re.match(r"^[a-z0-9\-]+$", session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    return json.loads(path.read_text())


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if not _re.match(r"^[a-z0-9\-]+$", session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID")
    path = SESSIONS_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()
    return {"ok": True}


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 200
    system: str = ""
    provider: str = "claude"


@app.post("/api/ai/generate")
async def generate(req: GenerateRequest):
    if req.provider == "gemini" and _gemini_client is not None:
        allowed, retry_after = _gemini_text_limiter.acquire()
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Gemini rate limit: try again in {retry_after:.0f}s (free tier: 15 req/min)",
            )
        try:
            cfg = _gemini_types.GenerateContentConfig(
                max_output_tokens=req.max_tokens,
                system_instruction=req.system if req.system else None,
            )
            response = _gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=req.prompt,
                config=cfg,
            )
            return {"content": response.text, "provider": "gemini"}
        except Exception:
            pass  # fall through to Claude

    # Claude (default or fallback when Gemini key not configured or failed)
    if not client:
        raise HTTPException(status_code=503, detail="Claude API unavailable: ANTHROPIC_API_KEY not configured")

    fallback = req.provider == "gemini"
    kwargs = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": req.max_tokens,
        "messages": [{"role": "user", "content": req.prompt}],
    }
    if req.system:
        kwargs["system"] = req.system

    try:
        message = client.messages.create(**kwargs)
        return {"content": message.content[0].text, "provider": "claude", "fallback": fallback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    campaign: str
    query: str
    history: list = []
    sessionNumber: int = 1

@app.post("/api/ai/chat")
async def chat(req: ChatRequest):
    # 1. Load Tiered Context
    context = load_campaign_context(
        campaign=req.campaign,
        query=req.query,
        token_budget=3500 # Leave room for history/response
    )
    
    if not client:
        raise HTTPException(status_code=503, detail="Claude API unavailable: ANTHROPIC_API_KEY not configured")

    # 2. Prepare Messages — enforce user/assistant alternation (Anthropic requirement)
    raw_messages = []
    for msg in req.history:
        role = "assistant" if msg["role"] == "assistant" else "user"
        raw_messages.append({"role": role, "content": msg["content"]})

    normalized: list[dict] = []
    for msg in raw_messages:
        if normalized and normalized[-1]["role"] == msg["role"]:
            normalized[-1]["content"] += "\n\n" + msg["content"]
        else:
            normalized.append({"role": msg["role"], "content": msg["content"]})

    if normalized and normalized[0]["role"] == "assistant":
        normalized = normalized[1:]

    normalized.append({"role": "user", "content": req.query})

    # 3. System Prompt — campaign context is static per session, so cache it
    system_prompt = f"""You are an expert D&D Dungeon Master Assistant.
Use the provided campaign context to help the DM run the session.
Be concise, helpful, and creative.

{context}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=normalized,
        )
        return {"content": message.content[0].text, "provider": "claude"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Session Companion Lifecycle ──────────────────────────────────────────────

class SessionStartRequest(BaseModel):
    campaign: str
    sessionNumber: int

@app.post("/api/session/start")
async def start_session(req: SessionStartRequest):
    camp_dir = CAMPAIGN_BASE / req.campaign
    if not camp_dir.exists():
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # 1. PC Stats
    pcs = list((camp_dir / "pcs").glob("*.md"))
    
    # 2. Existing Summaries
    summaries = list((camp_dir / "sessions").glob("*.md"))
    
    # 3. BM25 Indexing check (placeholder for now)
    entities = list((camp_dir / "npcs").glob("*.md")) + list((camp_dir / "locations").glob("*.md"))
    
    return {
        "campaign": req.campaign,
        "session": req.sessionNumber,
        "activeContext": {
            "pcs": len(pcs),
            "pastSummaries": len(summaries),
            "indexedEntities": len(entities)
        }
    }

class NoteAppendRequest(BaseModel):
    campaign: str
    text: str

@app.post("/api/session/notes/append")
async def append_note(req: NoteAppendRequest):
    camp_dir = CAMPAIGN_BASE / req.campaign
    transcripts_dir = camp_dir / "sessions" / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = time.strftime("%Y-%m-%d")
    path = transcripts_dir / f"raw_{date_str}.txt"
    
    with open(path, "a") as f:
        f.write(f"\n[{time.strftime('%H:%M:%S')}] {req.text}")
    
    return {"ok": True, "path": str(path)}

@app.get("/api/session/summaries/{campaign}")
async def list_session_summaries(campaign: str):
    sessions_dir = CAMPAIGN_BASE / campaign / "sessions"
    if not sessions_dir.exists():
        return {"sessions": []}
    results = []
    for f in sorted(sessions_dir.glob("session_*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        m = _re.match(r"session_(\d+)\.md", f.name)
        if m:
            num = int(m.group(1))
            text = f.read_text()
            title = next((l.lstrip("#").strip() for l in text.splitlines() if l.strip()), f"Session {num}")
            saved_at = time.strftime("%Y-%m-%d", time.localtime(f.stat().st_mtime))
            results.append({"sessionNumber": num, "title": title, "savedAt": saved_at})
    return {"sessions": results}


@app.get("/api/session/chat/{campaign}/{session_number}")
async def get_chat_history(campaign: str, session_number: int):
    chat_path = CAMPAIGN_BASE / campaign / "sessions" / f"chat_{session_number}.json"
    if not chat_path.exists():
        return {"history": []}
    return {"history": json.loads(chat_path.read_text())}


@app.post("/api/session/chat/{campaign}/{session_number}")
async def save_chat_history(campaign: str, session_number: int, body: dict):
    sessions_dir = CAMPAIGN_BASE / campaign / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    chat_path = sessions_dir / f"chat_{session_number}.json"
    chat_path.write_text(json.dumps(body.get("history", []), indent=2))
    return {"ok": True}


@app.get("/api/session/prep/{campaign}/{session_number}")
async def get_prep_history(campaign: str, session_number: int):
    chat_path = CAMPAIGN_BASE / campaign / "sessions" / f"chat_{session_number}_prep.json"
    if not chat_path.exists():
        return {"history": []}
    return {"history": json.loads(chat_path.read_text())}


@app.post("/api/session/prep/{campaign}/{session_number}")
async def save_prep_history(campaign: str, session_number: int, body: dict):
    sessions_dir = CAMPAIGN_BASE / campaign / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    chat_path = sessions_dir / f"chat_{session_number}_prep.json"
    chat_path.write_text(json.dumps(body.get("history", []), indent=2))
    return {"ok": True}


class FinalizeRequest(BaseModel):
    campaign: str
    sessionNumber: int

@app.post("/api/session/finalize")
async def finalize_session(req: FinalizeRequest):
    camp_dir = CAMPAIGN_BASE / req.campaign
    raw_text = None

    # Try transcript file first (note-append workflow)
    date_str = time.strftime("%Y-%m-%d")
    raw_path = camp_dir / "sessions" / "transcripts" / f"raw_{date_str}.txt"
    if raw_path.exists():
        raw_text = raw_path.read_text()

    # Fallback: reconstruct from saved chat history
    if not raw_text:
        chat_path = camp_dir / "sessions" / f"chat_{req.sessionNumber}.json"
        if chat_path.exists():
            history = json.loads(chat_path.read_text())
            raw_text = "\n\n".join(
                f"[{m['role'].upper()}]: {m['content']}" for m in history
            )

    if not raw_text:
        raise HTTPException(status_code=404, detail="No session notes or chat history found")
    
    # AI Processing (Claude Sonnet recommended for reasoning)
    system_prompt = f"""You are an expert D&D assistant. Summarize the following raw session notes into a structured Markdown log.
Focus on: Plot Points, NPCs Met, Loot Found, PC Decisions, and Outstanding Questions.
Be concise but thorough.

Campaign: {req.campaign}
Session: {req.sessionNumber}"""

    if not client:
        raise HTTPException(status_code=503, detail="Claude API unavailable: ANTHROPIC_API_KEY not configured")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": f"Raw Notes:\n{raw_text}"}],
        )
        summary_md = message.content[0].text
        
        # Save Layer 2 Summary
        summary_path = camp_dir / "sessions" / f"session_{req.sessionNumber}.md"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary_md)
        
        return {"ok": True, "path": str(summary_path), "summary": summary_md}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Summarization failed: {e}")

# ── Tactics & Monsters ───────────────────────────────────────────────────────

@app.get("/api/tactics/{slug}")
async def get_tactics(slug: str):
    cache = {}
    if TACTICS_CACHE.exists():
        cache = json.loads(TACTICS_CACHE.read_text())

    if slug in cache:
        return {"tactics": cache[slug], "cached": True}

    return {"tactics": None, "cached": False}


@app.post("/api/tactics/{slug}")
async def generate_tactics(slug: str, body: dict):
    stat_block = body.get("stat_block", "")
    monster_name = body.get("name", slug)

    system_instruction = 'You are an expert D&D dungeon master who has read "The Monsters Know What They\'re Doing." Respond only with valid JSON, no markdown.'
    user_prompt = f"""Given this monster's stat block, describe how it fights intelligently in 3-4 concise bullet points.
Then provide a flee/surrender threshold (at what HP % does it retreat, and why — based on its nature and lore).

Monster: {monster_name}
Stat block summary: {stat_block}

Respond with JSON only:
{{
  "tactics": ["bullet 1", "bullet 2", "bullet 3"],
  "flee_threshold": "Flees at ~X% HP if [condition] — [brief lore reason]."
}}"""

    raw = None

    # Try Gemini first (free tier, 1000 req/day)
    if _gemini_client is not None:
        allowed, retry_after = _gemini_text_limiter.acquire()
        if allowed:
            try:
                cfg = _gemini_types.GenerateContentConfig(
                    max_output_tokens=400,
                    system_instruction=system_instruction,
                )
                response = _gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=user_prompt,
                    config=cfg,
                )
                raw = response.text
            except Exception:
                raw = None  # fall through to Claude

    # Fall back to Claude if Gemini unavailable or failed
    if raw is None:
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=system_instruction,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = message.content[0].text
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    try:
        match = _re.search(r"\{[\s\S]*\}", raw)
        if not match:
            raise ValueError("No JSON in response")
        tactics_data = json.loads(match.group())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {e}")

    cache = {}
    if TACTICS_CACHE.exists():
        cache = json.loads(TACTICS_CACHE.read_text())
    cache[slug] = tactics_data
    TACTICS_CACHE.write_text(json.dumps(cache, indent=2))

    return {"tactics": tactics_data, "cached": False}


NPCS_DIR = TOOLS_DIR / "npcs"
PORTRAITS_DIR = NPCS_DIR / "portraits"


@app.get("/api/npcs")
async def list_npcs():
    NPCS_DIR.mkdir(exist_ok=True)
    npcs = []
    for f in sorted(NPCS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            portrait_path = PORTRAITS_DIR / f"{f.stem}.png"
            if portrait_path.exists():
                data["portraitUrl"] = f"/tools/npcs/portraits/{f.stem}.png"
            npcs.append(data)
        except Exception:
            pass
    return {"npcs": npcs}


@app.post("/api/npcs")
async def save_npc(body: dict):
    NPCS_DIR.mkdir(exist_ok=True)
    name = body.get("name", "Unknown")
    npc_id = _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") + "-" + str(int(time.time()))
    body["_id"] = npc_id
    (NPCS_DIR / f"{npc_id}.json").write_text(json.dumps(body, indent=2))
    return {"id": npc_id}


@app.delete("/api/npcs/{npc_id}")
async def delete_npc(npc_id: str):
    if not _re.match(r"^[a-z0-9\-]+$", npc_id):
        raise HTTPException(status_code=400, detail="Invalid NPC ID")
    path = NPCS_DIR / f"{npc_id}.json"
    if path.exists():
        path.unlink()
    portrait_path = PORTRAITS_DIR / f"{npc_id}.png"
    if portrait_path.exists():
        portrait_path.unlink()
    return {"ok": True}


def _download_portrait(image_url: str, dest_path: Path):
    import urllib.request
    req = urllib.request.Request(image_url, headers={"User-Agent": "DMToolkit/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        dest_path.write_bytes(resp.read())


@app.post("/api/npcs/{npc_id}/portrait")
async def save_portrait(npc_id: str, body: dict):
    if not _re.match(r"^[a-z0-9\-]+$", npc_id):
        raise HTTPException(status_code=400, detail="Invalid NPC ID")
    image_url = body.get("imageUrl", "")
    if not image_url:
        raise HTTPException(status_code=400, detail="imageUrl required")
    PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    portrait_path = PORTRAITS_DIR / f"{npc_id}.png"
    try:
        await asyncio.to_thread(_download_portrait, image_url, portrait_path)
        return {"ok": True, "portraitUrl": f"/tools/npcs/portraits/{npc_id}.png"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portrait download failed: {e}")


CAMPAIGN_DIR = Path(__file__).parent / "campaign"


@app.get("/api/campaigns")
async def get_campaigns():
    return {"campaigns": list_campaigns()}


class NewCampaignRequest(BaseModel):
    name: str
    world: str = ""
    tone: str = ""
    themes: str = ""
    schedule: str = ""


@app.post("/api/campaigns/create")
async def create_campaign(req: NewCampaignRequest):
    safe_name = _re.sub(r"[^\w\s-]", "", req.name).strip().replace(" ", "_")
    if not safe_name:
        raise HTTPException(400, "Invalid campaign name")
    camp_dir = CAMPAIGN_DIR / safe_name
    if camp_dir.exists():
        raise HTTPException(409, f"Campaign '{safe_name}' already exists")

    camp_dir.mkdir(parents=True)
    for sub in ("pcs", "npcs", "locations", "sessions"):
        (camp_dir / sub).mkdir()

    world_lines = [f"# World: {req.name}\n"]
    if req.world:
        world_lines.append(f"\n{req.world}\n")
    (camp_dir / "WORLD.md").write_text("".join(world_lines))

    (camp_dir / "FACTIONS.md").write_text(f"# Factions: {req.name}\n\n")

    dm_ref_lines = [
        f"# DM Reference: {req.name}\n\n",
        "## House Rules\n- \n\n",
        f"## Session Schedule / Player Info\n",
    ]
    if req.schedule:
        dm_ref_lines.append(f"- **Schedule:** {req.schedule}\n")
    else:
        dm_ref_lines.append("- **Schedule:** \n")
    dm_ref_lines.append("- **Players:**\n  - \n\n")
    if req.tone or req.themes:
        dm_ref_lines.append("## Campaign Tone & Themes\n")
        if req.tone:
            dm_ref_lines.append(f"- **Tone:** {req.tone}\n")
        if req.themes:
            dm_ref_lines.append(f"- **Themes:** {req.themes}\n")
        dm_ref_lines.append("\n")
    dm_ref_lines.append("## Important Decisions Made\n- \n")
    (camp_dir / "DM_REFERENCE.md").write_text("".join(dm_ref_lines))

    return {"campaign": safe_name}


@app.get("/api/campaign/factions")
async def get_campaign_factions(campaign: str):
    factions_path = CAMPAIGN_DIR / campaign / "FACTIONS.md"
    if not factions_path.exists():
        return {"factions": []}
    text = factions_path.read_text()
    factions = [
        m.group(1).strip()
        for m in _re.finditer(r"^##\s+(.+)", text, _re.MULTILINE)
        if "relationship" not in m.group(1).lower()
    ]
    return {"factions": factions}


@app.get("/api/campaign/locations")
async def get_campaign_locations(campaign: str):
    loc_dir = CAMPAIGN_DIR / campaign / "locations"
    if not loc_dir.exists():
        return {"locations": []}
    locations = []
    for f in sorted(loc_dir.glob("*.md")):
        text = f.read_text()
        for line in text.splitlines():
            if line.startswith("# "):
                locations.append(line[2:].strip())
                break
        else:
            locations.append(f.stem.replace("_", " ").title())
    return {"locations": locations}


@app.get("/api/campaign/context")
async def get_campaign_context(campaign: str, hints: str = ""):
    hint_list = [h.strip() for h in hints.split(",") if h.strip()] if hints else []
    context = load_campaign_context(campaign, hint_list)
    return {"context": context, "campaign": campaign}


@app.get("/api/campaign/search")
async def search_campaign(campaign: str, q: str):
    if not q.strip():
        return {"results": []}
    try:
        from utils.bm25_index import get_campaign_index
        index = get_campaign_index(campaign)
        files = index.get_top_matches(q, n=3)
        results = []
        for f in files:
            content = f.read_text(encoding="utf-8")
            name = f.stem.replace("_", " ").title()
            results.append({
                "name": name,
                "type": f.parent.name,
                "excerpt": content[:300].strip(),
            })
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}


def _parse_int(text, pattern):
    import re
    m = re.search(pattern, text)
    return int(m.group(1)) if m else None


def _parse_pc_full_stats(text: str) -> dict:
    import re
    result = {}

    prof_m = re.search(r"\*\*Proficiency Bonus:\*\*\s*([+-]?\d+)", text)
    if prof_m:
        result["profBonus"] = prof_m.group(1)

    pp_m = re.search(r"\*\*Passive Perception:\*\*\s*(\d+)", text)
    if pp_m:
        result["passivePerception"] = int(pp_m.group(1))

    ac_m = re.search(r"\*\*AC:\*\*\s*(\d+)", text)
    if ac_m:
        result["ac"] = int(ac_m.group(1))

    # Ability scores — strip markup, then match each stat
    ab_line_m = re.search(r"\*\*STR\*\*.*?\*\*CHA\*\*[^\n]+", text)
    if ab_line_m:
        ab_line = re.sub(r"\*+", "", ab_line_m.group())
        stats = {}
        for m in re.finditer(r"([A-Z]{3})\s+(\d+)\s+\(([+-]?\d+)\)", ab_line):
            stats[m.group(1)] = [int(m.group(2)), m.group(3)]
        if stats:
            result["stats"] = stats

    # Saving throws — strip markup, match each stat bonus
    st_m = re.search(r"## Saving Throws\n(.+)", text)
    if st_m:
        st_line = re.sub(r"[*\\]", "", st_m.group(1))
        saves = {}
        for m in re.finditer(r"([A-Z]{3})\s+([+-]\d+)", st_line):
            saves[m.group(1)] = m.group(2)
        if saves:
            result["savingThrows"] = ", ".join(f"{k} {v}" for k, v in saves.items())

    # Skills
    skills_m = re.search(r"## Skills\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if skills_m:
        pairs = re.findall(r"-\s+(.+?)(?:\s+\(.*?\))?:\s*([+-]\d+)", skills_m.group(1))
        if pairs:
            result["skills"] = ", ".join(f"{n} {b}" for n, b in pairs)

    # Languages
    lang_m = re.search(r"## Languages\n(.+)", text)
    if lang_m:
        result["languages"] = lang_m.group(1).strip()

    return result


@app.get("/api/players")
async def get_players():
    import re
    players = []
    for pc_file in sorted(CAMPAIGN_DIR.glob("*/pcs/*.md")):
        try:
            text = pc_file.read_text()
            name = None
            for line in text.splitlines():
                if line.startswith("# "):
                    name = line[2:].strip()
                    break
            if not name:
                continue

            hp = _parse_int(text, r"\*\*Max HP:\*\*\s*(\d+)")
            level = _parse_int(text, r"\*\*Total Level:\*\*\s*(\d+)")

            init_m = re.search(r"\*\*Initiative:\*\*\s*([+-]?\d+)", text)
            initiative_bonus = int(init_m.group(1)) if init_m else None

            class_m = re.search(r"\*\*Class:\*\*\s*(.+)", text)
            race_m = re.search(r"\*\*Race:\*\*\s*(.+)", text)

            entry = {
                "name": name,
                "campaign": pc_file.parent.parent.name,
                "hp": hp,
                "level": level,
                "initiativeBonus": initiative_bonus,
                "charClass": class_m.group(1).strip() if class_m else None,
                "race": race_m.group(1).strip() if race_m else None,
            }
            entry.update(_parse_pc_full_stats(text))
            players.append(entry)
        except Exception:
            pass
    return {"players": players}


class CreateCampaignRequest(BaseModel):
    name: str

@app.post("/api/campaign/create")
async def create_campaign(req: CreateCampaignRequest):
    # Sanitize name for folder
    folder_name = _re.sub(r"[^a-z0-9]+", "_", req.name.lower()).strip("_")
    if not folder_name:
        raise HTTPException(status_code=400, detail="Invalid campaign name")
    
    camp_dir = CAMPAIGN_BASE / folder_name
    if camp_dir.exists():
        raise HTTPException(status_code=400, detail="Campaign already exists")
    
    # Scaffold structure
    camp_dir.mkdir(parents=True)
    (camp_dir / "npcs").mkdir()
    (camp_dir / "locations").mkdir()
    (camp_dir / "pcs").mkdir()
    (camp_dir / "sessions").mkdir()
    (camp_dir / "sessions" / "transcripts").mkdir()
    
    # Create base files
    (camp_dir / "WORLD.md").write_text(f"# {req.name}\n\n## Overview\n[Add your campaign overview here]")
    (camp_dir / "FACTIONS.md").write_text("# Factions\n\n## [Faction Name]\nDescription here.")
    
    return {"ok": True, "campaign": folder_name}


class SaveEntityRequest(BaseModel):
    campaign: str
    type: str  # "npc" or "location"
    data: dict

@app.post("/api/campaign/save_entity")
async def save_campaign_entity(req: SaveEntityRequest):
    camp_dir = CAMPAIGN_BASE / req.campaign
    if not camp_dir.exists():
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    target_dir = camp_dir / (req.type + "s")
    target_dir.mkdir(exist_ok=True)
    
    name = req.data.get("name", "Unnamed").strip()
    file_name = _re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") + ".md"
    file_path = target_dir / file_name
    
    content = ""
    if req.type == "npc":
        d = req.data
        # Format NPC Markdown
        content = f"""# {name}

## At a Glance
- **Role:** {d.get('role', '')}
- **Location:** {d.get('location', '')}
- **Stat Block:** {d.get('statBlock', '')}
- **Faction:** {d.get('faction', '')}

## Appearance
{d.get('description', d.get('appearance', ''))}

## Voice & Manner
- **Voice Quirk:** {d.get('voiceQuirk', '')}
- **Physical Tell:** {d.get('physicalTell', '')}

## Motivations
- **Want (immediate):** {d.get('immediateWant', d.get('want_immediate', ''))}
- **Want (deep):** {d.get('deepWant', d.get('want_deep', ''))}
- **Secret:** {d.get('secret', '')}

## Relationships
{d.get('relationships', '')}

## Sample Dialogue
"""
        dialogue = d.get('dialogue', [])
        if isinstance(dialogue, list):
            for line in dialogue:
                content += f"> \"{line}\"\n\n"
        
        content += f"\n## DM Notes\n{d.get('notes', d.get('dm_notes', ''))}\n"
        
    elif req.type == "location":
        d = req.data
        content = f"""# {name}

## Overview
{d.get('overview', '')}

## Sensory Details
- **Sights:** {d.get('sights', '')}
- **Sounds:** {d.get('sounds', '')}
- **Smells:** {d.get('smells', '')}

## Key Features
{d.get('features', '')}

## NPCs Present
{d.get('npcs', '')}

## DM Notes
{d.get('notes', '')}
"""
    
    file_path.write_text(content.strip() + "\n")
    
    # Refresh BM25 cache for this campaign
    try:
        from utils.bm25_index import _indices
        if req.campaign in _indices:
            _indices[req.campaign]._refresh_index()
    except Exception:
        pass
        
    return {"ok": True, "path": str(file_path)}


# Serve tool HTML files directly at /tools/<name>.html
app.mount("/tools", StaticFiles(directory=str(TOOLS_DIR), html=False), name="tools")


@app.get("/")
async def root():
    return FileResponse(str(TOOLS_DIR / "session_companion.html"))

def find_available_port(start_port=8000, max_attempts=10):
    import socket
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port

if __name__ == "__main__":
    import uvicorn

    if PORTABLE:
        import webbrowser
        port = find_available_port(8080)
        print(f"\n--- DM Toolkit (Portable) starting at http://localhost:{port} ---")
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(f"http://localhost:{port}")
        threading.Thread(target=open_browser, daemon=True).start()
    else:
        port = PORT
        print(f"\n--- DM Toolkit starting on port {port} ---")

    uvicorn.run("server:app", host="127.0.0.1", port=port, log_level="info")
