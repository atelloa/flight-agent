from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from src.flight_agent.graph import compiled_graph
from src.flight_agent.persistence.agent_runs import (
    finish_agent_run,
    migrate_legacy_agent_run_statuses,
    start_agent_run,
)
from src.flight_agent.persistence.db import create_tables
from src.flight_agent.state import FlightMonitorState


OVERRIDABLE_CONFIG_KEYS = {
    "fetch_mode",
    "claude_mode",
    "telegram_enabled",
    "review_mode",
}

ROUTE_CONFIG_KEYS = {
    "origin",
    "destination",
    "trip_type",
    "date",
    "return_date",
    "max_price",
    "max_stops",
}

REQUIRED_ROUTE_CONFIG_KEYS = {
    "date",
    "max_price",
    "max_stops",
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
    effective_routes: dict
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


def parse_route_id(route: str) -> tuple[str, str, str]:
    parts = route.split("-")

    if len(parts) == 2:
        origin, destination = parts
        trip_type = "one_way"
    elif len(parts) == 3 and parts[2] == "RT":
        origin, destination = parts[:2]
        trip_type = "round_trip"
    else:
        raise ValueError(
            f"Ruta invalida '{route}': use LIM-CUZ o LIM-CUZ-RT"
        )

    if any(len(code) != 3 or not code.isalpha() for code in (origin, destination)):
        raise ValueError(
            f"Ruta invalida '{route}': use codigos IATA de tres letras"
        )

    return origin, destination, trip_type


def validate_routes_overrides(routes_overrides: dict | None) -> dict:
    if routes_overrides is None:
        return {}

    if not isinstance(routes_overrides, dict) or not routes_overrides:
        raise ValueError("Debe enviarse al menos una ruta")

    if len(routes_overrides) > 10:
        raise ValueError("Se permiten como maximo 10 rutas por corrida")

    validated_routes = {}

    for raw_route, raw_config in routes_overrides.items():
        route = str(raw_route).strip().upper()

        if not isinstance(raw_config, dict):
            raise ValueError(f"Configuracion invalida para la ruta {route}")

        unknown_keys = set(raw_config) - ROUTE_CONFIG_KEYS
        missing_keys = REQUIRED_ROUTE_CONFIG_KEYS - set(raw_config)

        if unknown_keys:
            unknown = ", ".join(sorted(unknown_keys))
            raise ValueError(f"Campos no permitidos en {route}: {unknown}")

        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"Faltan campos en {route}: {missing}")

        fallback_origin, fallback_destination, fallback_trip_type = parse_route_id(route)

        origin = str(raw_config.get("origin", fallback_origin)).strip().upper()
        destination = str(
            raw_config.get("destination", fallback_destination)
        ).strip().upper()
        trip_type = str(
            raw_config.get("trip_type", fallback_trip_type)
        ).strip().lower()

        if any(
            len(code) != 3 or not code.isalpha()
            for code in (origin, destination)
        ):
            raise ValueError(f"Ruta invalida '{route}': codigos IATA invalidos")

        if origin == destination:
            raise ValueError(f"Ruta invalida '{route}': origen y destino son iguales")

        if trip_type not in {"one_way", "round_trip"}:
            raise ValueError(
                f"trip_type de {route} debe ser 'one_way' o 'round_trip'"
            )

        expected_route = (
            f"{origin}-{destination}-RT"
            if trip_type == "round_trip"
            else f"{origin}-{destination}"
        )
        if route != expected_route:
            raise ValueError(
                f"El identificador {route} no coincide con la configuracion; "
                f"se esperaba {expected_route}"
            )

        if expected_route in validated_routes:
            raise ValueError(f"Ruta duplicada: {expected_route}")

        date_value = str(raw_config["date"])
        try:
            outbound_date = datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError as error:
            raise ValueError(
                f"Fecha invalida para {route}: use YYYY-MM-DD"
            ) from error

        raw_return_date = raw_config.get("return_date")
        return_date_value = None

        if trip_type == "round_trip":
            if not raw_return_date:
                raise ValueError(f"return_date es obligatorio para {route}")

            return_date_value = str(raw_return_date)
            try:
                return_date = datetime.strptime(return_date_value, "%Y-%m-%d")
            except ValueError as error:
                raise ValueError(
                    f"Fecha de regreso invalida para {route}: use YYYY-MM-DD"
                ) from error

            if return_date <= outbound_date:
                raise ValueError(
                    f"La fecha de regreso de {route} debe ser posterior a la ida"
                )
        elif raw_return_date not in (None, ""):
            raise ValueError(
                f"return_date solo se permite para rutas round_trip: {route}"
            )

        max_price = raw_config["max_price"]
        if isinstance(max_price, bool) or not isinstance(max_price, (int, float)):
            raise ValueError(f"max_price de {route} debe ser numerico")
        if max_price <= 0:
            raise ValueError(f"max_price de {route} debe ser mayor que 0")

        max_stops = raw_config["max_stops"]
        if isinstance(max_stops, bool) or not isinstance(max_stops, int):
            raise ValueError(f"max_stops de {route} debe ser entero")
        if max_stops < 0 or max_stops > 5:
            raise ValueError(f"max_stops de {route} debe estar entre 0 y 5")

        validated_routes[expected_route] = {
            "origin": origin,
            "destination": destination,
            "trip_type": trip_type,
            "date": date_value,
            "return_date": return_date_value,
            "max_price": float(max_price),
            "max_stops": max_stops,
        }

    return validated_routes


def build_effective_routes(state: FlightMonitorState) -> dict:
    preferred_dates = state.global_config.get("preferred_dates", {})
    effective_routes = {}

    for route, route_config in state.routes_config.items():
        preferred_date = preferred_dates.get(route)
        effective_routes[route] = {
            "origin": route_config.get("origin"),
            "destination": route_config.get("destination"),
            "trip_type": route_config.get("trip_type", "one_way"),
            "date": (
                preferred_date.strftime("%Y-%m-%d")
                if preferred_date is not None
                else None
            ),
            "return_date": route_config.get("return_date"),
            "max_price": route_config.get("max_price"),
            "max_stops": route_config.get("max_stops"),
        }

    return effective_routes


class AgentRunner:
    """Executes one full flight-agent run.

    This application-level runner is shared by entry points such as the CLI,
    the API and, in a future sprint, a background worker.
    """

    def run(
        self,
        config_overrides: dict | None = None,
        routes_overrides: dict | None = None,
        raise_on_error: bool = True,
        run_id: str | None = None,
    ) -> AgentRunResult:
        validated_overrides = validate_config_overrides(config_overrides)
        validated_routes = validate_routes_overrides(routes_overrides)
        create_tables()
        migrate_legacy_agent_run_statuses()

        state = FlightMonitorState()
        state.run_id = run_id or str(uuid4())[:8]
        state.config_overrides = validated_overrides
        state.routes_overrides = validated_routes

        started_at = datetime.now()
        start_agent_run(
            run_id=state.run_id,
            started_at=str(started_at),
            requested_routes=validated_routes or None,
        )

        run_start = perf_counter()
        result = None
        run_status = "running"
        error_message = None
        captured_error = None

        try:
            result = compiled_graph.invoke(state)
            run_status = "completed"

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
            effective_routes = build_effective_routes(state)

            finish_agent_run(
                run_id=state.run_id,
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
                effective_routes=effective_routes,
            )

        run_result = AgentRunResult(
            run_id=state.run_id,
            status=run_status,
            duration_seconds=run_duration,
            flights_found=flights_found,
            alerts_generated=alerts_generated,
            recoverable_errors_count=recoverable_errors_count,
            effective_config=effective_config,
            effective_routes=effective_routes,
            error_message=error_message,
            result=result,
        )

        if captured_error and raise_on_error:
            raise captured_error

        return run_result


def run_agent(
    config_overrides: dict | None = None,
    routes_overrides: dict | None = None,
    raise_on_error: bool = True,
    run_id: str | None = None,
) -> AgentRunResult:
    return AgentRunner().run(
        config_overrides=config_overrides,
        routes_overrides=routes_overrides,
        raise_on_error=raise_on_error,
        run_id=run_id,
    )
