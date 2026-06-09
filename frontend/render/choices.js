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
  area.innerHTML = '';

  if (!choices || choices.length === 0) return;

  choices.forEach((c, i) => {
    const trustHidden   = guideTrust < 50 && c.type === 'safe';
    const effectiveType = trustHidden ? 'hidden' : c.type;

    const btn = document.createElement('button');
    btn.className = `choice-btn ${effectiveType}`;
    btn.onclick   = () => selectChoice(btn, i);

    const tag = document.createElement('span');
    tag.className   = `choice-tag tag-${effectiveType}`;
    tag.textContent = trustHidden
      ? '???'
      : c.type.charAt(0).toUpperCase() + c.type.slice(1);

    const conseq = document.createElement('span');
    conseq.className   = 'choice-consequence';
    conseq.textContent = trustHidden
      ? '(Dorje has stopped labelling your options.)'
      : c.consequence;

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