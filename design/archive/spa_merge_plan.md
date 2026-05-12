# SPA Merge Plan: Combine All Tools Into `tools/dm_toolkit.html`

**Authored:** 2026-05-07  
**Goal:** Merge all six individual HTML tools into a single `tools/dm_toolkit.html` React SPA.  
**Old files:** Keep as fallback — do not delete yet.

---

## Background & Motivation

The toolkit currently has six separate HTML files in `tools/`:

| File | Lines | Framework |
|---|---|---|
| `combat_companion.html` | 2,624 | React + Babel |
| `npc_forge.html` | 1,759 | React + Babel |
| `session_companion.html` | 1,124 | **Alpine.js** |
| `lore_builder.html` | 477 | React + Babel |
| `scene_painter.html` | 992 | React + Babel |
| `dm_learning_guide.html` | 1,243 | React + Babel |

Each file:
- Loads React, Babel, and Google Fonts independently (6× redundant CDN fetches)
- Has identical CSS custom property definitions copy-pasted verbatim
- Navigates between tools via full page reload (`<a href="/tools/other.html">`)
- Stores per-tool settings (AI provider, active campaign) in separate localStorage keys
- Calls `/api/campaigns` on every mount independently

Combining into one SPA eliminates all of the above: one CDN load, one CSS block, instant tab switching, one shared settings store, one campaign fetch.

---

## Target Architecture

```
tools/dm_toolkit.html
├── <head>
│   ├── One Google Fonts link (Cinzel + Crimson Pro)
│   ├── React 18.3.1 (development UMD)
│   ├── ReactDOM 18.3.1
│   └── Babel standalone 7.29.0
├── <style>  (merged CSS — single set of design tokens)
├── <script type="text/babel">
│   ├── AppContext  (aiProvider, activeCampaign, campaigns, activeTab, handoffData)
│   ├── TweaksPanel + helpers  (inlined from tweaks-panel.jsx)
│   ├── SessionTool  (rewrite of session_companion — Alpine → React)
│   ├── NPCForgeTool  (from npc_forge.html)
│   ├── ScenePainterTool  (from scene_painter.html)
│   ├── LoreBuilderTool  (from lore_builder.html)
│   ├── CombatTool  (from combat_companion.html)
│   ├── DMGuideTool  (from dm_learning_guide.html)
│   └── App  (header nav + tab switcher + AppContext.Provider)
└── ReactDOM.createRoot(document.getElementById('root')).render(<App />)
```

---

## Step 1 — Create the Shell File

Create `tools/dm_toolkit.html` with:

### 1a. `<head>` block

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>DM Toolkit</title>
<link rel="icon" type="image/png" href="/tools/DnDIcon-Small.png" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&display=swap" rel="stylesheet" />
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y" crossorigin="anonymous"></script>
```

### 1b. `<style>` block

The design tokens are nearly identical across all six files. Merge them into one canonical block:

```css
:root {
  --bg:          #111318;
  --bg-panel:    #16191f;
  --bg-card:     #1c2028;
  --bg-input:    #13161c;
  --border:      #2a2f3d;
  --border-bright: #3a4255;
  --border-glow: #c9a84c55;
  --gold:        #c9a84c;
  --gold-dim:    #9e7c2e;       /* some tools use #8a7035 — pick one */
  --gold-bright: #e8c875;
  --gold-glow:   rgba(201,168,76,0.15);
  --text:        #dde3f0;
  --text-muted:  #8a92a8;
  --text-dim:    #555d72;
  --danger:      #a04040;
  --blue:        #4a78c4;
  --red:         #c44a4a;
  --teal:        #3da894;
  --green:       #5aab6a;
  --serif:       'Cinzel', serif;
  --body:        'Crimson Pro', Georgia, serif;
  --radius:      6px;
  --radius-lg:   12px;
  --shadow-gold: 0 0 24px #c9a84c22, 0 2px 8px #00000080;
  --shadow-card: 0 2px 16px #00000060;
}

/* ... global reset, body, scrollbar, and background texture from any existing tool ... */
```

After the token block, add all global styles that are **truly shared** (body, scrollbars, .btn, .input, etc.). Tool-specific styles that only appear in one tool should be scoped either by a class prefix (`.npc-*`, `.combat-*`) or placed inside the component's inline JSX `style={{}}` props.

**Consolidation rule:** If a CSS class appears in only one tool file, keep it as a scoped class in that tool's section. If it appears in 2+ tools with the same definition, move it to the shared block.

### 1c. `<body>` + root div

```html
<body>
<div id="root"></div>
<script type="text/babel">
const { useState, useEffect, useRef, useCallback, useContext, createContext } = React;
```

---

## Step 2 — Define AppContext

Place this near the top of the `<script type="text/babel">` block, before any tool components:

```jsx
const AppContext = createContext(null);

const APP_SETTINGS_KEY = 'dm_toolkit_settings';

function loadSettings() {
  try {
    return JSON.parse(localStorage.getItem(APP_SETTINGS_KEY)) || {};
  } catch { return {}; }
}
```

The `App` component (Step 8) provides the context. All tools consume it via `useContext(AppContext)`.

**Context shape:**
```js
{
  // Navigation
  activeTab,       // 'session' | 'npc' | 'scene' | 'lore' | 'combat' | 'guide'
  setActiveTab,

  // Shared settings (persisted to localStorage under APP_SETTINGS_KEY)
  aiProvider,      // 'claude' | 'gemini'
  setAiProvider,

  // Campaign (fetched once, shared across all tools)
  campaigns,       // string[]
  activeCampaign,
  setActiveCampaign,

  // Cross-tool handoff (replaces localStorage 'dm_toolkit_handoff')
  handoffData,     // null | { type, concept, location, encounter }
  setHandoffData,
}
```

**Persistence:** `aiProvider` and `activeCampaign` should be saved to localStorage under `APP_SETTINGS_KEY` whenever they change. Read them back on app mount.

---

## Step 3 — Inline TweaksPanel

Copy the full contents of `tools/tweaks-panel.jsx` into the `<script type="text/babel">` block, immediately after the AppContext definition. Remove the final `Object.assign(window, {...})` call — these functions are now locally scoped within the script. All tool components that previously called `useTweaks(TWEAK_DEFAULTS)` will continue to work because the function is defined in the same scope.

**Important:** The `useTweaks` hook in the original file posts to `window.parent` for the Claude Code design tool integration. This is fine to keep as-is — it's a no-op when not running inside the design tool iframe.

---

## Step 4 — Build the App Shell (Nav + Tab Router)

```jsx
const TABS = [
  { id: 'session', label: '📜 Session',    icon: '📜' },
  { id: 'npc',     label: '🎭 NPC Forge',  icon: '🎭' },
  { id: 'scene',   label: '🎨 Scene',      icon: '🎨' },
  { id: 'lore',    label: '🏰 Lore',       icon: '🏰' },
  { id: 'combat',  label: '⚔️ Combat',     icon: '⚔️' },
  { id: 'guide',   label: '📚 Guide',      icon: '📚' },
];

function App() {
  const saved = loadSettings();
  const [activeTab, setActiveTab] = useState(saved.activeTab || 'session');
  const [aiProvider, setAiProvider] = useState(saved.aiProvider || 'claude');
  const [activeCampaign, setActiveCampaign] = useState(saved.activeCampaign || '');
  const [campaigns, setCampaigns] = useState([]);
  const [handoffData, setHandoffData] = useState(null);
  const [resetKeys, setResetKeys] = useState({ session:0, npc:0, scene:0, lore:0, combat:0, guide:0 });
  const resetTool = useCallback((id) => setResetKeys(prev => ({ ...prev, [id]: prev[id] + 1 })), []);

  // Fetch campaigns once at app level
  useEffect(() => {
    fetch('/api/campaigns')
      .then(r => r.json())
      .then(d => {
        const list = d.campaigns || [];
        setCampaigns(list);
        if (!activeCampaign && list.length > 0) setActiveCampaign(list[0]);
      })
      .catch(() => {});
  }, []);

  // Persist settings
  useEffect(() => {
    localStorage.setItem(APP_SETTINGS_KEY, JSON.stringify({ activeTab, aiProvider, activeCampaign }));
  }, [activeTab, aiProvider, activeCampaign]);

  const ctx = { activeTab, setActiveTab, aiProvider, setAiProvider,
                campaigns, activeCampaign, setActiveCampaign,
                handoffData, setHandoffData, resetTool };

  return (
    <AppContext.Provider value={ctx}>
      <div id="app">
        <header className="header">
          <span className="header-logo">DM Toolkit</span>
          <nav className="header-nav">
            {TABS.map(t => (
              <button key={t.id}
                className={`nav-btn${activeTab === t.id ? ' active' : ''}`}
                onClick={() => setActiveTab(t.id)}>
                {t.label}
              </button>
            ))}
          </nav>
          {/* AI provider toggle — visible on all tools */}
          <div className="header-ai-toggle">
            {['claude','gemini'].map(v => (
              <button key={v}
                className={`ai-btn${aiProvider === v ? ' active' : ''}`}
                onClick={() => setAiProvider(v)}>
                {v === 'claude' ? 'Claude' : 'Gemini'}
              </button>
            ))}
          </div>
        </header>

        <main className="tool-area">
          {TABS.map(t => (
            <div key={`${t.id}-${resetKeys[t.id]}`}
                 style={{ display: activeTab === t.id ? 'contents' : 'none' }}>
              {t.id === 'session' && <SessionTool />}
              {t.id === 'npc'     && <NPCForgeTool />}
              {t.id === 'scene'   && <ScenePainterTool />}
              {t.id === 'lore'    && <LoreBuilderTool />}
              {t.id === 'combat'  && <CombatTool />}
              {t.id === 'guide'   && <DMGuideTool />}
            </div>
          ))}
        </main>
      </div>
    </AppContext.Provider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
```

**Tab switching behavior — always-mounted with CSS visibility:**

All six tools are mounted simultaneously at startup and toggled visible/hidden via CSS `display`. This preserves each tool's full React state (in-progress generations, form inputs, chat history, combatant list) when the user switches tabs and back.

```jsx
<main className="tool-area">
  {TABS.map(t => (
    <div key={`${t.id}-${resetKeys[t.id]}`}
         style={{ display: activeTab === t.id ? 'contents' : 'none' }}>
      {t.id === 'session' && <SessionTool />}
      {t.id === 'npc'     && <NPCForgeTool />}
      {t.id === 'scene'   && <ScenePainterTool />}
      {t.id === 'lore'    && <LoreBuilderTool />}
      {t.id === 'combat'  && <CombatTool />}
      {t.id === 'guide'   && <DMGuideTool />}
    </div>
  ))}
</main>
```

Use `display: contents` for the active wrapper (so the tool's own flex/grid layout fills `tool-area` correctly) and `display: none` for inactive ones.

**Per-tool Clear button — useResetKey pattern:**

Since state now persists across tab switches, each tool needs a way to wipe itself back to a blank slate. Add a "Clear" button to each tool's existing header row. Implement via a `resetKeys` counter map in the App component:

```jsx
// In App state:
const [resetKeys, setResetKeys] = useState({ session:0, npc:0, scene:0, lore:0, combat:0, guide:0 });
const resetTool = useCallback((id) => setResetKeys(prev => ({ ...prev, [id]: prev[id] + 1 })), []);
```

The wrapper div key is `${t.id}-${resetKeys[t.id]}`. When `resetTool('npc')` is called, that key changes, React unmounts and remounts just the NPC Forge — all its state is wiped — without touching any other tool.

Add `resetTool` to AppContext so each tool can call it from its own Clear button. Clear button placement: right-aligned in the tool's header row, ghost/secondary style (no gold emphasis). Label: "Clear" with a ↺ prefix.

---

## Step 5 — Migrate Tools (in order of complexity)

### Removing per-tool boilerplate before porting each tool:

Before pasting a tool's JSX into the combined file, strip:
1. The entire `<head>` block (CDN scripts, font links — already in the shell)
2. The outer `<html>`, `<body>` tags and `<div id="root">`
3. The `ReactDOM.createRoot(...).render(...)` call at the bottom
4. The `const { useState, useEffect, ... } = React;` destructure (already at top of script)
5. The `<script type="text/babel" src="/tools/tweaks-panel.jsx">` tag (inlined in Step 3)
6. All CSS inside the tool's own `<style>` block (see CSS handling below)

**CSS handling per tool:**
- Copy each tool's `<style>` content into a scratch document alongside the shared CSS (Step 1b)
- Delete any rule that is already covered by the shared block
- Rename any remaining tool-specific classes with a prefix: `.npc-*`, `.combat-*`, `.scene-*`, `.lore-*`, `.session-*`, `.guide-*`
- Add those prefixed rules to the shared `<style>` block under a comment like `/* ── NPC Forge ── */`

### 5a. DMGuideTool (DM Learning Guide) — Start here

`dm_learning_guide.html` — 1,243 lines, React, no API calls, no campaign dependency.

- Rename the root component from whatever it's called to `DMGuideTool`
- It uses `useTweaks` — this now refers to the inlined version; no change needed
- Remove the nav links in the header (replaced by the App shell nav)
- Expose as a named function: `function DMGuideTool() { ... }`

### 5b. LoreBuilderTool

`lore_builder.html` — 477 lines, React, calls `/api/campaigns` and `/api/ai/generate`.

- Rename root component to `LoreBuilderTool`
- Replace internal `const [activeCampaign, setActiveCampaign] = useState('')` with `const { activeCampaign, setActiveCampaign, campaigns, aiProvider } = useContext(AppContext)`
- Remove the tool's own `fetch('/api/campaigns')` call on mount — campaigns now come from context
- Remove the nav links in the header
- Replace `tweaks.aiProvider` references with `aiProvider` from context
- Remove the per-tool `useTweaks(TWEAK_DEFAULTS)` call and `<TweaksPanel>` usage that contains only the AI provider toggle (it's now in the global header). If the tool has other tweaks beyond the AI provider (e.g., temperature sliders), keep those.

### 5c. ScenePainterTool

`scene_painter.html` — 992 lines, React, calls `/api/ai/generate` and `/api/campaign/*`.

Same steps as 5b, plus:

- **Cross-tool handoff OUT:** Scene Painter has a "Send to NPC Forge" action that currently calls:
  ```js
  localStorage.setItem('dm_toolkit_handoff', JSON.stringify({ type, concept, location, encounter }));
  ```
  Replace with:
  ```js
  const { setHandoffData, setActiveTab } = useContext(AppContext);
  // ...
  setHandoffData({ type, concept, location: concept, encounter: concept });
  setActiveTab('npc');
  ```

### 5d. NPCForgeTool

`npc_forge.html` — 1,759 lines, React, most complex React tool.

Same steps as 5b, plus:

- **Cross-tool handoff IN:** NPC Forge currently reads:
  ```js
  const handoff = localStorage.getItem('dm_toolkit_handoff');
  ```
  Replace with:
  ```js
  const { handoffData, setHandoffData } = useContext(AppContext);
  ```
  In the `useEffect` that previously checked localStorage, check `handoffData` instead. After consuming it, call `setHandoffData(null)` to clear.

- The `localStorage.setItem('npc_forge_campaign', activeCampaign)` per-tool persistence is replaced by the shared `activeCampaign` in AppContext.

### 5e. SessionTool — Alpine → React Rewrite

`session_companion.html` — 1,124 lines. The Alpine component is defined in `Alpine.data('companion', () => ({...}))` starting around line 893.

This is the most involved migration. The Alpine component has these state properties:

```js
// From Alpine companion data object — map to React useState:
view,               // 'splash' | 'live'
campaigns,          // → from AppContext
activeCampaign,     // → from AppContext
sessionNumber,
chatHistory,        // []
message,
loading,
prepMode,           // bool
prepContent,        // string
sessionNotes,       // string
showFinalize,       // bool
showNewCampaign,    // bool
newCampaignName,    // string
```

**Rewrite approach:**
1. Create `function SessionTool() { ... }` using React
2. Map each Alpine property to `useState`
3. Map each Alpine method (sendMessage, finalizeSession, etc.) to regular async functions inside the component
4. Convert Alpine template directives to JSX:
   - `x-if` / `x-show` → conditional rendering
   - `x-for` → `.map()`
   - `x-model` → `value={} onChange={}`
   - `@click` → `onClick={}`
   - `:class` / `:style` → JSX equivalents
5. `campaigns` and `activeCampaign` come from `useContext(AppContext)` — remove Alpine's own fetch
6. The `x-data="companion"` body tag and Alpine CDN script load are removed entirely

**Key Alpine methods to port:**
- `sendMessage()` — fetch('/api/ai/chat', ...) with history management
- `finalizeSession()` — fetch('/api/session/finalize', ...)
- `startPrep()` / `togglePrepMode()` — fetch('/api/session/prep', ...)
- `createCampaign()` — fetch('/api/campaigns', { method: 'POST', ... })
- `loadCampaignData()` — fetch('/api/campaign/context', ...) on activeCampaign change

The Alpine template HTML (lines ~593–892 in session_companion.html) is your JSX blueprint — convert the markup directly. Watch for `x-html` directives (used to render markdown output) — replace with `dangerouslySetInnerHTML={{ __html: marked(content) }}` or a simple pre/code block, same as the original behavior.

**Alpine-specific cleanup:**
- Remove the `<script src="//cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js">` tag
- Remove all `x-data`, `x-show`, `x-if`, `x-model`, `@click`, `:class`, `x-cloak`, `x-init` attributes from the JSX

### 5f. CombatTool

`combat_companion.html` — 2,624 lines, React, the largest and most self-contained tool.

- Rename root component to `CombatTool`
- `aiProvider` from context replaces the internal tweaks setting for AI portrait generation
- Remove the nav links
- Combat Companion has no campaign dependency, so no AppContext campaign wiring needed
- The tool's internal state (combatants, initiative order, etc.) remains fully local — no context needed
- Watch for the `TWEAK_DEFAULTS` block at the top of the script — remove it and replace `tweaks.aiProvider` with `aiProvider` from context. If there are other tweaks (portrait style, etc.), keep those as local state rather than in global context.

---

## Step 5g — Additional Optimizations (implement during the migration, not after)

### OPT-1: Deferred Mounting

**Problem:** With all six tools mounted simultaneously for state persistence, every tool fires its `useEffect` data-loading calls on page load — even tools the user hasn't visited. Combat Companion alone loads `/api/players`, `/api/sessions`, and the large `monsters.json` file at startup. Across all tools, this is 8–10 network requests before the user sees anything.

**Solution:** A `DeferredMount` wrapper that only activates a tool on first visit, then keeps it mounted permanently:

```jsx
function DeferredMount({ active, toolId, resetKey, children }) {
  const [activated, setActivated] = useState(active);
  useEffect(() => { if (active) setActivated(true); }, [active]);
  if (!activated) return null;
  return (
    <div key={resetKey} style={{ display: active ? 'contents' : 'none' }}>
      {children}
    </div>
  );
}
```

Update the `<main>` block in App to use it:

```jsx
<main className="tool-area">
  {TABS.map(t => (
    <DeferredMount key={t.id} active={activeTab === t.id}
                   toolId={t.id} resetKey={resetKeys[t.id]}>
      {t.id === 'session' && <SessionTool />}
      {t.id === 'npc'     && <NPCForgeTool />}
      {t.id === 'scene'   && <ScenePainterTool />}
      {t.id === 'lore'    && <LoreBuilderTool />}
      {t.id === 'combat'  && <CombatTool />}
      {t.id === 'guide'   && <DMGuideTool />}
    </DeferredMount>
  ))}
</main>
```

The initial tab (Session, `activeTab === 'session'` on load) activates immediately. Every other tool only mounts on first click. After that first activation, all are mounted permanently — `display: none` hides them, but React keeps their state alive. The `resetKey` prop on the inner wrapper (not the `DeferredMount` key) handles the Clear button behavior from Step 4.

**Result:** On startup, only Session Companion's data fetches fire. Combat's `monsters.json` and player/session loads are deferred until the user first opens Combat.

### OPT-2: Shared `useAIGenerate` Hook

NPC Forge, Scene Painter, and Lore Builder all duplicate the same pattern:

```js
setLoading(true);
setError(null);
try {
  const res = await fetch('/api/ai/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider: aiProvider, ... })
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  // ... use data
} catch (e) {
  setError(e.message);
} finally {
  setLoading(false);
}
```

Extract this to a shared hook defined near the top of the script, before the tool components:

```jsx
function useAIGenerate() {
  const { aiProvider } = useContext(AppContext);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = useCallback(async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/ai/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: aiProvider, ...payload }),
      });
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch (e) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [aiProvider]);

  return { generate, loading, error, setError };
}
```

Each tool replaces its manual fetch block with:
```js
const { generate, loading, error } = useAIGenerate();
// ...
const data = await generate({ type: 'npc', prompt: '...', campaign: activeCampaign });
if (data) { /* use it */ }
```

This also means the AI provider is always read from context, not from stale local state — fixing a subtle bug where changing the provider mid-session wouldn't take effect until the next render cycle.

### OPT-3: URL Hash Routing

Allow deep-linking to a specific tool via the URL hash (e.g., `/tools/dm_toolkit.html#combat`). Useful for bookmarks and for linking from the USER_GUIDE.

Add to the `App` component's initial state and a `hashchange` listener:

```jsx
// Replace the activeTab useState initialization:
const getTabFromHash = () => {
  const hash = window.location.hash.slice(1); // strip '#'
  return TABS.find(t => t.id === hash) ? hash : (saved.activeTab || 'session');
};
const [activeTab, setActiveTab] = useState(getTabFromHash);

// Sync hash on tab change:
const handleSetActiveTab = useCallback((id) => {
  setActiveTab(id);
  window.location.hash = id;
  localStorage.setItem(APP_SETTINGS_KEY, JSON.stringify({ ...loadSettings(), activeTab: id }));
}, []);

// Listen for browser back/forward:
useEffect(() => {
  const onHashChange = () => {
    const id = window.location.hash.slice(1);
    if (TABS.find(t => t.id === id)) setActiveTab(id);
  };
  window.addEventListener('hashchange', onHashChange);
  return () => window.removeEventListener('hashchange', onHashChange);
}, []);
```

Use `handleSetActiveTab` everywhere instead of `setActiveTab` (pass it as `setActiveTab` in context — callers don't need to know about the hash sync). Browser back/forward buttons now navigate between tool tabs.

### OPT-4: React Error Boundary Per Tool

If one tool throws an unhandled JS error, React will currently unmount the entire app. An error boundary per tool isolates crashes — the broken tool shows an error card, all others keep working.

Define once, near the top of the script:

```jsx
class ToolErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(e) { return { error: e }; }
  render() {
    if (this.state.error) return (
      <div style={{ padding: 32, color: 'var(--text-muted)', fontFamily: 'var(--body)' }}>
        <p style={{ color: 'var(--gold)', fontFamily: 'var(--serif)', marginBottom: 8 }}>
          This tool encountered an error.
        </p>
        <pre style={{ fontSize: 12, opacity: 0.6, whiteSpace: 'pre-wrap' }}>
          {this.state.error.message}
        </pre>
        <button onClick={() => this.setState({ error: null })}
                style={{ marginTop: 16 }}>Try again</button>
      </div>
    );
    return this.props.children;
  }
}
```

Wrap each tool slot inside `DeferredMount`:

```jsx
<DeferredMount ...>
  <ToolErrorBoundary>
    {t.id === 'npc' && <NPCForgeTool />}
    ...
  </ToolErrorBoundary>
</DeferredMount>
```

---

## Step 6 — Update the Global Header CSS

Add to the shared `<style>` block:

```css
/* App shell */
#app { height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

.header { height: 48px; background: var(--bg-panel); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 16px; padding: 0 20px; flex-shrink: 0; }

.header-logo { font-family: var(--serif); font-size: 13px; font-weight: 600;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); white-space: nowrap; }

.header-nav { display: flex; gap: 4px; flex: 1; }

.nav-btn { appearance: none; border: none; background: transparent; color: var(--text-muted);
  font-family: var(--serif); font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; padding: 6px 10px; border-radius: var(--radius); cursor: pointer;
  transition: color 0.15s, background 0.15s; }
.nav-btn:hover { color: var(--text); background: var(--bg-card); }
.nav-btn.active { color: var(--gold); background: var(--bg-card); }

.header-ai-toggle { display: flex; gap: 2px; }
.ai-btn { appearance: none; border: 1px solid var(--border); background: transparent;
  color: var(--text-muted); font-family: var(--body); font-size: 11px;
  padding: 3px 10px; border-radius: var(--radius); cursor: pointer; }
.ai-btn:hover { color: var(--text); }
.ai-btn.active { background: var(--bg-card); color: var(--gold); border-color: var(--gold-dim); }

.tool-area { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
```

---

## Step 7 — Update server.py

Add a route to serve the new combined file:

```python
@app.get("/tools/dm_toolkit.html", response_class=HTMLResponse)
async def dm_toolkit():
    p = TOOLS_DIR / "dm_toolkit.html"
    return HTMLResponse(p.read_text())
```

Optionally, add a root redirect so visiting `/` or the app root goes to the combined file instead of the old entry point. Check how the current root route works and update it accordingly.

---

## Step 8 — Verification Checklist

After building the file, verify each item before committing:

**Navigation:**
- [ ] Clicking each tab shows the correct tool
- [ ] Active tab is highlighted in the nav
- [ ] No page reload occurs when switching tabs
- [ ] Active tab and campaign selection survive a page refresh (loaded from localStorage)
- [ ] Switching away from a tool and back preserves its state (e.g., NPC Forge results, combat tracker)
- [ ] Clear button on each tool wipes only that tool's state (other tools unaffected)
- [ ] DM Learning Guide tab appears and renders content
- [ ] URL hash updates when switching tabs (`#session`, `#combat`, etc.)
- [ ] Navigating directly to `#combat` in the URL opens Combat tab
- [ ] Browser back/forward buttons navigate between tabs

**Performance:**
- [ ] Network tab on startup shows only Session Companion's data fetches; `monsters.json` does NOT load until Combat tab is first opened
- [ ] Changing the AI provider toggle updates the provider used on the next generate call (no stale closure)

**Shared state:**
- [ ] Changing AI provider in the header toggle updates the active tool immediately
- [ ] Selecting a campaign in one tool, then switching to another tool shows the same campaign selected
- [ ] Cross-tool handoff: Scene Painter "Send to NPC" button switches to NPC Forge tab and pre-fills the concept field

**Per-tool functionality (smoke test each):**
- [ ] Session Companion: campaign select, chat sends message, receives AI response
- [ ] NPC Forge: generate NPC, portrait loads, save to campaign
- [ ] Scene Painter: generate scene, copy read-aloud text, "Send to NPC" handoff
- [ ] Lore Builder: generate lore entry, save to campaign
- [ ] Combat Companion: add combatants, roll initiative, apply damage/conditions
- [ ] DM Learning Guide: renders content, no broken layout

**No regressions in old files (fallback still works):**
- [ ] `/tools/npc_forge.html` still loads and functions independently
- [ ] Old localStorage keys (`npc_forge_campaign`, `dm_toolkit_handoff`) are not broken by the new unified key

---

## Step 9 — Post-merge Cleanup (later pass)

These are NOT required for the initial implementation — defer until the SPA is confirmed working:

1. Update `USER_GUIDE.md` to reference `/tools/dm_toolkit.html` as the primary URL
2. Remove the Alpine CDN script from `session_companion.html` (old fallback, not the SPA)
3. Run `python scripts/package.py` to rebuild dist with the new file
4. Bump `VERSION` in `server.py` to `1.2.0` (new feature: unified SPA)
5. Consider whether to eventually delete the six individual tool files

---

## Known Risks & Notes

**`display: contents` browser support** is broad (all modern browsers) but has one quirk: some flexbox/grid children relationships break when the intermediary is `display: contents`. If a tool's layout relies on being a direct flex child of `tool-area`, it may need a small adjustment. Test each tool's scroll behavior after migration and fix any layout regressions with explicit `height: 100%; overflow: hidden` on the tool's own root element.

**Session Companion Alpine rewrite** is the highest-risk task. If you get stuck, an acceptable intermediate step is to keep Alpine loaded alongside React (add the Alpine CDN in the head, keep the Alpine component mostly intact, wrap it in a React component that renders it into a div via a ref). This avoids the rewrite at the cost of loading both frameworks.

**Babel standalone in-browser compilation** is slow for a ~8,000-line script. If load time is noticeably bad (>3s), the solution is to pre-compile the JSX with the Babel CLI into plain JS. This is a future optimization, not a day-1 concern.

**CSS specificity collisions** may occur when all six tools' CSS is in one block. If a style from one tool accidentally applies to another, add a wrapper div with a unique class per tool (`.session-tool`, `.npc-tool`, etc.) and scope the tool-specific rules under that class.

**tweaks-panel.jsx** posts `window.parent.postMessage` — this is safe in a non-iframe context (it just posts to itself and does nothing). No change needed.
