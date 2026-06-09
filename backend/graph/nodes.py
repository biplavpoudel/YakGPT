# backend/graph/nodes.py

from __future__ import annotations
from typing import Any, Dict, cast

from backend.graph.state import GameState
from backend.graph.data import LOCATIONS, SCENARIOS
from backend.domain.game_rules import apply_game_rules
from backend.llm.factory import get_llm_provider
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage


# ============================================================
# HELPERS
# ============================================================

def _str(val: Any) -> str:
    """Safely extract string from LLM response content."""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, list):
        # content blocks — grab first text block
        for block in val:
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", "")).strip()
        return ""
    return str(val).strip()


def _invoke(chain: Any, inputs: Dict[str, Any]) -> str:
    result = chain.invoke(inputs)
    if isinstance(result, AIMessage):
        return _str(result.content)
    return _str(result)


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

    loc_idx = state.get("locationIndex") or 0
    loc     = LOCATIONS[min(loc_idx, len(LOCATIONS) - 1)]

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
        state["current_situation_text"] = _invoke(prompt | llm, {
            "outcome": state.get("endState", ""),
            "loc":     loc["name"],
            "day":     state.get("day") or 1,
        })
        state["current_yak_narration"]  = ""
        state["current_journal_entry"]  = ""
        return state

    # --------------------------------------------------------
    # YAK NARRATION
    # --------------------------------------------------------
    yak_prompt = ChatPromptTemplate.from_template(
        "You are a cynical Himalayan pack yak.\n"
        "Location: {loc}. Trekker action: {action}.\n"
        "Health: {health}/100. Guide trust: {trust}/100.\n"
        "Respond in 2 sarcastic sentences. No emojis."
    )
    state["current_yak_narration"] = _invoke(yak_prompt | llm, {
        "loc":    loc["name"],
        "action": last_action,
        "health": state.get("health") or 100,
        "trust":  state.get("guideTrust") or 100,
    })

    # --------------------------------------------------------
    # ENVIRONMENT / SITUATION
    # --------------------------------------------------------
    env_prompt = ChatPromptTemplate.from_template(
        "Describe harsh Himalayan conditions in 2 sentences.\n"
        "Location: {loc}. Storm pressure: {storm}/100. Action: {action}.\n"
        "Focus on wind, oxygen scarcity, and physical strain."
    )
    state["current_situation_text"] = _invoke(env_prompt | llm, {
        "loc":    loc["name"],
        "storm":  state.get("stormPressure") or 0,
        "action": last_action,
    })

    # --------------------------------------------------------
    # DORJE'S JOURNAL
    # --------------------------------------------------------
    journal_prompt = ChatPromptTemplate.from_template(
        "Write a 2-sentence private journal entry from Dorje, an experienced Himalayan guide.\n"
        "Location: {loc}. Day: {day}. "
        "Trekker health: {health}/100. Acclimatization: {acclim}/100.\n"
        "Dorje silently evaluates whether the trekker will survive the pass."
    )
    state["current_journal_entry"] = _invoke(journal_prompt | llm, {
        "loc":   loc["name"],
        "day":   state.get("day") or 1,
        "health": state.get("health") or 100,
        "acclim": state.get("acclimatization") or 75,
    })

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