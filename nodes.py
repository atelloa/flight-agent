from state import FlightMonitorState


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