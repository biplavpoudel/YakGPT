// ============================================================
// VITALS RENDERER
// ============================================================

// ============================================================
// UPDATE ALL VITALS FROM STATE
// ============================================================
export function updateVitals(state) {
  if (!state) return;

  setVital('Health', state.health);
  setVital('Acclim', state.acclimatization);
  setVital('Energy', state.energy);
  setVital('Trust',  state.guideTrust);

  // Warnings
  toggleWarning('warnHealth', state.health          < 30);
  toggleWarning('warnAcclim', state.acclimatization < 30);
  toggleWarning('warnEnergy', state.energy          < 20);
  toggleWarning('warnTrust',  state.guideTrust      < 50);

  // Trust badge
  updateTrustBadge(state.guideTrust);
}

// ============================================================
// SET SINGLE VITAL BAR
// ============================================================
function setVital(name, val) {
  const el   = document.getElementById('val'  + name);
  const fill = document.getElementById('fill' + name);
  const clamped = Math.max(0, Math.min(100, val ?? 0));
  if (el)   el.textContent   = Math.round(clamped);
  if (fill) fill.style.width = clamped + '%';
}

// ============================================================
// TOGGLE WARNING TEXT
// ============================================================
function toggleWarning(id, show) {
  const el = document.getElementById(id);
  if (el) el.style.display = show ? 'block' : 'none';
}

// ============================================================
// TRUST BADGE
// ============================================================
function updateTrustBadge(guideTrust) {
  const tb = document.getElementById('trustBadge');
  if (!tb) return;

  if (guideTrust >= 70) {
    tb.textContent = 'Trust: High';
    tb.className   = 'trust-badge trust-high';
  } else if (guideTrust >= 40) {
    tb.textContent = 'Trust: Medium';
    tb.className   = 'trust-badge trust-medium';
  } else {
    tb.textContent = 'Trust: Low';
    tb.className   = 'trust-badge trust-low';
  }
}