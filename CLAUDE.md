# CLAUDE.md — DnD DM Toolkit

## Architecture & Workflow

- **Branching:** Create a feature branch from `main` before any implementation task (`feat-*` or `fix-*`).
- **Validation:** Run the server locally (`python server.py`) to verify changes before committing.

## Deployment — three targets, always keep in sync

Every meaningful change (new feature, bug fix, content update) must be pushed to **all three**:

| Target | Command |
|--------|---------|
| GitHub | `git push` |
| Raspberry Pi | `ssh rachett 'bash ~/deploy.sh dnd'` |
| dist package | `python scripts/package.py` (then commit the version bump) |

**Never skip dist.** It is the portable/desktop distribution for users without a Pi. If you deploy to GitHub and the Pi but forget dist, the downloadable package goes stale.

### When to rebuild dist

Rebuild dist (and bump the version in `server.py`) whenever:
- A new feature or tool is added
- A bug fix changes user-visible behavior
- Any file in `tools/`, `campaign/`, `utils/`, or `server.py` changes
- `USER_GUIDE.md` is updated

Version scheme: `MAJOR.MINOR.PATCH`
- PATCH — bug fixes
- MINOR — new features, tool additions
- MAJOR — breaking changes or full rewrites

### dist rebuild steps

```bash
# 1. Bump VERSION in server.py
# 2. Build the package
python scripts/package.py
# 3. Commit the version bump (dist/ is gitignored, no need to stage it)
git add server.py
git commit -m "chore: bump version to X.Y.Z"
git push
```

## Local Development

- **Run:** `python server.py` (activate `.venv` first: `source .venv/bin/activate`)
- **Environment:** `.venv/` in project root, Python 3.13, dependencies in `requirements.txt`

## Pi Deployment

- **Service:** `dnd-toolkit.service`
- **Path:** `/home/bgmaddox/dnd`
- **Deploy:** `ssh rachett 'bash ~/deploy.sh dnd'`
- **If git pull fails on Pi:** The Pi's working tree may have conflicts. Check with the user before running `git reset --hard origin/main && git clean -fd`.

## dm_toolkit.html — Navigation Guide

`tools/dm_toolkit.html` is a ~4200-line React SPA. **Never read it top-to-bottom.** Always grep first.

### Find any component instantly

```bash
# All major landmarks (section headers + top-level functions)
grep -n "^// ─\|^function \|^class \|^const TABS" tools/dm_toolkit.html

# Jump to a specific tool component
grep -n "function ScenePainterTool\|function NPCForgeTool" tools/dm_toolkit.html
```

### Component map (approximate line ranges)

| Lines | What's there |
|-------|-------------|
| 1–493 | `<style>` block — all CSS |
| 494–503 | `AppContext`, `APP_SETTINGS_KEY`, `loadSettings` |
| 504–639 | TweaksPanel helpers: `useTweaks`, `TweaksPanel`, `TweakSection/Row/Slider/Toggle/Radio/Color` |
| 640–683 | `DeferredMount`, `ToolErrorBoundary`, `useAIGenerate` hook |
| 686–1176 | `DMGuideTool` (DM Learning Guide — pure display, no AI calls) |
| 1177–1370 | `LoreBuilderTool` (save NPCs/locations to campaign files) |
| 1371–1777 | `ScenePainterTool` + sub-components (`ScenePillSelector`, `SceneOutput`) |
| 1778–2376 | `NPCForgeTool` + sub-components (`NPCOutput`, `NPCLoadingState`) |
| 2377–2878 | `SessionTool` (session companion — chat, oracle, handoffs) |
| 2879–3944 | `CombatTool` + all sub-components (`CombatantRow`, `LeftPanel`, `RightPanel`, `CenterPanel`, modals) |
| 3945–4050 | `App` root component (tab state, context provider, `DeferredMount` wiring) |
| 4050–4145 | `ReactDOM.createRoot` call |

### Key shared patterns

- **`AppContext`** — shared state: `aiProvider`, `activeCampaign`, `campaigns`, `activeTab`, `handoffData`, `resetTool`
- **`useAIGenerate()`** — shared fetch hook for `/api/ai/generate`; reads `aiProvider` from context. Use this for any new AI calls in Lore/Guide tools.
- **`DeferredMount`** — mounts a tool on first tab visit; keeps it mounted (hidden via `display:none`) on tab switch. `resetKey` increment triggers remount (Clear button).
- **AI generate calls in Scene/NPC** — use `system: "You are a JSON API..."` to enforce JSON output; campaign context goes in the prompt body, not the system param.
- **Cross-tool handoff** — `setHandoffData({type, concept, ...})` + `setActiveTab('npc'|'scene'|'combat')` in SessionTool; consumed via `useEffect([handoffData])` in the target tool.

### Editing strategy

1. `grep -n "function TargetTool"` to get the line number.
2. `Read` only the relevant range (tool function + its sub-components).
3. Edit with `Edit` using a unique surrounding context string.
4. Never read the CSS block (lines 1–493) unless editing styles.

## Campaign Data

- Campaign files live in `campaign/<name>/` — never auto-delete these.
- Empty subdirectories are preserved with `.gitkeep` files so the structure survives a fresh clone.
- `campaign/LMoP/` is the live campaign; `campaign/Example/` is the demo; `campaign/templates/` has blank templates.
