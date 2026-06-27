from panel import state
import yaml
from datetime import datetime
from src.flight_agent.state import FlightMonitorState


def load_config(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Carga configuracion desde config/routes.yaml.

    Lee: config/routes.yaml
    Escribe: state.routes_config y state.global_config
    """
    print("\n[NODE] load_config: cargando configuracion...")

    with open("config/routes.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Cargar rutas
    state.routes_config = {}
    for route, values in config["routes"].items():
        state.routes_config[route] = {
            "max_price": values["max_price"],
            "max_stops": values["max_stops"],
        }
        state.global_config["preferred_dates"][route] = datetime.strptime(
            values["date"], "%Y-%m-%d"
        )

    # Cargar config global
    state.global_config["date_range"] = config["global"]["date_range"]
    state.global_config["review_mode"] = config["global"]["review_mode"]
    state.global_config["fetch_mode"] = config["global"].get("fetch_mode", "live")
    state.global_config["claude_mode"] = config["global"].get("claude_mode", "live")
    state.global_config["telegram_enabled"] = config["global"].get("telegram_enabled", True)

    print(f"  Rutas cargadas: {list(state.routes_config.keys())}")
    print(f"  Review mode: {state.global_config['review_mode']}")
    print(f"  Fetch mode: {state.global_config['fetch_mode']}")
    print(f"  Claude mode: {state.global_config['claude_mode']}")
    print(f"  Telegram enabled: {state.global_config['telegram_enabled']}")
    return state