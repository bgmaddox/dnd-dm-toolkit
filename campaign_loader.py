from pathlib import Path
import re

CAMPAIGN_DIR = Path(__file__).parent / "campaign"

# Rough chars-per-token estimate for budget enforcement
_CHARS_PER_TOKEN = 4


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _tokens(text: str) -> int:
    return len(text) // _CHARS_PER_TOKEN


def _get_lean_pc_stats(campaign_path: Path) -> str:
    """Extracts compact PC info: Name (Class, PP, Languages)."""
    pcs_dir = campaign_path / "pcs"
    if not pcs_dir.exists():
        return ""
    
    lines = []
    for f in sorted(pcs_dir.glob("*.md")):
        text = _read(f)
        name = f.stem.replace("_", " ").title()
        char_class = "Unknown"
        pp = "10"
        langs = "Common"
        
        class_m = re.search(r"\*\*Class:\*\*\s*(.+)", text)
        if class_m: char_class = class_m.group(1).split(",")[0].strip()
        
        pp_m = re.search(r"\*\*Passive Perception:\*\*\s*(\d+)", text)
        if pp_m: pp = pp_m.group(1)
        
        lang_m = re.search(r"## Languages\n(.+)", text)
        if lang_m: langs = lang_m.group(1).strip()
        
        lines.append(f"- {name} ({char_class}, PP:{pp}, {langs})")
    
    if not lines:
        return ""
    return "### Party Stats\n" + "\n".join(lines)


def _get_recent_summaries(campaign_path: Path, count=3) -> str:
    """Loads the most recent N session summaries."""
    sessions_dir = campaign_path / "sessions"
    if not sessions_dir.exists():
        return ""
    
    summaries = sorted(sessions_dir.glob("session_*.md"), 
                       key=lambda x: int(re.search(r"\d+", x.stem).group() or 0), 
                       reverse=True)
    
    output = []
    for f in summaries[:count]:
        content = _read(f)
        if content:
            output.append(f"## {f.stem.replace('_', ' ').title()}\n{content}")
            
    if not output:
        return ""
    return "### Recent Session History\n\n" + "\n\n---\n\n".join(output)


def load_campaign_context(
    campaign: str,
    hints: list[str] | None = None,
    query: str | None = None,
    token_budget: int = 4000,
) -> str:
    """
    Build a multi-tiered campaign context string.
    
    Tiers:
    1. Rules & World (Global/Base)
    2. Lean PC Stats (Contextual)
    3. BM25 Entity Matches (On-demand)
    4. Recent Session Summaries (History)
    """
    base = CAMPAIGN_DIR / campaign
    if not base.exists():
        return ""

    sections: list[str] = []
    used = 0

    # Tier 1: Base Layer (Rules, World, Factions)
    base_files = [
        Path(__file__).parent / "DM_REFERENCE.md",
        base / "WORLD.md",
        base / "FACTIONS.md"
    ]
    
    for bf in base_files:
        content = _read(bf)
        if content:
            t = _tokens(content)
            if used + t <= token_budget:
                sections.append(content)
                used += t

    # Tier 2: Lean PC Stats
    pc_stats = _get_lean_pc_stats(base)
    if pc_stats:
        t = _tokens(pc_stats)
        if used + t <= token_budget:
            sections.append(pc_stats)
            used += t

    # Tier 3: BM25 / Hint Matches (NPCs & Locations)
    entity_files = []
    
    # Use BM25 if query is provided
    if query:
        try:
            from utils.bm25_index import get_campaign_index
            index = get_campaign_index(campaign)
            entity_files.extend(index.get_top_matches(query, n=2))
        except ImportError:
            pass
            
    # Also support explicit hints if provided
    if hints:
        from campaign_loader import _matching_files
        entity_files.extend(_matching_files(base / "npcs", hints))
        entity_files.extend(_matching_files(base / "locations", hints))
        
    # Deduplicate while preserving order
    seen = set()
    unique_entities = []
    for f in entity_files:
        if f not in seen:
            unique_entities.append(f)
            seen.add(f)

    for f in unique_entities:
        content = _read(f)
        if content:
            t = _tokens(content)
            if used + t <= token_budget:
                sections.append(f"### Entity: {f.stem.replace('_', ' ').title()}\n{content}")
                used += t

    # Tier 4: Recent Session Summaries
    summaries = _get_recent_summaries(base, count=2)
    if summaries:
        t = _tokens(summaries)
        if used + t <= token_budget:
            sections.append(summaries)
            used += t

    if not sections:
        return ""

    header = f"[Campaign context: {campaign} | Tokens: ~{used}]\n\n"
    return header + "\n\n---\n\n".join(sections)


def list_campaigns() -> list[str]:
    """Return names of all campaign directories that have a WORLD.md."""
    if not CAMPAIGN_DIR.exists():
        return []
    return [
        d.name
        for d in sorted(CAMPAIGN_DIR.iterdir())
        if d.is_dir() and (d / "WORLD.md").exists()
    ]
