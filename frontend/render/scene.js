// frontend/render/scene.js

import { renderChoices } from './choices.js';
import { updateVitals }  from './vitals.js';

let activeYakAudio = null;
const activeTypewriterTimers = new Map(); // to track running animation intervals

// ============================================================
// YAK MOOD
// Upgraded to dynamically prioritize our backend relationship tiers!
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
  const subIdx = state.subTurnIndex ?? 0; // <-- ADDED: Vital for multi-turn dictionary lookups
  
  const loc  = locations[idx] ?? locations[0];
  
  // --------------------------------------------------------
  // FIXED: Nested Multi-Turn Dictionary Traversal
  // Safely extracts the current sub-turn challenge block out of the camp dictionary array.
  // --------------------------------------------------------
  const campScenarios = scenarios[idx] ?? scenarios[0];
  let scen = null;
  
  if (Array.isArray(campScenarios)) {
    scen = campScenarios[subIdx] ?? campScenarios[0];
  } else {
    scen = campScenarios; // Safe fallback container check
  }
  
  if (!loc || !scen) return;

  // Capture the scene class NOW, before any async gap
  const sceneClass = loc.scene || 'scene-manang';

  // Background swap — use CSS transition on opacity via class toggle,
  // no setTimeout so the class is never set from a stale closure
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
  setText('dayBadge',     `Day ${loc.day} · ${loc.name}`);

  // Dynamic placeholders while the network round-trip stream is resolving
  setText('yakText',       'The mountain watches. Tashi is calculating your weight...');
  setText('situationText', `You stand at ${loc.name}. The pressure dial shifts.`);
  setText('factText',      scen.fact || '');

  const moodEl = document.getElementById('yakMood');
  if (moodEl) moodEl.textContent = getYakMood(state);

  // Apply dynamic color modifiers to the background body based on the tension tracker!
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

  // FIX: We only render static file choices if there isn't a live stream running 
  // or if the static scenario explicitly provides them.
  if (scen.choices && scen.choices.length > 0) {
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
// UPDATE NARRATION + AUDIO (UPDATED TO HANDLE DYNAMIC CHOICES)
// ============================================================
export function updateSceneNarration(data, currentGuideTrust = 100) {
  if (!data) return;

  if (data.yak) {
    streamTextTypewriter('yakText', data.yak, 14); 
  }
  if (data.situation) {
    streamTextTypewriter('situationText', data.situation, 8);
  }

  // If the server streams dynamic choices back, render them immediately!
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

// ============================================================
// UPDATE END NARRATION
// ============================================================
export function updateEndNarration(type, text) {
  const id = 'endNarration' + type.charAt(0).toUpperCase() + type.slice(1);
  const el = document.getElementById(id);
  if (el && text) el.textContent = text;
}

// ============================================================
// TRUE STREAMING TYPEWRITER ENGINE
// ============================================================
const textQueues = new Map();     // Holds raw pending string characters
const activeLoops = new Map();    // Tracks interval clocks for each element container

export function streamTextTypewriter(id, targetText, speed = 12) {
  const el = document.getElementById(id);
  if (!el) return;

  // 1. Initialize character queues if this is the first token package of the turn
  if (!textQueues.has(id)) {
    textQueues.set(id, []);
    el.textContent = ''; // Flash-wipe placeholder container text on day turn start
  }

  // 2. Diff incoming state text to find new characters, then push them to the array queue
  const currentTotalText = targetText || '';
  const renderedLength = el.textContent.length + textQueues.get(id).length;
  
  if (currentTotalText.length > renderedLength) {
    const newSlice = currentTotalText.slice(renderedLength);
    textQueues.get(id).push(...newSlice.split(''));
  }

  // 3. Fire up the processing pump cycle if it isn't active
  if (!activeLoops.has(id)) {
    const intervalId = setInterval(() => {
      const queue = textQueues.get(id);
      
      if (queue && queue.length > 0) {
        // Shift a single character off our stack array map and append to layout
        el.textContent += queue.shift();
      } else {
        // Idle condition reached: temporary pause out until next stream frame lands
        clearInterval(intervalId);
        activeLoops.delete(id);
      }
    }, speed);
    
    activeLoops.set(id, intervalId);
  }
}

// ============================================================
// HARD OVERRIDE RESET (For clearing templates safely)
// ============================================================
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) {
    // Force kill active interval loops and clear storage blocks
    if (activeLoops.has(id)) clearInterval(activeLoops.get(id));
    activeLoops.delete(id);
    textQueues.delete(id);
    
    el.textContent = value;
  }
}