# NPC Forge — Design Spec

Visual target established via Claude Design prototype. Build the Streamlit implementation
to match this layout and color system.

## Color System
| Token | Hex | Usage |
|-------|-----|-------|
| Background | `#111318` | Page background |
| Surface | `#1c2030` | Cards, sidebar |
| Surface 2 | `#252a3a` | Input fields, secondary cards |
| Gold | `#c9a84c` | Headings, accents, primary button, badge borders |
| Gold light | `#e2c875` | NPC name heading |
| Gold dim | `#8a6f2e` | Card label text, borders |
| Text | `#dde3f0` | Body copy |
| Text muted | `#8a92a8` | Secondary text, placeholders |
| Border | `#2e3450` | Card borders |

## Typography
- Headings: Georgia (serif) — NPC name, section heading, tool title
- Body / UI: Segoe UI or system sans-serif — labels, card content, inputs
- Dialogue: Georgia italic

## Layout

### Header Bar (full width, fixed)
- Left: "DM TOOLKIT" logo text
- Right: gold dot + "Campaign: [campaign name]"
- Background: surface color, 1px bottom border

### Left Sidebar (fixed width ~260px)
- Tool title: "NPC Forge" (gold, serif)
- Subtitle: "Describe a concept and forge a fully playable character in seconds."
- **Inputs:**
  - CONCEPT — text input, placeholder "e.g. nervous blacksmith, smug noble guard captain"
  - NAME — text input, optional badge, placeholder "Leave blank to generate"
  - FACTION / AFFILIATION — text input, optional badge, placeholder "e.g. Thieves Guild, Town Guard, None"
- **FORGE NPC button** — full width, gold background, dark text, ✦ icon prefix
- Keyboard hint: "Press Ctrl+Enter in any field to forge." (muted italic, small)
- **SAVED NPCS section** — list of previously generated NPCs, name + role tag per row

### Right Main Panel (scrollable)

#### 1. NPC Name
- Large serif heading, gold-light color
- Below: three pill badges — Role / Stat Block / Faction
  - Badge style: small caps, colored dot prefix, dark background, colored border per type

#### 2. Physical Description
- Section label: "PHYSICAL DESCRIPTION" (small caps, muted, spaced)
- Content block with gold left border (3px)
- 2 sentences max

#### 3. 2×2 Card Grid
Four equal cards with dark surface background, 1px border:
- **VOICE QUIRK** — top left
- **PHYSICAL TELL** — top right
- **IMMEDIATE WANT** — bottom left
- **SECRET** — bottom right

Each card: gold-dim label in small caps with em-dash prefix (— VOICE QUIRK), body text below.

#### 4. Deep Want / Fear
Full-width card, visually distinct from the 2×2 grid:
- Slightly different background shade (surface2) and subtle gold border
- Label: "— DEEP WANT / FEAR" in small caps
- 2-3 sentences — the underlying motivation or fear that drives the NPC

#### 5. Sample Dialogue
- Section label: "SAMPLE DIALOGUE"
- Dark surface block, large gold opening quotation mark decoration
- 2-3 lines, each prefixed with gold left border (2px), italic serif text
- Slight vertical spacing between lines

#### 6. Action Buttons
- **SAVE TO CAMPAIGN** — full width primary, gold background
- **↺ REGENERATE** — secondary/outline style, right of save or below

---

## Streamlit Implementation Notes

Streamlit doesn't natively support this level of custom styling, but it can be achieved with:
- `st.markdown()` with `unsafe_allow_html=True` for custom card HTML
- A CSS injection block via `st.markdown("<style>...</style>", unsafe_allow_html=True)`
  at the top of the page — import the color tokens and typography rules from this spec
- `st.columns([1, 2])` for the sidebar / main panel split
- `st.columns(2)` for the 2×2 card grid

The `dm_learning_guide.html` already has a working CSS implementation of this color system
and card style — reuse those styles directly in the Streamlit CSS injection block.

---

## Prototype Approval
Design reviewed and approved. Build target locked. Date: 2026-05-01
