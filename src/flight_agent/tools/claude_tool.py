import json
import anthropic
from src.flight_agent.tools.db import get_price_history

client = anthropic.Anthropic()


def analizar_con_claude(vuelo, max_price: float, historial: list) -> dict:
    """
    TOOL: Llama a Claude API para analizar un caso ambiguo.
    Devuelve decision estructurada en JSON.
    """
    if historial:
        precios = [f"${h['price']}" for h in historial[:10]]
        historial_texto = f"Historial reciente: {', '.join(precios)}"
    else:
        historial_texto = "Sin historial previo para esta ruta."

    prompt = f"""Eres un analista de precios de vuelos. Analiza este caso y decide si conviene alertar al usuario.

Vuelo:
- Ruta: {vuelo.route}
- Precio actual: ${vuelo.price}
- Escalas: {vuelo.stops}
- Aerolinea: {vuelo.airline}
- Fecha: {vuelo.date}

Configuracion del usuario:
- Precio maximo aceptable: ${max_price}

{historial_texto}

Contexto: Viaje de Thanksgiving 2026. Los precios suelen subir 15-20% en noviembre.

Responde SOLO con un JSON valido, sin texto adicional:
{{
  "decision": "alert | ignore | recheck | needs_review",
  "confidence": 0.0,
  "reason": "explicacion breve en español",
  "risk_flags": []
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = response.content[0].text.strip()

    # Limpiar markdown si Claude lo envuelve en bloques de codigo
    if "```" in texto:
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
        texto = texto.strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return {
            "decision": "needs_review",
            "confidence": 0.0,
            "reason": "Claude no devolvio JSON valido",
            "risk_flags": ["parse_error"]
        }