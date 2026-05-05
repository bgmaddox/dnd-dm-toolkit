#!/usr/bin/env python3
"""
Fetch a public D&D Beyond character and generate a campaign knowledge base markdown file.

Requirements:
  - Character must be set to Public in D&D Beyond sharing settings
    (Character Builder → Share → Public)

Usage:
  python fetch_character.py <character_url_or_id>
  python fetch_character.py <character_url_or_id> --campaign LMoP
  python fetch_character.py <character_url_or_id> --output path/to/file.md

Examples:
  python fetch_character.py 123456789
  python fetch_character.py https://www.dndbeyond.com/characters/123456789
"""

import sys
import json
import re
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install it with: pip install requests")
    sys.exit(1)

# ── Constants ─────────────────────────────────────────────────────────────────

STAT_NAMES = {1: "STR", 2: "DEX", 3: "CON", 4: "INT", 5: "WIS", 6: "CHA"}
STAT_FULL  = {"STR": "strength", "DEX": "dexterity", "CON": "constitution",
              "INT": "intelligence", "WIS": "wisdom", "CHA": "charisma"}

ALIGNMENT_MAP = {
    1: "Lawful Good",    2: "Neutral Good",    3: "Chaotic Good",
    4: "Lawful Neutral", 5: "True Neutral",    6: "Chaotic Neutral",
    7: "Lawful Evil",    8: "Neutral Evil",    9: "Chaotic Evil",
}

SKILL_MAP = {
    "acrobatics": "DEX", "animal-handling": "WIS", "arcana": "INT",
    "athletics": "STR",  "deception": "CHA",       "history": "INT",
    "insight": "WIS",    "intimidation": "CHA",    "investigation": "INT",
    "medicine": "WIS",   "nature": "INT",           "perception": "WIS",
    "performance": "CHA","persuasion": "CHA",       "religion": "INT",
    "sleight-of-hand": "DEX", "stealth": "DEX",    "survival": "WIS",
}

HIT_DICE = {
    "Barbarian": 12, "Fighter": 10, "Paladin": 10, "Ranger": 10,
    "Artificer": 8,  "Bard": 8,    "Cleric": 8,   "Druid": 8,
    "Monk": 8,       "Rogue": 8,   "Warlock": 8,
    "Sorcerer": 6,   "Wizard": 6,
}

SPELL_LEVEL_LABELS = {
    0: "Cantrips", 1: "1st Level", 2: "2nd Level", 3: "3rd Level",
    4: "4th Level", 5: "5th Level", 6: "6th Level", 7: "7th Level",
    8: "8th Level", 9: "9th Level",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def signed(n):
    return f"+{n}" if n >= 0 else str(n)

def mod(score):
    return (score - 10) // 2

def prof_bonus(total_level):
    return 2 + (total_level - 1) // 4

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()

# ── Data extraction ───────────────────────────────────────────────────────────

def get_ability_scores(data):
    """
    Build final ability scores from base stats + racial/feat bonuses.
    D&D Beyond stores these across three arrays:
      stats[]       — base scores set in character builder
      bonusStats[]  — fixed bonuses (older racial ASI format)
      overrideStats[] — hard overrides (e.g. Headband of Intellect)
    Racial bonuses using the newer "choose +2/+1" system appear in
    modifiers.race as type=bonus, subType=<stat>-score.
    """
    base     = {s["id"]: (s["value"] or 10) for s in data.get("stats", [])}
    bonuses  = {}
    for s in data.get("bonusStats", []):
        if s.get("value"):
            bonuses[s["id"]] = bonuses.get(s["id"], 0) + s["value"]
    overrides = {s["id"]: s["value"] for s in data.get("overrideStats", []) if s.get("value")}

    # Collect modifier-based bonuses (newer flexible ASI system)
    all_mods = []
    for mod_list in data.get("modifiers", {}).values():
        all_mods.extend(mod_list)
    for m in all_mods:
        if m.get("type") == "bonus" and m.get("subType", "").endswith("-score"):
            full_name = m["subType"].replace("-score", "").lower()
            stat_id = next((k for k, v in STAT_FULL.items() if v == full_name), None)
            if stat_id and m.get("value"):
                bonuses[list(STAT_NAMES.keys())[list(STAT_NAMES.values()).index(stat_id)]] = \
                    bonuses.get(list(STAT_NAMES.keys())[list(STAT_NAMES.values()).index(stat_id)], 0) + m["value"]

    scores = {}
    for stat_id, abbr in STAT_NAMES.items():
        if stat_id in overrides:
            scores[abbr] = overrides[stat_id]
        else:
            scores[abbr] = base.get(stat_id, 10) + bonuses.get(stat_id, 0)

    return scores

def get_saving_throw_profs(data):
    profs = set()
    for mod_list in data.get("modifiers", {}).values():
        for m in mod_list:
            if m.get("type") == "proficiency" and m.get("subType", "").endswith("-saving-throws"):
                full = m["subType"].replace("-saving-throws", "").lower()
                abbr = next((k for k, v in STAT_FULL.items() if v == full), None)
                if abbr:
                    profs.add(abbr)
    return profs

def get_skill_profs(data):
    """Returns dict of skill_slug -> 'proficiency' | 'expertise'"""
    profs = {}
    for mod_list in data.get("modifiers", {}).values():
        for m in mod_list:
            subtype = m.get("subType", "")
            if subtype in SKILL_MAP:
                if m.get("type") == "expertise":
                    profs[subtype] = "expertise"
                elif m.get("type") == "proficiency" and subtype not in profs:
                    profs[subtype] = "proficiency"
    return profs

def get_languages(data):
    seen, langs = set(), []
    for mod_list in data.get("modifiers", {}).values():
        for m in mod_list:
            if m.get("type") == "language":
                name = (m.get("friendlySubtypeName") or m.get("subType", "")).title()
                if name and name not in seen:
                    seen.add(name)
                    langs.append(name)
    return sorted(langs)

def get_spells(data):
    """Return dict of spell_level -> [spell names], only prepared/known spells."""
    by_level = {}

    # classSpells contains the prepared/known spell list
    for class_entry in data.get("classSpells", []):
        for spell in class_entry.get("spells", []):
            defn = spell.get("definition", {})
            name = defn.get("name")
            level = defn.get("level", 0)
            prepared = spell.get("prepared", False)
            always = spell.get("alwaysPrepared", False)
            if name and (level == 0 or prepared or always):
                by_level.setdefault(level, set()).add(name)

    # spells{} covers racial/feat/item spells
    for spell_list in data.get("spells", {}).values():
        for spell in (spell_list or []):
            defn = spell.get("definition", {})
            name = defn.get("name")
            level = defn.get("level", 0)
            if name:
                by_level.setdefault(level, set()).add(name)

    return {k: sorted(v) for k, v in sorted(by_level.items())}

def get_spell_slots(data, classes, total_level):
    """
    Returns a string summary of spell slots, e.g. "1st×4 / 2nd×3 / 3rd×2"
    Uses the standard full-caster / half-caster table. Best-effort.
    """
    FULL_CASTER  = {"Bard","Cleric","Druid","Sorcerer","Wizard"}
    HALF_CASTER  = {"Artificer","Paladin","Ranger"}
    THIRD_CASTER = {"Arcane Trickster","Eldritch Knight"}
    WARLOCK      = {"Warlock"}

    FULL_SLOTS = [
        [],
        [2],[3],[4,2],[4,3],[4,3,2],[4,3,3],[4,3,3,1],[4,3,3,2],
        [4,3,3,3,1],[4,3,3,3,2],[4,3,3,3,2,1],[4,3,3,3,2,1],
        [4,3,3,3,2,1,1],[4,3,3,3,2,1,1],[4,3,3,3,2,1,1,1],
        [4,3,3,3,2,1,1,1],[4,3,3,3,2,1,1,1,1],[4,3,3,3,3,1,1,1,1],
        [4,3,3,3,3,2,1,1,1],[4,3,3,3,3,2,2,1,1],
    ]

    caster_level = 0
    for cls in classes:
        name = cls["name"]
        lvl  = cls["level"]
        if name in FULL_CASTER:
            caster_level += lvl
        elif name in HALF_CASTER:
            caster_level += lvl // 2
        elif name in THIRD_CASTER:
            caster_level += lvl // 3
        elif name in WARLOCK:
            return None  # Warlocks use Pact Magic — handled separately

    if caster_level == 0:
        return None

    caster_level = min(caster_level, 20)
    slots = FULL_SLOTS[caster_level]
    ordinals = ["1st","2nd","3rd","4th","5th","6th","7th","8th","9th"]
    parts = [f"{ordinals[i]}×{n}" for i, n in enumerate(slots) if n > 0]
    return " / ".join(parts) if parts else None

def compute_max_hp(data, scores, classes):
    override = data.get("overrideHitPoints")
    if override:
        return override
    con_mod_val = mod(scores.get("CON", 10))
    total_hp = 0
    for cls in classes:
        hit_die = HIT_DICE.get(cls["name"], 8)
        lvl = cls["level"]
        avg = hit_die // 2 + 1
        total_hp += (hit_die + con_mod_val) + (lvl - 1) * (avg + con_mod_val)
    return max(total_hp, 1)

def get_notable_inventory(data):
    items = []
    for inv in data.get("inventory", []):
        defn     = inv.get("definition", {})
        name     = defn.get("name", "")
        equipped = inv.get("equipped", False)
        itype    = defn.get("type", "")
        if equipped or itype in ("Weapon", "Armor", "Shield"):
            items.append(name)
    return items

# ── Markdown generation ───────────────────────────────────────────────────────

def generate_markdown(raw):
    data = raw.get("data", raw)

    name = data.get("name", "Unknown")

    # Race
    race_name = (data.get("race") or {}).get("fullName") or \
                (data.get("race") or {}).get("baseName", "Unknown")

    # Classes
    classes = []
    for cls in data.get("classes", []):
        defn = cls.get("definition", {})
        sub  = (cls.get("subclassDefinition") or {}).get("name", "")
        classes.append({"name": defn.get("name", "?"), "level": cls.get("level", 1), "subclass": sub})
    total_level = sum(c["level"] for c in classes) or 1

    class_str = " / ".join(
        f"{c['name']} ({c['subclass']}) {c['level']}" if c["subclass"] else f"{c['name']} {c['level']}"
        for c in classes
    )

    background = ((data.get("background") or {}).get("definition") or {}).get("name", "Unknown")
    alignment  = ALIGNMENT_MAP.get(data.get("alignmentId"), "Unknown")

    scores    = get_ability_scores(data)
    pb        = prof_bonus(total_level)
    max_hp    = compute_max_hp(data, scores, classes)
    save_profs = get_saving_throw_profs(data)
    skill_profs = get_skill_profs(data)
    languages = get_languages(data)
    spells    = get_spells(data)
    slots_str = get_spell_slots(data, classes, total_level)
    items     = get_notable_inventory(data)

    traits    = data.get("traits") or {}
    personality = strip_html(traits.get("personalityTraits", ""))
    ideals      = strip_html(traits.get("ideals", ""))
    bonds       = strip_html(traits.get("bonds", ""))
    flaws       = strip_html(traits.get("flaws", ""))
    backstory   = strip_html(traits.get("backstory", ""))

    L = []

    L += [f"# {name}", ""]

    L += ["## Overview",
          f"- **Race:** {race_name}",
          f"- **Class:** {class_str}",
          f"- **Background:** {background}",
          f"- **Alignment:** {alignment}",
          f"- **Total Level:** {total_level}",
          f"- **Proficiency Bonus:** {signed(pb)}",
          ""]

    L += ["## Combat Stats",
          f"- **Max HP:** {max_hp}",
          f"- **AC:** *(verify on D&D Beyond — depends on equipment and class features)*",
          f"- **Initiative:** {signed(mod(scores.get('DEX', 10)))}",
          f"- **Passive Perception:** {10 + mod(scores.get('WIS', 10)) + (pb if 'perception' in skill_profs else 0)}",
          ""]

    L += ["## Ability Scores", ""]
    score_row = " | ".join(
        f"**{s}** {scores.get(s,10)} ({signed(mod(scores.get(s,10)))})"
        for s in ["STR","DEX","CON","INT","WIS","CHA"]
    )
    L += [score_row, ""]

    # Saving throws
    save_parts = []
    for s in ["STR","DEX","CON","INT","WIS","CHA"]:
        val   = scores.get(s, 10)
        total = mod(val) + (pb if s in save_profs else 0)
        marker = "\\*" if s in save_profs else ""
        save_parts.append(f"**{s}{marker}** {signed(total)}")
    L += ["## Saving Throws",
          " | ".join(save_parts) + "  *(*= proficient)*",
          ""]

    # Skills
    if skill_profs:
        L += ["## Skills"]
        for slug, ptype in sorted(skill_profs.items()):
            stat  = SKILL_MAP.get(slug, "?")
            total = mod(scores.get(stat, 10)) + pb * (2 if ptype == "expertise" else 1)
            label = slug.replace("-", " ").title()
            note  = " (Expertise)" if ptype == "expertise" else ""
            L.append(f"- {label}{note}: {signed(total)}")
        L.append("")

    if languages:
        L += ["## Languages", ", ".join(languages), ""]

    # Spells
    if spells:
        L += ["## Spells"]
        if slots_str:
            L += [f"**Spell Slots:** {slots_str}", ""]
        for lvl, spell_names in spells.items():
            L += [f"### {SPELL_LEVEL_LABELS.get(lvl, f'Level {lvl}')}",
                  ", ".join(spell_names), ""]

    if items:
        L += ["## Notable Equipment"]
        L += [f"- {item}" for item in items]
        L.append("")

    L += ["## Personality"]
    if personality: L += [f"**Traits:** {personality}", ""]
    if ideals:       L += [f"**Ideals:** {ideals}", ""]
    if bonds:        L += [f"**Bonds:** {bonds}", ""]
    if flaws:        L += [f"**Flaws:** {flaws}", ""]

    if backstory:
        L += ["## Backstory", backstory, ""]

    L += ["## DM Notes",
          "*(Add session-specific notes, secrets, and arc hooks here)*",
          ""]

    return "\n".join(L)

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert a D&D Beyond character to a campaign knowledge base markdown file.",
        epilog="""
Getting the character JSON (D&D Beyond blocks automated fetches):
  1. Open the character sheet in your browser while logged into D&D Beyond
  2. Open DevTools (F12) → Console tab
  3. Paste and run:
       fetch('/api/character/v5/character/CHARACTER_ID')
         .then(r=>r.json()).then(d=>console.log(JSON.stringify(d)))
     Replace CHARACTER_ID with the number from the URL.
  4. Copy the printed JSON, save it to a file (e.g. thorin.json)
  5. Run: python fetch_character.py --file thorin.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("character", nargs="?",
        help="D&D Beyond character URL or numeric ID (may fail due to D&D Beyond blocking)")
    parser.add_argument("--file", metavar="PATH",
        help="Path to a locally saved character JSON file (most reliable)")
    parser.add_argument("--campaign", default="LMoP",
        help="Campaign subfolder under campaign/ (default: LMoP)")
    parser.add_argument("--output",
        help="Override output file path")
    args = parser.parse_args()

    if not args.file and not args.character:
        parser.print_help()
        sys.exit(1)

    # ── Load from local file ──
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: file not found: {args.file}")
            sys.exit(1)
        print(f"Loading character from {args.file}...")
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error reading JSON: {e}")
            sys.exit(1)

    # ── Fetch from D&D Beyond ──
    else:
        raw_input = args.character.strip().rstrip("/")
        match = re.search(r"/characters?/(\d+)", raw_input)
        if match:
            char_id = match.group(1)
        elif raw_input.isdigit():
            char_id = raw_input
        else:
            print(f"Error: can't parse a character ID from: {raw_input!r}")
            sys.exit(1)

        print(f"Fetching character {char_id} from D&D Beyond...")
        url = f"https://www.dndbeyond.com/character/{char_id}/json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.dndbeyond.com/",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=15)
        except requests.RequestException as e:
            print(f"Network error: {e}")
            sys.exit(1)

        if resp.status_code in (403, 500):
            print(f"Error: HTTP {resp.status_code} — D&D Beyond is blocking automated requests.")
            print()
            print("Use --file instead. To get the JSON:")
            print("  1. Open the character in your browser while logged into D&D Beyond")
            print("  2. Open DevTools (F12) → Console")
            print(f"  3. Run: fetch('/api/character/v5/character/{char_id}').then(r=>r.json()).then(d=>console.log(JSON.stringify(d)))")
            print("  4. Copy the output, save to a .json file")
            print(f"  5. Run: python fetch_character.py --file yourfile.json")
            sys.exit(1)
        if resp.status_code == 404:
            print(f"Error: Character {char_id} not found.")
            sys.exit(1)
        if not resp.ok:
            print(f"Error: HTTP {resp.status_code} from D&D Beyond.")
            sys.exit(1)
        try:
            raw = resp.json()
        except Exception:
            print("Error: D&D Beyond returned invalid JSON.")
            sys.exit(1)

    data      = (raw.get("data") or raw)
    char_name = data.get("name", "character")
    safe_name = re.sub(r"[^a-z0-9]+", "_", char_name.lower()).strip("_")

    markdown = generate_markdown(raw)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(__file__).parent / "campaign" / args.campaign / "pcs" / f"{safe_name}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    print(f"Saved → {out_path}")
    print()
    print(markdown.split("\n")[0])  # Show character name as confirmation

if __name__ == "__main__":
    main()
