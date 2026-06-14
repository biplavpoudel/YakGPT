from typing import List, Dict, Any, Optional

# ============================================================
# LOCATIONS (STATIC WORLD MAP)
# ============================================================
LOCATIONS: List[Dict[str, Any]] = [
    {"name": "Manang", "alt": "3,540 m", "altNum": 3540, "day": 1},
    {"name": "Yak Kharka", "alt": "4,050 m", "altNum": 4050, "day": 3},
    {"name": "Thorong Phedi", "alt": "4,450 m", "altNum": 4450, "day": 4},
    {"name": "High Camp", "alt": "4,850 m", "altNum": 4850, "day": 5},
    {"name": "Thorong La Pass", "alt": "5,416 m", "altNum": 5416, "day": 6},
]

# ============================================================
# SCENARIOS (DENSE DRAMATIC PROGRESSION TREE)
# Maps to locationIndex via key, and subTurnIndex via array index.
# ============================================================
SCENARIOS: Dict[int, List[Dict[str, Any]]]= {
    # --------------------------------------------------------
    # LOCATION 0: MANANG (3,540 m)
    # --------------------------------------------------------
    0: [
        {
            "id": "manang_hub",
            "context": "altitude_acclimatization",
            "fact": "Acclimatization hikes to Ice Lake or attending the Himalayan Rescue Association clinic trains the cardiorespiratory matrix.",
            "peerEvent": "Dorje points up at the jagged ridgelines. Cloud formations are twisting dangerously around the upper peaks.",
            "choices": [
                {
                    "text": "Check into a local tea house inn, spend 100 rupees on ginger tea, and rest to adjust to the altitude drop.",
                    "log_summary": "Rented a room at a Manang inn to rest, hydrate, and slowly acclimate to 3,540 meters",
                    "deltaHealth": 10,
                    "deltaAcclim": 15,
                    "deltaEnergy": 20,
                    "deltaTrust": 5,
                    "deltaStorm": 10,
                    "rest": True # Loops back here, stays in Manang, increments a calendar day!
                },
                {
                    "text": "Attend the free evening medical brief at the Himalayan Rescue Association (HRA) clinic to learn about HAPE/HACE warning signs.",
                    "log_summary": "Attended the HRA medical briefing. Learned how to check for lung rattling and visual cognitive alignment drops",
                    "deltaHealth": 5,
                    "deltaAcclim": 25,
                    "deltaEnergy": -10,
                    "deltaTrust": 20,
                    "deltaStorm": 5,
                    "flag": "hra_briefing_attended"
                },
                {
                    "text": "Ignore the rest suggestions. Pack your heavy pack and hit the rocky trail upward toward Yak Kharka immediately.",
                    "log_summary": "Skipped basic safety rest protocols at Manang, pushing hard into high alpine elevations to beat weather delays",
                    "deltaHealth": -15,
                    "deltaAcclim": -20,
                    "deltaEnergy": -25,
                    "deltaTrust": -20,
                    "deltaStorm": 0,
                    "travel": True # Advances geographic location array straight to Yak Kharka!
                }
            ]
        },
        {
            "id": "manang_departure_gate",
            "context": "trail_exit",
            "fact": "Leaving a high-altitude baseline village without a clear tracking window leaves you vulnerable to sudden freezing winds.",
            "peerEvent": "A local porter warns that loose slate slides are falling along the higher tracks past Gunsang.",
            "choices": [
                {
                    "text": "Stay another afternoon at the lodge to double-check gear straps and drink boiled water rations.",
                    "log_summary": "Chose to delay trail departure for an extra afternoon to perform safety checks",
                    "deltaHealth": 5,
                    "deltaAcclim": 10,
                    "deltaEnergy": 15,
                    "deltaTrust": 10,
                    "deltaStorm": 15,
                    "rest": True
                },
                {
                    "text": "Pop a prophylactic pill of Diamox from your medical pouch to accelerate red blood cell oxygenation, then begin the steady ascent.",
                    "log_summary": "Consumed 1 unit of Diamox to medically combat upcoming hypoxia risks and began walking upper paths",
                    "deltaHealth": 5,
                    "deltaAcclim": 30,
                    "deltaEnergy": -15,
                    "deltaTrust": 10,
                    "deltaStorm": 5,
                    "consumeItem": "diamox",
                    "travel": True
                },
                {
                    "text": "Lace your boots, bypass the medicine check, and start hiking the steep switchback slopes to the upper alpine pastures.",
                    "log_summary": "Began the climb out of the Manang valley directly into the barren, thin-air alpine zones",
                    "deltaHealth": -10,
                    "deltaAcclim": 5,
                    "deltaEnergy": -20,
                    "deltaTrust": -5,
                    "deltaStorm": 5,
                    "travel": True
                }
            ]
        }
    ],

    # --------------------------------------------------------
    # LOCATION 1: YAK KHARKA (4,050 m)
    # --------------------------------------------------------
    1: [
        {
            "id": "yak_kharka_dilemma",
            "context": "moral_dilemma",
            "fact": "Hypothermia and dehydration mask themselves as simple exhaustion in the high alpine wilderness.",
            "peerEvent": "An unguided duo is stranded outside a windswept stone wall shelter. One is shivering violently, completely missing a glove.",
            "choices": [
                {
                    "text": "Open your pack, hand them 1 unit of your precious boiling water rations, and give them advice on wind shelter.",
                    "log_summary": "Sacrificed a boiling water ration to save a dehydrated, shivering unguided team outside Yak Kharka",
                    "deltaHealth": -5,
                    "deltaAcclim": 0,
                    "deltaEnergy": -10,
                    "deltaTrust": 25,
                    "deltaStorm": 5,
                    "consumeItem": "water"
                },
                {
                    "text": "Refuse to open your pack resources. Wave them toward the lower valley, and step straight inside the heated tea house common room.",
                    "log_summary": "Prioritized individual caloric safety over stranded trekkers, drawing quiet disapproval from Dorje",
                    "deltaHealth": 10,
                    "deltaAcclim": 0,
                    "deltaEnergy": 15,
                    "deltaTrust": -25,
                    "deltaStorm": 0
                },
                {
                    "text": "Hunker down inside the stable compound, pay the lodge owner for an extra night, and avoid moving up the freezing trail.",
                    "log_summary": "Rented an alcove berth at Yak Kharka to shelter from biting high-altitude winds",
                    "deltaHealth": 10,
                    "deltaAcclim": 15,
                    "deltaEnergy": 20,
                    "deltaTrust": 5,
                    "deltaStorm": 10,
                    "rest": True
                }
            ]
        },
        {
            "id": "yak_kharka_trail_leave",
            "context": "ams_escalation",
            "fact": "Hiding deep throbbing neural headaches at 4,000 meters accelerates internal capillary leaking into brain tissue (HACE).",
            "peerEvent": "Your vision blurs slightly as you lace your boots. Dorje looks closely at your pupils, holding a tracking oximeter.",
            "choices": [
                {
                    "text": "Confess that your head is pounding. Ask Dorje to check your vitals and rest here for another calendar weather cycle.",
                    "log_summary": "Formally admitted early cognitive altitude migraine symptoms to the guide, requesting a safety hold",
                    "deltaHealth": 15,
                    "deltaAcclim": 20,
                    "deltaEnergy": 10,
                    "deltaTrust": 25,
                    "deltaStorm": 15,
                    "rest": True
                },
                {
                    "text": "Drink a bottle of pure water to alleviate the brain pressure and push forward up the steep canyon trail toward Thorong Phedi.",
                    "log_summary": "Consumed 1 unit of water to clear a lingering high-altitude headache and advanced up-canyon",
                    "deltaHealth": -5,
                    "deltaAcclim": 5,
                    "deltaEnergy": -25,
                    "deltaTrust": 10,
                    "deltaStorm": 5,
                    "consumeItem": "water",
                    "travel": True
                },
                {
                    "text": "Lie directly to Dorje, hide your heavy gasping breathing, and force yourself onto the vertical scree trail without using supplies.",
                    "log_summary": "Concealed severe neural exhaustion symptoms from the guide to avoid an enforced descent checkpoint",
                    "deltaHealth": -30,
                    "deltaAcclim": -20,
                    "deltaEnergy": -35,
                    "deltaTrust": -30,
                    "deltaStorm": 0,
                    "travel": True
                }
            ]
        }
    ],

    # --------------------------------------------------------
    # LOCATION 2: THORONG PHEDI (4,450 m)
    # --------------------------------------------------------
    2: [
        {
            "id": "phedi_base_camp",
            "context": "weather_window_gamble",
            "fact": "Gales funneling between the high mountain valleys routinely create zero-visibility whiteouts by mid-morning.",
            "peerEvent": "The mountain lodge at Phedi is buzzing with nervous energy. Trekkers are debating whether to sleep here or push to High Camp.",
            "choices": [
                {
                    "text": "Secure a bed in the stone bunkhouse at Phedi, eat a heavy bowl of dal bhat, and refuse to step onto the exposed vertical moraine.",
                    "log_summary": "Elected to sleep at the lower Thorong Phedi base camp to protect lungs from extreme sub-zero exposure",
                    "deltaHealth": 15,
                    "deltaAcclim": 10,
                    "deltaEnergy": 25,
                    "deltaTrust": 10,
                    "deltaStorm": 10,
                    "rest": True
                },
                {
                    "text": "Munch on emergency rations from your pockets to restore glucose levels, pack your headlamp, and begin the brutal 400-meter climb to High Camp.",
                    "log_summary": "Consumed 1 unit of travel rations to fuel a punishing evening scramble up loose shale slopes to High Camp",
                    "deltaHealth": -15,
                    "deltaAcclim": 5,
                    "deltaEnergy": -20,
                    "deltaTrust": 15,
                    "deltaStorm": 5,
                    "consumeItem": "rations",
                    "travel": True
                },
                {
                    "text": "Force your way directly up the freezing ice switchbacks instantly without checking gear settings or taking caloric nourishment.",
                    "log_summary": "Attempted the vertical scree face to High Camp completely unhydrated in dropping light conditions",
                    "deltaHealth": -35,
                    "deltaAcclim": -15,
                    "deltaEnergy": -40,
                    "deltaTrust": -20,
                    "deltaStorm": 5,
                    "travel": True
                }
            ]
        }
    ],

    # --------------------------------------------------------
    # LOCATION 3: HIGH CAMP (4,850 m)
    # --------------------------------------------------------
    3: [
        {
            "id": "high_camp_crisis",
            "context": "hypoxia_delirium",
            "fact": "Loss of motor control or stumbling at 4,800m means your brain is swelling from a lack of oxygen atmospheric pressure.",
            "peerEvent": "Freezing gale-force winds are tearing violently at the corrugated tin roofs of the high shelter huts.",
            "choices": [
                {
                    "text": "Admit you are losing your physical coordination. Rely entirely on Dorje to lash your crampons and set a slow, defensive pace.",
                    "log_summary": "Surrendered field autonomy to Dorje due to severe high-altitude motor uncoordination",
                    "deltaHealth": 10,
                    "deltaAcclim": 5,
                    "deltaEnergy": -15,
                    "deltaTrust": 25,
                    "deltaStorm": 5
                },
                {
                    "text": "Take a heavy dose of Diamox to chemically force your lungs to process the thin air, then hunker down inside the stone common room.",
                    "log_summary": "Consumed your final Diamox reserves to combat fluid pressure buildup in the brain before the pass day",
                    "deltaHealth": 15,
                    "deltaAcclim": 35,
                    "deltaEnergy": 10,
                    "deltaTrust": 15,
                    "deltaStorm": 10,
                    "consumeItem": "diamox",
                    "rest": True
                },
                {
                    "text": "Ignite your headlamp at 3:00 AM, swallow a water ration, and step blindly into the pitch-black freezing void toward the summit marker.",
                    "log_summary": "Commenced the final high pass alpine push in pitch darkness to beat the 10:00 AM storm cutoff gale winds",
                    "deltaHealth": -20,
                    "deltaAcclim": 5,
                    "deltaEnergy": -35,
                    "deltaTrust": 10,
                    "deltaStorm": -20,
                    "consumeItem": "water",
                    "travel": True
                }
            ]
        }
    ],

    # --------------------------------------------------------
    # LOCATION 4: THORONG LA SUMMIT (5,416 m)
    # --------------------------------------------------------
    4: [
        {
            "id": "summit_climax",
            "context": "survival_threshold",
            "fact": "The human brain loses critical rational decision judgment within minutes of extended exposure to extreme high alpine winds.",
            "peerEvent": "The prayer flags are screaming in the wind. The cold is a physical wall. Your fingers are completely numb.",
            "choices": [
                {
                    "text": "Touch the chorten marker sign briefly, bypass photos, and run down the long, knee-shattering 1,600-meter vertical descent to Muktinath safety.",
                    "log_summary": "Evacuated the extreme high pass summit marker immediately to mitigate lethal hypothermia risks",
                    "deltaHealth": 10,
                    "deltaAcclim": 0,
                    "deltaEnergy": -30,
                    "deltaTrust": 20,
                    "deltaStorm": 0,
                    "travel": True
                },
                {
                    "text": "Eat your final travel rations to keep your core body temperature from crashing, then begin the technical descent through the glacier field.",
                    "log_summary": "Consumed final travel food rations at 5,416 meters to stave off systemic muscular failure on the descent",
                    "deltaHealth": 15,
                    "deltaAcclim": 0,
                    "deltaEnergy": -15,
                    "deltaTrust": 15,
                    "deltaStorm": 0,
                    "consumeItem": "rations",
                    "travel": True
                },
                {
                    "text": "Insist on unpacking your massive heavy cameras, taking off your heavy outer shell gloves, and staging a 30-minute celebratory photoshoot.",
                    "log_summary": "Delayed vital high-altitude escape path to capture photographs, exposing skin to extreme atmospheric frostbite risks",
                    "deltaHealth": -45,
                    "deltaAcclim": -15,
                    "deltaEnergy": -40,
                    "deltaTrust": -30,
                    "deltaStorm": 30,
                    "travel": True
                }
            ]
        }
    ],

    # --------------------------------------------------------
    # LOCATION 5: MUKTINATH / SANCTUARY (3,800 m)
    # --------------------------------------------------------
    5: [
        {
            "id": "thorong_la_victory",
            "context": "survival_threshold",
            "fact": "Muktinath offers rich atmospheric oxygen pressure, ancient eternal flame shrines, and safe vehicle access down to Jomsom.",
            "peerEvent": "Dorje extends a frostbitten hand with a deep, emotional smile. You have successfully conquered the pass.",
            "choices": [
                {
                    "text": "Pour a final cup of hot tea, gaze up at the giant snow peaks behind you, and celebrate your survival.",
                    "log_summary": "Successfully navigated the treacherous Annapurna Circuit, surviving the thin air and reaching sanctuary safely",
                    "deltaHealth": 100,
                    "deltaAcclim": 100,
                    "deltaEnergy": 100,
                    "deltaTrust": 100,
                    "deltaStorm": 0,
                    "travel": True
                }
            ]
        }
    ]
}