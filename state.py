from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict


@dataclass
class Flight:
    """Un vuelo individual"""
    id: str
    flight_number: str
    route: str
    price: float
    date: datetime
    airline: str
    stops: int = 0


@dataclass
class FlightMonitorState:
    """Expediente completo del agente de monitoreo"""

    # Config por ruta (max precio y escalas)
    routes_config: Dict = field(default_factory=lambda: {
        "LIM-MAD": {"max_stops": 2, "max_price": 700},
        "MAD-MCO": {"max_stops": 2, "max_price": 300},
        "MCO-LIM": {"max_stops": 2, "max_price": 600},
    })

    # Config global (fechas preferidas, rango de días)
    global_config: Dict = field(default_factory=lambda: {
        "date_range": 3,
        "preferred_dates": {},
    })

    # Vuelos encontrados en esta ejecución
    latest_offers: List = field(default_factory=list)

    # Resultados de evaluación
    rule_matches: List = field(default_factory=list)
    suspicious_cases: List = field(default_factory=list)

    # Alertas
    alerts_to_send: List = field(default_factory=list)

    # Auditoría
    run_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)