# backend/graph/nodes.py

from __future__ import annotations
import subprocess
import tempfile
import base64
import os
import io
from typing import Any, Dict, cast

from backend.graph.state import GameState
from backend.graph.data import LOCATIONS, SCENARIOS
from backend.domain.game_rules import apply_game_rules
from backend.llm.factory import get_llm_provider
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

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
        # LangChain allows configuring timeouts directly on the runnable execution
        result = chain.with_config(config={"timeout": 4.0}).invoke(inputs)
        #print(f"[INVOKE] raw result type: {type(result)}")
        #print(f"[INVOKE] raw result: {result}")
        if isinstance(result, AIMessage):
            return _str(result.content)
        return _str(result)
    except Exception as e:
        print(f"[FALLBACK TRIGGERED] LLM Error or Timeout: {e}")
        #import traceback
        #print(f"[FALLBACK TRIGGERED] {type(e).__name__}: {e}")
        #traceback.print_exc()
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
        # 'bm_george' or 'bm_fable' are outstanding options for deadpan British wit
        samples, sample_rate = tts.create(
            text=text, 
            voice="bm_george", 
            speed=1.05,        # Marginally speed it up for snappy comedic timing
            lang="en-gb"
        )
        
        # Write the audio matrix into an in-memory byte buffer
        buffer = io.BytesIO()
        sf.write(buffer, samples, sample_rate, format="WAV")
        buffer.seek(0)
        
        # Base64 encode the binary data stream
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
# NODE 2: MODEL SELECTION
# ============================================================
def select_llm_provider(state: GameState) -> GameState:
    storm = state.get("stormPressure") or 0
    trust = state.get("guideTrust") or 100

    if storm > 80:
        state["llm_provider"] = "fast"
    elif trust < 30:
        state["llm_provider"] = "cheap"
    else:
        state["llm_provider"] = "default"

    return state


# ============================================================
# NODE 3: LLM NARRATIONS
# ============================================================
def generate_llm_narrations(state: GameState) -> GameState:
    llm = get_llm_provider()
    model_type = llm.__class__.__name__

    base_dir = os.path.dirname(os.path.abspath(__file__))
    narration_path = os.path.join(base_dir, "prompts", "narration.md")

    loc_idx = state.get("locationIndex") or 0
    loc = LOCATIONS[min(loc_idx, len(LOCATIONS) - 1)]
    is_high_altitude = loc.get("altNum", 0) > 4400

    history = state.get("actionHistory") or []
    last_action: str = (
        str(history[-1].get("choiceText", "")) if history
        else "The journey begins."
    )

    # --------------------------------------------------------
    # END STATE — closing monologue only
    # --------------------------------------------------------
    if state.get("endState"):
        prompt = ChatPromptTemplate.from_template(
            "A Himalayan expedition ended: {outcome}. Location: {loc}. Day: {day}.\n"
            "Write 3 sentences from the mountain's perspective. "
            "Focus on silence, altitude, and inevitability."
        )
        state["current_situation_text"] = _invoke(
            prompt | llm, 
            {"outcome": state.get("endState", ""), "loc": loc["name"], "day": state.get("day") or 1},
            fallback_text=FALLBACKS["env_high"]
        )
        state["current_yak_narration"]  = ""
        state["current_yak_audio"]      = ""
        state["current_journal_entry"]  = ""
        return state

    # --------------------------------------------------------
    # YAK NARRATION & VOICE SETUP
    # --------------------------------------------------------

    # System prompt is pre-baked into my Ollama Modelfile.
    # Thus, to save context tokens, passing a lightweight user instruction message.
    if "ollama" in model_type.lower():
        yak_prompt_template = ChatPromptTemplate.from_template(
            "You are a cynical Himalayan pack yak.\n"
            "Location: {loc}. Trekker action: {action}.\n"
            "Health: {health}/100. Guide trust: {trust}/100.\n"
            "Respond in 2 sarcastic sentences. No emojis."
        )
    else:
        with open(narration_path, "r", encoding="utf-8") as f:
            yak_base_prompt = f.read()
        contextualized_instructions = (
            f"{yak_base_prompt}\n\n"
            "CURRENT GAME STATE CONTEXT:\n"
            "Location: {loc}. Trekker action: {action}.\n"
            "Health: {health}/100. Guide trust: {trust}/100.\n"
            "Respond in 2 sarcastic sentences. No emojis."
        )
        yak_prompt_template = ChatPromptTemplate.from_messages([
            ("system", contextualized_instructions)
        ])

    yak_fallback = FALLBACKS["yak_high_altitude"] if is_high_altitude else FALLBACKS["yak_general"]
    
    state["current_yak_narration"] = _invoke(
        yak_prompt_template | llm, 
        {
            "loc":    loc["name"],
            "action": last_action,
            "health": state.get("health") or 100,
            "trust":  state.get("guideTrust") or 100,
        },
        fallback_text=yak_fallback
    )

    # Generate the voice representation for Tashi right after his text updates
    state["current_yak_audio"] = _generate_piper_tts_base64(state["current_yak_narration"])

    # --------------------------------------------------------
    # ENVIRONMENT / SITUATION
    # --------------------------------------------------------
    env_prompt = ChatPromptTemplate.from_template(
        "Describe harsh Himalayan conditions in 2 sentences.\n"
        "Location: {loc}. Storm pressure: {storm}/100. Action: {action}.\n"
        "Focus on wind, oxygen scarcity, and physical strain."
    )
    env_fallback = FALLBACKS["env_high"] if (state.get("stormPressure") or 0) > 50 else FALLBACKS["env_low"]
    
    state["current_situation_text"] = _invoke(
        env_prompt | llm, 
        {
            "loc":    loc["name"],
            "storm":  state.get("stormPressure") or 0,
            "action": last_action,
        },
        fallback_text=env_fallback
    )

    # --------------------------------------------------------
    # DORJE'S JOURNAL
    # --------------------------------------------------------
    journal_prompt = ChatPromptTemplate.from_template(
        "Write a 2-sentence private journal entry from Dorje, an experienced Himalayan guide.\n"
        "Location: {loc}. Day: {day}. "
        "Trekker health: {health}/100. Acclimatization: {acclim}/100.\n"
        "Dorje silently evaluates whether the trekker will survive the pass."
    )
    journal_fallback = FALLBACKS["journal_risky"] if (state.get("health") or 100) < 50 else FALLBACKS["journal_safe"]
    
    state["current_journal_entry"] = _invoke(
        journal_prompt | llm, 
        {
            "loc":   loc["name"],
            "day":   state.get("day") or 1,
            "health": state.get("health") or 100,
            "acclim": state.get("acclimatization") or 75,
        },
        fallback_text=journal_fallback
    )

    return state


# ============================================================
# NODE 4: BUILD CHOICES INTO STATE
# ============================================================
def build_events(state: GameState) -> GameState:
    loc_idx = state.get("locationIndex") or 0

    if loc_idx < len(SCENARIOS):
        state["current_choices"] = SCENARIOS[loc_idx]["choices"]
    else:
        state["current_choices"] = []

    return state