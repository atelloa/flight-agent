from src.flight_agent.state import FlightMonitorState
from src.flight_agent.graph import compiled_graph
from uuid import uuid4
from time import perf_counter


state = FlightMonitorState()
state.run_id = str(uuid4())[:8]

print(f"[RUN] run_id: {state.run_id}")

run_start = perf_counter()

try:
    result = compiled_graph.invoke(state)
    run_status = "success"

except Exception as error:
    run_status = "failed"
    print(f"\n[RUN {state.run_id}] error={error}")
    raise

finally:
    run_duration = perf_counter() - run_start
    print(f"\n[RUN {state.run_id}] status={run_status} duracion_total={run_duration:.2f}s")

print(f"\n{'='*50}")
print("RESUMEN FINAL")
print(f"{'='*50}")
print(f"Vuelos encontrados : {len(result['latest_offers'])}")
print(f"Validos            : {len(result['rule_matches'])}")
print(f"Rechazados         : {len(result['suspicious_cases'])}")
print(f"Decisiones         : {len(result['alerts_to_send'])}")