// frontend/data.js
// Mirror of backend/graph/data.py — keep in sync manually or generate from API.

export const LOCATIONS = [
  { name: "Manang",          alt: "3,540 m", altNum: 3540, day: 1, scene: "scene-manang" },
  { name: "Yak Kharka",      alt: "4,050 m", altNum: 4050, day: 3, scene: "scene-yak-kharkha" },
  { name: "Thorong Phedi",   alt: "4,450 m", altNum: 4450, day: 4, scene: "scene-thorong-phedi" },
  { name: "High Camp",       alt: "4,850 m", altNum: 4850, day: 5, scene: "scene-high-camp" },
  { name: "Thorong La Pass", alt: "5,416 m", altNum: 5416, day: 6, scene: "scene-thorong-la" }
];

export const SCENARIOS = [
  // 0: Manang
  [
    {
      id: "manang_hub",
      context: "altitude_acclimatization",
      fact: "Acclimatization hikes to Ice Lake or attending the Himalayan Rescue Association clinic trains the cardiorespiratory matrix.",
      peerEvent: "Dorje points up at the jagged ridgelines. Cloud formations are twisting dangerously around the upper peaks.",
      choices: [
        {
          text: "Check into a local tea house inn, spend 100 rupees on ginger tea, and rest to adjust to the altitude drop.",
          consequence: "Rest and slowly acclimate to 3,540 meters."
        },
        {
          text: "Attend the free evening medical brief at the Himalayan Rescue Association (HRA) clinic to learn about HAPE/HACE warning signs.",
          consequence: "Learn to identify lung rattling and visual cognitive alignment drops."
        },
        {
          text: "Ignore the rest suggestions. Pack your heavy pack and hit the rocky trail upward toward Yak Kharka immediately.",
          consequence: "Skip safety rest protocols and push high alpine elevations."
        }
      ]
    },
    {
      id: "manang_departure_gate",
      context: "trail_exit",
      fact: "Leaving a high-altitude baseline village without a clear tracking window leaves you vulnerable to sudden freezing winds.",
      peerEvent: "A local porter warns that loose slate slides are falling along the higher tracks past Gunsang.",
      choices: [
        {
          text: "Stay another afternoon at the lodge to double-check gear straps and drink boiled water rations.",
          consequence: "Delay trail departure to perform safety checks."
        },
        {
          text: "Pop a prophylactic pill of Diamox from your medical pouch to accelerate red blood cell oxygenation, then begin the steady ascent.",
          consequence: "Use Diamox to accelerate oxygenation and begin ascent."
        },
        {
          text: "Lace your boots, bypass the medicine check, and start hiking the steep switchback slopes to the upper alpine pastures.",
          consequence: "Begin ascent directly into high-altitude zones without medicine."
        }
      ]
    }
  ],
  // 1: Yak Kharka
  [
    {
      id: "yak_kharka_dilemma",
      context: "moral_dilemma",
      fact: "Hypothermia and dehydration mask themselves as simple exhaustion in the high alpine wilderness.",
      peerEvent: "An unguided duo is stranded outside a windswept stone wall shelter. One is shivering violently, completely missing a glove.",
      choices: [
        {
          text: "Open your pack, hand them 1 unit of your precious boiling water rations, and give them advice on wind shelter.",
          consequence: "Consume water to aid stranded team, gaining Dorje's trust."
        },
        {
          text: "Refuse to open your pack resources. Wave them toward the lower valley, and step straight inside the heated tea house common room.",
          consequence: "Prioritize personal resources; lose Dorje's trust."
        },
        {
          text: "Hunker down inside the stable compound, pay the lodge owner for an extra night, and avoid moving up the freezing trail.",
          consequence: "Rest at Yak Kharka to shelter from biting winds."
        }
      ]
    },
    {
      id: "yak_kharka_trail_leave",
      context: "ams_escalation",
      fact: "Hiding deep throbbing neural headaches at 4,000 meters accelerates internal capillary leaking into brain tissue (HACE).",
      peerEvent: "Your vision blurs slightly as you lace your boots. Dorje looks closely at your pupils, holding a tracking oximeter.",
      choices: [
        {
          text: "Confess that your head is pounding. Ask Dorje to check your vitals and rest here for another calendar weather cycle.",
          consequence: "Admit AMS symptoms to the guide and take safety hold."
        },
        {
          text: "Drink a bottle of pure water to alleviate the brain pressure and push forward up the steep canyon trail toward Thorong Phedi.",
          consequence: "Consume water to combat headache and ascend to Thorong Phedi."
        },
        {
          text: "Lie directly to Dorje, hide your heavy gasping breathing, and force yourself onto the vertical scree trail without using supplies.",
          consequence: "Conceal severe exhaustion and force ascent."
        }
      ]
    }
  ],
  // 2: Thorong Phedi
  [
    {
      id: "phedi_base_camp",
      context: "weather_window_gamble",
      fact: "Gales funneling between the high mountain valleys routinely create zero-visibility whiteouts by mid-morning.",
      peerEvent: "The mountain lodge at Phedi is buzzing with nervous energy. Trekkers are debating whether to sleep here or push to High Camp.",
      choices: [
        {
          text: "Secure a bed in the stone bunkhouse at Phedi, eat a heavy bowl of dal bhat, and refuse to step onto the exposed vertical moraine.",
          consequence: "Sleep at Thorong Phedi to protect lungs from extreme sub-zero exposure."
        },
        {
          text: "Munch on emergency rations from your pockets to restore glucose levels, pack your headlamp, and begin the brutal 400-meter climb to High Camp.",
          consequence: "Consume food and make a punishing scramble to High Camp."
        },
        {
          text: "Force your way directly up the freezing ice switchbacks instantly without checking gear settings or taking caloric nourishment.",
          consequence: "Attempt dangerous scramble to High Camp completely unhydrated."
        }
      ]
    }
  ],
  // 3: High Camp
  [
    {
      id: "high_camp_crisis",
      context: "hypoxia_delirium",
      fact: "Loss of motor control or stumbling at 4,800m means your brain is swelling from a lack of oxygen atmospheric pressure.",
      peerEvent: "Freezing gale-force winds are tearing violently at the corrugated tin roofs of the high shelter huts.",
      choices: [
        {
          text: "Admit you are losing your physical coordination. Rely entirely on Dorje to lash your crampons and set a slow, defensive pace.",
          consequence: "Surrender field autonomy to Dorje due to coordination loss."
        },
        {
          text: "Take a heavy dose of Diamox to chemically force your lungs to process the thin air, then hunker down inside the stone common room.",
          consequence: "Consume Diamox and rest before the pass day."
        },
        {
          text: "Ignite your headlamp at 3:00 AM, swallow a water ration, and step blindly into the pitch-black freezing void toward the summit marker.",
          consequence: "Consume water and start high pass push in pitch darkness."
        }
      ]
    }
  ],
  // 4: Thorong La Pass
  [
    {
      id: "summit_climax",
      context: "survival_threshold",
      fact: "The human brain loses critical rational decision judgment within minutes of extended exposure to extreme high alpine winds.",
      peerEvent: "The prayer flags are screaming in the wind. The cold is a physical wall. Your fingers are completely numb.",
      choices: [
        {
          text: "Touch the chorten marker sign briefly, bypass photos, and run down the long, knee-shattering 1,600-meter vertical descent to Muktinath safety.",
          consequence: "Evacuate high pass summit immediately to mitigate hypothermia."
        },
        {
          text: "Eat your final travel rations to keep your core body temperature from crashing, then begin the technical descent through the glacier field.",
          consequence: "Consume food and begin descent through glacier field."
        },
        {
          text: "Insist on unpacking your massive heavy cameras, taking off your heavy outer shell gloves, and staging a 30-minute celebratory photoshoot.",
          consequence: "Delay summit escape for photos, exposing skin to extreme frostbite."
        }
      ]
    }
  ],
  // 5: Muktinath
  [
    {
      id: "thorong_la_victory",
      context: "survival_threshold",
      fact: "Muktinath offers rich atmospheric oxygen pressure, ancient eternal flame shrines, and safe vehicle access down to Jomsom.",
      peerEvent: "Dorje extends a frostbitten hand with a deep, emotional smile. You have successfully conquered the pass.",
      choices: [
        {
          text: "Pour a final cup of hot tea, gaze up at the giant snow peaks behind you, and celebrate your survival.",
          consequence: "Celebrate successful completion of the circuit."
        }
      ]
    }
  ]
];
