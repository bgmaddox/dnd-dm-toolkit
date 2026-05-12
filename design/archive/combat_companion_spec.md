# Combat Companion — Design Spec

Visual target established via Claude Design prototype. Build to match this layout and behavior.

## Color System (matches NPC Forge exactly)
| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#111318` | Page background |
| `--card` | `#1c2028` | Cards, panel backgrounds |
| `--card-hover` | `#222736` | Card hover state |
| `--border` | `#2a2f3d` | Default borders |
| `--border-bright` | `#3a4255` | Scrollbar thumb |
| `--gold` | `#c9a84c` | Headings, active states, buttons |
| `--gold-dim` | `#8a7035` | Dimmed gold accents |
| `--gold-glow` | `rgba(201,168,76,0.15)` | Glow effects |
| `--text` | `#dde3f0` | Primary text |
| `--text-dim` | `#8a93a8` | Secondary text |
| `--text-faint` | `#4e566a` | Hints, disabled states |
| `--blue` | `#4a78c4` | PC badge |
| `--red` | `#c44a4a` | Monster badge, flee callout |
| `--teal` | `#3da894` | Concentrating badge, freeform response |
| `--green` | `#5aab6a` | HP bar >50% |
| `--yellow` | `#c9a84c` | HP bar 25-50% |
| `--poison` | `#6db55e` | Poisoned badge |

## Fonts
- Headings: `Cinzel` (Google Fonts, serif)
- Body: `Crimson Pro` (Google Fonts, serif)

## Layout — Three Panels, Full Viewport Height

```
┌──────────────────────────────────────────────────────────┐
│  LEFT (240px)  │     CENTER (flex)      │  RIGHT (280px) │
│  Active        │  Monster Reference     │  AI Assist     │
│  Encounter     │  STAT BLOCK | TACTICS  │                │
└──────────────────────────────────────────────────────────┘
```

No header bar (unlike NPC Forge — full height goes to the three panels).

---

## Left Panel — Active Encounter

### Header
- "ACTIVE ENCOUNTER" label (gold, Cinzel, small caps)
- Encounter name (bold, larger)
- Terrain/conditions note (italic, muted, emoji icon prefix)

### Round Counter Strip
- "ROUND" label left, round number center (gold), "Initiative Order" right (faint)

### Combatant List
Each row is a card with:
- **Name** (Cinzel font; ALL CAPS for monsters, title case for PCs)
- **Type badge** — "PC" (blue pill) or "MON" (red pill)
- **HP bar** — thin 5px bar; green >50%, yellow 25-50%, red <25%, grey at 0
- **HP numbers** — `current/max` right-aligned, muted
- **Condition badges** — colored pills per condition (see condition color map below)
- **Active state** — gold border + gold left border + darker background + pulsing gold dot (top-right)

### Condition Color Map
| Condition | Background | Border | Text |
|-----------|-----------|--------|------|
| Concentrating | teal 25% | `#3da894` | `#3da894` |
| Unconscious | grey 20% | `#666` | `#999` |
| Frightened | red 25% | `#c44a4a` | `#e06868` |
| Poisoned | green 25% | `#6db55e` | `#6db55e` |
| Stunned | purple 25% | `#9b6ac8` | `#b48de0` |
| Prone | orange 25% | `#c9843c` | `#e0a060` |

### Buttons
- **NEXT TURN →** — full-width gold gradient button, advances active combatant cyclically
- **+ ADD COMBATANT** — faint text link, expands inline form (name, HP, type dropdown)

---

## Center Panel — Monster Reference

### Search Bar
- Full-width input with magnifying glass icon (⌕)
- Searches `monsters.json` by name (client-side, loaded on page load)
- Results displayed as a dropdown list on keystroke

### Monster Display Area (scrollable)
Once a monster is selected:

**Name + Tags**
- Monster name in large Cinzel gold heading
- Italic subtitle: "Size Type (Subtype), Alignment"
- Tag row: Size+Type badge (blue), CR badge (gold), XP badge (muted)

**Tabs — sticky at top of scroll area**
- `STAT BLOCK` | `TACTICS` — gold underline on active, faint text on inactive
- Tabs must stay visible when scrolling the content below them (`position: sticky`)

**STAT BLOCK tab:**
1. Quick stats bar (gold-tinted background): AC · HP · Speed
2. Ability score grid (6 columns): score + modifier per stat
3. Proficiencies block (2-column grid): Saving Throws, Skills, Senses, Languages
4. TRAITS section — italic bold name, then description
5. ACTIONS section — same format
6. BONUS ACTIONS — if present
7. REACTIONS — if present
8. LEGENDARY ACTIONS — if present (for boss monsters)

**TACTICS tab:**
1. "⚔ HOW TO PLAY THIS MONSTER" heading
2. 2-4 tactical bullet points in gold-tinted cards
3. **Flee/Surrender callout** — red left-border card with 🏃 icon and threshold description
   - Example: "Flees at ~30% HP if allies are dead — hobgoblins are disciplined, not suicidal."

**Tactics data strategy:**
- Generated on-demand by Claude (Haiku) on first monster lookup
- Cached in `tools/tactics_cache.json` keyed by monster slug
- Prompt: given the monster's stat block, abilities, and lore — how does it fight intelligently?
- Never regenerated unless cache is cleared

---

## Right Panel — AI Assist

### Header
- "AI Assist" (Cinzel, gold, 16px)
- "Powered by Claude" (faint, 11px)

### Three Quick-Action Buttons (always visible)
Each is a card button with icon + label + subtitle:
1. **⚡ Describe This Hit** — "Narrate a strike cinematically"
2. **🏃 Flee or Fight?** — "Would this monster retreat?"
3. **🎯 Smart Move** — "What's the tactical play?"

Active button: gold border + gold-tinted background

### Expanded Prompt Form (below buttons)
When a quick-action is selected, shows its input fields + GENERATE button.

**Describe This Hit:**
- Damage dealt (text input)
- Target HP state (dropdown: Fresh / Injured / Bloodied / Critical)
- Monster name auto-populated from center panel

**Flee or Fight?:**
- Monster HP % (text input)
- Situation (dropdown: Allies present / Allies fallen / Cornered / Open path to flee)
- Monster name auto-populated from center panel

**Smart Move:**
- Situation note (text input, optional)
- Monster name + full stat block summary auto-sent as context

### AI Response Card
- Dark background (`#141820`), gold left border
- "AI RESPONSE" label (gold-dim, tiny caps)
- Response text (italic, muted, 13px)
- "Consulting the arcane..." placeholder while loading

### Freeform Chat (pinned to bottom)
- Text input: "Ask anything..."
- Send button: → (gold)
- On Enter or click: sends full combat state as context automatically
  - Format: "Current combat: [name] ([type], [hp]/[maxHp] HP), ... Active: [name]"
- Response shown in teal-accented card above the input

---

## AI Prompt Architecture

All prompts auto-receive combat context from app state:
- Active combatant name and type
- Full combatant list with HP states

```javascript
// Pattern for all three quick prompts:
buildPrompt: (fieldValues, combatants, activeIdx) => {
  const active = combatants[activeIdx];
  // Build prompt using active.name, active.hp, etc.
}
```

Replace `window.claude.complete(promptText)` with:
```javascript
const res = await fetch('/api/ai/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ prompt: promptText, max_tokens: 200 })
});
const data = await res.json();
return data.content;
```

**Model:** `claude-haiku-4-5-20251001` for all three quick prompts and freeform chat.
Fast and cheap — responses should feel near-instant.

---

## Data Connections

| Feature | Data Source | Loading Strategy |
|---------|-------------|-----------------|
| Monster search | `tools/monsters.json` | Load full file client-side on page load |
| Condition descriptions | `tools/conditions.json` | Load client-side on page load |
| Monster tactics | `tools/tactics_cache.json` | Check cache first; generate with Haiku if missing |
| AI narration/advice | Claude API via `/api/ai/generate` | On-demand, Haiku model |

---

## Prototype Approval
Design reviewed and approved (two-iteration review). Date: 2026-05-01
