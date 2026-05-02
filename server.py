from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import re as _re
from campaign_loader import load_campaign_context, list_campaigns

load_dotenv()

app = FastAPI()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Gemini — optional, only active when GEMINI_API_KEY is set
_gemini_model = None
try:
    import google.generativeai as _genai
    _gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if _gemini_key:
        _genai.configure(api_key=_gemini_key)
        _gemini_model = _genai.GenerativeModel("gemini-1.5-flash")
except ImportError:
    pass

TOOLS_DIR = Path(__file__).parent / "tools"
TACTICS_CACHE = TOOLS_DIR / "tactics_cache.json"


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 200
    system: str = ""
    provider: str = "claude"


@app.post("/api/ai/generate")
async def generate(req: GenerateRequest):
    if req.provider == "gemini" and _gemini_model is not None:
        try:
            import google.generativeai as _genai
            model = _genai.GenerativeModel(
                "gemini-1.5-flash",
                system_instruction=req.system if req.system else None,
            )
            response = model.generate_content(
                req.prompt,
                generation_config=_genai.types.GenerationConfig(
                    max_output_tokens=req.max_tokens,
                ),
            )
            return {"content": response.text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Claude (default or fallback when Gemini key not configured)
    kwargs = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": req.max_tokens,
        "messages": [{"role": "user", "content": req.prompt}],
    }
    if req.system:
        kwargs["system"] = req.system

    try:
        message = client.messages.create(**kwargs)
        return {"content": message.content[0].text}
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

    prompt = f"""You are an expert D&D dungeon master who has read "The Monsters Know What They're Doing."
Given this monster's stat block, describe how it fights intelligently in 3-4 concise bullet points.
Then provide a flee/surrender threshold (at what HP % does it retreat, and why — based on its nature and lore).

Monster: {monster_name}
Stat block summary: {stat_block}

Respond with JSON only:
{{
  "tactics": ["bullet 1", "bullet 2", "bullet 3"],
  "flee_threshold": "Flees at ~X% HP if [condition] — [brief lore reason]."
}}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        match = __import__("re").search(r"\{[\s\S]*\}", raw)
        if not match:
            raise ValueError("No JSON in response")
        tactics_data = json.loads(match.group())

        cache = {}
        if TACTICS_CACHE.exists():
            cache = json.loads(TACTICS_CACHE.read_text())
        cache[slug] = tactics_data
        TACTICS_CACHE.write_text(json.dumps(cache, indent=2))

        return {"tactics": tactics_data, "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

            players.append({
                "name": name,
                "campaign": pc_file.parent.parent.name,
                "hp": hp,
                "level": level,
                "initiativeBonus": initiative_bonus,
                "charClass": class_m.group(1).strip() if class_m else None,
                "race": race_m.group(1).strip() if race_m else None,
            })
        except Exception:
            pass
    return {"players": players}


# Serve tool HTML files directly at /tools/<name>.html
app.mount("/tools", StaticFiles(directory=str(TOOLS_DIR), html=False), name="tools")


@app.get("/")
async def root():
    return FileResponse(str(TOOLS_DIR / "npc_forge.html"))
