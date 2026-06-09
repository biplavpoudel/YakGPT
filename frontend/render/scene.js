// ============================================================
// SCENE RENDERER
// ============================================================
import { renderChoices }   from './choices.js';
import { addJournalEntry } from './journal.js';
import { updateVitals }    from './vitals.js';

// ============================================================
// YAK MOOD — derived from state, no global dependency
// ============================================================
export function getYakMood(state) {
  if (state.health          < 30) return "Genuinely concerned";
  if (state.guideTrust      < 40) return "Deeply disappointed";
  if (state.acclimatization < 30) return "Medically alarmed";
  if (state.energy          < 20) return "Pitying";
  if (state.locationIndex  === 4) return "Unexpectedly moved";
  if (state.locationIndex   >= 3) return "Cautiously invested";
  return "Mildly contemptuous";
}

// ============================================================
// RENDER SCENE
// Takes state + data explicitly — no globals
// ============================================================
export function renderScene(state, locations, scenarios) {
  if (!state || !locations || !scenarios) return;

  const loc  = locations[state.locationIndex];
  const scen = scenarios[state.locationIndex];
  if (!loc || !scen) return;

  // Scene header crossfade
  const bg = document.getElementById('sceneBg');
  if (bg) {
    bg.style.opacity = '0';
    setTimeout(() => {
      bg.className     = 'scene-bg ' + (loc.scene || '');
      bg.style.opacity = '1';
    }, 400);
  }

  setText('sceneName',    loc.name);
  setText('sceneAlt',     loc.alt);
  setText('sceneTagline', loc.tagline || '');
  setText('dayBadge',     `Day ${loc.day} · ${loc.name}`);

  // Fallback narration text — replaced by LLM event when it arrives
  // If scen has yak/situation fields (legacy JS data), use them
  // If scen is pure data.py format (no yak/situation), show placeholder
  setText('yakText',       scen.yak      || 'The mountain watches. The yak thinks.');
  setText('situationText', scen.situation || 'You stand at ' + loc.name + '. The air is thin.');
  setText('factText',      scen.fact     || '');

  const moodEl = document.getElementById('yakMood');
  if (moodEl) moodEl.textContent = getYakMood(state);

  // Peer pressure event
  const peerSection = document.getElementById('peerSection');
  if (peerSection) {
    if (scen.peerEvent) {
      peerSection.classList.add('active');
      // peerEvent can be string or { display, llm_context }
      const displayText = typeof scen.peerEvent === 'object'
        ? scen.peerEvent.display
        : scen.peerEvent;
      setText('peerText', displayText);
    } else {
      peerSection.classList.remove('active');
    }
  }

  // Choices — pass guideTrust so safe label hides correctly
  renderChoices(scen.choices || [], state.guideTrust);

  // Vitals
  updateVitals(state);

  // Journal fallback entry
  addJournalEntry(state.locationIndex);
}

// ============================================================
// UPDATE SCENE TEXT FROM LLM EVENT
// Called when narration event arrives from SSE stream
// ============================================================
export function updateSceneNarration(data) {
  if (!data) return;
  if (data.yak)       setText('yakText',       data.yak);
  if (data.situation) setText('situationText', data.situation);
}

// ============================================================
// TRIGGER ENDSCREEN
// ============================================================
export function triggerEndscreen(type, narrationText) {
  // CSS class drives layout — hides panels, expands scene
  const container = document.getElementById('gameContainer');
  if (container) container.className = `game-container end-${type}`;

  // Scene photo crossfade
  const bg = document.getElementById('sceneBg');
  if (bg) {
    bg.style.opacity = '0';
    setTimeout(() => {
      bg.className     = 'scene-bg ' +
        (type === 'victory' ? 'scene-victory' : 'scene-gameover');
      bg.style.opacity = '1';
    }, 400);
  }

  // Scene info per ending
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

  // Show the endscreen
  const screenId = 'end' + type.charAt(0).toUpperCase() + type.slice(1);
  document.getElementById(screenId)?.classList.add('active');

  // Narration text — set immediately if provided, else show ellipsis
  const narrationId = `endNarration${type.charAt(0).toUpperCase() + type.slice(1)}`;
  const narrationEl = document.getElementById(narrationId);
  if (narrationEl) {
    narrationEl.textContent = narrationText || '...';
  }
}

// ============================================================
// UPDATE ENDSCREEN NARRATION
// Called when LLM end narration event arrives
// ============================================================
export function updateEndNarration(type, text) {
  const id = `endNarration${type.charAt(0).toUpperCase() + type.slice(1)}`;
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