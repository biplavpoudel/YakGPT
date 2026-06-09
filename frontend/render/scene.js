// frontend/render/scene.js

import { renderChoices } from './choices.js';
import { updateVitals }  from './vitals.js';

// ============================================================
// YAK MOOD
// ============================================================
export function getYakMood(state) {
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
// Called on boot and restart with (state, LOCATIONS, SCENARIOS).
// Does NOT touch journals or knowledge — those come from EventBus.
// ============================================================
export function renderScene(state, locations, scenarios) {
  if (!state || !locations || !scenarios) return;

  const loc  = locations[state.locationIndex]  ?? locations[0];
  const scen = scenarios[state.locationIndex]  ?? scenarios[0];
  if (!loc || !scen) return;

  // Scene background crossfade
  const bg = document.getElementById('sceneBg');
  if (bg) {
    bg.style.opacity = '0';
    setTimeout(() => {
      bg.className     = 'scene-bg ' + (loc.scene || 'scene-manang');
      bg.style.opacity = '1';
    }, 400);
  }

  setText('sceneName',    loc.name);
  setText('sceneAlt',     loc.alt);
  setText('sceneTagline', loc.tagline || '');
  setText('dayBadge',     `Day ${loc.day} · ${loc.name}`);

  // Placeholder text — replaced by LLM narration event when it arrives
  setText('yakText',       'The mountain watches. The yak thinks.');
  setText('situationText', `You stand at ${loc.name}. The air is thin.`);
  setText('factText',      scen.fact || '');

  // Yak mood
  const moodEl = document.getElementById('yakMood');
  if (moodEl) moodEl.textContent = getYakMood(state);

  // Peer pressure event
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

  // Choices
  renderChoices(scen.choices || [], state.guideTrust);

  // Vitals
  updateVitals(state);

  // NOTE: journal entry is NOT added here.
  // Journals are appended only when the 'narration' EventBus event fires
  // (i.e. after a real game step). This prevents duplicate entries on
  // boot and restart.
}

// ============================================================
// UPDATE NARRATION TEXT FROM LLM EVENT
// ============================================================
export function updateSceneNarration(data) {
  if (!data) return;
  if (data.yak)       setText('yakText',       data.yak);
  if (data.situation) setText('situationText', data.situation);
}

// ============================================================
// TRIGGER ENDSCREEN
// type: 'victory' | 'death' | 'evacuation'
// Builds element IDs as: "end" + capitalised(type)
//   → endVictory, endDeath, endEvacuation   (matches HTML)
// ============================================================
export function triggerEndscreen(type, narrationText) {
  const container = document.getElementById('gameContainer');
  if (container) container.className = `game-container end-${type}`;

  const bg = document.getElementById('sceneBg');
  if (bg) {
    bg.style.opacity = '0';
    setTimeout(() => {
      bg.className     = 'scene-bg ' +
        (type === 'victory' ? 'scene-victory' : 'scene-gameover');
      bg.style.opacity = '1';
    }, 400);
  }

  const endings = {
    victory: {
      name:    'Thorong La — 5,416m',
      alt:     '5,416 M',
      tagline: 'The mountain gave its permission. Not everyone gets it.',
      badge:   '🏔 You Survived',
    },
    death: {
      name:    'The Mountain Decides',
      alt:     'GAME OVER',
      tagline: 'The mountain gave its verdict. Quietly. Without drama.',
      badge:   '☠ You Did Not Survive',
    },
    evacuation: {
      name:    'Helicopter Evacuation',
      alt:     'EVACUATED',
      tagline: 'Dorje made the call before you did. That is what guides are for.',
      badge:   '🚁 Rescued',
    },
  };

  const e = endings[type] || endings.death;
  setText('sceneName',    e.name);
  setText('sceneAlt',     e.alt);
  setText('sceneTagline', e.tagline);
  setText('dayBadge',     e.badge);

  // "end" + first-letter-uppercased type → endVictory / endDeath / endEvacuation
  const screenId = 'end' + type.charAt(0).toUpperCase() + type.slice(1);
  document.getElementById(screenId)?.classList.add('active');

  const narrationId = 'endNarration' + type.charAt(0).toUpperCase() + type.slice(1);
  const narrationEl = document.getElementById(narrationId);
  if (narrationEl) narrationEl.textContent = narrationText || '...';
}

// ============================================================
// UPDATE END NARRATION (when LLM event arrives after endscreen shown)
// ============================================================
export function updateEndNarration(type, text) {
  const id = 'endNarration' + type.charAt(0).toUpperCase() + type.slice(1);
  const el = document.getElementById(id);
  if (el && text) el.textContent = text;
}

// ============================================================
// HELPER
// ============================================================
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}