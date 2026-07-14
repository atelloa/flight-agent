from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from src.flight_agent.graph import compiled_graph
from src.flight_agent.persistence.db import create_tables, save_agent_run
from src.flight_agent.state import FlightMonitorState


@dataclass
class AgentRunResult:
    run_id: str
    status: str
    duration_seconds: float
    flights_found: int
    alerts_generated: int
    recoverable_errors_count: int
    error_message: str | None
    result: dict | None


class AgentRunner:
    """Executes one full flight-agent run.

    This class is the application-level runner used by different entry points,
    such as the CLI today and the API in a later phase.
    """

    def run(self, raise_on_error: bool = True) -> AgentRunResult:
        create_tables()

        state = FlightMonitorState()
        state.run_id = str(uuid4())[:8]

        started_at = datetime.now()
        run_start = perf_counter()
        result = None
        run_status = "success"
        error_message = None
        captured_error = None

        try:
            result = compiled_graph.invoke(state)

        except Exception as error:
            run_status = "failed"
            error_message = str(error)
            captured_error = error

        finally:
            finished_at = datetime.now()
            run_duration = perf_counter() - run_start

            if result:
                recoverable_errors_count = len(result.get("errors", []))
                flights_found = len(result.get("latest_offers", []))
                alerts_generated = len(result.get("alerts_to_send", []))
            else:
                recoverable_errors_count = len(state.errors)
                flights_found = 0
                alerts_generated = 0

            save_agent_run(
                run_id=state.run_id,
                started_at=str(started_at),
                finished_at=str(finished_at),
                status=run_status,
                duration_seconds=run_duration,
                fetch_mode=state.global_config.get("fetch_mode"),
                claude_mode=state.global_config.get("claude_mode"),
                telegram_enabled=state.global_config.get("telegram_enabled"),
                flights_found=flights_found,
                alerts_generated=alerts_generated,
                error_message=error_message,
                recoverable_errors_count=recoverable_errors_count,
            )

        run_result = AgentRunResult(
            run_id=state.run_id,
            status=run_status,
            duration_seconds=run_duration,
            flights_found=flights_found,
            alerts_generated=alerts_generated,
            recoverable_errors_count=recoverable_errors_count,
            error_message=error_message,
            result=result,
        )

        if captured_error and raise_on_error:
            raise captured_error

        return run_result


def run_agent(raise_on_error: bool = True) -> AgentRunResult:
    return AgentRunner().run(raise_on_error=raise_on_error)
