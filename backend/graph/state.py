# backend/graph/state.py

from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict


# ============================================================
# GameState
#
# total=False means every key is optional at the TypedDict
# level, which is what LangGraph expects — it merges partial
# state updates from each node, so no key is "always present"
# from the type-checker's point of view.
#
# Use .get("key", default) everywhere in node functions and
# game_routes; never bare state["key"] on optional fields.
# ============================================================
class GameState(TypedDict, total=False):
    # core stats
    health:          int
    energy:          int
    acclimatization: int
    guideTrust:      int
    stormPressure:   int

    # progression
    locationIndex: int
    day:           int
    endState:      Optional[str]

    # per-turn input from frontend
    latest_choice_index: int

    # history
    actionHistory: List[Dict[str, Any]]

    # flags
    acclimatizationDayTaken: bool
    layersUsed:              bool
    backstoryUnlocked:       bool

    # llm routing (written by select_llm_provider)
    llm_provider: str

    # narration outputs (written by generate_llm_narrations)
    current_yak_narration:  str
    current_yak_audio:      str  # <-- ADDED FOR PIPER TTS DATA URI
    current_situation_text: str
    current_journal_entry:  str

    # choices for next turn (written by build_events)
    current_choices: List[Dict[str, Any]]

    # legacy
    events:   List[Dict[str, Any]]
    response: Dict[str, Any]