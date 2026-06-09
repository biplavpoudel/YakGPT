// frontend/data.js
// Mirror of backend/graph/data.py — keep in sync manually or generate from API.

// ============================================================
// LOCATIONS
// ============================================================
export const LOCATIONS = [
  { name: "Manang",          alt: "3,540 m", altNum: 3540, day: 1 },
  { name: "Yak Kharka",      alt: "4,050 m", altNum: 4050, day: 3 },
  { name: "Thorong Phedi",   alt: "4,450 m", altNum: 4450, day: 4 },
  { name: "High Camp",       alt: "4,850 m", altNum: 4850, day: 5 },
  { name: "Thorong La Pass", alt: "5,416 m", altNum: 5416, day: 6 },
];

// ============================================================
// SCENARIOS
// ============================================================
export const SCENARIOS = [
  {
    id: "manang_acclimatization",
    fact: "Acclimatization at Manang is critical to prevent Acute Mountain Sickness.",
    peerEvent: null,
    choices: [
      { type: "safe",     text: "Take an acclimatization hike and sleep at Manang.",   consequence: "Improves adaptation to altitude." },
      { type: "risky",    text: "Push directly to Yak Kharka.",                        consequence: "Reduced acclimatization increases risk." },
      { type: "reckless", text: "Skip ahead to Thorong Phedi in one push.",            consequence: "Severe altitude stress likely." },
    ],
  },
  {
    id: "yak_kharka_symptoms",
    fact: "Headache above 3000m is a primary symptom of AMS.",
    peerEvent: "A fellow trekker is showing early nausea symptoms.",
    choices: [
      { type: "safe",     text: "Report symptoms to Dorje and rest.",       consequence: "Proper rest improves recovery." },
      { type: "risky",    text: "Take medication and hide symptoms.",        consequence: "Symptoms masked but risk remains." },
      { type: "reckless", text: "Ignore symptoms and continue ascent.",      consequence: "High risk of altitude complications." },
    ],
  },
  {
    id: "thorong_phedi_preparation",
    fact: "Early morning starts reduce storm exposure risk at Thorong La.",
    peerEvent: "Experienced trekkers prepare gear quietly before dawn.",
    choices: [
      { type: "safe",     text: "Sleep early and start at 3am with guide.", consequence: "Optimal weather window usage." },
      { type: "risky",    text: "Start at 5am like most groups.",           consequence: "Narrower weather margin." },
      { type: "reckless", text: "Leave immediately despite conditions.",     consequence: "High exposure to unstable weather." },
    ],
  },
  {
    id: "high_camp_coordination",
    fact: "Loss of coordination may indicate early HACE.",
    peerEvent: null,
    choices: [
      { type: "safe",     text: "Perform coordination test and follow guide pace.", consequence: "Early detection reduces risk." },
      { type: "risky",    text: "Skip self-check and proceed normally.",            consequence: "Hidden risk may escalate." },
      { type: "reckless", text: "Rush ahead to stay warm.",                         consequence: "Severe energy depletion." },
    ],
  },
  {
    id: "thorong_la_summit",
    fact: "Thorong La is the highest and most exposed point of the circuit.",
    peerEvent: null,
    choices: [
      { type: "safe",     text: "Brief summit stop and immediate descent.", consequence: "Correct high-altitude behavior." },
      { type: "risky",    text: "Stay 30 minutes to take photos.",          consequence: "Increased exposure to cold and wind." },
      { type: "reckless", text: "Attempt to camp at the summit.",           consequence: "Extreme survival risk." },
    ],
  },
];