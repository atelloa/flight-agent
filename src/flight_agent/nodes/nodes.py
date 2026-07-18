from datetime import datetime

from src.flight_agent.persistence.db import (
    save_decisions,
    save_flights,
    save_review_queue,
)
from src.flight_agent.state import FlightMonitorState


def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def flight_search_id(flight) -> str:
    """Devuelve la busqueda concreta del vuelo, con fallback historico."""
    return flight.search_id or flight.route


def evaluate_rules(state: FlightMonitorState) -> FlightMonitorState:
    """Filtra vuelos segun las reglas de la busqueda que los produjo."""
    print("\n[NODE] evaluate_rules: evaluando vuelos...")

    for vuelo in state.latest_offers:
        config = state.routes_config.get(flight_search_id(vuelo))

        if not config:
            continue

        max_price = config["max_price"]
        max_stops = config["max_stops"]

        cumple_precio = vuelo.price <= max_price
        cumple_escalas = vuelo.stops <= max_stops

        if cumple_precio and cumple_escalas:
            state.rule_matches.append(vuelo)
            print(
                f"  ✅ {vuelo.flight_number} | {vuelo.route} | "
                f"${vuelo.price} | {vuelo.stops} escalas"
            )
        else:
            state.suspicious_cases.append(vuelo)
            print(
                f"  ❌ {vuelo.flight_number} | {vuelo.route} | "
                f"${vuelo.price} | {vuelo.stops} escalas"
            )

    print(
        f"\n[NODE] evaluate_rules: {len(state.rule_matches)} validos, "
        f"{len(state.suspicious_cases)} rechazados"
    )
    return state


def decision_router(state: FlightMonitorState) -> FlightMonitorState:
    """Decide la accion usando los limites de cada busqueda concreta."""
    print("\n[NODE] decision_router: decidiendo...")

    if not state.rule_matches and not state.suspicious_cases:
        print("  → no_match: ningun vuelo cumple restricciones")
        return state

    todos = state.rule_matches + state.suspicious_cases

    for vuelo in todos:
        config = state.routes_config.get(flight_search_id(vuelo))
        if not config:
            continue

        max_price = config["max_price"]
        limite_bajo = max_price * 0.90
        limite_alto = max_price * 1.10

        if vuelo.price <= limite_bajo:
            alerta = {
                "tipo": "clear_deal",
                "vuelo": vuelo,
                "mensaje": (
                    f"{vuelo.flight_number} ({vuelo.route}) a ${vuelo.price} "
                    f"con {vuelo.stops} escalas"
                ),
            }
            state.alerts_to_send.append(alerta)
            print(f"  → clear_deal: {alerta['mensaje']}")

        elif vuelo.price <= limite_alto:
            alerta = {
                "tipo": "ambiguous",
                "vuelo": vuelo,
                "mensaje": (
                    f"{vuelo.flight_number} ({vuelo.route}) a ${vuelo.price} "
                    f"esta en zona gris (limite ${max_price})"
                ),
            }
            state.alerts_to_send.append(alerta)
            print(f"  → ambiguous: {alerta['mensaje']}")

        else:
            alerta = {
                "tipo": "review",
                "vuelo": vuelo,
                "mensaje": (
                    f"{vuelo.flight_number} ({vuelo.route}) a ${vuelo.price} "
                    "supera limites"
                ),
            }
            state.alerts_to_send.append(alerta)
            print(f"  → review: {alerta['mensaje']}")

    print(f"\n[NODE] decision_router: {len(state.alerts_to_send)} decisiones tomadas")
    return state


def store_snapshot(state: FlightMonitorState) -> FlightMonitorState:
    """Guarda el snapshot crudo de vuelos en SQLite."""
    print(f"\n[{now_ts()}] [RUN {state.run_id}] [NODE store_snapshot] inicio")
    print("  Guardando snapshot...")

    fetch_mode = state.global_config.get("fetch_mode", "live")

    if fetch_mode == "cached":
        print("  [CACHE] Snapshot no guardado porque los vuelos vienen de SQLite")
        return state

    save_flights(state.latest_offers, datetime.now())
    print(f"  Guardados: {len(state.latest_offers)} vuelos raw")
    return state


def store_decisions(state: FlightMonitorState) -> FlightMonitorState:
    """Guarda decisiones del router en SQLite."""
    print("\n[NODE] store_decisions: guardando decisiones...")

    if state.alerts_to_send:
        save_decisions(state.alerts_to_send, datetime.now(), state.run_id)
        print(f"  Guardadas: {len(state.alerts_to_send)} decisiones")

    return state


def send_alert(state: FlightMonitorState) -> FlightMonitorState:
    """Envia alertas por Telegram y deriva revisiones humanas."""
    import requests

    from src.flight_agent.tools.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

    print("\n[NODE] send_alert: enviando alertas...")

    telegram_enabled = state.global_config.get("telegram_enabled", True)
    print(f"  Telegram enabled: {telegram_enabled}")

    if not telegram_enabled:
        print("  [TELEGRAM] Envio desactivado por configuracion")

    review_mode = state.global_config.get("review_mode", False)

    clear_deals = [
        alerta
        for alerta in state.alerts_to_send
        if alerta["tipo"] in ["clear_deal", "alert"]
    ]
    reviews = [
        alerta
        for alerta in state.alerts_to_send
        if alerta["tipo"] in ["review", "needs_review", "recheck"]
    ]

    if review_mode and reviews:
        save_review_queue(reviews, datetime.now(), state.run_id)
        print(f"  {len(reviews)} casos guardados en review_queue")
        reviews_telegram = []
    else:
        reviews_telegram = reviews

    if not clear_deals and not reviews_telegram:
        print("  Sin alertas para enviar a Telegram")
        return state

    if not telegram_enabled:
        return state

    mensaje = "✈️ *Flight Monitor Report*\n\n"

    if clear_deals:
        mensaje += "✅ *VUELOS DENTRO DEL PRESUPUESTO:*\n"
        for alerta in clear_deals:
            vuelo = alerta["vuelo"]
            mensaje += (
                f"  {vuelo.flight_number} | {vuelo.route} | ${vuelo.price} | "
                f"{vuelo.stops} escalas | {vuelo.airline}\n"
            )

    if reviews_telegram:
        mensaje += "\n❌ *VUELOS FUERA DEL PRESUPUESTO:*\n"
        for alerta in reviews_telegram:
            vuelo = alerta["vuelo"]
            mensaje += (
                f"  {vuelo.flight_number} | {vuelo.route} | ${vuelo.price} | "
                f"{vuelo.stops} escalas | {vuelo.airline}\n"
            )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje,
            "parse_mode": "Markdown",
        })

        if response.status_code == 200:
            print("  Alerta enviada a Telegram")
        else:
            error_info = {
                "node": "send_alert",
                "type": "telegram_http_error",
                "message": response.text,
                "status_code": response.status_code,
                "created_at": str(datetime.now()),
            }
            state.errors.append(error_info)
            print(
                "  [ERROR RECUPERABLE] Telegram respondio con error: "
                f"{response.text}"
            )

    except Exception as error:
        error_info = {
            "node": "send_alert",
            "type": "telegram_exception",
            "message": str(error),
            "created_at": str(datetime.now()),
        }
        state.errors.append(error_info)
        print(f"  [ERROR RECUPERABLE] Telegram fallo: {error}")

    return state
