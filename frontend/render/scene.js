// frontend/render/scene.js

import { renderChoices } from './choices.js';
import { updateVitals }  from './vitals.js';

let activeYakAudio = null;
const TYPEWRITER_SPEED_MS = 35; // Snappy comedic drawl

// State management for streaming text
const textQueues = new Map();     
const activeLoops = new Map();    
const streamFinished = new Map(); 
const processedLengths = new Map(); // Tracks string slicing offset independently of DOM length

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

// ============================================================
// YAK MOOD
// ============================================================
export function getYakMood(state) {
  const tier = state.relationshipTier;
  
  if (tier && tier.includes("Protective Companion")) return 'Unexpectedly protective';
  if (tier && tier.includes("Resigned Guardian"))    return 'Deeply hostile / Watching your steps';
  
  if (state.health          < 30) return 'Genuinely concerned';
  if (state.guideTrust      < 40) return 'Deeply disappointed';
  if (state.acclimatization < 30) return 'Medically alarmed';
  if (state.energy          < 20) return 'Pitying';
  if (state.locationIndex  === 4) return 'Unexpectedly moved';
  if (state.locationIndex   >= 3) return 'Cautiously invested';
  return 'Mildly contemptuous';
}

// ============================================================
// RENDER SCENE
// ============================================================
export function renderScene(state, locations, scenarios) {
  if (!state || !locations || !scenarios) return;

  const idx    = state.locationIndex ?? 0;
  const subIdx = state.subTurnIndex ?? 0; 
  
  const loc  = locations[idx] ?? locations[0];
  const campScenarios = scenarios[idx] ?? scenarios[0];
  let scen = null;
  
  if (Array.isArray(campScenarios)) {
    scen = campScenarios[subIdx] ?? campScenarios[0];
  } else {
    scen = campScenarios; 
  }
  
  if (!loc || !scen) return;

  const sceneClass = loc.scene || 'scene-manang';

  const bg = document.getElementById('sceneBg');
  if (bg) {
    const current = bg.getAttribute('data-scene');
    if (current !== sceneClass) {
      bg.style.transition = 'opacity 0.4s';
      bg.style.opacity    = '0';
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          bg.className        = 'scene-bg ' + sceneClass;
          bg.setAttribute('data-scene', sceneClass);
          bg.style.opacity    = '1';
        });
      });
    }
  }

  setText('sceneName',    loc.name);
  setText('sceneAlt',     loc.alt);
  setText('sceneTagline', loc.tagline || '');
  
  // enforcing live engine data primacy for days count
  const currentDay = state.day || loc.day || 1;
  setText('dayBadge', `Day ${currentDay} · ${loc.name}`);

  // Dynamic placeholder defaults reset gracefully before streaming
  setText('yakText',       'The mountain watches. Tashi is calculating your weight...');
  setText('situationText', `You stand at ${loc.name}. The pressure dial shifts.`);
  setText('factText',      scen.fact || '');

  const moodEl = document.getElementById('yakMood');
  if (moodEl) moodEl.textContent = getYakMood(state);

  if (state.tensionModifier) {
    const highTension = state.tensionModifier.includes("Suffocating") || state.tensionModifier.includes("Hostile");
    document.body.classList.toggle('stakes-escalated', highTension);
  }

  const peerSection = document.getElementById('peerSection');
  if (peerSection) {
    const hasPeer = !!scen.peerEvent;
    peerSection.classList.toggle('active', hasPeer);
    if (hasPeer) {
      const displayText = typeof scen.peerEvent === 'object'
        ? scen.peerEvent.display
        : scen.peerEvent;
      setText('peerText', displayText);
    }
  }

  // Fallback choices representation if stream choices are absent
  if (scen.choices && scen.choices.length > 0 && (!state.current_choices || state.current_choices.length === 0)) {
    renderChoices(scen.choices, state.guideTrust);
  }

  updateVitals(state);

  const tierDisplay = document.getElementById('relationshipTierDisplay');
  if (tierDisplay && state.relationshipTier) {
    tierDisplay.textContent = state.relationshipTier;
  }

  const tensionDisplay = document.getElementById('weatherStatus');
  if (tensionDisplay && state.tensionModifier) {
    tensionDisplay.textContent = state.tensionModifier;
  }
}

// ============================================================
// UPDATE NARRATION + AUDIO
// ============================================================
export function updateSceneNarration(data, currentGuideTrust = 100) {
  if (!data) return;

  if (data.yak) {
    streamTextTypewriter('yakText', data.yak); 
  }
  if (data.situation) {
    // Environment text instantly updates to maintain responsive atmosphere changes
    setText('situationText', data.situation);
  }

  if (data.choices && data.choices.length > 0) {
    renderChoices(data.choices, currentGuideTrust);
  }

  if (activeYakAudio) {
    activeYakAudio.pause();
    activeYakAudio = null;
  }

  const audioSource = data.audio || data.current_yak_audio;
  if (audioSource) {
    try {
      activeYakAudio = new Audio(audioSource);
      activeYakAudio.play().catch(err => console.warn('[Audio]', err));
    } catch (e) {
      console.error('[Audio init]', e);
    }
  }
}

// ============================================================
// TRUE STREAMING TYPEWRITER ENGINE (PATCHED)
// ============================================================
export function streamTextTypewriter(id, targetText) {
  const el = document.getElementById(id);
  if (!el) return;

  const currentTotalText = targetText || '';

  // 1. Structural initialization on turn change or clean stream
  if (!textQueues.has(id)) {
    textQueues.set(id, []);
    streamFinished.set(id, false);
    processedLengths.set(id, 0);
    el.textContent = ''; 
  }

  // 2. Safely calculate diffs using our standalone processed counter
  const lastProcessedIdx = processedLengths.get(id);
  if (currentTotalText.length > lastProcessedIdx) {
    const freshSlice = currentTotalText.slice(lastProcessedIdx);
    textQueues.get(id).push(...freshSlice.split(''));
    processedLengths.set(id, currentTotalText.length);
  }

  // 3. Execution rendering loop
  if (!activeLoops.has(id)) {
    const intervalId = setInterval(() => {
      const queue = textQueues.get(id);
      
      if (queue && queue.length > 0) {
        el.textContent += queue.shift();
      } else if (streamFinished.get(id) === true) {
        clearInterval(intervalId);
        activeLoops.delete(id);
        textQueues.delete(id);
        streamFinished.delete(id);
        processedLengths.delete(id);
      }
    }, TYPEWRITER_SPEED_MS);
    
    activeLoops.set(id, intervalId);
  }
}

export function markStreamAsComplete(id) {
  if (streamFinished.has(id)) {
    streamFinished.set(id, true);
  }
}

export function resetTypewriter(id) {
  if (activeLoops.has(id)) clearInterval(activeLoops.get(id));
  activeLoops.delete(id);
  textQueues.delete(id);
  streamFinished.delete(id);
  processedLengths.delete(id);
  
  const el = document.getElementById(id);
  if (el) el.textContent = '';
}

// ============================================================
// TRIGGER ENDSCREEN
// ============================================================
export function triggerEndscreen(type, narrationText) {
  const container = document.getElementById('gameContainer');
  if (container) container.className = `game-container end-${type}`;

  const bg = document.getElementById('sceneBg');
  if (bg) {
    const sceneClass = type === 'victory' ? 'scene-victory' : 'scene-gameover';
    bg.style.opacity = '0';
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        bg.className     = 'scene-bg ' + sceneClass;
        bg.setAttribute('data-scene', sceneClass);
        bg.style.opacity = '1';
      });
    });
  }

  const endings = {
    victory:    { name: 'Thorong La — 5,416m',    alt: '5,416 M',  tagline: 'The mountain gave its permission. Not everyone gets it.', badge: '🏔 You Survived' },
    death:      { name: 'The Mountain Decides',    alt: 'GAME OVER', tagline: 'The mountain gave its verdict. Quietly. Without drama.', badge: '☠ You Did Not Survive' },
    evacuation: { name: 'Helicopter Evacuation',   alt: 'EVACUATED', tagline: 'Dorje made the call before you did. That is what guides are for.', badge: '🚁 Rescued' },
  };

  const e = endings[type] || endings.death;
  setText('sceneName',    e.name);
  setText('sceneAlt',     e.alt);
  setText('sceneTagline', e.tagline);
  setText('dayBadge',     e.badge);

  const screenId = 'end' + type.charAt(0).toUpperCase() + type.slice(1);
  document.getElementById(screenId)?.classList.add('active');

  const narrationId = 'endNarration' + type.charAt(0).toUpperCase() + type.slice(1);
  const narEl = document.getElementById(narrationId);
  if (narEl) narEl.textContent = narrationText || '...';
}

export function updateEndNarration(type, text) {
  const id = 'endNarration' + type.charAt(0).toUpperCase() + type.slice(1);
  const el = document.getElementById(id);
  if (el && text) el.textContent = text;
}``