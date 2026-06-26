from src.flight_agent.state import FlightMonitorState
from src.flight_agent.graph import compiled_graph


state = FlightMonitorState()
result = compiled_graph.invoke(state)

print(f"\n{'='*50}")
print("RESUMEN FINAL")
print(f"{'='*50}")
print(f"Vuelos encontrados : {len(result['latest_offers'])}")
print(f"Validos            : {len(result['rule_matches'])}")
print(f"Rechazados         : {len(result['suspicious_cases'])}")
print(f"Decisiones         : {len(result['alerts_to_send'])}")