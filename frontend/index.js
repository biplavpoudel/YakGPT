// frontend/index.js

import { EventBus }                                    from './core/event.js';
import { renderChoices, getSelectedChoiceIndex,
         resetSelectedChoice, getSelectedChoiceText }   from './render/choices.js';
import { renderScene, triggerEndscreen,
         updateSceneNarration, markStreamAsComplete, 
         resetTypewriter, playYakAudio }                from './render/scene.js';
import { updateVitals }                                from './render/vitals.js';
import { addJournalEntry, clearJournal }               from './render/journal.js';
import { LOCATIONS, SCENARIOS }                        from './data.js';

// ============================================================
// GAME STATE (Synchronized with Python GameState)
// ============================================================
const INITIAL_STATE = {
  health: 100, acclimatization: 75, energy: 100, guideTrust: 100,
  locationIndex: 0, subTurnIndex: 0, day: 1, stormPressure: 0,
  relationshipTier: "Wary Observer",
  tensionModifier: "Low-Stakes / Discomfort",
  shortHistoryLog: [],
  inventory: { water: 3, diamox: 2, layers: 1, food: 2 }, // Matches domain defaults
  actionHistory: [], // Populated on choice confirmation
  acclimatizationDayTaken: false,
  layersUsed: false, backstoryUnlocked: false, endState: null,
};

let gameState = structuredClone(INITIAL_STATE);

// ============================================================
// LOADING
// ============================================================
function setYakLoading(on) {
  document.getElementById('yakThinking')?.classList.toggle('active', on);
  const yt = document.getElementById('yakText');
  if (on && yt) {
    resetTypewriter('yakText'); // Stop active typing loops on processing
    yt.innerHTML = '<span class="loading-dots"><span></span><span></span><span></span></span>';
  }
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

  const choiceText = getSelectedChoiceText(idx) || "Proceeding down the trail...";
  
  // 1. Log the choice locally
  gameState.actionHistory.push({
    locationIndex: gameState.locationIndex,
    subTurnIndex: gameState.subTurnIndex,
    choiceIndex: idx,
    choiceText: choiceText
  });

  const btn = document.getElementById('stepBtn');
  if (!btn) return;
  btn.disabled    = true;
  btn.textContent = 'Processing...';
  setYakLoading(true);
  setSituationLoading(true);

  const targetUrl = `${window.location.origin}/play`;

  try {
    const statePayload = { ...gameState };
    statePayload.latest_choice_index = idx;

    const res = await fetch(targetUrl, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: statePayload }),
    });
    
    if (!res.ok) throw new Error(`Backend server responded with status: ${res.status}`);

    const reader = res.body.getReader();
    const dec    = new TextDecoder();
    let    buf    = '';

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
        if (ev?.type) {
           EventBus.emit(ev.type, ev.payload);
        }
      }
    }

    markStreamAsComplete('yakText');

    // 🌟 THE FIX: Forcefully preserve and commit local modifications to cache
    // This stops state pollution on an immediate page reload/refresh
    sessionStorage.setItem('yak_game_state', JSON.stringify(gameState));

  } catch (err) {
    console.error('[takeStep] Critical connection failure:', err);
    EventBus.emit('error', { message: err.message || "Network request timed out or was terminated by the server host." });
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Confirm & Continue →';
    resetSelectedChoice();
    setYakLoading(false);
    setSituationLoading(false);
  }
}

// ============================================================
// INITIAL NARRATION FETCH
// ============================================================
async function fetchInitialNarration() {
  setYakLoading(true);
  setSituationLoading(true);

  try {

    const statePayload = { ...gameState };
    statePayload.latest_choice_index = -1; // Initializing marker

    const res = await fetch('/play', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: statePayload }), // Properly wrapped mapping
      // body: JSON.stringify({ state: { ...gameState, latest_choice_index: -1 } }),
    });
    if (!res.ok) throw new Error(`Backend error: ${res.status}`);

    const reader = res.body.getReader();
    const dec    = new TextDecoder();
    let    buf    = '';

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

    markStreamAsComplete('yakText');

  } catch (err) {
    console.error('[fetchInitialNarration]', err);
  } finally {
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

  // Evade inserting duplicate fact logs if tab configurations call it repeatedly
  const existingFacts = Array.from(panel.querySelectorAll('.knowledge-text')).map(el => el.textContent);
  if (existingFacts.includes(fact)) return;

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

  if (item === 'water')  gameState.energy = Math.min(100, (gameState.energy ?? 0) + 10);
  if (item === 'diamox') gameState.acclimatization  = Math.min(100, (gameState.acclimatization ?? 0) + 15);
  if (item === 'food')   gameState.energy = Math.min(100, (gameState.energy ?? 0) + 20);
  if (item === 'layers') gameState.layersUsed = true;

  updateVitals(gameState);
  updateInventoryDOM();

  sessionStorage.setItem('yak_game_state', JSON.stringify(gameState));
  document.getElementById('modalOverlay')?.classList.remove('active');
  renderScene(gameState, LOCATIONS, SCENARIOS);
}

// ============================================================
// RESTART
// ============================================================
function restartGame() {
  sessionStorage.removeItem('yak_game_state');
  gameState = structuredClone(INITIAL_STATE);
  clearJournal();

  // Hide the play audio button on restart
  const playBtn = document.getElementById('playAudioBtn');
  if (playBtn) playBtn.style.display = 'none';

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
  fetchInitialNarration();
}

// ============================================================
// END SCREEN DECISION LOG
// ============================================================
const POSITION_TYPE_LABELS = {
  0: { label: 'Deliberate', color: '#4caf50' },
  1: { label: 'Aggressive', color: '#ff9800' }
};

function renderEndRows(type) {
  const containerId = type === 'death'       ? 'autopsyRows'
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
    const loc  = LOCATIONS[entry.locationIndex] ?? { name: 'Unknown', alt: '' };
    const meta = POSITION_TYPE_LABELS[entry.choiceIndex] ?? { label: 'Custom', color: '#f44336' };
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

  EventBus.on('error', (errData) => {
    console.error("🚨 [EventBus] Critical Game Engine Error Caught:", errData);
    const sitText = document.getElementById('situationText');
    if (sitText) {
      sitText.innerHTML = `<span style="color:#ff6b6b; font-weight:bold;">⚠️ Trail pipeline error:</span> ${errData.message || JSON.stringify(errData)}`;
    }
  });

  EventBus.on('state_patch', patch => {
    if (!patch) return;

    // 1. Grab your fresh local choices history BEFORE overwriting the object
    const localHistory = gameState.actionHistory ?? [];
    
    // 2. Safely apply the backend balance changes (vitals, locations, etc.)
    gameState = { ...gameState, ...patch };
    
    // 3. Re-inject the decision logs if the backend omitted or emptied them
    if (!gameState.actionHistory || gameState.actionHistory.length === 0) {
      gameState.actionHistory = localHistory;
    }
    
    // 4. Commit the synchronized bundle to the browser cache
    sessionStorage.setItem('yak_game_state', JSON.stringify(gameState));

    // --- Rest of your UI rendering pipeline remains perfectly untouched ---
    renderScene(gameState, LOCATIONS, SCENARIOS);
    updateVitals(gameState);
    updateTrailFromState(gameState);
    updateWeatherFromState(gameState);
    updateInventoryDOM();

    const currentLocIdx = gameState.locationIndex;
    const currentSubIdx = gameState.subTurnIndex;
    const scenarioList  = SCENARIOS[currentLocIdx];
    
    if (scenarioList && scenarioList[currentSubIdx]) {
      const fact = scenarioList[currentSubIdx].fact;
      if (fact) addKnowledgeEntry(currentLocIdx, fact);
    }
  }); 

  EventBus.on('narration', data => {
    if (!data) return;
    // Persist narration data in session state to avoid LLM regeneration on refresh/resume
    gameState.lastNarration = data;
    sessionStorage.setItem('yak_game_state', JSON.stringify(gameState));

    updateSceneNarration(data, gameState.guideTrust);
    if (data.journal) addJournalEntry(data.journal);

    // Toggle the play audio button visibility based on whether audio exists
    const audioSource = data.audio || data.current_yak_audio;
    const playBtn = document.getElementById('playAudioBtn');
    if (playBtn) {
      playBtn.style.display = audioSource ? 'inline-block' : 'none';
    }
  });

  EventBus.on('choices', choices => {
    if (choices) renderChoices(choices, gameState.guideTrust);
  });

  EventBus.on('end_state', payload => {
    const type = payload?.type ?? payload;
    triggerEndscreen(type);
    renderEndRows(type); 
  });

  EventBus.on('done', () => {});
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
window.replayYakAudio      = () => {
  const audioSource = gameState.lastNarration?.audio || gameState.lastNarration?.current_yak_audio;
  if (audioSource) {
    playYakAudio(audioSource);
  }
};

// ============================================================
// ON BOOT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  initEventBindings();

  const savedState = sessionStorage.getItem('yak_game_state');
  const startBtn = document.getElementById('startTrekBtn');
  const resetBtn = document.getElementById('resetTrekBtn');

  if (savedState) {
    try {
      gameState = JSON.parse(savedState);
      console.log("🏔️ Session data restored from cache framework:", gameState);
      if (startBtn) startBtn.textContent = 'Resume Trek';
      if (resetBtn) resetBtn.style.display = 'inline-block';

      // Restore play audio button visibility if saved audio exists
      if (gameState.lastNarration) {
        const audioSource = gameState.lastNarration.audio || gameState.lastNarration.current_yak_audio;
        const playBtn = document.getElementById('playAudioBtn');
        if (playBtn) {
          playBtn.style.display = audioSource ? 'inline-block' : 'none';
        }
      }
    } catch (e) {
      console.error("Session serialization breakdown, falling back to clean initialization.", e);
      gameState = structuredClone(INITIAL_STATE);
      if (startBtn) startBtn.textContent = 'Start Trek';
      if (resetBtn) resetBtn.style.display = 'none';
    }
  } else {
    gameState = structuredClone(INITIAL_STATE);
    if (startBtn) startBtn.textContent = 'Start Trek';
    if (resetBtn) resetBtn.style.display = 'none';
  }

  // Set dynamic background image on start screen based on current locationIndex
  const startBg = document.getElementById('startBg');
  if (startBg) {
    const locImages = [
      '/scenes/manang.jpg',
      '/scenes/yak-kharkha.jpg',
      '/scenes/thorong-phedi.jpg',
      '/scenes/high-camp.jpg',
      '/scenes/thorong-la.jpg',
      '/scenes/victory.jpg'
    ];
    const imgUrl = locImages[gameState.locationIndex] ?? locImages[0];
    startBg.style.backgroundImage = `url('${imgUrl}')`;
  }

  // Clear stale backend choices before rendering local fallback choices
  delete gameState.current_choices;

  renderScene(gameState, LOCATIONS, SCENARIOS);
  updateVitals(gameState);
  updateTrailFromState(gameState);
  updateWeatherFromState(gameState);
  updateInventoryDOM();

  // Force-render choices from static scenario data for the current position
  const bootScenarios = SCENARIOS[gameState.locationIndex] ?? SCENARIOS[0];
  if (Array.isArray(bootScenarios)) {
    const bootScen = bootScenarios[gameState.subTurnIndex ?? 0] ?? bootScenarios[0];
    if (bootScen?.choices) renderChoices(bootScen.choices, gameState.guideTrust);
  }

  if (startBtn) {
    startBtn.onclick = () => {
      const overlay = document.getElementById('startScreen');
      if (overlay) overlay.classList.add('fade-out');

      console.log("[startBtn.onclick] resuming session? lastNarration:", gameState.lastNarration);

      if (gameState.lastNarration) {
        // Resume session: Restore saved UI content and trigger audio playback
        updateSceneNarration(gameState.lastNarration, gameState.guideTrust);
        markStreamAsComplete('yakText');
        if (gameState.lastNarration.journal) {
          clearJournal();
          addJournalEntry(gameState.lastNarration.journal);
        }
      } else {
        // Fresh session: Fetch narration from backend
        fetchInitialNarration();
      }
    };
  }

  if (resetBtn) {
    resetBtn.onclick = () => {
      const overlay = document.getElementById('startScreen');
      if (overlay) overlay.classList.add('fade-out');

      console.log("[resetBtn.onclick] Starting fresh session (from beginning).");
      restartGame();
    };
  }
});