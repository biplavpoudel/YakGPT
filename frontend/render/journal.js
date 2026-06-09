// ============================================================
// JOURNAL RENDERER
// ============================================================

// Fallback static entries — replaced by LLM narration node
const JOURNAL_FALLBACKS = [
  { day: "Day 1 · Manang · 3,540m",        text: "Day 1 with the new trekker. They seem eager but respectful enough. They actually listened when I pointed out the ice fall on Gangapurna. Maybe this one will be different. I have shown this trail to 200 people. Half tried to argue with the mountain. The mountain always won." },
  { day: "Day 3 · Yak Kharka · 4,050m",    text: "They mentioned the headache. Good. The ones who say nothing are the dangerous ones. I am cautiously optimistic about this trekker's survival instincts." },
  { day: "Day 4 · Thorong Phedi · 4,450m", text: "The German couple turned back this morning. This trekker asks me what I think the weather will do. A good sign — they are listening now." },
  { day: "Day 5 · High Camp · 4,850m",     text: "They did the coordination test without being asked. I did not show it, but I was relieved. There is something about this one that reminds me of the serious trekkers." },
  { day: "Day 6 · Thorong La · 5,416m",    text: "The pass. They made it. I have seen this view 47 times and it still stops me. The mountain gave its permission today. Not everyone gets it." },
];

// ============================================================
// ADD JOURNAL ENTRY
// Called with locIdx (fallback) OR text string (from LLM event)
// ============================================================
export function addJournalEntry(locIdxOrText) {
  const list = document.getElementById('journalEntries');
  if (!list) return;

  const div = document.createElement('div');
  div.className = 'journal-entry new-entry';

  if (typeof locIdxOrText === 'number') {
    // Fallback: use static entry for this location
    const entry = JOURNAL_FALLBACKS[locIdxOrText];
    if (!entry) return;
    div.innerHTML = `<div class="journal-entry-day">${entry.day}</div>${entry.text}`;
  } else if (typeof locIdxOrText === 'string') {
    // LLM-generated: plain text, no day header needed
    // (backend should include day header in the text if wanted)
    div.textContent = locIdxOrText;
  } else if (typeof locIdxOrText === 'object' && locIdxOrText !== null) {
    // Structured: { day, text } from LLM node
    div.innerHTML = `<div class="journal-entry-day">${locIdxOrText.day || ''}</div>${locIdxOrText.text || ''}`;
  }

  list.appendChild(div);
  list.scrollTop = list.scrollHeight;
}

// ============================================================
// REPLACE LAST ENTRY (called when LLM response arrives
// after fallback was already rendered)
// ============================================================
export function replaceLastJournalEntry(text) {
  const list = document.getElementById('journalEntries');
  if (!list) return;
  const last = list.lastElementChild;
  if (!last) return;

  // Preserve the day header if present
  const dayEl = last.querySelector('.journal-entry-day');
  const dayHTML = dayEl ? dayEl.outerHTML : '';
  last.innerHTML = dayHTML + text;
  last.classList.add('new-entry');
}

// ============================================================
// CLEAR JOURNAL (used on restart)
// ============================================================
export function clearJournal() {
  const list = document.getElementById('journalEntries');
  if (list) list.innerHTML = '';
}