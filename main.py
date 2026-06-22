from state import FlightMonitorState
from graph import compiled_graph
from datetime import datetime


state = FlightMonitorState()

state.routes_config = {
    "LIM-MAD": {"max_stops": 2, "max_price": 700},
    "MAD-MCO": {"max_stops": 2, "max_price": 500},
    "MCO-LIM": {"max_stops": 2, "max_price": 600},
}

state.global_config["preferred_dates"] = {
    "LIM-MAD": datetime(2026, 11, 15),
    "MAD-MCO": datetime(2026, 11, 23),
    "MCO-LIM": datetime(2026, 11, 29),
}

result = compiled_graph.invoke(state)

print(f"\n{'='*50}")
print("RESUMEN FINAL")
print(f"{'='*50}")
print(f"Vuelos encontrados : {len(result['latest_offers'])}")
print(f"Validos            : {len(result['rule_matches'])}")
print(f"Rechazados         : {len(result['suspicious_cases'])}")
print(f"Decisiones         : {len(result['alerts_to_send'])}")