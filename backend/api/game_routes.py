# backend/api/game_routes.py

from __future__ import annotations
import asyncio
import json
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.graph.pipeline import game_graph
from backend.graph.state import GameState

router = APIRouter()


class GameRequest(BaseModel):
    state: Dict[str, Any]


def ndjson_line(event: Dict[str, Any]) -> str:
    """One JSON object per line — matches frontend NDJSON parser."""
    return json.dumps(event) + "\n"


async def run_game_stream(
    client_state: Dict[str, Any],
) -> AsyncGenerator[str, None]:
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
async def play_game(request: GameRequest) -> StreamingResponse:
    return StreamingResponse(
        run_game_stream(request.state),
        media_type="text/plain",
    )