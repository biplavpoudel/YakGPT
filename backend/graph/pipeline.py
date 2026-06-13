from langgraph.graph import StateGraph, END
from backend.graph.state import GameState
from backend.graph.nodes import (
    apply_deterministic_rules,
    prepare_turn_context,
    generate_llm_narrations,
    build_events,
    route_after_turn
)

workflow = StateGraph(GameState)

workflow.add_node("apply_rules", apply_deterministic_rules)
workflow.add_node("prepare_context", prepare_turn_context)
workflow.add_node("generate_narrations", generate_llm_narrations)
workflow.add_node("build_events", build_events)

workflow.set_entry_point("apply_rules")
workflow.add_edge("apply_rules", "prepare_context")
workflow.add_edge("prepare_context", "generate_narrations")
# workflow.add_edge("generate_narrations", "build_events")

# This intercepts the execution line right after narrations are generated
workflow.add_conditional_edges(
    "generate_narrations",
    route_after_turn,
    {
        "build_events": "build_events",  # If router returns "build_events", go get choice buttons
        END: END                         # If router returns END, stop the engine immediately
    }
)

workflow.add_edge("build_events", END)

# Fiannly, we compile the workflow into an executable app
game_graph = workflow.compile()