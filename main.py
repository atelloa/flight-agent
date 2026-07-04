from src.flight_agent.state import FlightMonitorState
from src.flight_agent.graph import compiled_graph

from datetime import datetime
from src.flight_agent.persistence.db import create_tables, save_agent_run

from uuid import uuid4
from time import perf_counter

create_tables()

state = FlightMonitorState()
state.run_id = str(uuid4())[:8]

print(f"[RUN] run_id: {state.run_id}")

started_at = datetime.now()
run_start = perf_counter()
error_message = None

try:
    result = compiled_graph.invoke(state)
    run_status = "success"

except Exception as error:
    result = None
    run_status = "failed"
    error_message = str(error)
    print(f"\n[RUN {state.run_id}] error={error}")
    raise

finally:
    finished_at = datetime.now()
    run_duration = perf_counter() - run_start
    if result:
        recoverable_errors_count = len(result.get("errors", []))
    else:
        recoverable_errors_count = len(state.errors)

    save_agent_run(
        run_id=state.run_id,
        started_at=str(started_at),
        finished_at=str(finished_at),
        status=run_status,
        duration_seconds=run_duration,
        fetch_mode=state.global_config.get("fetch_mode"),
        claude_mode=state.global_config.get("claude_mode"),
        telegram_enabled=state.global_config.get("telegram_enabled"),
        flights_found=len(result["latest_offers"]) if result else 0,
        alerts_generated=len(result["alerts_to_send"]) if result else 0,
        error_message=error_message,
        recoverable_errors_count=recoverable_errors_count,
    )

    print(f"\n[RUN {state.run_id}] status={run_status} duracion_total={run_duration:.2f}s")

print(f"\n{'='*50}")
print("RESUMEN FINAL")
print(f"{'='*50}")
print(f"Vuelos encontrados : {len(result['latest_offers'])}")
print(f"Validos            : {len(result['rule_matches'])}")
print(f"Rechazados         : {len(result['suspicious_cases'])}")
print(f"Decisiones         : {len(result['alerts_to_send'])}")

print(f"Errores recuperables: {len(result['errors'])}")

if result["errors"]:
    print("\nERRORES RECUPERABLES")
    for error in result["errors"]:
        print(f"- [{error['node']}] {error['type']}: {error['message']}")