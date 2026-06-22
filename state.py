from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Flight:
    """Un vuelo"""
    id: str             # nuestro ID único (V001)
    flight_number: str  # código del vuelo (LA4989, IB1234, etc)
    route: str          # "LIM-MAD"
    price: float        # 450.50
    date: datetime      # cuándo sale
    airline: str        # "LATAM"
    stops: int = 0      # escalas

@dataclass
class AgentState:
    """El cuaderno compartido del agente"""
    flights: list = field(default_factory=list)
    decision: str = ""
    
    # GLOBALES (aplican a todos los viajes)
    global_config: dict = field(default_factory=lambda: {
        "date_range": 3,          # días antes/después a probar
        "preferred_dates": {},    # {"LIM-MAD": datetime, "MAD-USA": datetime, ...}
    })
    
    # POR RUTA (cada tramo tiene sus límites)
    routes_config: dict = field(default_factory=lambda: {
        "LIM-MAD": {"max_stops": 2, "max_price": 700},
        "MAD-USA": {"max_stops": 2, "max_price": 300},
        "USA-LIM": {"max_stops": 2, "max_price": 600},
    })