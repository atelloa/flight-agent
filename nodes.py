def encontrar_barato(agent_state):
    """Encuentra el vuelo más barato en la lista"""
    
    if not agent_state.flights:
        agent_state.decision = "No hay vuelos"
        return agent_state
    
    # Ordenar por precio
    vuelos_ordenados = sorted(agent_state.flights, key=lambda x: x.price)
    
    # El primero es el más barato
    barato = vuelos_ordenados[0]
    
    # Guardar decisión en el estado
    agent_state.decision = f"Mejor opción: {barato.route} a ${barato.price}"
    
    return agent_state

def validar_escalas(agent_state):
    """Valida vuelos según MAX_STOPS Y MAX_PRICE por ruta"""
    
    vuelos_validos = []
    
    for vuelo in agent_state.flights:
        # Obtener config de ESTA ruta
        ruta_config = agent_state.routes_config.get(vuelo.route)
        
        if not ruta_config:
            continue  # Si ruta no está configurada, ignora
        
        # Validar contra los límites de ESTA ruta
        max_stops = ruta_config["max_stops"]
        max_price = ruta_config["max_price"]
        
        # ¿Cumple?
        if vuelo.stops <= max_stops and vuelo.price <= max_price:
            vuelos_validos.append(vuelo)
    
    # Resultado
    if not vuelos_validos:
        agent_state.decision = "RECHAZADO: Ningún vuelo cumple restricciones"
        return agent_state
    
    # Si hay válidos, el más barato
    barato = min(vuelos_validos, key=lambda x: x.price)
    agent_state.decision = f"✓ VÁLIDO: {barato.flight_number} ({barato.route}) a ${barato.price} con {barato.stops} escalas"
    
    return agent_state