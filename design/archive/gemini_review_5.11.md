# AI Implementation Plan: Codebase Review & 5.11 Features

**Background & Motivation:**
The user wishes to implement the feature set outlined in `design/implementation_plan_5.11.md` while also addressing any existing bugs or improvements discovered during the codebase review. The goal is to provide a complete, bulletproof set of instructions for an AI agent to execute.

**Scope & Impact:**
- `tools/dm_toolkit.html`: Implementing new features for the `EncounterHelperTool` and `LootCalculatorTool` with minor logic fixes.
- `server.py`: Hardening the GitHub version checking logic.

**Proposed Solution (Implementation Steps):**

### 1. Fix Version Checker (`server.py`)
- **Location:** `check_updates()` function in `server.py`
- **Issue:** The list comprehension `[int(x) for x in VERSION.split(".")]` throws a `ValueError` if the version tag contains strings (e.g., `1.2.0-beta`). It falls back to basic string inequality, which can cause false positives for updates.
- **Fix:** Improve the `try...except` block to use a safer semantic versioning comparison (e.g., stripping non-numeric characters before integer conversion) to ensure the version check behaves correctly across alpha/beta releases.

### 2. Implement Encounter Tool Enhancements (`tools/dm_toolkit.html`)
- **Task E1 (Party Power Level Toggle):** Add state, multipliers, and UI elements. Multiply `partyThresholds` as defined in the original plan.
- **Task E2 (Environmental Hazard Checklist):** Add checkbox states and UI logic as defined in the original plan.
- **Task E3 (Action Economy Gauge - *Enhanced*):**
  - Use the logic outlined in the original plan, but **modify `getMonsterActionCount`** to also count legendary actions. This is crucial for boss encounters.
  - *Code Adjustment:*
    ```javascript
    function getMonsterActionCount(monster) {
      let count = 1;
      if (monster.actions && monster.actions.length > 0) {
        const attacks = monster.actions.filter(a => a.name && !a.name.toLowerCase().includes('multiattack'));
        count = Math.max(attacks.length, 1);
      }
      if (monster.legendary_actions && monster.legendary_actions.length > 0) {
        // Assume each legendary action adds to the action economy pool
        count += monster.legendary_actions.length; 
      }
      return count;
    }
    ```

### 3. Implement Loot Tool Enhancements (`tools/dm_toolkit.html`)
- **Task L1 (Appraisal & Fence Values):** Implement exact UI code from the original plan.
- **Task L2 (Thematic Loot Conversions):** Implement exact states, arrays, and rendering logic from the original plan.
- **Task L3 (Lore & Relic Generator - *Bug Fix*):**
  - **Issue:** Original plan contains a `ReferenceError` typo: `const vessel = pick(RELIC_VESSEL || RELIC_VESSELS.gem);`. `RELIC_VESSEL` is undefined.
  - **Fix:** Update the generator to: `const vessel = pick(RELIC_VESSELS.gem);`
- **Task L4 (Smart Party Filtering):** Implement filtering logic per the original plan.

**Verification & Testing:**
1. Start the server locally and ensure no crashes occur during startup.
2. Navigate to the Encounter tool. Select an "Ancient Red Dragon" and verify that its Legendary Actions are correctly contributing to the Action Economy Gauge.
3. Navigate to the Loot Tool. Click "Generate ✦" in the Relic Generator and ensure no console errors occur regarding `RELIC_VESSEL`.
4. Trigger the version check endpoint (`/api/updates/check`) to ensure it executes without errors.