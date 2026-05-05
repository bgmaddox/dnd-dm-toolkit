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

### 🎨 Scene Painter
Generate atmospheric read-aloud descriptions.
- Use the mood sliders to adjust the tone (e.g., more "Grim" or more "Ethereal").

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
- **D&D Beyond:** If you use D&D Beyond, you can use the `fetch_character.py` script (for technical users) to import your players' sheets automatically.

---

## 💡 Pro-Tips
- **Portable Mode:** You can move this entire folder to a USB drive and it will work on any computer that has Python installed.
- **API Costs:** Using Claude `haiku` is extremely cheap. A full session of generation usually costs less than $0.05 in API credits.
