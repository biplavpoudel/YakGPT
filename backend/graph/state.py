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
# ============================================================
class GameState(TypedDict, total=False):
    # Core stats
    health:          int
    energy:          int
    acclimatization: int
    guideTrust:      int
    stormPressure:   int

    # Progression & Time Realism
    locationIndex: int  # Current location in the LOCATIONS array
    subTurnIndex:  int  # Track multi-stage choices inside ONE location (e.g., 0=Arrival, 1=Night, 2=Departure)
    day:           int
    endState:      Optional[str]

    # Narrative Continuity & Escalation
    relationshipTier: str  # Dynamically updated state: "Protective", "Resigned", "Hostile"
    tensionModifier:  str  # Escalation multiplier: "Low-Stakes", "Hostile", "Suffocating"
    shortHistoryLog:  List[str] # Human-readable text log of the last 4 choices for the LLM's memory

    # Per-turn input from frontend
    latest_choice_index: int

    # Inventory
    # History (Raw payload data)
    actionHistory: List[Dict[str, Any]]

    inventory: Dict[str, int]

    # Flags
    acclimatizationDayTaken: bool
    layersUsed:              bool
    backstoryUnlocked:       bool

    # LLM routing
    llm_provider: str

    # Narration outputs
    current_yak_narration:  str
    current_yak_audio:      str  
    current_situation_text: str
    current_journal_entry:  str

    # Choices for next turn
    current_choices: List[Dict[str, Any]]

    # Legacy
    events:   List[Dict[str, Any]]
    response: Dict[str, Any]