# backend/domain/game_rules.py

from __future__ import annotations
from typing import Any, Dict, List

from backend.graph.data import LOCATIONS, SCENARIOS
from backend.graph.state import GameState


def clamp(val: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, val))


def compute_narrative_metadata(state: GameState) -> GameState:
    """
    Translates raw stats into narrative descriptors for LLM prompts.
    """
    trust   = state.get("guideTrust", 100)
    loc_idx = state.get("locationIndex", 0)
    storm   = state.get("stormPressure", 0)

    if trust >= 75:
        state["relationshipTier"] = "Protective Companion"
    elif trust >= 45:
        state["relationshipTier"] = "Wary Observer"
    else:
        state["relationshipTier"] = "Resigned Guardian"

    if loc_idx >= 4 or storm >= 80:
        state["tensionModifier"] = "Lethal / Suffocating"
    elif loc_idx >= 2 or storm >= 45:
        state["tensionModifier"] = "Hostile / Dangerous"
    else:
        state["tensionModifier"] = "Low-Stakes / Discomfort"

    return state


def update_rolling_history_log(state: GameState, log_summary: str) -> GameState:
    """Maintains a rolling context window of the last 4 major trail events."""
    if not log_summary:
        return state
        
    history_log = list(state.get("shortHistoryLog") or [])
    loc_idx = min(state.get("locationIndex", 0), len(LOCATIONS) - 1)
    current_loc_name = LOCATIONS[loc_idx]["name"]

    formatted_entry = f"At {current_loc_name} (Day {state.get('day', 1)}): {log_summary}."
    history_log.append(formatted_entry)

    if len(history_log) > 4:
        history_log = history_log[-4:]

    state["shortHistoryLog"] = history_log
    return state


def apply_game_rules(state: GameState) -> GameState:
    # --- PRERUN ACCELERATED END-STATE CHECK ---
    # Prevents index parsing traps when entering victory boundaries
    loc_now: int = state.get("locationIndex") or 0
    if loc_now >= len(LOCATIONS):
        state["endState"] = "victory"
        return state

    choice_idx: int = state.get("latest_choice_index") or 0
    loc_idx:    int = state.get("locationIndex")       or 0
    sub_idx:    int = state.get("subTurnIndex")        or 0

    if loc_idx not in SCENARIOS:
        return state

    sub_scenarios = SCENARIOS[loc_idx]

    if sub_idx >= len(sub_scenarios):
        sub_idx = len(sub_scenarios) - 1
        state["subTurnIndex"] = sub_idx

    scenario = sub_scenarios[sub_idx]
    choices: List[Dict[str, Any]] = scenario.get("choices", [])

    if not choices:
        return state

    if choice_idx < 0 or choice_idx >= len(choices):
        choice_idx = 0

    choice: Dict[str, Any] = choices[choice_idx]

    # --------------------------------------------------------
    # 1. INVENTORY CONSUMPTION + BONUS CALCULATION
    # --------------------------------------------------------
    item_to_consume = choice.get("consumeItem")
    inventory: Dict[str, int] = dict(
        state.get("inventory") or {"water": 3, "diamox": 2, "rations": 2, "layers": 1}
    )
    
    item_bonus_acclim = 0
    empty_pack_penalty_triggered = False

    if item_to_consume:
        if inventory.get(item_to_consume, 0) > 0:
            inventory[item_to_consume] -= 1
            if item_to_consume == "diamox":
                item_bonus_acclim = 15
        else:
            empty_pack_penalty_triggered = True
            state["health"] = clamp((state.get("health") or 100) - 20)

    state["inventory"] = inventory

    # --------------------------------------------------------
    # 2. STAT DELTAS (Combining Base Choice + Item Modifiers)
    # --------------------------------------------------------
    state["health"]          = clamp((state.get("health")          or 100) + (choice.get("deltaHealth") or 0))
    state["energy"]          = clamp((state.get("energy")          or 100) + (choice.get("deltaEnergy") or 0))
    state["acclimatization"] = clamp((state.get("acclimatization") or 75)  + (choice.get("deltaAcclim") or 0) + item_bonus_acclim)
    state["guideTrust"]      = clamp((state.get("guideTrust")      or 100) + (choice.get("deltaTrust")  or 0))
    state["stormPressure"]   = clamp((state.get("stormPressure")   or 0)   + (choice.get("deltaStorm")  or 0))

    flag: Any = choice.get("flag")
    if flag and isinstance(flag, str):
        state[flag] = True

    # --------------------------------------------------------
    # 3. NARRATIVE LOGGING (Clean Priority Resolution)
    # --------------------------------------------------------
    if empty_pack_penalty_triggered:
        log_summary = f"Attempted to use {item_to_consume} but pack was empty. Dehydration and mountain panic set in."
    else:
        log_summary = choice.get("log_summary", choice.get("text", ""))

    state = update_rolling_history_log(state, log_summary)

    history = list(state.get("actionHistory") or [])
    history.append({
        "locationIndex": loc_idx,
        "subTurnIndex":  sub_idx,
        "choiceIndex":   choice_idx,
        "choiceText":    choice.get("text", ""),
        "logSummary":    log_summary,
    })
    state["actionHistory"] = history

    # --------------------------------------------------------
    # 4. MOVEMENT LOGIC
    # --------------------------------------------------------
    is_rest   = choice.get("rest",   False)
    is_travel = choice.get("travel", False)

    if is_rest:
        state["day"]    = (state.get("day") or 1) + 1
        state["energy"] = clamp((state.get("energy") or 100) + 20)
        state["health"] = clamp((state.get("health") or 100) + 10)
    elif is_travel:
        next_loc = loc_idx + 1
        state["locationIndex"] = next_loc
        state["subTurnIndex"]  = 0

        # Enforcing that time moves forward by 1 day, or snaps to the destination's minimum day requirement
        if next_loc < len(LOCATIONS):
            # state["day"] = int(LOCATIONS[next_loc]["day"])
            static_min_day = int(LOCATIONS[next_loc]["day"])
            current_day    = (state.get("day") or 1) + 1
            state["day"]   = max(current_day, static_min_day)
    else:
        if sub_idx + 1 < len(sub_scenarios):
            state["subTurnIndex"] = sub_idx + 1

    # --------------------------------------------------------
    # 5. METADATA + END STATE CRITERIA
    # --------------------------------------------------------
    state = compute_narrative_metadata(state)

    health:  int = state.get("health")          or 0
    energy:  int = state.get("energy")          or 0
    trust:   int = state.get("guideTrust")       or 0
    acclim:  int = state.get("acclimatization")  or 0
    storm:   int = state.get("stormPressure")    or 0
    loc_now = state.get("locationIndex")        or 0

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