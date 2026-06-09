# backend/domain/game_rules.py

from __future__ import annotations
from typing import Any, Dict, List

from backend.graph.data import LOCATIONS, SCENARIOS
from backend.graph.state import GameState


def clamp(val: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, val))


def apply_game_rules(state: GameState) -> GameState:
    """
    Applies the chosen delta, advances location, detects end state.
    All reads use .get() with defaults — no bare key access on
    optional TypedDict fields.
    """
    choice_idx:  int = state.get("latest_choice_index") or 0
    loc_idx:     int = state.get("locationIndex")       or 0

    if loc_idx >= len(SCENARIOS):
        return state

    scenario = SCENARIOS[loc_idx]
    choices: List[Dict[str, Any]] = scenario.get("choices", [])

    if choice_idx < 0 or choice_idx >= len(choices):
        choice_idx = 0

    choice: Dict[str, Any] = choices[choice_idx]

    # --------------------------------------------------------
    # APPLY DELTAS
    # --------------------------------------------------------
    state["health"]          = clamp((state.get("health")          or 100) + (choice.get("deltaHealth") or 0))
    state["energy"]          = clamp((state.get("energy")          or 100) + (choice.get("deltaEnergy") or 0))
    state["acclimatization"] = clamp((state.get("acclimatization") or 75)  + (choice.get("deltaAcclim") or 0))
    state["guideTrust"]      = clamp((state.get("guideTrust")      or 100) + (choice.get("deltaTrust")  or 0))
    state["stormPressure"]   = clamp((state.get("stormPressure")   or 0)   + (choice.get("deltaStorm")  or 0))

    # --------------------------------------------------------
    # FLAGS
    # --------------------------------------------------------
    flag: Any = choice.get("flag")
    if flag and isinstance(flag, str):
        state[flag] = True  # type: ignore[literal-required]

    # --------------------------------------------------------
    # RECORD ACTION
    # --------------------------------------------------------
    history: List[Dict[str, Any]] = list(state.get("actionHistory") or [])
    history.append({
        "locationIndex": loc_idx,
        "choiceIndex":   choice_idx,
        "choiceText":    choice.get("text", ""),
        "choiceType":    choice.get("type", ""),
    })
    state["actionHistory"] = history

    # --------------------------------------------------------
    # ADVANCE LOCATION
    # --------------------------------------------------------
    next_loc = loc_idx + 1
    if next_loc < len(LOCATIONS):
        state["locationIndex"] = next_loc
        state["day"]           = int(LOCATIONS[next_loc]["day"])
    else:
        state["locationIndex"] = next_loc

    # --------------------------------------------------------
    # END STATE DETECTION
    # --------------------------------------------------------
    health:  int = state.get("health")          or 0
    energy:  int = state.get("energy")          or 0
    trust:   int = state.get("guideTrust")      or 0
    acclim:  int = state.get("acclimatization") or 0
    storm:   int = state.get("stormPressure")   or 0
    loc_now: int = state.get("locationIndex")   or 0

    if loc_now >= len(LOCATIONS):
        state["endState"] = "victory"
    elif health <= 0 or energy <= 0:
        state["endState"] = "death"
    elif trust <= 0 or acclim <= 0:
        state["endState"] = "evacuation"
    elif storm >= 100 and loc_now >= 3:
        state["endState"] = "death"
    else:
        state["endState"] = None

    return state