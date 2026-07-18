from datetime import datetime, timedelta

import requests

from src.flight_agent.observability.logging import (
    log_node_start,
    log_node_end,
)
from src.flight_agent.persistence.db import get_latest_flights_snapshot
from src.flight_agent.state import Flight, FlightMonitorState
from src.flight_agent.tools.config import SERP_API_KEY


def parsear_resultado(
    resultado: dict,
    route_id: str,
    search_id: str,
) -> Flight | None:
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
        id=f"{search_id}-{flight_number}",
        flight_number=flight_number,
        route=route_id,
        price=price,
        date=departure_time,
        airline=airline,
        stops=stops,
        search_id=search_id,
    )


def buscar_ruta(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    route_id: str,
    search_id: str,
    trip_type: str = "one_way",
    return_date: str | None = None,
) -> list:
    """Llama a SerpAPI para una busqueda one-way o round-trip."""
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
        vuelo = parsear_resultado(
            resultado=resultado,
            route_id=route_id,
            search_id=search_id,
        )
        if vuelo is not None:
            vuelos.append(vuelo)

    return vuelos


def fetch_flights(state: FlightMonitorState) -> FlightMonitorState:
    """Busca vuelos para todas las búsquedas efectivas de la corrida."""
    start_time = log_node_start(
        state,
        "fetch_flights",
        "Buscando vuelos..."
    )

    fetch_mode = state.global_config.get("fetch_mode", "live")
    print(f"  Fetch mode activo: {fetch_mode}")

    if fetch_mode == "cached":
        selected_searches = set(state.routes_config)
        cached_flights = get_latest_flights_snapshot()
        vuelos = [
            vuelo
            for vuelo in cached_flights
            if vuelo.search_id in selected_searches
        ]
        state.latest_offers.extend(vuelos)

        print(
            f"  [CACHE] Vuelos cargados para las busquedas seleccionadas: {len(vuelos)}"
        )
        if not vuelos:
            print(
                "  [CACHE] No hay datos del ultimo snapshot para esas busquedas. "
                "Use fetch_mode=live la primera vez."
            )
        log_node_end(state, "fetch_flights", start_time)
        return state

    dates = state.global_config.get("preferred_dates", {})
    date_range = state.global_config.get("date_range", 0)

    for search_id, config in state.routes_config.items():
        departure_id = config["origin"]
        arrival_id = config["destination"]
        route_id = config["route_id"]
        trip_type = config.get("trip_type", "one_way")
        base_date = dates.get(search_id)

        if not base_date:
            print(f"  [SKIP] {search_id}: sin fecha configurada")
            continue

        base_return_date = None
        if trip_type == "round_trip":
            raw_return_date = config.get("return_date")
            if not raw_return_date:
                print(f"  [SKIP] {search_id}: sin fecha de regreso")
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
        print(
            f"  Buscando {route_id} ({search_label}) "
            f"[{search_id}] en {len(date_pairs)} fechas..."
        )

        for outbound, returning in date_pairs:
            outbound_str = outbound.strftime("%Y-%m-%d")
            return_str = returning.strftime("%Y-%m-%d") if returning else None

            vuelos = buscar_ruta(
                departure_id=departure_id,
                arrival_id=arrival_id,
                outbound_date=outbound_str,
                route_id=route_id,
                search_id=search_id,
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
