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

### ⚖️ Encounter Helper
A tactical tool for balancing combat on the fly.
- **XP Budgeting:** Add monsters to see the encounter difficulty for your party size.
- **Battlefield Conditions:** Toggle hazards like "Neutral Bystanders" or "Difficult Terrain" to see how they impact the narrative challenge.
- **Action Economy:** Tracks the ratio of party actions vs. monster actions to warn you if an encounter might be a "slugfest" or a "stomp."

### 💰 Loot Calculator
Generate treasure that fits the moment.
- **Thematic Loot:** Select a monster type (Elemental, Aberration, Undead, etc.) to convert gold values into flavor-rich items like *Crystallized elemental cores* or *Corrupted mind-shards*.
- **Hoard Generator:** Quickly roll for CR-appropriate treasure hoards, including magic items filtered by party role.

### 📅 Campaign Calendar
Track the passage of time and weather in your world.
- **Weather Tracking:** Roll for random weather or manually set conditions for any day.
- **Session Notes:** Keep brief notes on what happened each day to ensure your timeline stays consistent.
- **Dynamic Portrayal:** The calendar helps you narrate the changing seasons and environment as the party travels.

### 🎲 Random Tables
Quick-roll tables for those "I search the room" moments.
- **Variety:** Includes tables for Travel Encounters, Dungeon Rooms, City Street Events, Local Rumors, and Random Trinkets.
- **Traps:** Use the "Random Traps" table to instantly generate mechanical or magical hazards for a secure area.

### 🎭 Ambiance Tool
Set the mood with a complete sensory experience.
- **Visual Moods:** The toolkit's background glow shifts colors to match your active mood (e.g., warm amber for Tavern, cold blue for Dungeon).
- **Scene Layers:** Toggle environmental loops like *Rain, Wind, or Fire* independently of the music tracks.
- **✨ Sensory Mood:** Click "Refresh" to get an AI-generated sensory description to help you narrate the environment's smells, sounds, and feel.
- **Soundboard:** A compact SFX grid categorized by Tactical, Utility, and Scene effects.
- **Silence All:** A global emergency mute button to instantly stop all music and SFX.

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
