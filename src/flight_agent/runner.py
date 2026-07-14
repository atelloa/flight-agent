from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from src.flight_agent.graph import compiled_graph
from src.flight_agent.persistence.db import create_tables, save_agent_run
from src.flight_agent.state import FlightMonitorState


OVERRIDABLE_CONFIG_KEYS = {
    "fetch_mode",
    "claude_mode",
    "telegram_enabled",
    "review_mode",
}


@dataclass
class AgentRunResult:
    run_id: str
    status: str
    duration_seconds: float
    flights_found: int
    alerts_generated: int
    recoverable_errors_count: int
    effective_config: dict
    error_message: str | None
    result: dict | None


def validate_config_overrides(config_overrides: dict | None) -> dict:
    overrides = dict(config_overrides or {})

    unknown_keys = set(overrides) - OVERRIDABLE_CONFIG_KEYS
    if unknown_keys:
        unknown = ", ".join(sorted(unknown_keys))
        raise ValueError(f"Overrides no permitidos: {unknown}")

    fetch_mode = overrides.get("fetch_mode")
    if fetch_mode is not None and fetch_mode not in {"cached", "live"}:
        raise ValueError("fetch_mode debe ser 'cached' o 'live'")

    claude_mode = overrides.get("claude_mode")
    if claude_mode is not None and claude_mode not in {"mock", "live"}:
        raise ValueError("claude_mode debe ser 'mock' o 'live'")

    for boolean_key in ("telegram_enabled", "review_mode"):
        if boolean_key in overrides and type(overrides[boolean_key]) is not bool:
            raise ValueError(f"{boolean_key} debe ser true o false")

    return overrides


class AgentRunner:
    """Executes one full flight-agent run.

    This class is the application-level runner used by different entry points,
    such as the CLI today and the API in a later phase.
    """

    def run(
        self,
        config_overrides: dict | None = None,
        raise_on_error: bool = True,
    ) -> AgentRunResult:
        validated_overrides = validate_config_overrides(config_overrides)
        create_tables()

        state = FlightMonitorState()
        state.run_id = str(uuid4())[:8]
        state.config_overrides = validated_overrides

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

            effective_config = {
                key: state.global_config.get(key)
                for key in OVERRIDABLE_CONFIG_KEYS
            }

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
            effective_config=effective_config,
            error_message=error_message,
            result=result,
        )

        if captured_error and raise_on_error:
            raise captured_error

        return run_result


def run_agent(
    config_overrides: dict | None = None,
    raise_on_error: bool = True,
) -> AgentRunResult:
    return AgentRunner().run(
        config_overrides=config_overrides,
        raise_on_error=raise_on_error,
    )
