from src.flight_agent.state import FlightMonitorState
from src.flight_agent.tools.db import create_tables, save_flights, save_decisions, save_review_queue
from datetime import datetime


def evaluate_rules(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Filtra vuelos según reglas duras por ruta.
    
    Lee: state.latest_offers y state.routes_config
    Escribe: state.rule_matches y state.suspicious_cases
    """
    print("\n[NODE] evaluate_rules: evaluando vuelos...")

    for vuelo in state.latest_offers:
        config = state.routes_config.get(vuelo.route)

        if not config:
            continue

        max_price = config["max_price"]
        max_stops = config["max_stops"]

        cumple_precio = vuelo.price <= max_price
        cumple_escalas = vuelo.stops <= max_stops

        if cumple_precio and cumple_escalas:
            state.rule_matches.append(vuelo)
            print(f"  ✅ {vuelo.flight_number} | {vuelo.route} | ${vuelo.price} | {vuelo.stops} escalas")
        else:
            state.suspicious_cases.append(vuelo)
            print(f"  ❌ {vuelo.flight_number} | {vuelo.route} | ${vuelo.price} | {vuelo.stops} escalas")

    print(f"\n[NODE] evaluate_rules: {len(state.rule_matches)} válidos, {len(state.suspicious_cases)} rechazados")
    return state

def decision_router(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Decide qué acción tomar basado en los resultados de evaluate_rules.

    Lee: state.rule_matches y state.suspicious_cases
    Escribe: state.alerts_to_send
    """
    print("\n[NODE] decision_router: decidiendo...")

    if not state.rule_matches and not state.suspicious_cases:
        print("  → no_match: ningún vuelo cumple restricciones")
        return state

    for vuelo in state.rule_matches:
        alerta = {
            "tipo": "clear_deal",
            "vuelo": vuelo,
            "mensaje": f"{vuelo.flight_number} ({vuelo.route}) a ${vuelo.price} con {vuelo.stops} escalas"
        }
        state.alerts_to_send.append(alerta)
        print(f"  → clear_deal: {alerta['mensaje']}")

    for vuelo in state.suspicious_cases:
        alerta = {
            "tipo": "review",
            "vuelo": vuelo,
            "mensaje": f"{vuelo.flight_number} ({vuelo.route}) a ${vuelo.price} supera límites"
        }
        state.alerts_to_send.append(alerta)
        print(f"  → review: {alerta['mensaje']}")

    print(f"\n[NODE] decision_router: {len(state.alerts_to_send)} decisiones tomadas")
    return state

def store_snapshot(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Guarda raw snapshot de vuelos en SQLite.

    Lee: state.latest_offers (todos los vuelos crudos de SerpAPI)
    Escribe: SQLite tabla flights
    """
    print("\n[NODE] store_snapshot: guardando en SQLite...")

    create_tables()

    now = datetime.now()

    save_flights(state.latest_offers, now)
    print(f"  Guardados: {len(state.latest_offers)} vuelos raw")

    return state

def store_decisions(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Guarda decisiones del router en SQLite.

    Lee: state.alerts_to_send
    Escribe: SQLite tabla decisions
    """
    print("\n[NODE] store_decisions: guardando decisiones...")

    now = datetime.now()

    if state.alerts_to_send:
        save_decisions(state.alerts_to_send, now)
        print(f"  Guardadas: {len(state.alerts_to_send)} decisiones")

    return state
def send_alert(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Envia alertas por Telegram.
    Si review_mode=True: solo envia clear_deal, guarda review en SQLite.
    Si review_mode=False: envia todo por Telegram.

    Lee: state.alerts_to_send y state.global_config
    Escribe: Telegram + SQLite review_queue (si review_mode=True)
    """
    import requests
    from src.flight_agent.tools.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    from src.flight_agent.tools.db import save_review_queue
    from datetime import datetime

    print("\n[NODE] send_alert: enviando alertas...")

    review_mode = state.global_config.get("review_mode", False)

    clear_deals = [a for a in state.alerts_to_send if a["tipo"] == "clear_deal"]
    reviews = [a for a in state.alerts_to_send if a["tipo"] == "review"]

    # Manejar reviews segun review_mode
    if review_mode and reviews:
        save_review_queue(reviews, datetime.now())
        print(f"  {len(reviews)} casos guardados en review_queue")
        reviews_telegram = []  # no enviar por Telegram
    else:
        reviews_telegram = reviews  # enviar por Telegram

    # Si no hay nada que enviar
    if not clear_deals and not reviews_telegram:
        print("  Sin alertas para enviar a Telegram")
        return state

    # Construir mensaje
    mensaje = "✈️ *Flight Monitor Report*\n\n"

    if clear_deals:
        mensaje += "✅ *VUELOS DENTRO DEL PRESUPUESTO:*\n"
        for alerta in clear_deals:
            v = alerta["vuelo"]
            mensaje += f"  {v.flight_number} | {v.route} | ${v.price} | {v.stops} escalas | {v.airline}\n"

    if reviews_telegram:
        mensaje += "\n❌ *VUELOS FUERA DEL PRESUPUESTO:*\n"
        for alerta in reviews_telegram:
            v = alerta["vuelo"]
            mensaje += f"  {v.flight_number} | {v.route} | ${v.price} | {v.stops} escalas | {v.airline}\n"

    # Enviar a Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    })

    if response.status_code == 200:
        print(f"  Alerta enviada a Telegram")
    else:
        print(f"  Error enviando alerta: {response.text}")

    return state