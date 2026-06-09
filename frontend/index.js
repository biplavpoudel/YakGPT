// frontend/index.js

import { EventBus }                      from './core/event.js';
import { renderChoices,
         getSelectedChoiceIndex,
         resetSelectedChoice }           from './render/choices.js';
import { renderScene, triggerEndscreen } from './render/scene.js';
import { updateVitals }                  from './render/vitals.js';
import { addJournalEntry, clearJournal } from './render/journal.js';
import { LOCATIONS, SCENARIOS }          from './data.js';

// ============================================================
// GAME STATE
// ============================================================
const INITIAL_STATE = {
  health: 100, acclimatization: 75, energy: 100, guideTrust: 100,
  locationIndex: 0, day: 1, stormPressure: 0,
  inventory: { water: 3, diamox: 2, layers: 1, food: 2 },
  actionHistory: [], acclimatizationDayTaken: false,
  layersUsed: false, backstoryUnlocked: false, endState: null,
};

let gameState = structuredClone(INITIAL_STATE);

// ============================================================
// LOADING
// ============================================================
function setYakLoading(on) {
  document.getElementById('yakThinking')?.classList.toggle('active', on);
  const yt = document.getElementById('yakText');
  if (on && yt) yt.innerHTML =
    '<span class="loading-dots"><span></span><span></span><span></span></span>';
}

function setSituationLoading(on) {
  const el = document.getElementById('situationText');
  if (on && el) el.textContent = 'Reading the mountain...';
}

// ============================================================
// TEXT SETTERS
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
// GAME STEP
// ============================================================
async function takeStep() {
  const idx = getSelectedChoiceIndex();
  if (idx < 0) return;

  const btn = document.getElementById('stepBtn');
  if (!btn) return;
  btn.disabled    = true;
  btn.textContent = 'Processing...';
  setYakLoading(true);
  setSituationLoading(true);

  try {
    const res = await fetch('/play', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: { ...gameState, latest_choice_index: idx } }),
    });
    if (!res.ok) throw new Error(`Backend error: ${res.status}`);

    const reader = res.body.getReader();
    const dec    = new TextDecoder();
    let   buf    = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const parts = buf.split('\n');
      buf = parts.pop() ?? '';
      for (const line of parts) {
        if (!line.trim()) continue;
        let ev;
        try { ev = JSON.parse(line); } catch { continue; }
        if (ev?.type) EventBus.emit(ev.type, ev.payload);
      }
    }
  } catch (err) {
    console.error('[takeStep]', err);
    alert('Game engine failed. Check console.');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Confirm & Continue →';
    resetSelectedChoice();
    setYakLoading(false);
    setSituationLoading(false);
  }
}

// ============================================================
// TRAIL
// ============================================================
function updateTrailFromState(state) {
  LOCATIONS.forEach((_, i) => {
    const dot    = document.getElementById('dot' + i);
    const nameEl = document.getElementById('nodeName' + i);
    const altEl  = document.getElementById('nodeAlt' + i);
    if (!dot) return;

    const done    = i < state.locationIndex;
    const current = i === state.locationIndex;
    const peak    = i === 4;

    dot.className = 'trail-dot ' +
      (done ? 'done' : current ? 'current' : 'locked') +
      (peak ? ' peak' : '');
    dot.innerHTML = peak ? '<span>▲</span>' : done ? '✓' : current ? '★' : '○';

    if (nameEl) nameEl.className = 'trail-node-name' + (current ? ' current' : done ? ' done' : '');
    if (altEl)  altEl.className  = 'trail-node-alt'  + (current ? ' current' : done ? ' done' : '');
  });
}

// ============================================================
// WEATHER
// ============================================================
function updateWeatherFromState(state) {
  const s    = state.stormPressure ?? 0;
  const fill = document.getElementById('stormFill');
  const pct  = document.getElementById('stormPct');
  if (fill) fill.style.width = s + '%';
  if (pct)  pct.textContent  = Math.round(s) + '%';

  document.body.classList.toggle('weather-storm', s > 65);
  document.body.classList.toggle('weather-warn',  s > 35 && s <= 65);

  const dot   = document.getElementById('weatherDot');
  const label = document.getElementById('weatherLabel');
  if (s > 65)      { dot?.setAttribute('class','weather-dot storm'); if(label) label.textContent='Storm building'; }
  else if (s > 35) { dot?.setAttribute('class','weather-dot warn');  if(label) label.textContent='Clouds gathering'; }
  else             { dot?.setAttribute('class','weather-dot clear'); if(label) label.textContent='Clear skies'; }
}

// ============================================================
// INVENTORY DOM
// ============================================================
function updateInventoryDOM() {
  const inv = gameState.inventory ?? {};
  ['water','diamox','layers','food'].forEach(item => {
    const qty = inv[item] ?? 0;
    const qtyEl = document.getElementById('qty-' + item);
    const invEl = document.getElementById('inv-' + item);
    if (qtyEl) qtyEl.textContent = '×' + qty;
    if (invEl) invEl.classList.toggle('depleted', qty <= 0);
  });
}

// ============================================================
// KNOWLEDGE LOG
// ============================================================
const KNOWLEDGE_CATEGORIES = [
  'Altitude Medicine', 'AMS Warning Signs',
  'Weather Strategy',  'HACE Detection', 'Summit Protocol',
];

function addKnowledgeEntry(locIdx, fact) {
  const panel = document.getElementById('knowledgePanel');
  if (!panel || !fact) return;
  const div = document.createElement('div');
  div.className = 'knowledge-item new';
  div.innerHTML = `
    <div class="knowledge-category">${KNOWLEDGE_CATEGORIES[locIdx] ?? 'Altitude Knowledge'}</div>
    <div class="knowledge-text">${fact}</div>
  `;
  panel.appendChild(div);
  setTimeout(() => div.classList.remove('new'), 2000);
}

// ============================================================
// TAB SWITCHING
// HTML: buttons have data-tab="trail|guide|knowledge"
//       panels have id="tab-trail|tab-guide|tab-knowledge"
// ============================================================
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.tab === name)
  );
  document.querySelectorAll('.panel-body').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + name)?.classList.add('active');
}

// ============================================================
// INVENTORY MODAL
// closeInventoryModal receives the click event from the overlay's
// onclick; we only close if the overlay itself was clicked (not
// a child element inside .modal).
// ============================================================
function openInventoryModal() {
  document.getElementById('modalOverlay')?.classList.add('active');
}

function closeInventoryModal(event) {
  if (event.target === document.getElementById('modalOverlay')) {
    document.getElementById('modalOverlay').classList.remove('active');
  }
}

function useItem(item) {
  const inv = gameState.inventory ?? {};
  if (!inv[item] || inv[item] <= 0) return;
  inv[item]--;
  gameState.inventory = inv;

  if (item === 'water')  gameState.energy          = Math.min(100, (gameState.energy          ?? 0) + 10);
  if (item === 'diamox') gameState.acclimatization  = Math.min(100, (gameState.acclimatization  ?? 0) + 15);
  if (item === 'food')   gameState.energy           = Math.min(100, (gameState.energy           ?? 0) + 20);
  if (item === 'layers') gameState.layersUsed = true;

  updateVitals(gameState);
  updateInventoryDOM();
  document.getElementById('modalOverlay')?.classList.remove('active');
}

// ============================================================
// RESTART
// ============================================================
function restartGame() {
  gameState = structuredClone(INITIAL_STATE);
  clearJournal();

  // Remove dynamically added knowledge entries; keep static ones
  document.querySelectorAll('#knowledgePanel .knowledge-item.dynamic')
    .forEach(el => el.remove());

  document.querySelectorAll('.endscreen').forEach(el => el.classList.remove('active'));
  document.getElementById('gameContainer')?.setAttribute('class', 'game-container');

  renderScene(gameState, LOCATIONS, SCENARIOS);
  updateVitals(gameState);
  updateTrailFromState(gameState);
  updateWeatherFromState(gameState);
  updateInventoryDOM();
  switchTab('trail');
}

// ============================================================
// EVENT BUS BINDINGS
// ============================================================
function initEventBindings() {
  EventBus.on('state_patch', patch => {
    if (!patch) return;
    gameState = { ...gameState, ...patch };
    updateVitals(gameState);
    updateTrailFromState(gameState);
    updateWeatherFromState(gameState);
  });

  EventBus.on('narration', data => {
    if (!data) return;
    if (data.yak)       setYakText(data.yak);
    if (data.situation) setSituationText(data.situation);
    if (data.journal)   addJournalEntry(data.journal);

    // Add the fact for the location we just completed
    const prevIdx = Math.max(0, (gameState.locationIndex ?? 1) - 1);
    const fact    = SCENARIOS[prevIdx]?.fact;
    if (fact) addKnowledgeEntry(prevIdx, fact);
  });

  EventBus.on('choices', choices => {
    if (choices) renderChoices(choices, gameState.guideTrust);
  });

  EventBus.on('end_state', payload => {
    triggerEndscreen(payload?.type ?? payload);
  });
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
  updateInventoryDOM();
});