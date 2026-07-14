from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from src.flight_agent.graph import compiled_graph
from src.flight_agent.persistence.db import create_tables, save_agent_run
from src.flight_agent.state import FlightMonitorState


@dataclass
class AgentRunResult:
    run_id: str
    status: str
    duration_seconds: float
    state: dict[str, Any] | None
    error_message: str | None
    recoverable_errors_count: int


def create_run_id() -> str:
    return str(uuid4())[:8]


def run_agent(run_id: str | None = None) -> AgentRunResult:
    create_tables()

    state = FlightMonitorState()
    state.run_id = run_id or create_run_id()

    started_at = datetime.now()
    run_start = perf_counter()
    error_message = None
    result = None

    try:
        result = compiled_graph.invoke(state)
        run_status = "success"

    except Exception as error:
        run_status = "failed"
        error_message = str(error)
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

    return AgentRunResult(
        run_id=state.run_id,
        status=run_status,
        duration_seconds=run_duration,
        state=result,
        error_message=error_message,
        recoverable_errors_count=recoverable_errors_count,
    )
