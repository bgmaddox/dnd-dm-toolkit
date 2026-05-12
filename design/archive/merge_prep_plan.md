# Merge Prep Plan: feat-optimizations → feat-packaging → main

**Authored:** 2026-05-06  
**Branch context:** All fixes land on `feat-packaging` before merging to `main`.  
**Source branches reviewed:** `gemini-review`, `feat-optimizations`

---

## Phase 1 — Cherry-pick `feat-optimizations` commits

The two commits on `feat-optimizations` are net-positive and target real gaps. Cherry-pick them onto `feat-packaging`:

```bash
git cherry-pick d3bc99a   # feat: session prep endpoints, flexible PC parsing, portrait cooldowns
git cherry-pick 8fa3f1d   # fix: finalizeSession persistence in prepMode, remove dupe AI toggle
```

**Expected conflict:** `tools/session_companion.html` — the working tree already added a Lore Builder nav link. Keep that addition and accept the prep-mode logic from the cherry-pick. The diff is non-overlapping so resolution should be straightforward.

---

## Phase 2 — Fix blocking I/O in async routes (`server.py`)

Two endpoints block the event loop with synchronous HTTP calls inside `async def` handlers.

**`check_updates`** — uses `requests.get()` with a 2s timeout:

```python
import asyncio
# replace the requests.get call:
response = await asyncio.to_thread(
    requests.get,
    f"https://api.github.com/repos/{repo}/releases/latest",
    timeout=2,
    headers={"Accept": "application/vnd.github.v3+json"}
)
```

**`save_portrait`** — uses `urllib.request.urlopen()` with a 20s timeout. Extract to a helper and thread it:

```python
def _download_portrait(image_url: str, dest_path: Path):
    req = urllib.request.Request(image_url, headers={"User-Agent": "DMToolkit/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        dest_path.write_bytes(resp.read())

# in the route handler:
await asyncio.to_thread(_download_portrait, image_url, portrait_path)
```

No new dependency — `asyncio` is stdlib. Add `import asyncio` to the top-level imports.

---

## Phase 3 — Fix `finalize_session` fallback (`server.py`)

Currently raises HTTP 404 if the DM didn't use the note-append feature during the session. Most DMs will use the chat interface instead, making this endpoint nearly always broken. Fix by falling back to the saved chat history:

```python
@app.post("/api/session/finalize")
async def finalize_session(req: FinalizeRequest):
    camp_dir = CAMPAIGN_BASE / req.campaign
    raw_text = None

    # Try transcript file first (note-append workflow)
    date_str = time.strftime("%Y-%m-%d")
    raw_path = camp_dir / "sessions" / "transcripts" / f"raw_{date_str}.txt"
    if raw_path.exists():
        raw_text = raw_path.read_text()

    # Fallback: reconstruct source material from saved chat history
    if not raw_text:
        chat_path = camp_dir / "sessions" / f"chat_{req.sessionNumber}.json"
        if chat_path.exists():
            history = json.loads(chat_path.read_text())
            raw_text = "\n\n".join(
                f"[{m['role'].upper()}]: {m['content']}" for m in history
            )

    if not raw_text:
        raise HTTPException(status_code=404, detail="No session notes or chat history found")

    # ... rest of the function unchanged
```

---

## Phase 4 — Add prompt caching to `/api/ai/chat` (`server.py`)

**Highest-impact technical optimization.** The campaign context (WORLD.md + FACTIONS.md + PC stats + session summaries) is 2,000–4,000 tokens of static content rebuilt identically on every turn. Without caching, every message in a multi-turn session re-bills the full context. With `cache_control`, only the first message in a session pays for it — estimated 80–90% cost reduction for long sessions.

Replace the plain system prompt string with a structured content block:

```python
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    system=[
        {
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=normalized,
)
```

**Why this works here:** The campaign context is built from disk files and is identical across every turn in a session. The Anthropic cache TTL is 5 minutes — well within a typical DM's message cadence at the table. This is a textbook cache candidate.

**Verification:** After merging, confirm a cache hit by checking `response.usage.cache_read_input_tokens > 0` on the second message of a session. Can be logged server-side temporarily.

---

## Phase 5 — Fix missing `load_dotenv()` call (`server.py`)

`load_dotenv` is imported but only called inside `setup_wizard()`, which only runs when `PORTABLE=1`. On local dev without that flag set, `.env` files are silently ignored and Claude API calls fail.

Add one unconditional call before the PORTABLE check:

```python
load_dotenv()  # always load .env if present; systemd env vars take precedence on Pi

if PORTABLE:
    setup_wizard()
```

The Pi is safe — systemd service env vars are in the environment before Python starts and win over anything in `.env`. Desktop PORTABLE mode runs the wizard which also calls `load_dotenv`. The bare call here is a no-op for both; it just unbreaks local development.

---

## Phase 6 — BM25 index stale-after-write bug (`utils/bm25_index.py`)

The global `_indices` dict caches the BM25 index in-process with no invalidation. When the DM saves a new NPC via the NPC Forge, the in-memory index still reflects the old state until server restart. This is especially relevant on the Pi where the server runs continuously between sessions.

Fix with mtime-based cache busting:

```python
def get_campaign_index(campaign_name: str) -> BM25Index:
    from campaign_loader import CAMPAIGN_DIR
    path = CAMPAIGN_DIR / campaign_name

    cached = _indices.get(campaign_name)
    if cached:
        newest = max(
            (f.stat().st_mtime for folder in ["npcs", "locations"]
             for f in (path / folder).glob("*.md") if (path / folder).exists()),
            default=0
        )
        if newest > cached._built_at:
            del _indices[campaign_name]

    if campaign_name not in _indices:
        index = BM25Index(path)
        index._built_at = time.time()
        _indices[campaign_name] = index
    return _indices[campaign_name]
```

Also add `self._built_at = time.time()` in `BM25Index.__init__`.

---

## Phase 7 — Cleanup artifacts

- **Delete** `design/lastaction.md` — this is Gemini's own operation trace, committed by accident. No project value.
- **Delete** `design/last.md` (currently untracked in working tree) — same artifact type.
- **Add to `.gitignore`:** `design/last*.md` to prevent recurrence.

---

## Phase 8 — Restore `campaign/LMoP/DM_REFERENCE.md` content

The `feat-optimizations` branch added a `campaign/LMoP/DM_REFERENCE.md` with placeholder content that partially overwrote real campaign data:

| Field | Was | Now (needs restoring) |
|---|---|---|
| Important Decisions | "None yet" | "Saved Sildar Hallwinter", "Decided to head to Phandalin before Cragmaw Castle" |
| Session Schedule | "Bi-weekly on Saturdays" | Actual schedule (bi-weekly Tuesdays) |
| Campaign Tone | "with a touch of mystery" | "with moments of mystery" |
| Campaign Themes | "Reclaiming lost history" | "Reclaiming lost legacy" |

Restore from the pre-cherry-pick content or manually correct before committing.

---

## Summary

| # | File(s) | Change | Priority |
|---|---|---|---|
| 1 | — | Cherry-pick 2 commits from `feat-optimizations` | High |
| 2 | `server.py` | `check_updates` + `save_portrait` → `asyncio.to_thread` | High |
| 3 | `server.py` | `finalize_session` chat-history fallback | High |
| 4 | `server.py` | Prompt caching on `/api/ai/chat` system content | High (cost) |
| 5 | `server.py` | Bare `load_dotenv()` before PORTABLE check | Medium |
| 6 | `utils/bm25_index.py` | mtime-based cache invalidation | Medium |
| 7 | `design/lastaction.md`, `design/last.md` | Delete + gitignore `design/last*.md` | Low |
| 8 | `campaign/LMoP/DM_REFERENCE.md` | Restore real campaign data | Low |

**Merge order:** Cherry-pick first (Phase 1), apply all fixes on `feat-packaging`, then open a PR to `main`.
