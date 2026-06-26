import requests
from datetime import datetime
from src.flight_agent.tools.config import SERP_API_KEY
from src.flight_agent.state import Flight, FlightMonitorState


def parsear_resultado(resultado: dict, route: str) -> Flight:
    """
    Convierte un resultado de SerpAPI en un objeto Flight.
    
    Un resultado tiene:
    - price: precio total
    - total_duration: duración total en minutos
    - flights[]: segmentos del viaje
    """
    segmentos = resultado.get("flights", [])
    primer_segmento = segmentos[0]
    ultimo_segmento = segmentos[-1]

    flight_number = primer_segmento.get("flight_number", "N/A")
    airline = primer_segmento.get("airline", "N/A")
    price = float(resultado.get("price", 0))
    stops = len(segmentos) - 1
    duration_minutes = resultado.get("total_duration", 0)

    departure_time_str = primer_segmento["departure_airport"]["time"]
    arrival_time_str = ultimo_segmento["arrival_airport"]["time"]
    departure_time = datetime.strptime(departure_time_str, "%Y-%m-%d %H:%M")
    arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%d %H:%M")

    return Flight(
        id=f"{route}-{flight_number}",
        flight_number=flight_number,
        route=route,
        price=price,
        date=departure_time,
        airline=airline,
        stops=stops,
    )


def buscar_ruta(departure_id: str, arrival_id: str, date: str) -> list:
    """
    Llama a SerpAPI y devuelve lista de Flight objects.
    """
    route = f"{departure_id}-{arrival_id}"

    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": date,
        "type": 2,
        "api_key": SERP_API_KEY,
    }

    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    if "error" in data:
        print(f"[ERROR] SerpAPI: {data['error']}")
        return []

    vuelos = []
    for resultado in data.get("best_flights", []):
        vuelo = parsear_resultado(resultado, route)
        vuelos.append(vuelo)

    return vuelos


def fetch_flights(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Busca vuelos para todas las rutas configuradas.
    Busca en un rango de fechas (date_range dias antes y despues).

    Lee: state.routes_config y state.global_config
    Escribe: state.latest_offers
    """
    print("\n[NODE] fetch_flights: buscando vuelos...")

    dates = state.global_config.get("preferred_dates", {})
    date_range = state.global_config.get("date_range", 0)

    for route, config in state.routes_config.items():
        departure_id, arrival_id = route.split("-")
        base_date = dates.get(route)

        if not base_date:
            print(f"  [SKIP] {route}: sin fecha configurada")
            continue

        # Generar rango de fechas
        fechas = []
        for delta in range(-date_range, date_range + 1):
            from datetime import timedelta
            fechas.append(base_date + timedelta(days=delta))

        print(f"  Buscando {route} en {len(fechas)} fechas...")

        for fecha in fechas:
            date_str = fecha.strftime("%Y-%m-%d")
            vuelos = buscar_ruta(departure_id, arrival_id, date_str)
            state.latest_offers.extend(vuelos)

            if vuelos:
                print(f"    {date_str}: {len(vuelos)} vuelos")
            else:
                print(f"    {date_str}: sin resultados")

    print(f"[NODE] fetch_flights: total {len(state.latest_offers)} vuelos")
    return state