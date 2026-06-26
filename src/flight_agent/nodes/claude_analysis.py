from src.flight_agent.state import FlightMonitorState
from src.flight_agent.tools.claude_tool import analizar_con_claude
from src.flight_agent.tools.db import get_price_history


def claude_analysis(state: FlightMonitorState) -> FlightMonitorState:
    """
    NODE: Analiza casos ambiguos con Claude.

    Lee: state.alerts_to_send (tipo=ambiguous)
    Escribe: actualiza tipo a alert/ignore/recheck/needs_review
             agrega claude_confidence, claude_reason, claude_risk_flags
    """
    print("\n[NODE] claude_analysis: analizando casos ambiguos...")

    ambiguos = [a for a in state.alerts_to_send if a["tipo"] == "ambiguous"]

    if not ambiguos:
        print("  Sin casos ambiguos para analizar")
        return state

    print(f"  {len(ambiguos)} casos ambiguos encontrados")

    for alerta in state.alerts_to_send:
        if alerta["tipo"] != "ambiguous":
            continue

        vuelo = alerta["vuelo"]
        config = state.routes_config.get(vuelo.route, {})
        max_price = config.get("max_price", 0)
        historial = get_price_history(vuelo.route)

        print(f"  Analizando {vuelo.flight_number} ({vuelo.route}) a ${vuelo.price}...")

        resultado = analizar_con_claude(vuelo, max_price, historial)

        alerta["tipo"] = resultado["decision"]
        alerta["claude_confidence"] = resultado["confidence"]
        alerta["claude_reason"] = resultado["reason"]
        alerta["claude_risk_flags"] = resultado.get("risk_flags", [])

        print(f"    → {resultado['decision']} (confianza: {resultado['confidence']})")
        print(f"    → {resultado['reason']}")

    return state