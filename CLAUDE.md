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

## Campaign Data

- Campaign files live in `campaign/<name>/` — never auto-delete these.
- Empty subdirectories are preserved with `.gitkeep` files so the structure survives a fresh clone.
- `campaign/LMoP/` is the live campaign; `campaign/Example/` is the demo; `campaign/templates/` has blank templates.
