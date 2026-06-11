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
# 20 steps per IP per hour — enough to finish the game 4x over.
# Keeps one bad actor from draining your API credits.
# In-memory only; resets on container restart (fine for HF Spaces).
# ============================================================
_request_log: defaultdict = defaultdict(list)
MAX_STEPS_PER_HOUR = int(20)
 
def check_rate_limit(ip: str) -> None:
    now = time()
    # We drop entries older than 1 hour
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
    # Cast plain dict to GameState — LangGraph accepts dicts that
    # match the TypedDict shape; cast avoids the pyright error.
    typed_state: GameState = client_state  # type: ignore[assignment]

    try:
        result: GameState = game_graph.invoke(typed_state)  # type: ignore[arg-type]
    except Exception as exc:
        yield ndjson_line({"type": "error", "payload": str(exc)})
        return

    # --------------------------------------------------------
    # STATE PATCH  — EventBus.on('state_patch')
    # --------------------------------------------------------
    yield ndjson_line({
        "type": "state_patch",
        "payload": {
            "health":          result.get("health"),
            "energy":          result.get("energy"),
            "acclimatization": result.get("acclimatization"),
            "guideTrust":      result.get("guideTrust"),
            "stormPressure":   result.get("stormPressure"),
            "locationIndex":   result.get("locationIndex"),
            "day":             result.get("day"),
            "endState":        result.get("endState"),
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


# FastAPI handles the req parameter automatically by dependency injection. So we don't declare it anywhere else.
@router.post("/play")
async def play_game(request: GameRequest, req: Request) -> StreamingResponse:
    check_rate_limit(req.client.host if req.client else "unknown")
    return StreamingResponse(
        run_game_stream(request.state),
        media_type="text/plain",
    )