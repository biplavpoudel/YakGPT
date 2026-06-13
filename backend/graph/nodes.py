from __future__ import annotations
import subprocess
import tempfile
import base64
import os
import io
from typing import Any, Dict, List, cast

from backend.graph.state import GameState
from backend.graph.data import LOCATIONS, SCENARIOS
from backend.domain.game_rules import apply_game_rules
from backend.llm.factory import get_llm_provider
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser

import soundfile as sf
from kokoro_onnx import Kokoro

# Initialize paths relative to environment configuration or defaults
MODEL_PATH = os.getenv("KOKORO_MODEL_PATH", "models/kokoro-v1.0.onnx")
VOICES_PATH = os.getenv("KOKORO_VOICES_PATH", "models/voices-v1.0.bin")


# ============================================================
# NARRATIVE FALLBACK DICTIONARY (FAILSAFES)
# ============================================================
FALLBACKS = {
    "yak_general": "The trekker pauses by the mani wall, staring at the incline. The wind shifts, carrying the scent of snow and human regret.",
    "yak_high_altitude": "Another step, another gasp for air near the frozen scree. They all think the mountain cares about their summit goals.",
    "env_low": "The air is thin and biting cold. Loose shale crunches underfoot as the trail winds further up the valley.",
    "env_high": "A brutal crosswind whips ice crystals across the trail. Visibility is dropping, and every breath feels like swallowing glass.",
    "journal_safe": "Pace is steady, but the real test is higher up. The mountain will reveal what kind of trekker they are soon enough.",
    "journal_risky": "They are struggling with the thin air. I will need to watch them closely. The pass does not forgive stubbornness."
}

# ============================================================
# HELPERS
# ============================================================

def _str(val: Any) -> str:
    """Safely extract string from LLM response content."""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, list):
        for block in val:
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", "")).strip()
        return ""
    return str(val).strip()


def _invoke(chain: Any, inputs: Dict[str, Any], fallback_text: str) -> str:
    """Invokes the LLM chain with a try-except wrapper as a safety net."""
    try:
        result = chain.with_config(config={"timeout": 4.0}).invoke(inputs)
        return _str(result)
    except Exception as e:
        print(f"[FALLBACK TRIGGERED] LLM Error or Timeout: {e}")
        return fallback_text

# Global singleton so it initializes ONCE on server boot
_kokoro_instance = None

def get_kokoro_tts():
    global _kokoro_instance
    if _kokoro_instance is None:
        if os.path.exists(MODEL_PATH) and os.path.exists(VOICES_PATH):
            print(f"[TTS] Loading Kokoro engine from {MODEL_PATH}...")
            _kokoro_instance = Kokoro(MODEL_PATH, VOICES_PATH)
        else:
            print(f"[TTS WARNING] Kokoro files not found. Audio generation will be skipped.")
    return _kokoro_instance


def _generate_piper_tts_base64(text: str) -> str:
    """
    Synthesizes text into high-quality sarcastic speech entirely in RAM 
    and returns a Base64 data URI string.
    """
    tts = get_kokoro_tts()
    if not tts:
        return ""

    try:
        samples, sample_rate = tts.create(
            text=text, 
            voice="bm_george", 
            speed=1.05,        # Marginally speed it up for snappy comedic timing
            lang="en-gb"
        )
        
        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format="WAV")
        buffer.seek(0)
        
        base64_audio = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:audio/wav;base64,{base64_audio}"

    except Exception as e:
        print(f"[TTS EXCEPTION] Kokoro failed synthesis loop: {e}")
        return ""
    

# ============================================================
# NODE 1: DETERMINISTIC RULES
# ============================================================
def apply_deterministic_rules(state: GameState) -> GameState:
    return apply_game_rules(state)


# ============================================================
# NODE 2: STATE INITIALIZATION & SANITATION (REPLACED SELECTOR)
# ============================================================
def prepare_turn_context(state: GameState) -> GameState:
    """
    If a player has a completely normal turn where nothing special happens,
    our rules engine might not write anything for relationshipTier or tensionModifier.
    If those slots are totally empty (None), our LLM prompt will panic and crash
    because it doesn't know how to fill in the blank text template.

    This function checks those slots. If they are empty,
    it fills them with standard baseline defaults like "Wary Observer" or "Low-Stakes".
    It ensures that every single turn looks uniform and pristine right before the LLM reads it.
    """
    # Enforce standard single-instance tracker tag
    state["llm_provider"] = "default"
    
    # Initialize baseline text fallbacks if rules engine updates are partial
    if not state.get("relationshipTier"):
        state["relationshipTier"] = "Wary Observer"

    if not state.get("tensionModifier"):
        state["tensionModifier"] = "Low-Stakes / Discomfort"
        
    return state


# ============================================================
# NODE 3: LLM NARRATIONS
# ============================================================
def generate_llm_narrations(state: GameState) -> GameState:
    llm = get_llm_provider()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    narration_path = os.path.join(base_dir, "prompts", "narration.md")

    loc_idx = state.get("locationIndex") or 0
    loc = LOCATIONS[min(loc_idx, len(LOCATIONS) - 1)]
    is_high_altitude = loc.get("altNum", 0) > 4400

    relationship = state.get("relationshipTier", "Wary Observer")
    tension = state.get("tensionModifier", "Low-Stakes / Discomfort")
    
    history_list: List[str] = state.get("shortHistoryLog") or []
    if history_list:
        history_context = "\n".join([f"- {item}" for item in history_list])
    else:
        history_context = "- The journey has just commenced from the lower trailheads."

    # --------------------------------------------------------
    # END STATE — Closing monologue configuration
    # --------------------------------------------------------
    if state.get("endState"):
        prompt = ChatPromptTemplate.from_template(
            "A Himalayan expedition ended with outcome: {outcome}. Location: {loc}. Day: {day}.\n"
            "RECORDED JOURNEY HISTORY:\n{history}\n\n"
            "Write 3 intense sentences from the mountain's perspective. "
            "Focus on absolute silence, freezing altitude, and the inevitability of your judgment."
        )
        closing_text = _invoke(
            prompt | llm | StrOutputParser(), 
            {
                "outcome": state.get("endState", ""), 
                "loc": loc["name"], 
                "day": state.get("day") or 1,
                "history": history_context
            },
            fallback_text=FALLBACKS["env_high"]
        )
        
        state["current_yak_narration"]  = closing_text
        state["current_situation_text"] = "The journey terminates here."
        state["current_journal_entry"]  = "Log closed."
        state["current_yak_audio"]      = _generate_piper_tts_base64(closing_text)
        return state

    # --------------------------------------------------------
    # YAK NARRATION & VOICE SETUP
    # --------------------------------------------------------
    with open(narration_path, "r", encoding="utf-8") as f:
        yak_base_prompt = f.read()
        
    yak_prompt_template = ChatPromptTemplate.from_messages([
        ("system", yak_base_prompt), 
        ("human", (
            "DYNAMIC RELATIONSHIP & STAKES CONTEXT:\n"
            "- Tashi's Relationship Tier to Trekker: {relationship}\n"
            "- Mountain Environmental Tension Level: {tension}\n\n"
            "CURRENT TURN VARIABLES:\n"
            "Location: {loc} ({alt}). Day: {day}.\n"
            "Physical Health: {health}/100. Guide Trust: {trust}/100. Storm Wall Pressure: {storm}/100.\n\n"
            "INSTRUCTION: Respond directly to the trekker's path choices and state using exactly 2 to 3 sarcastic, world-weary sentences. Do not summarize the stats."
        ))
    ])

    yak_fallback = FALLBACKS["yak_high_altitude"] if is_high_altitude else FALLBACKS["yak_general"]
    
    state["current_yak_narration"] = _invoke(
        yak_prompt_template | llm | StrOutputParser(), 
        {
            "loc":         loc["name"],
            "alt":         loc["alt"],
            "day":         state.get("day") or 1,
            "health":      state.get("health") or 100,
            "trust":       state.get("guideTrust") or 100,
            "storm":       state.get("stormPressure") or 0,
            "history_log": history_context  # Matches our narration.md key
        },
        fallback_text=yak_fallback
    )

    state["current_yak_audio"] = _generate_piper_tts_base64(state["current_yak_narration"])

    # --------------------------------------------------------
    # ENVIRONMENT / SITUATION
    # --------------------------------------------------------
    env_prompt = ChatPromptTemplate.from_template(
        "You are the oppressive atmosphere of the high Himalayas.\n"
        "STAKES MODIFIER: {tension}\n"
        "RECORDED JOURNEY CONTEXT:\n{history}\n\n"
        "Describe the immediate physical environmental conditions in exactly 2 sentences.\n"
        "Location: {loc} ({alt}). Storm Wall: {storm}/100.\n"
        "Focus on wind velocity, oxygen scarcity, physical strain, and how past choices are catching up to their body right now."
    )
    env_fallback = FALLBACKS["env_high"] if (state.get("stormPressure") or 0) > 50 else FALLBACKS["env_low"]
    
    state["current_situation_text"] = _invoke(
        env_prompt | llm | StrOutputParser(), 
        {
            "loc":     loc["name"],
            "alt":     loc["alt"],
            "storm":   state.get("stormPressure") or 0,
            "tension": tension,
            "history": history_context
        },
        fallback_text=env_fallback
    )

    # --------------------------------------------------------
    # DORJE'S JOURNAL
    # --------------------------------------------------------
    journal_prompt = ChatPromptTemplate.from_template(
        "You are Dorje, an experienced Himalayan guide writing a private log entry.\n"
        "YOUR CURRENT RELATIONSHIP STATE: {relationship}\n"
        "THE TREKKER'S ACTION RECORD:\n{history}\n\n"
        "Write a raw, 2-sentence private journal entry evaluating the trekker.\n"
        "Location: {loc}. Day: {day}. Health: {health}/100. Acclimatization: {acclim}/100.\n"
        "Reflect directly on their past choices, your current level of trust in them, and whether they will survive the pass or become a fatal liability."
    )
    journal_fallback = FALLBACKS["journal_risky"] if (state.get("health") or 100) < 50 else FALLBACKS["journal_safe"]
    
    state["current_journal_entry"] = _invoke(
        journal_prompt | llm | StrOutputParser(), 
        {
            "loc":          loc["name"],
            "day":          state.get("day") or 1,
            "health":       state.get("health") or 100,
            "acclim":       state.get("acclimatization") or 75,
            "relationship": relationship,
            "history":      history_context
        },
        fallback_text=journal_fallback
    )

    return state


# ============================================================
# NODE 4: BUILD CHOICES INTO STATE
# ============================================================
def build_events(state: GameState) -> GameState:
    """
    Looks up the nested multi-scenario structure using locationIndex 
    and subTurnIndex keys sequentially. Fixes engine soft-locks by 
    injecting functional flow flags into emergency choices.
    """
    loc_idx = state.get("locationIndex") or 0
    sub_idx = state.get("subTurnIndex") or 0

    if loc_idx in SCENARIOS:
        sub_scenarios = SCENARIOS[loc_idx]
        if sub_scenarios and sub_idx < len(sub_scenarios):
            state["current_choices"] = sub_scenarios[sub_idx]["choices"]
            return state
        elif sub_scenarios and len(sub_scenarios) > 0:
            state["current_choices"] = sub_scenarios[0]["choices"]
            return state

    print(f"[CHOICES WARNING] Lookup failed for loc_idx: {loc_idx}, sub_idx: {sub_idx}. Injecting emergency choices.")
    
    if loc_idx == 1: # Yak Kharka
        state["current_choices"] = [
            {
                "text": "Rest a bit longer at Yak Kharka to let your lungs adjust.", 
                "consequence": "Improves acclimatization slightly, but delays trail progress.",
                "rest": True
            },
            {
                "text": "Pack your gear and push on up the trail toward Thorong Phedi.", 
                "consequence": "Outruns the climbing storm pressure but increases AMS risk.",
                "travel": True
            }
        ]
    else: # General baseline fallback array
        state["current_choices"] = [
            {
                "text": "Conserve your energy reserves and proceed with caution.", 
                "consequence": "Minimizes vitality drain metrics.",
                "rest": True
            },
            {
                "text": "Increase your hiking pace to reach the next camp early.", 
                "consequence": "Reduces regional exposure duration at a high physical cost.",
                "travel": True
            }
        ]

    return state

# ============================================================
# NODE 4: THE ROUTER FUNCTION
# ============================================================
# End State Conditional Routing Edge
def route_after_turn(state: GameState) -> str:
    """
    Checks if an endscreen state has been reached. 
    If yes, we bypass future choices and terminate the graph loop immediately.
    """
    if state.get("endState"):
        return "__end__"
    return "events"