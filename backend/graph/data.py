# backend/graph/data.py

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
# SCENARIOS (PURE GAME INPUT DATA)
# NOTE:
# - NO narrative duplication
# - NO emojis in logic layer
# - NO backend story writing (handled by LLM nodes)
# ============================================================
SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "manang_acclimatization",
        "context": "high_altitude_entry",
        "risk_level": "low",
        "fact": "Acclimatization at Manang is critical to prevent Acute Mountain Sickness.",
        "peerEvent": None,
        "choices": [
            {
                "type": "safe",
                "text": "Take an acclimatization hike and sleep at Manang.",
                "consequence": "Improves adaptation to altitude.",
                "deltaHealth": 0,
                "deltaAcclim": 15,
                "deltaEnergy": -5,
                "deltaTrust": 5,
                "deltaStorm": 8,
                "flag": "acclimatizationDayTaken",
            },
            {
                "type": "risky",
                "text": "Push directly to Yak Kharka.",
                "consequence": "Reduced acclimatization increases risk.",
                "deltaHealth": -5,
                "deltaAcclim": -10,
                "deltaEnergy": -15,
                "deltaTrust": -10,
                "deltaStorm": 15,
            },
            {
                "type": "reckless",
                "text": "Skip ahead to Thorong Phedi in one push.",
                "consequence": "Severe altitude stress likely.",
                "deltaHealth": -20,
                "deltaAcclim": -25,
                "deltaEnergy": -25,
                "deltaTrust": -25,
                "deltaStorm": 22,
            },
        ],
    },

    {
        "id": "yak_kharka_symptoms",
        "context": "ams_warning",
        "risk_level": "medium",
        "fact": "Headache above 3000m is a primary symptom of AMS.",
        "peerEvent": "A fellow trekker is showing early nausea symptoms.",
        "choices": [
            {
                "type": "safe",
                "text": "Report symptoms to Dorje and rest.",
                "consequence": "Proper rest improves recovery.",
                "deltaHealth": 5,
                "deltaAcclim": 10,
                "deltaEnergy": 10,
                "deltaTrust": 15,
                "deltaStorm": 10,
            },
            {
                "type": "risky",
                "text": "Take medication and hide symptoms.",
                "consequence": "Symptoms masked but risk remains.",
                "deltaHealth": -5,
                "deltaAcclim": -15,
                "deltaEnergy": -5,
                "deltaTrust": -15,
                "deltaStorm": 12,
            },
            {
                "type": "reckless",
                "text": "Ignore symptoms and continue ascent.",
                "consequence": "High risk of altitude complications.",
                "deltaHealth": -20,
                "deltaAcclim": -20,
                "deltaEnergy": -20,
                "deltaTrust": -25,
                "deltaStorm": 20,
            },
        ],
    },

    {
        "id": "thorong_phedi_preparation",
        "context": "weather_window",
        "risk_level": "medium",
        "fact": "Early morning starts reduce storm exposure risk at Thorong La.",
        "peerEvent": "Experienced trekkers prepare gear quietly before dawn.",
        "choices": [
            {
                "type": "safe",
                "text": "Sleep early and start at 3am with guide.",
                "consequence": "Optimal weather window usage.",
                "deltaHealth": 5,
                "deltaAcclim": 5,
                "deltaEnergy": 10,
                "deltaTrust": 10,
                "deltaStorm": 8,
            },
            {
                "type": "risky",
                "text": "Start at 5am like most groups.",
                "consequence": "Narrower weather margin.",
                "deltaHealth": -5,
                "deltaAcclim": -5,
                "deltaEnergy": -5,
                "deltaTrust": -10,
                "deltaStorm": 18,
            },
            {
                "type": "reckless",
                "text": "Leave immediately despite conditions.",
                "consequence": "High exposure to unstable weather.",
                "deltaHealth": -15,
                "deltaAcclim": -10,
                "deltaEnergy": -20,
                "deltaTrust": -30,
                "deltaStorm": 30,
            },
        ],
    },

    {
        "id": "high_camp_coordination",
        "context": "extreme_altitude",
        "risk_level": "high",
        "fact": "Loss of coordination may indicate early HACE.",
        "peerEvent": None,
        "choices": [
            {
                "type": "safe",
                "text": "Perform coordination test and follow guide pace.",
                "consequence": "Early detection reduces risk.",
                "deltaHealth": 5,
                "deltaAcclim": 5,
                "deltaEnergy": -10,
                "deltaTrust": 15,
                "deltaStorm": 5,
            },
            {
                "type": "risky",
                "text": "Skip self-check and proceed normally.",
                "consequence": "Hidden risk may escalate.",
                "deltaHealth": -10,
                "deltaAcclim": -15,
                "deltaEnergy": -15,
                "deltaTrust": -15,
                "deltaStorm": 12,
            },
            {
                "type": "reckless",
                "text": "Rush ahead to stay warm.",
                "consequence": "Severe energy depletion.",
                "deltaHealth": -25,
                "deltaAcclim": -10,
                "deltaEnergy": -30,
                "deltaTrust": -20,
                "deltaStorm": 15,
            },
        ],
    },

    {
        "id": "thorong_la_summit",
        "context": "summit_phase",
        "risk_level": "extreme",
        "fact": "Thorong La is the highest and most exposed point of the circuit.",
        "peerEvent": None,
        "choices": [
            {
                "type": "safe",
                "text": "Brief summit stop and immediate descent.",
                "consequence": "Correct high-altitude behavior.",
                "deltaHealth": 5,
                "deltaAcclim": 0,
                "deltaEnergy": -10,
                "deltaTrust": 5,
                "deltaStorm": 0,
            },
            {
                "type": "risky",
                "text": "Stay 30 minutes to take photos.",
                "consequence": "Increased exposure to cold and wind.",
                "deltaHealth": -10,
                "deltaAcclim": -5,
                "deltaEnergy": -15,
                "deltaTrust": -5,
                "deltaStorm": 20,
            },
            {
                "type": "reckless",
                "text": "Attempt to camp at the summit.",
                "consequence": "Extreme survival risk.",
                "deltaHealth": -40,
                "deltaAcclim": -30,
                "deltaEnergy": -40,
                "deltaTrust": -40,
                "deltaStorm": 50,
            },
        ],
    },
]