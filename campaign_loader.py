from pathlib import Path

CAMPAIGN_DIR = Path(__file__).parent / "campaign"

# Rough chars-per-token estimate for budget enforcement
_CHARS_PER_TOKEN = 4


def _read(path: Path) -> str:
    try:
        return path.read_text().strip()
    except Exception:
        return ""


def _tokens(text: str) -> int:
    return len(text) // _CHARS_PER_TOKEN


def _matching_files(directory: Path, hints: list[str]) -> list[Path]:
    """Return .md files whose filename or first heading matches any hint."""
    if not directory.exists():
        return []
    matches = []
    for f in sorted(directory.glob("*.md")):
        name = f.stem.replace("_", " ").lower()
        preview = _read(f)[:300].lower()
        for hint in hints:
            if hint.lower() in name or hint.lower() in preview:
                matches.append(f)
                break
    return matches


def load_campaign_context(
    campaign: str,
    hints: list[str] | None = None,
    token_budget: int = 2000,
) -> str:
    """
    Build a campaign context string for injection into an AI prompt.

    Always loads WORLD.md and FACTIONS.md as the base layer.
    If hints are provided, loads matching NPC and location files within budget.
    Returns an empty string if the campaign directory doesn't exist.
    """
    base = CAMPAIGN_DIR / campaign
    if not base.exists():
        return ""

    sections: list[str] = []
    used = 0

    for filename in ("WORLD.md", "FACTIONS.md"):
        content = _read(base / filename)
        if content:
            t = _tokens(content)
            if used + t <= token_budget:
                sections.append(content)
                used += t

    if hints:
        entity_files = (
            _matching_files(base / "npcs", hints)
            + _matching_files(base / "locations", hints)
        )
        for f in entity_files:
            content = _read(f)
            if not content:
                continue
            t = _tokens(content)
            if used + t <= token_budget:
                sections.append(content)
                used += t

    if not sections:
        return ""

    header = f"[Campaign context: {campaign}]\n\n"
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
