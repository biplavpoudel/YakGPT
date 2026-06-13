// ============================================================
// CHOICES RENDERER
// ============================================================
import { EventBus } from '../core/event.js';

// selectedChoiceIndex lives here — choices.js owns this state
let selectedChoiceIndex = -1;

export function getSelectedChoiceIndex() {
  return selectedChoiceIndex;
}

export function resetSelectedChoice() {
  selectedChoiceIndex = -1;
  const stepBtn = document.getElementById('stepBtn');
  if (stepBtn) stepBtn.disabled = true;
  document.querySelectorAll('.choice-btn')
    .forEach(b => b.classList.remove('selected'));
}

// ============================================================
// RENDER CHOICES
// guideTrust passed in — no global gameState dependency
// ============================================================
export function renderChoices(choices, guideTrust = 100) {
  const area = document.getElementById('choicesArea');
  if (!area) return;

  // FIX: Do not wipe the DOM if the choices payload is empty or invalid.
  // This protects the buttons rendered by scene.js from being overwritten 
  // by an empty backend stream payload.
  if (!choices || choices.length === 0) return;

  // Now it is safe to clear and render
  area.innerHTML = '';

  choices.forEach((c, i) => {
    // --------------------------------------------------------
    // ADAPTIVE METADATA EXTRACTION
    // Index 0 is systematically treated as the deliberate/safe path.
    // If trust collapses, the guide refuses to point it out.
    // --------------------------------------------------------
    const isSafeIndex   = (i === 0);
    const trustHidden   = guideTrust < 50 && isSafeIndex;
    
    // Aesthetic fallbacks for styling (keeps your CSS rule bindings happy)
    const displayType   = isSafeIndex ? 'safe' : 'risky';
    const effectiveType = trustHidden ? 'hidden' : displayType;

    const btn = document.createElement('button');
    btn.className = `choice-btn ${effectiveType}`;
    btn.onclick   = () => selectChoice(btn, i);

    const tag = document.createElement('span');
    tag.className   = `choice-tag tag-${effectiveType}`;
    
    // Dynamic text masking based on Dorje's active respect for you
    tag.textContent = trustHidden
      ? '???'
      : displayType.charAt(0).toUpperCase() + displayType.slice(1);

    const conseq = document.createElement('span');
    conseq.className   = 'choice-consequence';
    
    // Our new choices don't carry hardcoded 'consequence' strings because
    // the LLM computes the narrative fallout dynamically. 
    // We display a clean immersion prompt instead.
    conseq.textContent = trustHidden
      ? '(Dorje remains silent. He refuses to guide your judgment.)'
      : (c.consequence || '⚠️ This decision will permanently alter your path metric weights.');

    btn.appendChild(tag);
    btn.appendChild(document.createTextNode(' ' + c.text));
    btn.appendChild(conseq);
    area.appendChild(btn);
  });
}

// ============================================================
// CHOICE SELECTION
// ============================================================
function selectChoice(btn, idx) {
  document.querySelectorAll('.choice-btn')
    .forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedChoiceIndex = idx;

  const stepBtn = document.getElementById('stepBtn');
  if (stepBtn) stepBtn.disabled = false;

  // Emit so index.js knows a choice was made
  EventBus.emit('choice_selected', idx);
}