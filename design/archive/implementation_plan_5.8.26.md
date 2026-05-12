# Implementation Plan — DM Toolkit Updates (2026-05-08)

> **For AI Agent Use** — All changes target a single file: `tools/dm_toolkit.html` (~4161 lines). Each task references exact line numbers and component names. Tasks within a section are independent unless a dependency is noted.

## Progress Summary (as of 2026-05-09)

| # | Task | Status |
|---|------|--------|
| 1.1 | Scene Painter — remove inner box | ✅ Done |
| 1.2 | DM Guide — "When to Call for Rolls" section | ✅ Done |
| 2.1 | NPC Forge — fix portrait generation | ✅ Done |
| 2.2 | NPC Forge — auto-add to campaign on save | ✅ Done |
| 3.1 | Combat — show dead combatants | ✅ Done |
| 3.2 | Combat — inline rename | ✅ Done |
| 3.3 | Combat — duplicate monster | ✅ Done |
| 3.4 | Combat — loot tracker per monster | ✅ Done |
| 3.5 | Combat — dice modifier toggles (Bless/Bane/Guidance) | ✅ Done |
| 3.6 | Combat — advantage/disadvantage toggles | ✅ Done |
| 3.7 | Combat — advantage turn counter + event log | ✅ Done |
| 3.8 | Combat — Booming Blade tracker | ✅ Done |
| 3.9 | Combat — expanded PC stat block | ✅ Done |
| 4.1 | New tool — Encounter Helper | ✅ Done |
| 4.2 | New tool — Campaign Calendar | ✅ Done |
| 4.3 | New tool — Loot & Hoard Calculator | ✅ Done |
| 4.4 | New tool — Ambiance Tool | ✅ Done |

**17 of 17 tasks complete. Plan fully implemented. Deployed as v1.2.0.**

---

## Project Context

**Single-file app:** `tools/dm_toolkit.html` is a self-contained React app (no build step). React runs via CDN babel-standalone. All tools are React components embedded in this one file, rendered under a tab nav by the `App` component (~line 4070).

**Run locally:** `uvicorn server:app --reload` from `/Users/brettmaddox/Documents/CODING/DnD/`
Then open: `http://localhost:8000/tools/dm_toolkit.html`

**Key component map (all in `dm_toolkit.html`):**

| Component | Starts at line |
|-----------|---------------|
| CSS / style block | ~14 |
| `DMGuideTool` | 687 |
| `LoreBuilderTool` | 1178 |
| `ScenePainterTool` | 1492 |
| `SceneOutput` (sub-component) | 1435 |
| `NPCForgeTool` | 1917 |
| `SessionTool` | 2426 |
| `CombatTool` | 3970 |
| `CombatantRow` | 3005 |
| `LeftPanel` (combat) | 3171 |
| `CenterPanel` (combat) | 3260 |
| `RightPanel` (combat) | 3574 |
| `AddCombatantModal` | 3698 |
| `App` (tab switcher) | 4070 |

**Conventions:**
- React hooks only (`useState`, `useCallback`, `useEffect`, `useRef`) — no Redux
- CSS lives in a single `<style>` block at the top of the file; uses CSS custom properties (`var(--gold)`, `var(--bg-card)`, `var(--border)`, etc.) — always use these, never hardcode colors
- API calls use `fetch()` against `/api/*` endpoints defined in `server.py`
- New tabs are added in the `App` component's `TABS` array (~line 4070) and rendered in the tab switcher block (~line 4123–4147)
- Portrait generation for NPCs uses Pollinations.ai: `https://image.pollinations.ai/prompt/{prompt}?width=512&height=512&nologo=true&model=flux&seed={n}`

---

## Section 1 — Scene Painter

### ✅ Task 1.1 — Remove the inner box from the output area

**File:** `tools/dm_toolkit.html`

**Problem (confirmed):** The `scene-right` panel is the outer container. Inside `SceneOutput` (line 1435), each of the three output sections — `.read-aloud-block` (line 1454, CSS line 190), `.detail-card` items (line 1465, CSS line 195), and `.dm-note-block` (line 1476) — has its own `border` and `background`, creating a box-within-a-box appearance. The content should live directly in the panel without each section needing its own bordered card.

**What to do:**
1. Remove the `border` and `background` from `.read-aloud-block` (CSS line ~190). Keep the `border-left: 3px solid var(--gold-dim)` accent and the padding — just drop the full border and dark background (`#0e1016`). The decorative `"` pseudo-element can stay.
2. Remove the `border` and `background: var(--bg-card)` from `.detail-card` (CSS line ~195). Keep padding and the flex layout so the `▸` bullet and text still align. Add a subtle `border-bottom: 1px solid var(--border)` to visually separate items from each other without boxing each one.
3. Remove the `border` and `background` from `.dm-note-block`. The red label (`DM Only`) and red text color are enough to distinguish it — no box needed.
4. The `scene-right` panel already has padding — the sections should breathe within it as flat content blocks, not nested cards.

**Acceptance:** Generate a scene. The three output sections (read-aloud, details, DM note) sit as flat content within the right panel — no double borders, no nested backgrounds. The gold left accent on the read-aloud block and the red DM label still provide visual distinction.

> ✅ **Implemented:** Removed border/background from `.read-aloud-block`, `.detail-card`, and `.dm-note-block`. Gold and red left-border accents retained. Detail items separated by thin `border-bottom` dividers. Deployed 2026-05-09.

---

### Task 1.2 — DM Guide: "When to Call for Rolls" section + link from Scene Painter

**File:** `tools/dm_toolkit.html`

**Context:** `DMGuideTool` starts at line 687. It renders static advice content in a scrollable panel. New content should match the existing pattern: expandable section with a header and cards.

**What to do:**

**Part A — AI Review (do before writing code):**
Draft the roll-guidance content below, then send it in a single Gemini request (`mcp__gemini-collab__ask_gemini`) asking for improvement suggestions. Incorporate any good feedback, then write the final version into the component.

Draft content for review:
> **When to Call for a Roll** — The two-part test: (1) the outcome is genuinely uncertain, and (2) failure has a meaningful consequence. If either is missing, just narrate the outcome.
>
> - **Don't roll** when success is automatic for a trained character (a fighter climbing a normal wall), when failure would block all progress, or when nothing interesting happens on a miss.
> - **Social (Persuasion/Deception/Intimidation):** Roll only when the NPC has reason to resist AND the stakes matter. Don't roll for a friendly shopkeeper being helpful.
> - **Exploration (Athletics/Acrobatics):** Roll for risky physical feats — climbing in a storm, leaping a chasm. Don't roll for walking up stairs.
> - **Perception/Investigation:** Roll when something is genuinely hidden. Never hide key plot information behind a failed check.
> - **Stealth:** Roll when there's someone to detect them and detection is plausible.
> - **Combat creative actions:** Most combat uses attack rolls. Only call for a skill check when a player attempts something outside normal attack mechanics (pushing a boulder, swinging on a chandelier).
> - **Passive Perception:** Use it for background awareness — players shouldn't need to announce "I search for traps" for obvious dangers.

**Part B — Add the section to `DMGuideTool` (line 687):**
Add a new collapsible/expandable section titled "When to Call for Rolls" in the `DMGuideTool` component, following the same visual pattern as existing sections. Use one card per category (Social / Exploration / Perception / Stealth / Combat Creative). Each card: category name + "Roll when…" + "Don't roll when…" in a two-line format.

**Part C — Add a link from Scene Painter:**
In `ScenePainterTool` (line 1492), find the `.lore-hint` div (around line 1751). Add a small text link below the existing hint text: `Roll guidance →` that switches the active tab to "guide" (calls `setActiveTab('guide')` via context or prop). Check how `setActiveTab` is passed — it comes from `App` via context (`AppContext`) at line 497.

**Acceptance:** Open DM Guide tab → see "When to Call for Rolls" section with category cards. Open Scene Painter → click "Roll guidance →" → tab switches to DM Guide.

---

## Section 2 — NPC Forge

### Task 2.1 — Diagnose and fix portrait generation

**File:** `tools/dm_toolkit.html`

**Where:** `NPCForgeTool` starts at line 1917. The `generatePortrait` function is inside this component. It builds a Pollinations.ai URL and loads it via `new Image()`.

**What to do:**
1. The user sees an error message when clicking Generate, confirming a network or CORS failure with Pollinations.ai — not a display/state bug.
2. Open browser DevTools (Network tab) and click Generate. Check whether the Pollinations.ai request is blocked (CORS error in console) or returns a non-200 status.
3. **Primary fix — server-side proxy:** Add a `/api/portrait-proxy` endpoint in `server.py` that accepts a `url` query parameter, fetches the image server-side using `urllib.request`, and streams it back as `image/png`. This bypasses any browser CORS restriction:
```python
@app.get("/api/portrait-proxy")
async def portrait_proxy(url: str):
    import urllib.request
    from fastapi.responses import Response
    req = urllib.request.Request(url, headers={"User-Agent": "DMToolkit/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    return Response(content=data, media_type="image/png")
```
4. In `dm_toolkit.html`, find `generatePortrait` inside `NPCForgeTool` (~line 1917). Change the `img.src` from the direct Pollinations URL to `"/api/portrait-proxy?url=" + encodeURIComponent(pollinationsUrl)`.
5. If the proxy also fails (Pollinations URL itself is broken), test the URL format directly: `https://image.pollinations.ai/prompt/test?width=512&height=512&nologo=true&model=flux` in a browser. If broken, check Pollinations.ai docs for the current URL format and update accordingly.

**Acceptance:** Click "Generate" on any NPC → portrait appears within ~20 seconds, no error message.

---

### Task 2.2 — Auto-add saved NPC to active campaign

**Files:** `tools/dm_toolkit.html` (NPC save call), `server.py` (save endpoint)

**Context:** When a campaign is active in NPC Forge, saving an NPC writes to `tools/npcs/` (the global NPC store). The campaign's `npcs/` markdown directory (at `campaign/{name}/npcs/`) is what `campaign_loader.py` reads for context — it does NOT get updated on NPC save.

**What to do:**

**In `server.py`:**
1. Find the `POST /api/npcs` endpoint.
2. Add an optional `campaign` field to the request body.
3. If `campaign` is non-empty, after saving the NPC JSON, write a markdown file to `campaign/{campaign}/npcs/{slug}.md` using this format:
```markdown
# {name}

**Role:** {role}
**Faction:** {faction or "None"}
**Stat Block:** {statBlock}

## Description
{description}

## Voice & Mannerisms
- **Voice quirk:** {voiceQuirk}
- **Physical tell:** {physicalTell}

## In This Interaction
- **Want:** {want}
- **Secret:** {secret}

## Sample Dialogue
{dialogue lines, one per bullet}
```
4. Return the markdown path in the response: `{ "ok": true, "mdPath": "campaign/..." }`.

**In `dm_toolkit.html` (`NPCForgeTool`, ~line 1917):**
1. When saving, include `campaign: activeCampaign` in the POST body.
2. On success, if `mdPath` is returned, show a brief inline message: "Saved to campaign" (green, fades after 2s).

**Acceptance:** With a campaign selected, forge and save an NPC. Check `campaign/{name}/npcs/` — a `.md` file exists with the NPC's full profile. The NPC Forge tab shows "Saved to campaign."

---

## Section 3 — Combat Companion

> All tasks modify `tools/dm_toolkit.html`. The `CombatTool` component starts at line 3970. The combatant data flows from `CombatTool` state → `LeftPanel` (3171) → `CombatantRow` (3005).

**Current combatant model** (inferred from `AddCombatantModal` at line 3698 and `CombatantRow` at line 3005):
```js
{
  id, name, type,          // type: "PC" | "Monster" | "NPC"
  hp, maxHp, initiative,
  conditions: [],          // [{name, duration, durationType}]
  notes: ""
}
```

Tasks 3.5–3.8 extend this model. Do 3.1–3.4 first since they don't touch the data model.

---

### ✅ Task 3.1 — Show dead/defeated combatants

**Where:** `CombatantRow` (line 3005), `LeftPanel.nextTurn` (~line 3176), CSS block.

**What to do:**
1. In the CSS block, add:
```css
.combatant-dead { opacity: 0.4; }
.combatant-dead .combatant-name { text-decoration: line-through; }
```
2. In `CombatantRow` (line 3005), check `combatant.hp <= 0`. Add `combatant-dead` to the row's className and prepend a `☠` skull glyph before the name.
3. In `LeftPanel`, find `nextTurn()` (~line 3176). When advancing `activeIdx`, skip any combatant where `hp <= 0`. Use a loop: increment index, wrapping with modulo, until a living combatant is found (or a full loop has occurred — stop to avoid infinite loop if all are dead).
4. Do NOT remove dead combatants from the list.

**Acceptance:** Set a combatant to 0 HP → row dims, skull appears, name is struck through. Click Next Turn → the dead combatant is skipped.

---

### Task 3.2 — Edit combatant name inline

**Where:** `CombatantRow` (line 3005). Add a new `onRename(id, newName)` prop, implemented in `LeftPanel` (line 3171) and passed down.

**What to do:**
1. Add local state to `CombatantRow`: `const [editing, setEditing] = useState(false)`.
2. When `editing` is false, show the name as text with a small ✏ icon that appears on row hover (use CSS: `.edit-btn { opacity: 0; } .combatant-row:hover .edit-btn { opacity: 0.6; }`).
3. When `editing` is true, replace the name text with an `<input>` pre-filled with the name. On `blur` or `Enter`, call `onRename(combatant.id, inputValue)` and set `editing` to false.
4. In `LeftPanel`, implement `renameCombatant(id, newName)` that updates the combatant in state via `setCombatants`.
5. Pass `onRename={renameCombatant}` through `LeftPanel` → `CombatantRow`.

**Acceptance:** Hover a combatant row → ✏ appears → click it → name becomes editable input → type new name, press Enter → name updates in the list.

---

### Task 3.3 — Duplicate a monster

**Where:** `CombatantRow` (line 3005), `LeftPanel` (line 3171).

**What to do:**
1. Add a copy icon (⧉) button to `CombatantRow` that appears on hover, alongside the ✏ from Task 3.2. Only show for `type === "Monster"`.
2. Add `onDuplicate(id)` prop to `CombatantRow`.
3. In `LeftPanel`, implement `duplicateCombatant(id)`:
   - Find the combatant
   - Generate a new `id`: `Date.now() + Math.random()`
   - Name: if the name ends in a number (e.g. "Goblin 2"), increment it. Otherwise append " 2". Pattern: `/^(.*?)(\s\d+)?$/` to split base + number.
   - Reset `hp` to `maxHp`, clear `conditions: []`
   - Insert the copy immediately after the original in the array
4. Pass `onDuplicate={duplicateCombatant}` through to `CombatantRow`.

**Acceptance:** Add "Goblin" → click ⧉ → "Goblin 2" appears below with full HP, no conditions. Click ⧉ on "Goblin 2" → "Goblin 3" appears.

---

### Task 3.4 — Loot tracker per monster

**Where:** `CombatantRow` (line 3005), combatant model.

**What to do:**
1. Add `loot: ""` to the default combatant object in `AddCombatantModal` (line 3698).
2. In `CombatantRow`, add a small 💰 icon button that renders only for `type === "Monster"`.
3. Clicking 💰 toggles a `lootOpen` local state. When open, show a `<textarea>` below the row for freeform loot notes ("12 gp, shortsword, potion of healing").
4. On textarea `onChange`, call a new `onLootChange(id, val)` prop. In `LeftPanel`, update the combatant's `loot` field in state.
5. If `loot` is non-empty and the drawer is closed, show the loot text as dim italic below the combatant name (no icon needed — just the text).

**Acceptance:** Add a monster → click 💰 → textarea appears → type "50 gp, rusty dagger" → click 💰 again to close → "50 gp, rusty dagger" shown in dim italic below name.

---

### Task 3.5 — Dice Modifier Toggles (Bless / Bane / Guidance)

**Where:** `CombatantRow` (line 3005), combatant model, `AddCombatantModal` (line 3698).

**Model change:** Add `diceModifiers: { bless: false, bane: false, guidance: false }` to the default combatant.

**D&D context:**
- **Bless** (+1d4 to attack rolls and saving throws) — concentration, gold color
- **Bane** (-1d4 to attack rolls and saving throws) — concentration, red color
- **Guidance** (+1d4 to one ability check) — cantrip, teal color

**What to do:**
1. In `CombatantRow`, add a small `±` toggle button after the existing icons (pencil, copy). Clicking toggles local `diceModOpen` state — this is a **separate panel** from Adv/Disadv (Task 3.6).
2. When `diceModOpen`, show a compact chip row below the combatant:
   - `[+1d4 ATK/SAV]` — gold when active (Bless)
   - `[-1d4 ATK/SAV]` — red when active (Bane)
   - `[+1d4 CHECK]` — teal when active (Guidance)
3. Each chip calls `onModifierChange(id, key, value)`. In `LeftPanel`, update the combatant in state.
4. **Mutual exclusion:** toggling Bless turns off Bane and vice versa. Guidance is independent.
5. When any modifier is active and the panel is closed, show a small colored dot badge next to the combatant name.

**Acceptance:** Toggle Bless → gold badge appears on row. Toggle Bane → Bless off, red badge appears. Toggle Guidance → separate teal badge. All independent of Adv/Disadv panel.

---

### Task 3.6 — Advantage / Disadvantage Toggles

**Where:** Combatant model, `CombatantRow`, `LeftPanel`.
**Independent of Task 3.5** — this is a separate expandable panel on the row, not shared.

**Model change:** Add to combatant:
```js
advDisadv: {
  attackOut: null,     // "adv" | "dis" | null
  attackIn: null,      // "adv" | "dis" | null
  saves: null,         // "adv" | "dis" | null
  abilityCheck: null,  // "adv" | "dis" | null
  hexAbility: ""       // e.g. "Strength" — for Hex-style targeted penalties
}
```

**D&D context:**
- **Vex** (weapon mastery): attacker gains ADV on their next attack after hitting
- **Sap** (weapon mastery): target has DIS on their next attack roll
- **Hex** (spell): target has DIS on a specific ability check type

**What to do:**
1. In `CombatantRow`, add a second small toggle button (e.g. `▲▼`) that toggles a separate `advOpen` local state — distinct from `diceModOpen` (Task 3.5). Both panels can be open simultaneously.
2. When `advOpen`, show four rows below the combatant (under the dice panel if that's also open):
   - "Attacks Out" — [ADV] [DIS] toggle pair
   - "Attacks In" — [ADV] [DIS] toggle pair
   - "Saves" — [ADV] [DIS] toggle pair
   - "Ability Checks" — [ADV] [DIS] toggle pair + small text input "which ability?" (for Hex)
3. Each toggle calls `onAdvDisadvChange(id, key, value)`. In `LeftPanel`, update combatant state.
4. Show colored badges in the collapsed row: green pill = ADV, red pill = DIS, abbreviated label ("ATK↑", "ATK↓", "SAV", "CHK").

**Acceptance:** Toggle ADV on "Attacks Out" → green "ATK↑" badge appears. Toggle DIS on "Saves" → red "SAV" badge appears. Dice modifier panel and Adv/Disadv panel open/close independently.

---

### Task 3.7 — Advantage turn counter (auto-expiry with event log)

**Where:** Combatant model, `CombatantRow`, `LeftPanel.nextTurn`.
**Depends on:** Task 3.6.

**Model change:** Extend `advDisadv` values from `"adv"/"dis"` to objects:
```js
attackOut: null | { state: "adv"|"dis", turns: null|number }
```
(null = cleared; turns null = permanent/manual; turns = N = auto-expires after N of this combatant's turns)

Also add `combatLog: []` to `CombatTool` state — array of `{ msg: string, round: number }`.

**What to do:**
1. In the expanded modifier panel, add a turn counter selector next to each ADV/DIS toggle: `[∞]` `[1]` `[2]` `[3]`. Default is `∞` (manual). Selecting a number sets `turns: N`.
2. In `LeftPanel.nextTurn()` (line ~3176): when the turn advances *past* a combatant (i.e., it was just their turn), iterate through their `advDisadv` keys. For any with `turns !== null`, decrement by 1. If it reaches 0, clear that state and push to `combatLog`: `"{name}'s {label} ({state}) expired – Round {roundNumber}"`.
3. Show the last 5 log entries in a collapsible "⚡ Event Log" area at the bottom of `LeftPanel`, below the combatant list. Toggle open/closed with a small button.

**Acceptance:** Set ADV on attacks out for "1 turn" → advance past that combatant's turn → ADV clears, log entry appears in Event Log panel.

---

### Task 3.8 — Booming Blade tracker

**Where:** Combatant model, `CombatantRow`, `LeftPanel`.
**Depends on:** Task 3.7 (uses `combatLog`).

**D&D context:** Booming Blade — on hit, the target is wreathed in booming energy. If the target willingly moves before the start of the caster's next turn, they take 1d8 thunder damage (2d8 at 5th level). The DM needs to flag which creature has this condition and get a prompt when their turn comes up.

**Model change:** Add `boomingBlade: false` to combatant.

**What to do:**
1. In the expanded modifier panel (Task 3.5), add a `[☈ Booming Blade]` toggle chip with teal/purple styling.
2. When active, show a prominent `☈` badge on the collapsed row.
3. In `LeftPanel.nextTurn()`: when the turn advances TO a combatant with `boomingBlade: true`, display a temporary alert banner inside `LeftPanel` (not a modal — just a yellow banner at the top of the combatant list):
   > ⚡ **{Name}** has Booming Blade — did they move?
   > `[Yes — Took Damage]` `[No — Did Not Move]`
4. `[Yes — Took Damage]` → push to `combatLog`: `"{Name} took Booming Blade damage (1d8 thunder) – Round {N}"` → clear `boomingBlade` flag.
5. `[No — Did Not Move]` → push to log: `"{Name}'s Booming Blade expired without triggering"` → clear flag.

**Acceptance:** Mark a monster with ☈ → advance to their turn → yellow alert banner appears with both buttons. Click "Yes — Took Damage" → log entry appears, ☈ badge disappears.

---

### Task 3.9 — More stats in PC stat block (center panel)

**Where:** `CenterPanel` (line 3260), `AddCombatantModal` (line 3698), combatant model.

**Context:** When a PC is selected in the center panel, check what currently renders — likely a minimal card or placeholder. The center panel's `CenterPanel` component switches display based on the selected combatant type.

**Model change:** Add optional PC fields to combatant:
```js
ac: null, passivePerception: null, spellSaveDC: null, concentration: ""
```

**What to do:**
1. In `AddCombatantModal` (line 3698), detect when `type === "PC"` is selected. Show additional optional fields: AC, Passive Perception, Spell Save DC.
2. In `CenterPanel` (line 3260), find where PC combatants are rendered. Expand the PC display to show:
   - Name + class + level (from existing fields if present)
   - HP current/max (from combatant state)
   - AC | Passive Perception | Spell Save DC — in a stat row
   - Active concentration field (editable text: "Concentration: ___")
   - Any active modifiers from Tasks 3.5/3.6 displayed as a summary row
3. The concentration field should update the combatant's `concentration` value via `setCombatants` in `CombatTool`.

**Acceptance:** Add a PC with name "Elara", AC 16, PP 14, Spell Save DC 15 → select Elara in the center panel → see all stats displayed. Edit the concentration field → value persists in state.

---

## Section 4 — New Features (New Tabs)

New tabs are added to the `TABS` array in `App` (~line 4070) and rendered in the tab switcher block (~lines 4123–4147). Each new tool is a new React component function added to `dm_toolkit.html` before the `App` function.

> **File size note:** `dm_toolkit.html` is already 4161 lines. Each new tool adds ~300–600 lines. Add them sequentially before the `App` function (~line 4060), in order: EncounterHelperTool → LootCalculatorTool → CampaignCalendarTool → AmbianceTool.

---

### Task 4.1 — Encounter Helper (XP Budget Calculator)

**New component:** `EncounterHelperTool`
**New tab:** `{ id: 'encounter', label: '⚔ Encounter', icon: '⚔' }`

**Context:** D&D 5.5e XP budget method. Each monster has a known XP value by CR. Party difficulty is the sum of per-PC thresholds × party size. `monsters.json` is already served at `/tools/monsters.json` and contains CR and XP for all SRD monsters.

**XP thresholds (per PC, 5.5e — embed as a constant):**
```js
const XP_THRESHOLDS = {
  1:  { low:25,   mod:50,   high:75,   deadly:100  },
  2:  { low:50,   mod:100,  high:150,  deadly:200  },
  3:  { low:75,   mod:150,  high:225,  deadly:400  },
  4:  { low:125,  mod:250,  high:375,  deadly:500  },
  5:  { low:250,  mod:500,  high:750,  deadly:1100 },
  6:  { low:300,  mod:600,  high:900,  deadly:1400 },
  7:  { low:350,  mod:750,  high:1100, deadly:1700 },
  8:  { low:450,  mod:900,  high:1400, deadly:2100 },
  9:  { low:550,  mod:1100, high:1600, deadly:2400 },
  10: { low:600,  mod:1200, high:1900, deadly:2800 },
};
// For levels 11–20: multiply level 10 values by 1.5 / 2 / 2.5 / 3 as a reasonable approximation
```

**Layout (three columns):**

**Left — Party Setup:**
- Party size: number input (2–8, default 4)
- Party level: number input (1–20, default 5)
- Computed threshold display: Low / Moderate / High / Deadly XP totals (party size × per-PC threshold), shown as colored chips

**Center — Monster Builder:**
- Search input that filters `monsters.json` by name (load once via `fetch('/tools/monsters.json')` on mount, store in state)
- Results list: name + CR + XP — click to add to the encounter
- Encounter list below search: each entry shows monster name, CR, XP, quantity +/- controls, and a remove button
- Running total XP displayed prominently at the bottom of this column

**Right — Difficulty Readout:**
- Large color-coded label: **Low** (green) / **Moderate** (yellow) / **High** (orange) / **Deadly** (red) / **Beyond Deadly** (pulsing red)
- Flavor text per tier (e.g., Deadly = "High chance of PC death. Use for boss encounters or climactic fights.")
- "Send to Combat" button: saves the encounter monster list to `localStorage` under key `combat_prefill` (array of `{ name, count }` objects), then calls `setActiveTab('combat')` via `AppContext`. In `CombatTool`, add a `useEffect` on mount that checks `localStorage.getItem('combat_prefill')` — if present, use the existing `allMonsters` data to look up each monster by name, create combatant entries (one per count), add them to state, then delete the key from localStorage so it doesn't re-trigger on next open.

**No AI, no new API endpoints.** All math is local.

**Acceptance:** Set 4 PCs at level 5 (party thresholds: Low=1000, Mod=2000, High=3000, Deadly=4400). Add 1 Young Dragon (CR 10, 5900 XP) → readout shows "Deadly". Remove it, add 8 Goblins (25 XP each = 200) → shows "Low". Click "Send to Combat" → Combat tab opens with 8 Goblins pre-loaded.

---

### Task 4.2 — Loot & Hoard Calculator

**New component:** `LootCalculatorTool`
**New tab:** `{ id: 'loot', label: '💰 Loot', icon: '💰' }`

**Context:** Based on D&D 5e DMG treasure tables. Replaces mid-session DMG page-flipping. No AI needed — pure dice math on static tables.

**Embed these tables as JS constants:**

Individual treasure by CR tier (d100 roll → result):
```js
// CR 0-4
[{min:1,max:30,cp:[5,6],sp:0,ep:0,gp:0,pp:0},
 {min:31,max:60,cp:0,sp:[4,6],ep:0,gp:0,pp:0},
 {min:61,max:70,cp:0,sp:0,ep:[3,6],gp:0,pp:0},
 {min:71,max:95,cp:0,sp:0,ep:0,gp:[3,6],pp:0},
 {min:96,max:100,cp:0,sp:0,ep:0,gp:0,pp:[1,6]}]
// (similar patterns for CR 5-10, 11-16, 17+)
```

Magic item tiers (simplified — embed a static list of ~30 common/uncommon items):
```js
const MAGIC_ITEMS_A = ["Potion of Healing","Spell Scroll (1st level)","Potion of Climbing",...];
const MAGIC_ITEMS_B = ["Potion of Greater Healing","Bag of Holding","Cloak of Protection",...];
```

**Layout:**

**Left — Configuration:**
- Mode toggle: Individual Loot / Hoard
- CR input or CR-tier selector (0–4 / 5–10 / 11–16 / 17+)
- For Individual: number of monsters (1–20)
- Roll button

**Center — Result:**
- Itemized output: "240 cp, 45 sp, 12 gp" + any magic items
- "Roll Again" button
- "Copy" button (copies as plain text to clipboard)

**Right — Session Log:**
- "Save This Loot" button appends the current result to `localStorage` list
- Shows last 10 saved entries with a timestamp label
- "Clear Log" button

**Acceptance:** Select CR 5–10 / Hoard / click Roll → see coins + 1–2 magic items. Click Roll Again → different result. Click Copy → clipboard has formatted text. Click Save → entry appears in Session Log.

---

### Task 4.3 — Campaign Calendar & Weather Tracker

**New component:** `CampaignCalendarTool`
**New tab:** `{ id: 'calendar', label: '📅 Calendar', icon: '📅' }`
**New API endpoints in `server.py`:**
- `GET /api/campaign/{name}/calendar` — returns `calendar.json` or a default structure
- `POST /api/campaign/{name}/calendar` — saves `calendar.json`

**Data model** (`campaign/{name}/calendar.json`):
```json
{
  "currentDay": 1,
  "currentMonth": 0,
  "climate": "temperate",
  "months": ["Month 1","Month 2","Month 3","Month 4","Month 5","Month 6","Month 7","Month 8","Month 9","Month 10","Month 11","Month 12"],
  "entries": {
    "0-1": { "weather": "clear", "temp": "cool", "notes": "" }
  }
}
```
Key format: `"{monthIndex}-{day}"`.

**Weather roll tables (embed as constants — weighted by climate):**
```js
const WEATHER_BY_CLIMATE = {
  temperate: ["Clear","Clear","Overcast","Light Rain","Heavy Rain","Fog","Snow"],
  desert:    ["Clear","Clear","Clear","Dust Storm","Scorching","Haze","Clear"],
  arctic:    ["Blizzard","Heavy Snow","Snow","Overcast","Clear","Ice Fog","Blizzard"],
  coastal:   ["Clear","Sea Mist","Light Rain","Heavy Rain","Storm","Fog","Clear"],
  magical:   ["Clear","Magical Glow","Ethereal Mist","Arcane Storm","Eerie Silence","Clear","Faerie Shimmer"],
};
```

**Layout:**

**Left — Month Grid:**
- Climate selector dropdown at top
- Campaign selector (uses `activeCampaign` from context, or a local dropdown if context isn't available)
- Month navigation (< Prev Month | Month Name | Next Month >)
- Small "Rename" button next to the month name that lets the DM edit it inline (e.g. rename "Month 3" to "Ches" if they want to use a setting-specific calendar later)
- 30-day grid (5×6). Each cell shows day number + a weather icon if an entry exists. Current day highlighted gold.
- Click a day cell to select it and open its editor in the right panel.

**Center/Right — Day Editor:**
- Selected day header: "Day {N}, {Month Name}"
- Weather dropdown: Clear / Overcast / Light Rain / Heavy Rain / Fog / Snow / Blizzard / Dust Storm / Magical / Storm / Other
- Temperature: Hot / Warm / Cool / Cold / Freezing
- Notes textarea
- "Roll Weather" button (uses weighted random from `WEATHER_BY_CLIMATE` for the current climate)
- "Save Day" button (auto-saves to server if campaign active, or to `localStorage` if no campaign)
- Navigation: `← Prev Day` | `Today` | `Next Day →` — "Today" highlights and selects `currentDay`. "Next Day →" also advances `currentDay`.

**Acceptance:** Select a campaign → navigate to day 5 → add weather "Fog" and notes "Party enters Barovia" → Save → day 5 shows fog icon on grid. Click "Next Day →" → day 6 is now current. Reload app → day 5 entry persists. Click "Roll Weather" → random weather appears in dropdown.

---

### Task 4.4 — Ambiance Tool (Music & Sound Effects)

**New component:** `AmbianceTool`
**New tab:** `{ id: 'ambiance', label: '🎵 Ambiance', icon: '🎵' }`

**Approach:** Browser-native Web Audio API + curated free audio. The agent must investigate and verify sources before hardcoding any URLs — don't assume availability.

**Investigation step (do this first, before writing any component code):**
1. Test whether Incompetech streaming URLs are CORS-accessible from `localhost:8000`. Try: `https://incompetech.com/music/royalty-free/mp3-royaltyfree/Constancy%20Part%20Three.mp3` in a `fetch()` call from the browser console. If blocked, use the portrait proxy pattern: add `/api/audio-proxy?url={encoded}` in `server.py` and route all audio through it.
2. For SFX, test Freesound.org CC0 direct links, or use the Zapsplat free tier. If external sources are unreliable, consider encoding a small number of short SFX as base64 data URIs directly in the JS (acceptable for sounds under ~50KB).
3. Pick whichever sources reliably work and document them in a comment at the top of `AmbianceTool`.

**Fallback:** If no audio can reliably play, render the preset buttons as links that open a curated YouTube/Spotify playlist in a new tab, with a note in the SFX panel: "Sound effects require a network connection."

**Atmosphere presets (embed track metadata as constants):**
```js
const PRESETS = [
  { id: "tavern",   label: "Tavern",    icon: "🍺", track: "Constancy Part Three", artist: "Kevin MacLeod", url: "..." },
  { id: "dungeon",  label: "Dungeon",   icon: "🏚", track: "Ominous", artist: "Kevin MacLeod", url: "..." },
  { id: "forest",   label: "Forest",    icon: "🌲", track: "The Forest and the Trees", artist: "Kevin MacLeod", url: "..." },
  { id: "combat",   label: "Combat",    icon: "⚔",  track: "Clash Defiant", artist: "Kevin MacLeod", url: "..." },
  { id: "mystical", label: "Mystical",  icon: "✨", track: "Floating Cities", artist: "Kevin MacLeod", url: "..." },
  { id: "town",     label: "Town",      icon: "🏘", track: "Merry Go", artist: "Kevin MacLeod", url: "..." },
  { id: "storm",    label: "Storm",     icon: "🌩", track: "Stormfront", artist: "Kevin MacLeod", url: "..." },
];
```
(Look up and verify each URL before hardcoding.)

**SFX list (one-shot):**
Door creak, Thunder crack, Sword clash, Magic shimmer, Tavern crowd cheer, Crackling fire, Dramatic sting.

**Layout:**

**Left — Presets:**
- Large clickable preset cards (icon + label). Active preset highlighted gold. Clicking loads that preset's track and begins playing (or resumes if already playing same preset).

**Center — Music Player:**
- Track name + artist
- Play/Pause button + loop indicator (always loop)
- Music volume slider (0–100)
- Attribution line: "Music by {artist} / incompetech.com — CC BY"

**Right — SFX Panel:**
- Grid of SFX buttons. Each is a large pill button with icon + label.
- SFX volume slider (separate from music)
- SFX play via `new Audio(url).play()` — one-shot, overlaps music.

**Use `useRef` for the music `<audio>` element** to persist it across re-renders without recreating it.

**Fallback UI:** If audio loading fails (network error or CORS), replace the play button with a grayed "Unavailable" state and show a small message: "Audio unavailable — check network or try the proxy setting."

**Acceptance:** Click "Dungeon" preset → music starts looping. Adjust music volume → volume changes. Click "Thunder crack" SFX → brief thunder plays over music. Music continues uninterrupted. Click another preset → music crossfades (or immediately switches) to new track.

---

## Implementation Order (Recommended)

Work in this order to get value fast and avoid large diffs in the same sections:

1. **3.1** — dead combatants (2 touches: CSS + `CombatantRow` + `nextTurn`)
2. **3.2** — edit name inline (UI only, `CombatantRow`)
3. **3.3** — duplicate monster (`CombatantRow` + `LeftPanel`)
4. **3.4** — loot tracker per monster (small model addition)
5. **1.1** — scene painter inner box (CSS/JSX, small)
6. **3.5 + 3.6** — dice modifiers + adv/disadv (do together; shared expanded panel)
7. **3.7** — turn counter + event log (extends 3.6)
8. **3.8** — booming blade (extends 3.7 log)
9. **3.9** — PC stat block expansion
10. **2.1** — portrait fix (diagnose first, unknown scope)
11. **2.2** — NPC → campaign markdown (touches `server.py`)
12. **1.2** — DM Guide rolls section (Gemini review pass first)
13. **4.1** — Encounter Helper (new component, large)
14. **4.3** — Loot Calculator (new component, large)
15. **4.2** — Calendar (new component + `server.py` endpoints)
16. **4.4** — Ambiance (investigate audio sources first)

---

## Agent Notes

- **Branch per task:** `git checkout -b feature/<short-name>` before starting. Merge to `main` and deploy after each task.
- **One file:** All tool changes go in `tools/dm_toolkit.html`. Don't create new `.html` files — add new components and tabs inside the existing file.
- **No build step:** Components are `<script type="text/babel">` blocks. No webpack/npm needed.
- **CSS vars only:** Use `var(--gold)`, `var(--bg-card)`, etc. from the existing `:root` block (~line 15). Don't hardcode hex colors.
- **Test locally:** `uvicorn server:app --reload` → `http://localhost:8000/tools/dm_toolkit.html`
- **Gemini rate limits:** Max 15 RPM / 250k TPM. Only use for Task 1.2 content review. One batched request.
- **Deploy after each merged task:** `ssh rachett 'bash ~/deploy.sh dnd'`
- **`server.py` changes** (Tasks 2.2, 4.3): restart uvicorn after editing to pick up changes.
