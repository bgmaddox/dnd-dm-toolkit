# DM Toolkit — User Guide

Welcome to your AI-powered DM Toolkit. This suite of tools is designed to help you run faster, more immersive D&D sessions with the help of Claude AI.

---

## 🚀 Getting Started

1. **Unzip the toolkit:** Place the folder somewhere convenient (like your Documents folder).
2. **Launch the app:**
   - **macOS:** Double-click the **DM Toolkit** icon.
   - **Windows:** Double-click `run_toolkit.bat`.
3. **First-Run Setup:**
   - A window will appear asking for your **Anthropic API Key**.
   - If you don't have one, get it at [console.anthropic.com](https://console.anthropic.com/).
   - Once entered, the toolkit will automatically open in your web browser.

---

## 🛠️ The Tools

### 🎭 NPC Forge
Build distinct NPCs in seconds. 
- **Portraits:** Click the portrait to regenerate a new AI image for that NPC.
- **Handoff:** Click "Send to Scene Painter" to instantly start writing a scene featuring that NPC.

### ⚔️ Combat Companion
A live tracker for your encounters.
- **AI Tactics:** Click the "Brain" icon on any monster to get a customized tactical plan based on their abilities.
- **HP Tracking:** Quickly adjust health for a whole group of enemies at once.

### 📜 Session Companion (AI Chat)
Your personal co-DM that knows your world.
- **Campaign Context:** Select your campaign from the dropdown. The AI will read your files in the `campaign/` folder to answer questions about your lore.
- **Session History:** It remembers what happened in previous sessions if you've finalized your notes.

### 🏰 Lore Builder
Create your own campaigns and lore without ever opening a text editor.
- **New Campaign:** Type a name and hit "Create" to scaffold a new world folder.
- **Form-Based Entry:** Fill out fields for NPCs and Locations, and hit "Save" to automatically generate the Markdown files in the right place.
- **Markdown Powered:** Everything you save is stored as a simple `.md` file, so it's easy to back up or edit manually later if you want.

---

## 🌳 Trying the Example Campaign

I've included an example campaign called **"Oakhaven"** to show you how the context search works.

1. Open the **Session Companion**.
2. Select **Example** from the campaign dropdown.
3. Try asking:
   - *"Tell me about the conflict between the Circle of Roots and the Iron Axemen."*
   - *"What does Thistle know about the Elder Oak?"*

---

## 📁 Managing Your Lore

The toolkit reads simple text files (Markdown) from the `campaign/` folder.

- **To start a new campaign:** Create a new folder inside `campaign/` (e.g., `campaign/Strahd/`).
- **Templates:** Use the files in `campaign/templates/` as a guide for your NPCs, locations, and session notes.
### Importing Characters from D&D Beyond

The `scripts/fetch_character.py` script converts a D&D Beyond character sheet into a Markdown file the toolkit can read. D&D Beyond blocks automated fetches, so you first export the JSON via a browser bookmarklet, then run the script.

**Step 1 — Install the bookmarklet (one time)**

1. Right-click your browser bookmarks bar → **Add page** (Chrome) or **Add bookmark** (Firefox/Safari)
2. Name it something like `⬇ DDB Export`
3. Paste the following as the **URL** (the entire line):

```
javascript:(function(){var m=location.pathname.match(/\/characters?\/(\d+)/);if(!m)return alert('Open a D&D Beyond character page first.');fetch('/api/character/v5/character/'+m[1]).then(function(r){return r.json()}).then(function(d){var name=(d.data&&d.data.name?d.data.name:'character').replace(/\s+/g,'_');var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(d)],{type:'application/json'}));a.download=name+'.json';a.click()}).catch(function(e){alert('Error: '+e.message)})})();
```

**Step 2 — Export a character sheet**

1. Open the character's sheet on D&D Beyond (you must be logged in)
2. Click the `⬇ DDB Export` bookmark — a `.json` file downloads automatically

**Step 3 — Import into the toolkit**

```bash
python scripts/fetch_character.py --file ~/Downloads/Aria_Vex.json --campaign LMoP
```

Replace `Aria_Vex.json` with the downloaded filename and `LMoP` with your campaign folder name. The script writes a Markdown file to `campaign/<name>/pcs/` automatically. Repeat whenever a character levels up or changes gear.

---

## 💡 Pro-Tips
- **Portable Mode:** You can move this entire folder to a USB drive and it will work on any computer that has Python installed.
- **API Costs:** Using Claude `haiku` is extremely cheap. A full session of generation usually costs less than $0.05 in API credits.
