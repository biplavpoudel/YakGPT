// frontend/index.js

import { EventBus }                                        from './core/event.js';
import { renderChoices, getSelectedChoiceIndex,
         resetSelectedChoice }                             from './render/choices.js';
import { renderScene, triggerEndscreen,
         updateSceneNarration }                            from './render/scene.js';
import { updateVitals }                                    from './render/vitals.js';
import { addJournalEntry, clearJournal }                   from './render/journal.js';
import { LOCATIONS, SCENARIOS }                            from './data.js';

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
      method:  'POST',
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
  if (s > 65)      { dot?.setAttribute('class','weather-dot storm'); if (label) label.textContent = 'Storm building'; }
  else if (s > 35) { dot?.setAttribute('class','weather-dot warn');  if (label) label.textContent = 'Clouds gathering'; }
  else             { dot?.setAttribute('class','weather-dot clear'); if (label) label.textContent = 'Clear skies'; }
}

// ============================================================
// INVENTORY DOM
// ============================================================
function updateInventoryDOM() {
  const inv = gameState.inventory ?? {};
  ['water','diamox','layers','food'].forEach(item => {
    const qty   = inv[item] ?? 0;
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
  div.className = 'knowledge-item new dynamic';
  div.innerHTML = `
    <div class="knowledge-category">${KNOWLEDGE_CATEGORIES[locIdx] ?? 'Altitude Knowledge'}</div>
    <div class="knowledge-text">${fact}</div>
  `;
  panel.appendChild(div);
  setTimeout(() => div.classList.remove('new'), 2000);
}

// ============================================================
// TAB SWITCHING
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
  document.querySelectorAll('#knowledgePanel .knowledge-item.dynamic').forEach(el => el.remove());
  document.querySelectorAll('.endscreen').forEach(el => el.classList.remove('active'));
  document.getElementById('gameContainer')?.setAttribute('class', 'game-container');
  ['autopsyRows', 'evacRows', 'victoryRows'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '';
  });

  renderScene(gameState, LOCATIONS, SCENARIOS);
  updateVitals(gameState);
  updateTrailFromState(gameState);
  updateWeatherFromState(gameState);
  updateInventoryDOM();
  switchTab('trail');
}

// ============================================================
// END SCREEN DECISION LOG
// ============================================================
const CHOICE_TYPE_LABELS = {
  safe:     { label: 'Safe',     color: '#4caf50' },
  risky:    { label: 'Risky',   color: '#ff9800' },
  reckless: { label: 'Reckless', color: '#f44336' },
};

function renderEndRows(type) {
  const containerId = type === 'death'      ? 'autopsyRows'
                    : type === 'evacuation' ? 'evacRows'
                    : 'victoryRows';

  const container = document.getElementById(containerId);
  if (!container) return;

  const history = gameState.actionHistory ?? [];
  if (history.length === 0) {
    container.innerHTML = '<div style="color:var(--snow-faint);font-size:11px;">No decisions recorded.</div>';
    return;
  }

  container.innerHTML = history.map(entry => {
    const loc     = LOCATIONS[entry.locationIndex] ?? { name: 'Unknown', alt: '' };
    const meta    = CHOICE_TYPE_LABELS[entry.choiceType] ?? { label: entry.choiceType, color: '#888' };
    return `
      <div style="display:flex; gap:10px; align-items:flex-start; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div style="min-width:90px; font-family:var(--font-mono); font-size:9px; color:var(--snow-faint); padding-top:2px;">
          ${loc.name}<br>${loc.alt}
        </div>
        <div style="flex:1; font-size:11px; color:var(--snow-dim);">
          ${entry.choiceText}
        </div>
        <div style="font-family:var(--font-mono); font-size:9px; font-weight:600; color:${meta.color}; white-space:nowrap; padding-top:2px;">
          ${meta.label}
        </div>
      </div>`;
  }).join('');
}

// ============================================================
// EVENT BUS BINDINGS
// ============================================================
function initEventBindings() {
  EventBus.on('state_patch', patch => {
    if (!patch) return;
    gameState = { ...gameState, ...patch };
    // renderScene updates the header (name, alt, day badge, background image,
    // fact text, peer event, choices) whenever location changes.
    // It sets placeholder yak/situation text which the subsequent
    // 'narration' event will immediately overwrite with LLM content.
    renderScene(gameState, LOCATIONS, SCENARIOS);
    updateVitals(gameState);
    updateTrailFromState(gameState);
    updateWeatherFromState(gameState);
  });

  // narration event owns ALL text + audio updates.
  // Route through updateSceneNarration so scene.js manages
  // the audio lifecycle (stop previous, play new).
  EventBus.on('narration', data => {
    if (!data) return;

    // updateSceneNarration handles yak text, situation text, and audio playback
    updateSceneNarration(data);

    // Journal goes to the guide tab
    if (data.journal) addJournalEntry(data.journal);

    // Knowledge log: fact from the location we just left
    const prevIdx = Math.max(0, (gameState.locationIndex ?? 1) - 1);
    const fact    = SCENARIOS[prevIdx]?.fact;
    if (fact) addKnowledgeEntry(prevIdx, fact);
  });

  EventBus.on('choices', choices => {
    if (choices) renderChoices(choices, gameState.guideTrust);
  });

  EventBus.on('end_state', payload => {
    const type = payload?.type ?? payload;
    triggerEndscreen(type);
    renderEndRows(type);
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