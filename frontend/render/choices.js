// ============================================================
// CHOICES RENDERER (RPG 3-Tier Risk Color-Coded)
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

  // Protects the DOM from being overwritten by empty backend payloads
  if (!choices || choices.length === 0) return;

  // Safe to clear and render
  area.innerHTML = '';

  choices.forEach((c, i) => {
    // --------------------------------------------------------
    // EXTRACT RPG RISK TIERS
    // 1. First checks if backend explicitly provided a 'tier' ('safe' | 'risky' | 'reckless')
    // 2. If missing, falls back to position-based indexing (0=safe, 1=risky, 2=reckless)
    // --------------------------------------------------------
    let displayType = c.type;
    
    if (!displayType) {
      if (i === 0) displayType = 'safe';
      else if (i === 1) displayType = 'risky';
      else displayType = 'reckless';
    }

    // Dorje hides the conservative/safe choice if he doesn't respect you
    const trustHidden = guideTrust < 50 && displayType === 'safe';
    const effectiveType = trustHidden ? 'hidden' : displayType;

    const btn = document.createElement('button');
    btn.className = `choice-btn ${effectiveType}`;
    btn.onclick   = () => selectChoice(btn, i);

    // Build the visual RPG tag
    const tag = document.createElement('span');
    tag.className = `choice-tag tag-${effectiveType}`;
    
    if (trustHidden) {
      tag.textContent = '???';
    } else {
      // Human-readable labels matching your design specs
      if (displayType === 'safe') tag.textContent = 'Conservative';
      else if (displayType === 'risky') tag.textContent = 'Calculated';
      else if (displayType === 'reckless') tag.textContent = 'Reckless';
    }

    // Build the immersive consequence subtext
    const conseq = document.createElement('span');
    conseq.className = 'choice-consequence';
    
    conseq.textContent = trustHidden
      ? '(Dorje remains silent. He refuses to guide your judgment.)'
      : (c.consequence || '⚠️ This decision will permanently alter your path metric weights.');

    // Assemble components cleanly
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

// ============================================================
// GET SELECTED CHOICE TEXT
// Extracts the clean decision string for history arrays
// ============================================================
export function getSelectedChoiceText(selectedIndex) {
  if (selectedIndex < 0) return "Proceeding down the trail...";
  
  const buttons = document.querySelectorAll('.choice-btn');
  if (buttons.length > selectedIndex) {
    const btn = buttons[selectedIndex];
    
    const clone = btn.cloneNode(true);
    clone.querySelectorAll('.choice-tag, .choice-consequence').forEach(el => el.remove());
    
    return clone.textContent.trim();
  }
  
  return "Proceeding down the trail...";
}