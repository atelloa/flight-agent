from datetime import datetime

import yaml

from src.flight_agent.observability.logging import (
    log_node_start,
    log_node_end,
)
from src.flight_agent.searches import build_route_id, build_search_id
from src.flight_agent.state import FlightMonitorState


OVERRIDABLE_GLOBAL_CONFIG_KEYS = (
    "fetch_mode",
    "claude_mode",
    "telegram_enabled",
    "review_mode",
)


def build_base_searches(routes_config: dict) -> dict:
    """Convierte las rutas del YAML en búsquedas concretas de solo ida."""
    searches = {}

    for route_id, values in routes_config.items():
        origin, destination = route_id.split("-")
        search_id = build_search_id(
            origin=origin,
            destination=destination,
            trip_type="one_way",
            outbound_date=values["date"],
        )
        searches[search_id] = {
            "search_id": search_id,
            "route_id": build_route_id(origin, destination),
            "origin": origin,
            "destination": destination,
            "trip_type": "one_way",
            "date": values["date"],
            "return_date": None,
            "max_price": values["max_price"],
            "max_stops": values["max_stops"],
        }

    return searches


def load_config(state: FlightMonitorState) -> FlightMonitorState:
    """Carga el YAML base y aplica búsquedas/modos temporales de la corrida.

    Lee: config/routes.yaml, state.routes_overrides y state.config_overrides.
    Escribe: state.routes_config y state.global_config.
    """
    start_time = log_node_start(
        state,
        "load_config",
        "Cargando configuracion..."
    )

    with open("config/routes.yaml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    searches_source = (
        state.routes_overrides
        if state.routes_overrides
        else build_base_searches(config["routes"])
    )

    state.routes_config = {}
    state.global_config["preferred_dates"] = {}

    for search_id, values in searches_source.items():
        state.routes_config[search_id] = {
            "search_id": search_id,
            "route_id": values["route_id"],
            "origin": values["origin"],
            "destination": values["destination"],
            "trip_type": values["trip_type"],
            "return_date": values.get("return_date"),
            "max_price": values["max_price"],
            "max_stops": values["max_stops"],
        }
        state.global_config["preferred_dates"][search_id] = datetime.strptime(
            values["date"], "%Y-%m-%d"
        )

    state.global_config["date_range"] = config["global"]["date_range"]
    state.global_config["review_mode"] = config["global"]["review_mode"]
    state.global_config["fetch_mode"] = config["global"].get("fetch_mode", "live")
    state.global_config["claude_mode"] = config["global"].get("claude_mode", "live")
    state.global_config["telegram_enabled"] = config["global"].get(
        "telegram_enabled",
        True,
    )

    for key in OVERRIDABLE_GLOBAL_CONFIG_KEYS:
        if key in state.config_overrides:
            state.global_config[key] = state.config_overrides[key]

    print(f"  Busquedas cargadas: {list(state.routes_config.keys())}")
    print(f"  Review mode: {state.global_config['review_mode']}")
    print(f"  Fetch mode: {state.global_config['fetch_mode']}")
    print(f"  Claude mode: {state.global_config['claude_mode']}")
    print(f"  Telegram enabled: {state.global_config['telegram_enabled']}")

    if state.routes_overrides:
        print(f"  Busquedas temporales aplicadas: {list(state.routes_overrides.keys())}")

    if state.config_overrides:
        print(f"  Overrides globales aplicados: {state.config_overrides}")

    log_node_end(state, "load_config", start_time)
    return state
