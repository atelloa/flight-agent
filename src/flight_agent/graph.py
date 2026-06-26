from langgraph.graph import StateGraph, END
from src.flight_agent.state import FlightMonitorState
from src.flight_agent.nodes.load_config import load_config
from src.flight_agent.nodes.fetch_flights import fetch_flights
from src.flight_agent.nodes.nodes import evaluate_rules, decision_router, store_snapshot, store_decisions, send_alert

def build_graph():
    graph = StateGraph(FlightMonitorState)

    graph.add_node("config", load_config)
    graph.add_node("fetch", fetch_flights)
    graph.add_node("snapshot", store_snapshot)
    graph.add_node("evaluate", evaluate_rules)
    graph.add_node("router", decision_router)
    graph.add_node("decisions", store_decisions)
    graph.add_node("alert", send_alert)

    graph.add_edge("config", "fetch")
    graph.add_edge("fetch", "snapshot")
    graph.add_edge("snapshot", "evaluate")
    graph.add_edge("evaluate", "router")
    graph.add_edge("router", "decisions")
    graph.add_edge("decisions", "alert")
    graph.add_edge("alert", END)

    graph.set_entry_point("config")

    return graph.compile()


compiled_graph = build_graph()