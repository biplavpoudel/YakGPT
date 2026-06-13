from __future__ import annotations
from typing import Any, Dict, List

from backend.graph.data import LOCATIONS, SCENARIOS
from backend.graph.state import GameState


def clamp(val: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, val))


def compute_narrative_metadata(state: GameState) -> GameState:
    """
    Translates raw stats into clear narrative descriptors for the LLM prompts.
    Provides escalation stakes and relationship tracking context.
    """
    trust = state.get("guideTrust", 100)
    loc_idx = state.get("locationIndex", 0)
    storm = state.get("stormPressure", 0)

    # Compute Dorje's Relationship Tier
    if trust >= 75:
        state["relationshipTier"] = "Protective Companion (Deep professional respect and mutual reliance)"
    elif trust >= 45:
        state["relationshipTier"] = "Wary Observer (Neutral, keeping a close eye on your physical liabilities)"
    else:
        state["relationshipTier"] = "Resigned Guardian (Deeply hostile, views you as an immediate safety hazard)"

    # Compute Environmental Escalation Stakes
    if loc_idx >= 4 or storm >= 80:
        state["tensionModifier"] = "Lethal / Suffocating (Thorong La Pass Death Zone - zero margins, freezing alpine whiteout risk)"
    elif loc_idx >= 2 or storm >= 45:
        state["tensionModifier"] = "Hostile / Dangerous (High Alpine Altitude - hypoxia setting in, body actively deteriorating)"
    else:
        state["tensionModifier"] = "Strenuous / Psychological (Lower Valleys - heavy exertion, acclimating cardiovascular matrix)"

    return state


def update_rolling_history_log(state: GameState, log_summary: str) -> GameState:
    """Maintains a rolling context log window of the last 4 major trail events."""
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
    """
    Processes actions dynamically. Handles stay/rest logic loopbacks, 
    inventory reduction, and validates survival criteria bounds.
    """
    choice_idx: int = state.get("latest_choice_index") or 0
    loc_idx:    int = state.get("locationIndex")       or 0
    sub_idx:    int = state.get("subTurnIndex")        or 0

    if loc_idx not in SCENARIOS:
        return state

    sub_scenarios = SCENARIOS[loc_idx]
    
    # Boundary check: if subTurnIndex gets warped out of bounds, lock it to final event
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
    # 1. DYNAMIC INVENTORY CONSUMPTION CHECK
    # --------------------------------------------------------
    item_to_consume = choice.get("consumeItem")
    inventory = state.get("inventory", {"water": 3, "diamox": 2, "rations": 2})
    
    if item_to_consume:
        if inventory.get(item_to_consume, 0) > 0:
            inventory[item_to_consume] -= 1
            # If they successfully used Diamox, offset upcoming altitude damage
            if item_to_consume == "diamox":
                state["acclimatization"] = clamp(state.get("acclimatization", 50) + 15)
        else:
            # Resource check penalty: Action failed due to an empty pack!
            state["health"] = clamp(state.get("health", 100) - 20)
            choice["deltaTrust"] = choice.get("deltaTrust", 0) - 15
            log_summary = f"Attempted to use {item_to_consume} but your pack was completely empty! Dehydration and panic set in."
            state = update_rolling_history_log(state, log_summary)
    
    state["inventory"] = inventory

    # --------------------------------------------------------
    # 2. APPLY CORE STAT DELTAS
    # --------------------------------------------------------
    state["health"]          = clamp((state.get("health")          or 100) + (choice.get("deltaHealth") or 0))
    state["energy"]          = clamp((state.get("energy")          or 100) + (choice.get("deltaEnergy") or 0))
    state["acclimatization"] = clamp((state.get("acclimatization") or 75)  + (choice.get("deltaAcclim") or 0))
    state["guideTrust"]      = clamp((state.get("guideTrust")      or 100) + (choice.get("deltaTrust")  or 0))
    state["stormPressure"]   = clamp((state.get("stormPressure")   or 0)   + (choice.get("deltaStorm")  or 0))

    # Save state flags
    flag: Any = choice.get("flag")
    if flag and isinstance(flag, str):
        state[flag] = True

    # --------------------------------------------------------
    # 3. NARRATIVE LOGGING
    # --------------------------------------------------------
    log_summary = choice.get("log_summary", choice.get("text", ""))
    state = update_rolling_history_log(state, log_summary)

    history = list(state.get("actionHistory") or [])
    history.append({
        "locationIndex": loc_idx,
        "subTurnIndex":  sub_idx,
        "choiceIndex":   choice_idx,
        "choiceText":    choice.get("text", ""),
        "logSummary":    log_summary
    })
    state["actionHistory"] = history

    # --------------------------------------------------------
    # 4. ADVANCED BRACHING & MOVEMENT LOGIC
    # --------------------------------------------------------
    is_rest_action = choice.get("rest", False)
    is_travel_action = choice.get("travel", False)

    if is_rest_action:
        # Loop back on the same scenario block! Do not advance location or subTurnIndex.
        # This keeps the player at the tea house/inn to buy items, sleep, or re-evaluate.
        state["day"] = state.get("day", 1) + 1
        # Give a small automatic resting recovery baseline
        state["energy"] = clamp(state.get("energy", 100) + 20)
        state["health"] = clamp(state.get("health", 100) + 10)
    
    elif is_travel_action:
        # Player packed their gear and pushed forward to the next base trail node map
        next_loc = loc_idx + 1
        state["locationIndex"] = next_loc
        state["subTurnIndex"] = 0
        if next_loc < len(LOCATIONS):
            state["day"] = int(LOCATIONS[next_loc]["day"])
            
    else:
        # Standard structural micro-encounter scenario progression inside the current camp
        if sub_idx + 1 < len(sub_scenarios):
            state["subTurnIndex"] = sub_idx + 1
        else:
            # If out of micro-events but no direct travel action was forced, default stay put
            # until the explicit "Leave Camp" decision node is intentionally chosen.
            pass

    # --------------------------------------------------------
    # 5. SYNC METADATA & BOUNDARY CHECKS
    # --------------------------------------------------------
    state = compute_narrative_metadata(state)

    health:  int = state.get("health", 0)
    energy:  int = state.get("energy", 0)
    trust:   int = state.get("guideTrust", 0)
    acclim:  int = state.get("acclimatization", 0)
    storm:   int = state.get("stormPressure", 0)
    loc_now: int = state.get("locationIndex", 0)

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