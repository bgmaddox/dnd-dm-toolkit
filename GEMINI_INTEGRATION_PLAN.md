# Gemini API Integration & Enhancement Plan

This document outlines the strategy for integrating the Gemini API into the D&D Toolkit and provides suggestions for technical and content enhancements.

## 1. Gemini API Integration

### Backend Changes (`server.py`)
*   **New Dependency**: Add `google-generativeai` to `requirements.txt`.
*   **Configuration**: 
    *   Add `GEMINI_API_KEY` to `.env`.
    *   Initialize the Gemini client in `server.py`.
*   **API Update**:
    *   Modify `GenerateRequest` Pydantic model to include `provider: str = "claude"`.
    *   Update the `/api/ai/generate` endpoint to switch between Anthropic and Google based on the `provider` field.
    *   Use `gemini-1.5-flash` as the default Gemini model for speed and generous free-tier limits (15 RPM).
*   **Free Tier Optimization**:
    *   Implement a simple "cooldown" or retry logic if 429 (Rate Limit) is encountered.
    *   Ensure system prompts are efficiently handled (Gemini 1.5 supports system instructions).

### Shared UI Changes (`tools/tweaks-panel.jsx`)
*   **Provider Toggle**: Add a new tweak control in the `TweaksPanel` for "AI Provider".
    *   Options: `Claude (Haiku)`, `Gemini (Flash)`.
    *   This ensures the toggle is available across NPC Forge, Scene Painter, and Combat Assistant without duplicating code.

### Frontend Tool Updates
*   **Data Passing**: Update `fetch` calls in all HTML tools to include `provider: tweaks.aiProvider` in the request body.
*   **Footer Info**: Update the "Powered by..." info text in each tool to dynamically display the current provider and estimated cost/tier.

---

## 2. Suggested Enhancements

### Technical Enhancements
*   **Direct File Persistence**:
    *   Add a backend endpoint `/api/campaign/save_entity` to save generated NPCs or Scenes directly to the campaign's `.md` files.
    *   Update the "Save to Campaign" button in tools to call this API instead of just updating local state.
*   **Combat State Persistence**:
    *   Allow the Combat Assistant to save the current initiative order and HP status to a JSON file in the campaign folder, enabling session resumes.
*   **Context-Aware Scene Painting**:
    *   Improve Scene Painter by automatically pulling in nearby NPCs or active factions when generating room descriptions.
*   **Gemini 1.5 Pro for "Boss" Content**:
    *   Add a "High Quality" toggle that switches Gemini to `1.5-pro` for more complex or important generations (keeping in mind the lower free-tier limits).

### Content & Feature Enhancements
*   **Concept Randomizer**: Add a "🎲" button next to the Concept input in NPC Forge and Scene Painter to generate random prompts (e.g., "A drunk monk with a secret map").
*   **Loot & Treasure Generator**:
    *   Integrate `magic_items.json` more deeply to allow the AI to suggest appropriate loot based on the NPC or Scene.
*   **Image Generation (Experimental)**:
    *   If using Gemini, explore using Imagen (if available in the tier/region) to generate NPC portraits or scene mood art.
*   **Voice/Tone Guides**:
    *   Add presets for NPC voices (e.g., "Cockney", "Formal", "Whispering") to the forge inputs.

---

## 3. Implementation Steps (Phased)

### Phase 1: Foundation
1. Update `requirements.txt` and `.env`.
2. Implement Gemini support in `server.py`.
3. Add the Provider toggle to `tweaks-panel.jsx`.

### Phase 2: Integration
1. Update NPC Forge to support the toggle and Gemini.
2. Update Scene Painter.
3. Update Combat Assistant (Tactics generation).

### Phase 3: Persistence & Polish
1. Implement the `/api/campaign/save_entity` endpoint.
2. Add "Save to Campaign" functionality to all tools.
3. Add the "Randomizer" and other UI polish.
