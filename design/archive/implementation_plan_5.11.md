# Implementation Plan — Encounter & Loot Enhancements (2026-05-11)

> **For AI Agent Use** — All changes target a single file: `tools/dm_toolkit.html`.
> Current component ranges: `EncounterHelperTool` starts ~line 4975, `LootCalculatorTool` starts ~line 5168.
> Verify with: `grep -n "function EncounterHelperTool\|function LootCalculatorTool" tools/dm_toolkit.html`

## Progress Summary

| # | Task | Status |
|---|------|--------|
| E1 | Encounter — Party Power Level toggle | ✅ Done |
| E2 | Encounter — Environmental Hazard checklist | ✅ Done |
| E3 | Encounter — Action Economy Gauge | ✅ Done |
| L1 | Loot — Appraisal & Fence values | ✅ Done |
| L2 | Loot — Thematic Loot Conversions | ✅ Done |
| L3 | Loot — Lore & Relic Generator | ✅ Done |
| L4 | Loot — Smart Party Filtering | ✅ Done |

---

## Conventions (same as prior plans)

- **CSS vars only:** `var(--gold)`, `var(--bg-card)`, `var(--text-muted)`, etc.
- **No new API endpoints** — all features are pure frontend JS.
- **No new files** — everything goes inside `tools/dm_toolkit.html`.
- **Test locally:** `uvicorn server:app --reload` → `http://localhost:8000/tools/dm_toolkit.html#encounter` or `#loot`
- **Deploy after all tasks merged:** `git push && ssh rachett 'bash ~/deploy.sh dnd'`
- **Bump version** to `1.3.0` in `server.py` after deploy, then rebuild dist: `python scripts/package.py`

---

## ENCOUNTER TOOL TASKS

### Task E1 — Party Power Level Toggle

**Component:** `EncounterHelperTool` (~line 4975)
**Where to add:** Left Panel ("Party Setup"), after the Party Level input (~line 5062).

**What it does:** The official XP math assumes standard gear and tactics. This toggle lets the DM nudge the party's effective "budget" upward when the group has heavy magic items or plays optimized builds — preventing routine stomps at "High" difficulty.

**Implementation:**

1. Add state: `const [powerLevel, setPowerLevel] = useState('standard');`

2. Add a constant for the multipliers (place near the top of the component, alongside the existing `inputStyle`/`labelStyle` locals):
```js
const POWER_MULTIPLIERS = { standard: 1.0, 'high-magic': 1.15, optimized: 1.30 };
```

3. In the Left Panel JSX, after the party level input block, add:
```jsx
<div style={{ marginBottom: 18 }}>
  <div style={sectionHead}>Party Power</div>
  {['standard', 'high-magic', 'optimized'].map(lvl => (
    <button key={lvl}
      onClick={() => setPowerLevel(lvl)}
      style={{
        display: 'block', width: '100%', marginBottom: 4, padding: '5px 10px',
        background: powerLevel === lvl ? 'rgba(201,168,76,0.12)' : 'none',
        border: `1px solid ${powerLevel === lvl ? 'var(--gold-dim)' : 'var(--border)'}`,
        color: powerLevel === lvl ? 'var(--gold)' : 'var(--text-muted)',
        borderRadius: 4, cursor: 'pointer', fontSize: '0.95rem', textAlign: 'left',
      }}>
      {lvl === 'standard' ? 'Standard' : lvl === 'high-magic' ? 'High Magic (+15%)' : 'Highly Optimized (+30%)'}
    </button>
  ))}
  {powerLevel !== 'standard' && (
    <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: 4 }}>
      XP budget inflated — you can push past the standard threshold safely.
    </div>
  )}
</div>
```

4. Apply the multiplier to `partyThresholds`. Find the existing `partyThresholds` object (~line 5027) and multiply each value:
```js
const multiplier = POWER_MULTIPLIERS[powerLevel];
const partyThresholds = {
  low:    thresholds.low    * partySize * multiplier,
  mod:    thresholds.mod    * partySize * multiplier,
  high:   thresholds.high   * partySize * multiplier,
  deadly: thresholds.deadly * partySize * multiplier,
};
```

**Acceptance:** Set party to 4 × level 5 (Deadly = 4400 XP normally). Add a Banshee (1100 XP) and a Shadow Demon (700 XP) — total 1800, should show "Low". Switch to "High Magic" → thresholds inflate by 15% → same monsters may show "Low" still but the threshold display updates. Switch to "Highly Optimized" → thresholds inflate 30%. The threshold chips on the left panel update in real time.

---

### Task E2 — Environmental Hazard Checklist

**Component:** `EncounterHelperTool`
**Where to add:** Left Panel, after the XP Thresholds chips (below the threshold display, ~line 5077). Also add an output indicator in the Right Panel.

**What it does:** A fight against the same goblins is vastly harder when they're on a bridge with arrow slits. This checklist doesn't change XP math (it can't — terrain has no XP value), but it adds a visible "Difficulty Bump" badge reminding the DM that the environment is acting as a phantom modifier.

**Implementation:**

1. Add state: `const [hazards, setHazards] = useState([]);`

2. Add constant (near top of component with other locals):
```js
const HAZARD_OPTIONS = [
  "Enemy has High Ground",
  "Difficult Terrain limits melee",
  "Enemies behind significant cover",
  "Environmental Hazards (lava, fire, spells)",
  "Party split / can't regroup",
  "Enemies alerted, not surprised",
];
```

3. Add a toggle handler:
```js
function toggleHazard(h) {
  setHazards(prev => prev.includes(h) ? prev.filter(x => x !== h) : [...prev, h]);
}
```

4. In the Left Panel JSX, after the threshold chips block, add:
```jsx
<div style={{ marginTop: 18 }}>
  <div style={sectionHead}>Battlefield Conditions</div>
  {HAZARD_OPTIONS.map(h => (
    <label key={h} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, cursor: 'pointer', fontSize: '0.95rem', color: hazards.includes(h) ? 'var(--text)' : 'var(--text-muted)' }}>
      <input type="checkbox" checked={hazards.includes(h)} onChange={() => toggleHazard(h)}
        style={{ accentColor: 'var(--gold)', width: 14, height: 14 }} />
      {h}
    </label>
  ))}
</div>
```

5. In the Right Panel, after the existing difficulty readout and before the "Send to Combat" button, add:
```jsx
{hazards.length > 0 && (
  <div style={{ margin: '14px 0', padding: '10px 12px', background: 'rgba(224,140,48,0.10)', border: '1px solid #8a4e10', borderRadius: 6 }}>
    <div style={{ fontSize: '0.95rem', color: '#e08c30', fontWeight: 600, marginBottom: 4 }}>
      ⚠ Battlefield: +{hazards.length} condition{hazards.length > 1 ? 's' : ''}
    </div>
    {hazards.map(h => (
      <div key={h} style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginLeft: 4 }}>· {h}</div>
    ))}
    <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', marginTop: 6 }}>
      Terrain acts as a phantom modifier — treat this encounter as effectively harder than the XP rating suggests.
    </div>
  </div>
)}
```

**Acceptance:** Check "Enemy has High Ground" and "Difficult Terrain" → orange "⚠ Battlefield: +2 conditions" panel appears in the right column listing both conditions. Uncheck them → panel disappears. Checklist and difficulty readout are independent (checking hazards doesn't change the XP math or difficulty label).

---

### Task E3 — Action Economy Gauge

**Component:** `EncounterHelperTool`
**Where to add:** Right Panel, after the existing difficulty readout and Battlefield Conditions (Task E2), before the "Send to Combat" button.

**What it does:** Counts total PC actions (party size × 1) versus total monster actions (number of action entries per monster × count). Warns when the ratio is heavily skewed. A party of 4 vs. a single boss is an action economy mismatch; 4 PCs vs. 20 skeletons is another kind of mismatch.

**Implementation:**

1. Calculate monster actions using the `actions` array in monsters.json. Each monster entry has an `actions` array (may be undefined for some SRD entries). Add a helper that gets the action count for a monster:
```js
function getMonsterActionCount(monster) {
  let count = 1;
  if (monster.actions && monster.actions.length > 0) {
    // Count non-multiattack entries as individual attacks
    const attacks = monster.actions.filter(a =>
      a.name && !a.name.toLowerCase().includes('multiattack')
    );
    count = Math.max(attacks.length, 1);
  }
  // Legendary actions: bosses always get exactly 3 legendary action uses per round
  // regardless of how many options they have, so cap the addition at 3.
  if (monster.legendary_actions && monster.legendary_actions.length > 0) {
    count += 3;
  }
  return count;
}
```

2. Compute totals in the component body (not inside JSX):
```js
const partyActions = partySize;
const monsterActions = encounter.reduce((sum, e) => sum + getMonsterActionCount(e.monster) * e.count, 0);
const actionRatio = monsterActions > 0 ? (partyActions / monsterActions) : null;
```

3. In the Right Panel JSX, after the hazards block (Task E2) and before "Send to Combat":
```jsx
{encounter.length > 0 && actionRatio !== null && (
  <div style={{ marginBottom: 16 }}>
    <div style={sectionHead}>Action Economy</div>
    <div style={{ display: 'flex', gap: 18, marginBottom: 8, fontSize: '1rem' }}>
      <div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Party</div>
        <div style={{ fontWeight: 600 }}>{partyActions} action{partyActions !== 1 ? 's' : ''}</div>
      </div>
      <div style={{ color: 'var(--text-dim)', alignSelf: 'center' }}>vs.</div>
      <div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Monsters</div>
        <div style={{ fontWeight: 600 }}>{monsterActions} action{monsterActions !== 1 ? 's' : ''}</div>
      </div>
    </div>
    {actionRatio >= 2 && (
      <div style={{ fontSize: '0.9rem', color: 'var(--green)', background: 'rgba(90,171,106,0.10)', border: '1px solid #2a5c38', borderRadius: 5, padding: '7px 10px' }}>
        ⚠ Party outnumbers monsters {Math.round(actionRatio)}:1 — consider adding minions or giving the boss Legendary Actions to stay competitive.
      </div>
    )}
    {actionRatio <= 0.5 && (
      <div style={{ fontSize: '0.9rem', color: 'var(--red)', background: 'rgba(196,74,74,0.10)', border: '1px solid #5c2a2a', borderRadius: 5, padding: '7px 10px' }}>
        ⚠ Monsters outnumber the party — high volume can overwhelm even low-CR encounters. Consider using group Initiative for speed.
      </div>
    )}
    {actionRatio > 0.5 && actionRatio < 2 && (
      <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
        Ratio {partyActions}:{monsterActions} — action economy is balanced.
      </div>
    )}
  </div>
)}
```

**Acceptance:** Add 4 Goblins (1 action each) with party size 4 → shows "4 vs. 4 — balanced." Add 4 more Goblins (now 8 total) → shows monster outnumber warning. Remove goblins, add 1 Ancient Dragon (has legendary_actions array) with party of 4 → dragon counts as `n_actions + 3` for legendary slots, so the ratio shifts appropriately (boss gets credit for its legendary economy). Changing party size updates the gauge live.

---

## LOOT TOOL TASKS

### Task L1 — Appraisal & Fence Values

**Component:** `LootCalculatorTool` (~line 5168)
**Where to add:** Center Panel, inside the result block, after the coin rows (~line 5372).

**What it does:** The instant a party finds loot, they ask "where can we sell this?" This pre-calculates the two standard merchant offers so the DM doesn't do arithmetic mid-roleplay.

**Implementation:**

1. Add a GP-equivalent conversion helper (place near `rollDie`/`rollSpec` helpers, ~line 5200):
```js
function totalGpValue(coins) {
  return (coins.cp || 0) * 0.01
       + (coins.sp || 0) * 0.1
       + (coins.ep || 0) * 0.5
       + (coins.gp || 0) * 1
       + (coins.pp || 0) * 10;
}
```

2. In the Center Panel, inside the `result` block (after the coin rows `</div>` around line 5372), add:
```jsx
{(() => {
  const trueGp = totalGpValue(result.coins);
  if (trueGp < 1) return null;
  const merchant = Math.round(trueGp * 0.5);
  const fence = Math.round(trueGp * 0.3);
  return (
    <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
      <div style={{ fontSize: '0.95rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>Trade Values</div>
      <div className="loot-coin-row">
        <span style={{ color: 'var(--text-dim)' }}>Merchant (50%)</span>
        <span style={{ color: 'var(--gold)', fontWeight: 600 }}>{merchant.toLocaleString()} gp</span>
      </div>
      <div className="loot-coin-row">
        <span style={{ color: 'var(--text-dim)' }}>Black Market Fence (30%)</span>
        <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{fence.toLocaleString()} gp</span>
      </div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 4 }}>
        True value: {trueGp.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 1})} gp
      </div>
    </div>
  );
})()}
```

**Note on `loot-coin-row`:** This CSS class is already defined for the coin display rows. Reuse it.

**Acceptance:** Roll individual CR 5–10 loot → coins appear → "Trade Values" section appears below with Merchant and Fence prices. A result with 120 gp should show Merchant: 60 gp, Fence: 36 gp. No magic items only runs → only appears if coins > 0.

---

### Task L2 — Thematic Loot Conversions

**Component:** `LootCalculatorTool`
**Where to add:** Left Panel config (a new "Monster Type" dropdown), plus new rendering logic in the Center Panel.

**What it does:** Converts the raw coin output to flavored, immersion-friendly item descriptions when a non-Humanoid monster type is selected. "45 gp from wolves" becomes "Pristine wolf pelt (20 gp) + Rare gall bladder, alchemy component (25 gp)." Humanoid is the exception — bandits and guards carry actual coin purses, so Humanoid keeps the raw coins and adds flavor items on top (personal effects, trinkets) rather than replacing the coins.

**Implementation:**

1. Add a constant for thematic items near the top of `LootCalculatorTool` (after the existing table constants):
```js
const THEMATIC_LOOT = {
  beast: [
    { name: "Pristine fur pelt",              value: 15 },
    { name: "Polished claws or talons",        value: 10 },
    { name: "Intact tusk or horn",             value: 20 },
    { name: "Rare gall bladder (alchemy use)", value: 25 },
    { name: "Exotic feathers",                 value: 8  },
    { name: "Venom sac (intact)",              value: 30 },
    { name: "Hardened hide section",           value: 12 },
  ],
  undead: [
    { name: "Tarnished silver locket",         value: 15 },
    { name: "Antique coins (mixed, old era)",  value: 20 },
    { name: "Cracked funerary urn",            value: 8  },
    { name: "Blackened bone dust (alchemy)",   value: 12 },
    { name: "Faded noble signet ring",         value: 18 },
    { name: "Ancient burial cloth, intact",    value: 25 },
  ],
  humanoid: [
    { name: "Coin pouch with mixed coins",     value: 20 },
    { name: "Worn leather belt pouch",         value: 5  },
    { name: "Gambling dice and card deck",     value: 3  },
    { name: "Forged travel papers",            value: 15 },
    { name: "Cheap religious medallion",       value: 8  },
    { name: "Guard captain's signet",          value: 22 },
  ],
  dragon: [
    { name: "Dragon scale (damaged)",          value: 40 },
    { name: "Hoarded gold coins (old mint)",   value: 30 },
    { name: "Rough gem fragment",              value: 25 },
    { name: "Melted gold ingot",               value: 35 },
    { name: "Ancient coin, rare origin",       value: 50 },
  ],
  fiend: [
    { name: "Brimstone crystal (magical use)", value: 20 },
    { name: "Cursed trinket (identify first)", value: 15 },
    { name: "Soul coin (one trapped soul)",    value: 100},
    { name: "Hellish ichor vial",              value: 30 },
    { name: "Infernal contract fragment",      value: 18 },
  ],
  construct: [
    { name: "Precision clockwork gear",        value: 12 },
    { name: "Arcane power cell (depleted)",    value: 20 },
    { name: "Mithril linkage segment",         value: 25 },
    { name: "Runed iron plate",                value: 15 },
    { name: "Spell-inscribed gem (cracked)",   value: 30 },
  ],
  fey: [
    { name: "Moondew vial (faerie magic)",     value: 20 },
    { name: "Enchanted acorn trinket",         value: 12 },
    { name: "Dreamstone sliver",               value: 35 },
    { name: "Bottled moonlight (small)",       value: 18 },
    { name: "Faerie blossom, preserved",       value: 10 },
  ],
};
const MONSTER_TYPES = ['none', 'beast', 'undead', 'humanoid', 'dragon', 'fiend', 'construct', 'fey'];
```

2. Add state: `const [monsterType, setMonsterType] = useState('none');`

3. Add a conversion helper:
```js
function convertToThematic(gpValue, type) {
  if (type === 'none' || gpValue < 1) return null;
  const pool = THEMATIC_LOOT[type] || [];
  let remaining = Math.round(gpValue);
  const items = [];
  // Greedily assign items until value is covered
  const shuffled = [...pool].sort(() => Math.random() - 0.5);
  for (const item of shuffled) {
    if (remaining <= 0) break;
    const qty = Math.max(1, Math.round(remaining / item.value));
    const usedQty = Math.min(qty, Math.ceil(remaining / item.value));
    const usedVal = Math.min(usedQty * item.value, remaining);
    items.push({ name: item.name, value: usedVal });
    remaining -= usedVal;
  }
  if (remaining > 0 && items.length > 0) {
    items[items.length - 1].value += remaining; // attach remainder to last item
  }
  return items;
}
```

4. In the Left Panel, add a "Monster Type" selector below the CR Tier block and above the Roll button:
```jsx
<div style={{ marginBottom: 18 }}>
  <div style={{ fontSize: '0.95rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>Monster Type</div>
  <select
    value={monsterType}
    onChange={e => setMonsterType(e.target.value)}
    style={{ width: '100%', background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 4, padding: '5px 8px', fontSize: '0.95rem' }}>
    <option value="none">None (raw coins)</option>
    {MONSTER_TYPES.filter(t => t !== 'none').map(t => (
      <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
    ))}
  </select>
  {monsterType !== 'none' && (
    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 4 }}>
      Gold converted to thematic items
    </div>
  )}
</div>
```

5. In the Center Panel result block, modify the coins section. The behavior differs by type:
- **Humanoid:** show the raw coins as normal, then append themed flavor items below as "Personal Effects"
- **All other types:** replace coins entirely with themed items

Find the coin display block (~line 5360) and replace with:
```jsx
{(() => {
  const isHumanoid = monsterType === 'humanoid';
  const showRawCoins = monsterType === 'none' || isHumanoid;
  const gp = totalGpValue(result.coins);
  const themed = (monsterType !== 'none') ? convertToThematic(gp, monsterType) : null;

  return (
    <div style={{ marginBottom: 16 }}>
      {/* Raw coins — always shown for 'none' or 'humanoid' */}
      {showRawCoins && (
        <>
          {Object.entries(result.coins).map(([coin, val]) =>
            val > 0 ? (
              <div key={coin} className="loot-coin-row">
                <span style={{ color: 'var(--text-dim)' }}>{COIN_LABELS[coin]}</span>
                <span style={{ fontWeight: 600, color: 'var(--gold)' }}>{val.toLocaleString()}</span>
              </div>
            ) : null
          )}
          {Object.values(result.coins).every(v => v === 0) && (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No coins</div>
          )}
        </>
      )}

      {/* Themed items — replaces coins for non-humanoid types; supplements for humanoid */}
      {themed && themed.length > 0 && (
        <div style={{ marginTop: isHumanoid ? 12 : 0, paddingTop: isHumanoid ? 10 : 0, borderTop: isHumanoid ? '1px solid var(--border)' : 'none' }}>
          <div style={{ fontSize: '0.9rem', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: 6 }}>
            {isHumanoid ? 'Personal Effects' : `${monsterType.charAt(0).toUpperCase() + monsterType.slice(1)} Loot`}
          </div>
          {themed.map((item, i) => (
            <div key={i} className="loot-coin-row">
              <span style={{ color: 'var(--text)' }}>{item.name}</span>
              <span style={{ color: isHumanoid ? 'var(--text-muted)' : 'var(--gold)', fontWeight: 600 }}>
                {item.value} gp
              </span>
            </div>
          ))}
          {!isHumanoid && (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: 6 }}>
              True value: ~{Math.round(gp)} gp
            </div>
          )}
        </div>
      )}
    </div>
  );
})()}
```

**Acceptance:**
- Set Monster Type to "Beast," roll → instead of raw coins, see "Beast Loot: Pristine fur pelt (X gp) + Polished claws (Y gp)" with a true value annotation. No coin denominations shown.
- Set Monster Type to "Humanoid," roll → raw coins display normally, then a "Personal Effects" section appears below the coins with flavor items (in muted color, not gold, since they supplement rather than replace).
- Set Monster Type back to "None" → raw coins only, no themed section.
- Copy button still works (update `formatFull` to include themed items if they exist — for humanoid, append the personal effects after the coins).

**Update `formatFull`:** In the `formatFull` function (~line 5261), add a branch: if `monsterType !== 'none'`, build the copy string from themed items instead of coins.

---

### Task L3 — Lore & Relic Generator

> **Bug noted by Gemini review:** The generator code below contains a fixed typo. `RELIC_VESSEL` (undefined) was corrected to `RELIC_VESSELS.gem`. Do not reintroduce `RELIC_VESSEL`.

**Component:** `LootCalculatorTool`
**Where to add:** A new collapsible section at the bottom of the Center Panel (below the Roll Again / Copy buttons), and a standalone "Generate Relic" button.

**What it does:** Instead of "Ruby worth 500gp," the DM gets "A fist-sized, blood-red stone veined with amber, carved in the style of the Old Mage War era. It hums faintly when held." Instant worldbuilding material, no AI needed.

**Implementation:**

1. Add dictionaries near the top of `LootCalculatorTool`:
```js
const RELIC_ERAS = ["the Age of Arcanum","the Old Mage War era","the Collapsed Empire","the Sundering","pre-Sundering antiquity","the First Kingdom period","unknown ancient origin"];
const RELIC_MATERIALS = {
  gem:    ["deep crimson ruby","pale blue sapphire","sea-green emerald","smoky topaz","star-white diamond","ink-black onyx","amber-gold citrine"],
  metal:  ["tarnished silver","aged brass","dark iron","worn bronze","dull mithril","corroded gold"],
  stone:  ["smooth obsidian","speckled granite","carved limestone","polished jade","rough quartz"],
  other:  ["pale ivory","dark mahogany","salt-white bone","petrified heartwood","iridescent shell"],
};
const RELIC_TRAITS = ["slightly warm to the touch","cold despite the ambient heat","faintly luminescent in darkness","vibrates almost imperceptibly","smells of old smoke and copper","leaves a faint metallic taste in the mouth","casts no shadow","feels lighter than it should"];
const RELIC_VESSELS = {
  gem:    ["set in tarnished brass","wrapped in fraying silver wire","mounted on a cracked ivory base","loose, no setting","sealed in amber","fitted in corroded gold filigree"],
  other:  ["wrapped in faded silk","bound with old leather cord","sealed in a lead-lined pouch","tied with a signet ribbon"],
};
const RELIC_TYPES = ["gem","art object","coin","weapon fragment","religious icon","scroll case","signet ring","statuette"];
```

2. Add state: `const [relic, setRelic] = useState(null);`

3. Add a generator function:
```js
function generateRelic() {
  function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
  const type = pick(RELIC_TYPES);
  const isGem = type === 'gem';
  const era = pick(RELIC_ERAS);
  const trait = pick(RELIC_TRAITS);
  // Value: 50–1000 gp (weighted toward lower)
  const valueTiers = [50,100,150,250,500,750,1000];
  const value = pick(valueTiers);
  let desc;
  if (isGem) {
    const mat = pick(RELIC_MATERIALS.gem);
    const vessel = pick(RELIC_VESSELS.gem);  // RELIC_VESSEL was a typo — use RELIC_VESSELS.gem
    desc = `A ${mat} ${vessel}, dating to ${era}. It is ${trait}.`;
  } else if (type === 'art object') {
    const mat = pick([...RELIC_MATERIALS.metal, ...RELIC_MATERIALS.stone, ...RELIC_MATERIALS.other]);
    desc = `A ${mat} figurine from ${era}. It is ${trait}.`;
  } else {
    const mat = pick(RELIC_MATERIALS.other);
    desc = `A ${mat} ${type} from ${era}. It is ${trait}.`;
  }
  setRelic({ type, desc, value });
}
```

4. In the Center Panel, after the Roll Again / Copy button row (~line 5381–5393), add:
```jsx
<div style={{ marginTop: 20, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
    <div style={{ fontSize: '0.95rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Relic / Art Object</div>
    <button
      onClick={generateRelic}
      style={{ padding: '4px 12px', background: 'none', border: '1px solid var(--border)', borderRadius: 4, color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.9rem' }}>
      Generate ✦
    </button>
  </div>
  {relic ? (
    <div style={{ fontSize: '1rem', color: 'var(--text)', lineHeight: 1.6, padding: '10px 12px', background: 'var(--bg-card)', borderRadius: 5, border: '1px solid var(--border)' }}>
      <div style={{ marginBottom: 6 }}>{relic.desc}</div>
      <div style={{ fontSize: '0.9rem', color: 'var(--gold)' }}>Value: {relic.value.toLocaleString()} gp</div>
    </div>
  ) : (
    <div style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>Generate a flavorful art object or gem.</div>
  )}
</div>
```

Note: The Relic Generator is independent of the Roll button — it has its own "Generate ✦" button.

**Acceptance:** Click "Generate ✦" → a descriptive relic appears with a value. Click again → different description and value. The section is always visible in the Center Panel, independent of the Roll result.

---

### Task L4 — Smart Party Filtering

**Component:** `LootCalculatorTool`
**Where to add:** Left Panel, below the Monster Type selector. Activated only in Hoard mode (magic items only roll on Hoard, not Individual — so filtering only matters there).

**What it does:** Rolling a +2 Greataxe for a party of casters and rogues is a letdown. This lets the DM set a party composition so magic item rolls exclude non-viable drops.

**Design decision (Party Filtering):** Rather than per-class proficiency mapping (too granular), use **role-based filtering** — the DM checks which roles the party has. Each role unlocks a category of magic items. An item must match at least one active role to be kept in the pool.

**Implementation:**

1. Add role-to-item-category mapping and tag magic items. Define tags alongside the existing `MAGIC_ITEMS_*` constants:

```js
// Item tags: 'melee' | 'ranged' | 'armor' | 'caster' | 'utility'
const MAGIC_ITEM_TAGS = {
  "Potion of Healing":           ['utility'],
  "Spell Scroll (Cantrip)":      ['caster'],
  "Potion of Climbing":          ['utility'],
  "Spell Scroll (1st level)":    ['caster'],
  "Spell Scroll (2nd level)":    ['caster'],
  "Spell Scroll (3rd level)":    ['caster'],
  "Spell Scroll (4th–6th level)":['caster'],
  "Potion of Greater Healing":   ['utility'],
  "Potion of Superior Healing":  ['utility'],
  "Potion of Supreme Healing":   ['utility'],
  "Bag of Holding":              ['utility'],
  "Driftglobe":                  ['utility'],
  "Cloak of Protection":         ['utility','armor'],
  "Periapt of Health":           ['utility'],
  "Eyes of the Eagle":           ['utility','ranged'],
  "Lantern of Revealing":        ['utility'],
  "Wand of Magic Missiles":      ['caster'],
  "Bracers of Archery":          ['ranged'],
  "Ring of Protection":          ['utility'],
  "Flame Tongue":                ['melee'],
  "Staff of Striking":           ['melee','caster'],
  "Necklace of Fireballs":       ['caster'],
  "Manual of Bodily Health":     ['utility'],
  "Cube of Force":               ['caster','utility'],
  "Wand of the War Mage +2":     ['caster'],
  "Holy Avenger":                ['melee'],
  "Staff of Power":              ['caster'],
  "Manual of Gainful Exercise":  ['utility'],
  "Deck of Many Things":         ['utility'],
  "Ring of Regeneration":        ['utility'],
  "Ioun Stone (Fortitude)":      ['utility'],
  "Iron Golem Manual":           ['utility'],
};

// Role → accepted item categories
const ROLE_CATEGORIES = {
  melee:  ['melee','utility'],
  ranged: ['ranged','utility'],
  caster: ['caster','utility'],
  tank:   ['armor','melee','utility'],
};
const ROLE_OPTIONS = [
  { id: 'melee',  label: 'Melee (Fighter, Barbarian, Paladin)' },
  { id: 'ranged', label: 'Ranged (Ranger, Rogue)' },
  { id: 'caster', label: 'Caster (Wizard, Sorcerer, Warlock, Bard, Cleric)' },
  { id: 'tank',   label: 'Tank / Heavy Armor (Fighter, Paladin)' },
];
```

2. Add state: `const [partyRoles, setPartyRoles] = useState([]);`

3. Add toggle and filter helpers:
```js
function toggleRole(r) {
  setPartyRoles(prev => prev.includes(r) ? prev.filter(x => x !== r) : [...prev, r]);
}
function filterItemForParty(itemName) {
  if (partyRoles.length === 0) return true; // no filter active
  const tags = MAGIC_ITEM_TAGS[itemName] || ['utility'];
  const acceptedCats = new Set(partyRoles.flatMap(r => ROLE_CATEGORIES[r] || []));
  return tags.some(t => acceptedCats.has(t));
}
function filteredPool(pool) {
  return pool.filter(filterItemForParty);
}
```

4. In the Left Panel, after the Monster Type selector, add (visible only when mode === 'hoard'):
```jsx
{mode === 'hoard' && (
  <div style={{ marginBottom: 18 }}>
    <div style={{ fontSize: '0.95rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>Party Roles</div>
    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: 6 }}>Filter magic items to viable drops</div>
    {ROLE_OPTIONS.map(r => (
      <label key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, cursor: 'pointer', fontSize: '0.9rem', color: partyRoles.includes(r.id) ? 'var(--text)' : 'var(--text-muted)' }}>
        <input type="checkbox" checked={partyRoles.includes(r.id)} onChange={() => toggleRole(r.id)}
          style={{ accentColor: 'var(--gold)', width: 14, height: 14 }} />
        {r.label}
      </label>
    ))}
    {partyRoles.length > 0 && (
      <div style={{ fontSize: '0.8rem', color: 'var(--gold-dim)', marginTop: 4 }}>
        Filtering active — magic items matched to party.
      </div>
    )}
  </div>
)}
```

5. In the `roll` function (~line 5224), inside the hoard branch, change `pickRandom(tableArr)` to filter first:
```js
// Original:
magicItems.push(pickRandom(tableArr));
// Replace with:
const viable = filteredPool(tableArr);
const pool = viable.length > 0 ? viable : tableArr; // fallback to unfiltered if no match
magicItems.push(pickRandom(pool));
```

**Acceptance:** Set Hoard mode, CR 5–10. Check only "Caster" → roll a few times → magic items should be spell scrolls, wands, or utility items; never Flame Tongue or Bracers of Archery. Uncheck all → full item table used again. Individual mode → party role section is hidden (filtering doesn't apply).

---

## Implementation Order

Work in this order (simplest to most complex, minimal diff conflicts):

| Step | Task | Why this order |
|------|------|---------------|
| 1 | **L1** — Appraisal & Fence | Add-only in Center Panel; isolated, trivial |
| 2 | **E1** — Power Level toggle | Add-only in Left Panel; simple multiplier |
| 3 | **E2** — Hazard checklist | Add-only in Left Panel + Right Panel; no math changes |
| 4 | **L3** — Relic Generator | New section in Center Panel; fully independent |
| 5 | **E3** — Action Economy Gauge | Right Panel addition; reads existing `encounter` state |
| 6 | **L2** — Thematic Conversions | Modifies existing coin render + adds Left Panel selector |
| 7 | **L4** — Smart Party Filtering | Modifies `roll()` function + adds Left Panel section |

---

## Agent Notes

- **One file:** All changes go in `tools/dm_toolkit.html`. Do not create new files.
- **Grep first:** `grep -n "function LootCalculatorTool\|function EncounterHelperTool" tools/dm_toolkit.html` to confirm current line numbers before editing.
- **CSS vars only:** `var(--gold)`, `var(--bg-card)`, `var(--border)`, etc. Never hardcode hex.
- **No build step:** Components are `<script type="text/babel">`. Edits are live on reload.
- **Test locally:** Reload `http://localhost:8000/tools/dm_toolkit.html#loot` or `#encounter` after each task.
- **No AI calls needed:** All seven features are pure JavaScript — no new `/api/*` endpoints.
- **Version bump:** After all tasks are merged and deployed, bump `server.py` VERSION to `1.3.0` and run `python scripts/package.py`.
