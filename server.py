from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic
import json
import os
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
import re as _re
from campaign_loader import load_campaign_context, list_campaigns

load_dotenv()

app = FastAPI()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

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


@app.get("/api/npcs")
async def list_npcs():
    NPCS_DIR.mkdir(exist_ok=True)
    npcs = []
    for f in sorted(NPCS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            npcs.append(json.loads(f.read_text()))
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
    return {"ok": True}


CAMPAIGN_DIR = Path(__file__).parent / "campaign"


@app.get("/api/campaigns")
async def get_campaigns():
    return {"campaigns": list_campaigns()}


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


# Serve tool HTML files directly at /tools/<name>.html
app.mount("/tools", StaticFiles(directory=str(TOOLS_DIR), html=False), name="tools")


@app.get("/")
async def root():
    return FileResponse(str(TOOLS_DIR / "npc_forge.html"))
