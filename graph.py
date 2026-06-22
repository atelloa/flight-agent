from langgraph.graph import StateGraph, END
from state import FlightMonitorState
from fetch_flights import fetch_flights
from nodes import evaluate_rules, decision_router


def build_graph():
    graph = StateGraph(FlightMonitorState)

    graph.add_node("fetch", fetch_flights)
    graph.add_node("evaluate", evaluate_rules)
    graph.add_node("router", decision_router)

    graph.add_edge("fetch", "evaluate")
    graph.add_edge("evaluate", "router")
    graph.add_edge("router", END)

    graph.set_entry_point("fetch")

    return graph.compile()


compiled_graph = build_graph()