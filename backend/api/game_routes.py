# backend/api/game_routes.py

from __future__ import annotations
import asyncio
import json
from collections import defaultdict
from time import time
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.graph.pipeline import game_graph
from backend.graph.state import GameState

router = APIRouter()

# ============================================================
# RATE LIMITER
# ============================================================
_request_log: defaultdict = defaultdict(list)
MAX_STEPS_PER_HOUR = int(20)
 
def check_rate_limit(ip: str) -> None:
    now = time()
    
    _request_log[ip] = [t for t in _request_log[ip] if now - t < 3600]
    if len(_request_log[ip]) >= MAX_STEPS_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail="Rate limit reached (20 steps/hour). Come back later. I can't afford it!",
        )
    _request_log[ip].append(now)
 

# ============================================================
# REQUEST MODEL
# ============================================================
class GameRequest(BaseModel):
    state: Dict[str, Any]

# ============================================================
# NDJSON HELPER
# ============================================================
def ndjson_line(event: Dict[str, Any]) -> str:
    """One JSON object per line — matches frontend NDJSON parser."""
    return json.dumps(event) + "\n"

 
# ============================================================
# GAME STREAM
# ============================================================  
async def run_game_stream(client_state: Dict[str, Any]) -> AsyncGenerator[str, None]:
    # --------------------------------------------------------
    # ADAPTIVE BRIDGE: Map Frontend camelCase to Backend snake_case
    # --------------------------------------------------------
    typed_state: Dict[str, Any] = {**client_state}
    
    # 1. Extract and sanitize location track positions
    loc_idx = client_state.get("locationIndex", 0)
    
    # 2. DYNAMIC LOOKUP: Prevent the static altitude narration bug!
    # Pull the exact elevation context string from your data map layout
    from backend.graph.data import LOCATIONS
    current_location_data = LOCATIONS[min(loc_idx, len(LOCATIONS) - 1)]
    dynamic_altitude = current_location_data.get("alt", "3,540 m")
    
    # 3. Synchronize variable layout names for LangChain template ingestion
    typed_state["guide_trust"]   = client_state.get("guideTrust", 100)
    typed_state["storm"]         = client_state.get("stormPressure", 0)
    typed_state["trust"]         = client_state.get("guideTrust", 100)
    typed_state["loc"]           = loc_idx
    typed_state["alt"]           = dynamic_altitude  # <-- Now accurately tracks trail elevation!
    
    if "latest_choice_index" in client_state:
        typed_state["latest_choice_index"] = client_state["latest_choice_index"]

    # 4. Initialize or retain persistent inventory counters
    typed_state["inventory"] = client_state.get("inventory", {"water": 3, "diamox": 2, "food": 2, "layers": 1})
    
    try:
        # Pass the bridged dictionary state down into your graph runner
        result: GameState = await game_graph.ainvoke(typed_state)  # type: ignore[arg-type]
    except Exception as exc:
        yield ndjson_line({"type": "error", "payload": {"message": str(exc)}})
        return

    # --------------------------------------------------------
    # STATE PATCH  — EventBus.on('state_patch')
    # --------------------------------------------------------
    yield ndjson_line({
        "type": "state_patch",
        "payload": {
            "health":           result.get("health"),
            "energy":           result.get("energy"),
            "acclimatization": result.get("acclimatization"),
            "guideTrust":       result.get("guideTrust") or result.get("guide_trust") or 100,
            "stormPressure":    result.get("stormPressure") or result.get("storm") or 0,
            "locationIndex":    result.get("locationIndex"),
            "subTurnIndex":     result.get("subTurnIndex") or 0,
            "day":              result.get("day"),
            "endState":         result.get("endState"),
            "relationshipTier": result.get("relationshipTier") or "Wary Observer",
            "tensionModifier":  result.get("tensionModifier") or "Low-Stakes",
            "shortHistoryLog":  result.get("shortHistoryLog") or [],
            "inventory":        result.get("inventory", {"water": 3, "diamox": 2, "food": 2, "layers": 1})
        },
    })
    await asyncio.sleep(0.02)

    # --------------------------------------------------------
    # NARRATION  — EventBus.on('narration')
    # --------------------------------------------------------
    yield ndjson_line({
        "type": "narration",
        "payload": {
            "yak":      result.get("current_yak_narration"),
            "situation": result.get("current_situation_text"),
            "journal":  result.get("current_journal_entry"),
            "audio":    result.get("current_yak_audio") or "",
        },
    })
    await asyncio.sleep(0.02)

    # --------------------------------------------------------
    # CHOICES  — EventBus.on('choices')
    # --------------------------------------------------------
    choices = result.get("current_choices") or []
    if choices:
        yield ndjson_line({"type": "choices", "payload": choices})
        await asyncio.sleep(0.02)

    # --------------------------------------------------------
    # END STATE  — EventBus.on('end_state')
    # --------------------------------------------------------
    end_state = result.get("endState")
    if end_state:
        yield ndjson_line({"type": "end_state", "payload": {"type": end_state}})

    yield ndjson_line({"type": "done", "payload": True})

@router.post("/play")
async def play_game(request: GameRequest, req: Request) -> StreamingResponse:
    check_rate_limit(req.client.host if req.client else "unknown")
    return StreamingResponse(
        run_game_stream(request.state),
        media_type="text/plain",
    )