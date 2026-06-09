// frontend/index.js

// ============================================================
// IMPORTS
// ============================================================
import { EventBus }                          from './core/event.js';
import { renderChoices,
         getSelectedChoiceIndex,
         resetSelectedChoice }               from './render/choices.js';
import { renderScene, triggerEndscreen }     from './render/scene.js';
import { updateVitals }                      from './render/vitals.js';
import { addJournalEntry, clearJournal }     from './render/journal.js';
import { LOCATIONS, SCENARIOS }              from './data.js';

// ============================================================
// GAME STATE
// ============================================================
const INITIAL_STATE = {
  health:          100,
  acclimatization: 75,
  energy:          100,
  guideTrust:      100,
  locationIndex:   0,
  day:             1,
  stormPressure:   0,
  inventory: { water: 3, diamox: 2, layers: 1, food: 2 },
  actionHistory:   [],
  acclimatizationDayTaken: false,
  layersUsed:      false,
  backstoryUnlocked: false,
  endState:        null,
};

let gameState = { ...INITIAL_STATE };

// ============================================================
// LOADING STATES
// ============================================================
function setYakLoading(isLoading) {
  const thinking = document.getElementById('yakThinking');
  const yakText  = document.getElementById('yakText');
  if (!thinking || !yakText) return;

  if (isLoading) {
    thinking.classList.add('active');
    yakText.innerHTML =
      '<span class="loading-dots"><span></span><span></span><span></span></span>';
  } else {
    thinking.classList.remove('active');
  }
}

function setSituationLoading(isLoading) {
  const el = document.getElementById('situationText');
  if (!el) return;
  if (isLoading) el.textContent = 'Reading the mountain...';
}

// ============================================================
// BASIC SETTERS
// ============================================================
function setYakText(text) {
  const el = document.getElementById('yakText');
  if (el) el.textContent = text;
}

function setSituationText(text) {
  const el = document.getElementById('situationText');
  if (el) el.textContent = text;
}

// ============================================================
// MAIN GAME STEP
// ============================================================
async function takeStep() {
  const selectedChoiceIndex = getSelectedChoiceIndex();  // owned by choices.js
  if (selectedChoiceIndex < 0) return;

  const stepBtn = document.getElementById('stepBtn');
  if (!stepBtn) return;

  stepBtn.disabled    = true;
  stepBtn.textContent = 'Processing...';

  setYakLoading(true);
  setSituationLoading(true);

  try {
    const res = await fetch('/play', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        state: {
          ...gameState,
          latest_choice_index: selectedChoiceIndex,
        },
      }),
    });

    if (!res.ok) throw new Error(`Backend error: ${res.status}`);

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let   buffer  = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Backend sends one JSON object per line (NDJSON)
      const parts = buffer.split('\n');
      buffer = parts.pop();  // keep incomplete trailing line

      for (const line of parts) {
        if (!line.trim()) continue;

        let event;
        try {
          event = JSON.parse(line);
        } catch (e) {
          console.error('[SSE] Invalid JSON line:', line);
          continue;
        }

        if (!event?.type) continue;

        EventBus.emit(event.type, event.payload);
      }
    }

  } catch (err) {
    console.error('[takeStep] Error:', err);
    alert('Game engine failed. Check console.');
  } finally {
    stepBtn.disabled    = false;  // re-enable so player can pick next choice
    stepBtn.textContent = 'Confirm & Continue →';
    resetSelectedChoice();        // clears selectedChoiceIndex in choices.js
    setYakLoading(false);
    setSituationLoading(false);
  }
}

// ============================================================
// STATE HELPERS
// ============================================================
function applyStatePatch(patch) {
  if (!patch) return;
  gameState = { ...gameState, ...patch };
}

// ============================================================
// TRAIL UPDATE
// ============================================================
function updateTrailFromState(state) {
  if (!state) return;

  for (let i = 0; i < LOCATIONS.length; i++) {
    const dot = document.getElementById('dot' + i);
    if (!dot) continue;

    const isDone    = i < state.locationIndex;
    const isCurrent = i === state.locationIndex;

    dot.className =
      'trail-dot ' +
      (isDone ? 'done' : isCurrent ? 'current' : 'locked') +
      (i === 4 ? ' peak' : '');
  }
}

// ============================================================
// WEATHER UPDATE
// ============================================================
function updateWeatherFromState(state) {
  if (!state) return;

  const s    = state.stormPressure || 0;
  const fill = document.getElementById('stormFill');
  const pct  = document.getElementById('stormPct');

  if (fill) fill.style.width   = s + '%';
  if (pct)  pct.textContent    = Math.round(s) + '%';

  document.body.classList.toggle('weather-storm', s > 65);
  document.body.classList.toggle('weather-warn',  s > 35 && s <= 65);
}

// ============================================================
// EVENT BINDINGS
// ============================================================
function initEventBindings() {
  // STATE PATCH — update vitals, trail, weather
  EventBus.on('state_patch', (patch) => {
    applyStatePatch(patch);
    updateVitals(gameState);
    updateTrailFromState(gameState);
    updateWeatherFromState(gameState);
  });

  // NARRATION — yak text, situation, journal
  EventBus.on('narration', (data) => {
    if (!data) return;
    if (data.yak)       setYakText(data.yak);
    if (data.situation) setSituationText(data.situation);
    if (data.journal)   addJournalEntry(data.journal);
  });

  // CHOICES — re-render choice buttons
  EventBus.on('choices', (choices) => {
    if (choices) renderChoices(choices, gameState.guideTrust);
  });

  // END STATE — trigger endscreen overlay
  EventBus.on('end_state', (payload) => {
    const type = payload?.type || payload;
    triggerEndscreen(type);
  });
}

// ============================================================
// RESTART
// ============================================================
function restartGame() {
  gameState = { ...INITIAL_STATE };
  clearJournal();
  renderScene(gameState, LOCATIONS, SCENARIOS);
  updateVitals(gameState);
  updateTrailFromState(gameState);
  updateWeatherFromState(gameState);

  // Hide all endscreens
  document.querySelectorAll('[id^="end"]').forEach(el => el.classList.remove('active'));
}

// ============================================================
// INVENTORY MODAL
// ============================================================
function openInventoryModal() {
  document.getElementById('inventoryModal')?.classList.add('active');
}

function closeInventoryModal() {
  document.getElementById('inventoryModal')?.classList.remove('active');
}

function useItem(item) {
  const inv = gameState.inventory || {};
  if (!inv[item] || inv[item] <= 0) return;

  inv[item]--;

  if (item === 'water')  gameState.energy          = Math.min(100, gameState.energy          + 15);
  if (item === 'diamox') gameState.acclimatization  = Math.min(100, gameState.acclimatization + 20);
  if (item === 'food')   gameState.energy            = Math.min(100, gameState.energy          + 10);
  if (item === 'layers') { gameState.layersUsed = true; }

  updateVitals(gameState);
}

// ============================================================
// TAB SWITCHER (journal / inventory panel)
// ============================================================
function switchTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

  document.querySelector(`.tab-btn[data-tab="${tabName}"]`)?.classList.add('active');
  document.getElementById(`tab-${tabName}`)?.classList.add('active');
}

// ============================================================
// EXPOSE TO HTML onclick HANDLERS
// ============================================================
window.takeStep            = takeStep;
window.restartGame         = restartGame;
window.openInventoryModal  = openInventoryModal;
window.closeInventoryModal = closeInventoryModal;
window.useItem             = useItem;
window.switchTab           = switchTab;

// ============================================================
// BOOT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  initEventBindings();
  renderScene(gameState, LOCATIONS, SCENARIOS);
  updateVitals(gameState);
  updateTrailFromState(gameState);
  updateWeatherFromState(gameState);
});