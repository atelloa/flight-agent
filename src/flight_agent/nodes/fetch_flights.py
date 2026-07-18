from datetime import datetime, timedelta

import requests

from src.flight_agent.tools.config import SERP_API_KEY
from src.flight_agent.state import Flight, FlightMonitorState
from src.flight_agent.persistence.db import get_latest_flights_snapshot
from src.flight_agent.observability.logging import (
    log_node_start,
    log_node_end,
)


def parsear_resultado(resultado: dict, route: str) -> Flight | None:
    """Convierte un resultado de SerpAPI en un Flight resumido.

    En una busqueda round_trip, ``price`` representa la tarifa combinada
    reportada por Google Flights para ida y vuelta. Los segmentos disponibles
    en esta primera respuesta corresponden a la opcion de salida.
    """
    segmentos = resultado.get("flights", [])
    if not segmentos:
        return None

    primer_segmento = segmentos[0]

    flight_number = primer_segmento.get("flight_number", "N/A")
    airline = primer_segmento.get("airline", "N/A")
    price = float(resultado.get("price", 0))
    stops = len(segmentos) - 1

    departure_time_str = primer_segmento["departure_airport"]["time"]
    departure_time = datetime.strptime(departure_time_str, "%Y-%m-%d %H:%M")

    return Flight(
        id=f"{route}-{flight_number}",
        flight_number=flight_number,
        route=route,
        price=price,
        date=departure_time,
        airline=airline,
        stops=stops,
    )


def buscar_ruta(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    route: str,
    trip_type: str = "one_way",
    return_date: str | None = None,
) -> list:
    """Llama a SerpAPI para una ruta one-way o round-trip."""
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "type": 1 if trip_type == "round_trip" else 2,
        "api_key": SERP_API_KEY,
    }

    if trip_type == "round_trip":
        params["return_date"] = return_date

    response = requests.get(
        "https://serpapi.com/search",
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        print(f"[ERROR] SerpAPI: {data['error']}")
        return []

    vuelos = []
    for resultado in data.get("best_flights", []):
        vuelo = parsear_resultado(resultado, route)
        if vuelo is not None:
            vuelos.append(vuelo)

    return vuelos


def fetch_flights(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Busca vuelos para todas las rutas efectivas de la corrida.
    Busca en un rango de fechas (date_range dias antes y despues).

    Lee: state.routes_config y state.global_config
    Escribe: state.latest_offers
    """
    start_time = log_node_start(
        state,
        "fetch_flights",
        "Buscando vuelos..."
    )

    fetch_mode = state.global_config.get("fetch_mode", "live")
    print(f"  Fetch mode activo: {fetch_mode}")

    if fetch_mode == "cached":
        selected_routes = set(state.routes_config)
        cached_flights = get_latest_flights_snapshot()
        vuelos = [
            vuelo
            for vuelo in cached_flights
            if vuelo.route in selected_routes
        ]
        state.latest_offers.extend(vuelos)

        print(
            f"  [CACHE] Vuelos cargados para las rutas seleccionadas: {len(vuelos)}"
        )
        if not vuelos:
            print(
                "  [CACHE] No hay datos del ultimo snapshot para esas rutas. "
                "Use fetch_mode=live para rutas nuevas o round-trip."
            )
        log_node_end(state, "fetch_flights", start_time)
        return state

    dates = state.global_config.get("preferred_dates", {})
    date_range = state.global_config.get("date_range", 0)

    for route, config in state.routes_config.items():
        departure_id = config["origin"]
        arrival_id = config["destination"]
        trip_type = config.get("trip_type", "one_way")
        base_date = dates.get(route)

        if not base_date:
            print(f"  [SKIP] {route}: sin fecha configurada")
            continue

        base_return_date = None
        if trip_type == "round_trip":
            raw_return_date = config.get("return_date")
            if not raw_return_date:
                print(f"  [SKIP] {route}: sin fecha de regreso")
                continue
            base_return_date = datetime.strptime(raw_return_date, "%Y-%m-%d")

        date_pairs = []
        for delta in range(-date_range, date_range + 1):
            outbound = base_date + timedelta(days=delta)
            returning = (
                base_return_date + timedelta(days=delta)
                if base_return_date is not None
                else None
            )
            date_pairs.append((outbound, returning))

        search_label = "ida y vuelta" if trip_type == "round_trip" else "solo ida"
        print(f"  Buscando {route} ({search_label}) en {len(date_pairs)} fechas...")

        for outbound, returning in date_pairs:
            outbound_str = outbound.strftime("%Y-%m-%d")
            return_str = returning.strftime("%Y-%m-%d") if returning else None

            vuelos = buscar_ruta(
                departure_id=departure_id,
                arrival_id=arrival_id,
                outbound_date=outbound_str,
                route=route,
                trip_type=trip_type,
                return_date=return_str,
            )
            state.latest_offers.extend(vuelos)

            dates_label = (
                f"{outbound_str} -> {return_str}"
                if return_str
                else outbound_str
            )
            if vuelos:
                print(f"    {dates_label}: {len(vuelos)} vuelos")
            else:
                print(f"    {dates_label}: sin resultados")

    print(f"[NODE] fetch_flights: total {len(state.latest_offers)} vuelos")
    log_node_end(state, "fetch_flights", start_time)
    return state
