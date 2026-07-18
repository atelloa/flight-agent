from datetime import datetime

import yaml

from src.flight_agent.observability.logging import (
    log_node_start,
    log_node_end,
)
from src.flight_agent.state import FlightMonitorState


OVERRIDABLE_GLOBAL_CONFIG_KEYS = (
    "fetch_mode",
    "claude_mode",
    "telegram_enabled",
    "review_mode",
)


def route_metadata(route: str, values: dict) -> tuple[str, str, str]:
    parts = route.split("-")
    inferred_trip_type = "round_trip" if parts[-1] == "RT" else "one_way"

    origin = values.get("origin", parts[0])
    destination = values.get("destination", parts[1])
    trip_type = values.get("trip_type", inferred_trip_type)

    return origin, destination, trip_type


def load_config(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Carga configuracion base desde config/routes.yaml y aplica
    overrides temporales de rutas y modos globales para una corrida.

    Lee: config/routes.yaml, state.routes_overrides y state.config_overrides
    Escribe: state.routes_config y state.global_config
    """
    start_time = log_node_start(
        state,
        "load_config",
        "Cargando configuracion..."
    )

    with open("config/routes.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    routes_source = state.routes_overrides or config["routes"]

    # Construir rutas efectivas para esta corrida
    state.routes_config = {}
    state.global_config["preferred_dates"] = {}

    for route, values in routes_source.items():
        origin, destination, trip_type = route_metadata(route, values)

        state.routes_config[route] = {
            "origin": origin,
            "destination": destination,
            "trip_type": trip_type,
            "return_date": values.get("return_date"),
            "max_price": values["max_price"],
            "max_stops": values["max_stops"],
        }
        state.global_config["preferred_dates"][route] = datetime.strptime(
            values["date"], "%Y-%m-%d"
        )

    # Cargar config global base
    state.global_config["date_range"] = config["global"]["date_range"]
    state.global_config["review_mode"] = config["global"]["review_mode"]
    state.global_config["fetch_mode"] = config["global"].get("fetch_mode", "live")
    state.global_config["claude_mode"] = config["global"].get("claude_mode", "live")
    state.global_config["telegram_enabled"] = config["global"].get("telegram_enabled", True)

    # Aplicar overrides globales solo para esta corrida
    for key in OVERRIDABLE_GLOBAL_CONFIG_KEYS:
        if key in state.config_overrides:
            state.global_config[key] = state.config_overrides[key]

    print(f"  Rutas cargadas: {list(state.routes_config.keys())}")
    print(f"  Review mode: {state.global_config['review_mode']}")
    print(f"  Fetch mode: {state.global_config['fetch_mode']}")
    print(f"  Claude mode: {state.global_config['claude_mode']}")
    print(f"  Telegram enabled: {state.global_config['telegram_enabled']}")

    if state.routes_overrides:
        print(f"  Rutas temporales aplicadas: {list(state.routes_overrides.keys())}")

    if state.config_overrides:
        print(f"  Overrides globales aplicados: {state.config_overrides}")

    log_node_end(state, "load_config", start_time)
    return state
