# backend/graph/pipeline.py

from __future__ import annotations
from typing import cast

from langgraph.graph import StateGraph, END
from backend.graph.state import GameState
from backend.graph.nodes import (
    apply_deterministic_rules,
    generate_llm_narrations,
    select_llm_provider,
    build_events,
)


# ============================================================
# GRAPH CONSTRUCTION
# ============================================================
def create_game_graph():
    workflow: StateGraph = StateGraph(GameState)

    # --------------------------------------------------------
    # NODES
    # --------------------------------------------------------
    workflow.add_node("rules",      apply_deterministic_rules)
    workflow.add_node("llm_select", select_llm_provider)
    workflow.add_node("narration",  generate_llm_narrations)
    workflow.add_node("events",     build_events)

    # --------------------------------------------------------
    # ENTRY POINT
    # --------------------------------------------------------
    workflow.set_entry_point("rules")

    # --------------------------------------------------------
    # EDGES  (every node must be reachable)
    # rules → llm_select → narration → events → END
    # --------------------------------------------------------
    workflow.add_edge("rules",      "llm_select")
    workflow.add_edge("llm_select", "narration")
    workflow.add_edge("narration",  "events")   # was → "finalize" (removed)
    workflow.add_edge("events",     END)

    return workflow.compile()


# ============================================================
# SINGLETON
# ============================================================
game_graph = create_game_graph()