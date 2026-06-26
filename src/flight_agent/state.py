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

    # Config por ruta - se carga desde config/routes.yaml
    routes_config: Dict = field(default_factory=dict)

    # Config global - se carga desde config/routes.yaml
    global_config: Dict = field(default_factory=lambda: {
        "date_range": 3,
        "preferred_dates": {},
    })

    # Vuelos encontrados en esta ejecucion
    latest_offers: List = field(default_factory=list)

    # Resultados de evaluacion
    rule_matches: List = field(default_factory=list)
    suspicious_cases: List = field(default_factory=list)

    # Alertas
    alerts_to_send: List = field(default_factory=list)

    # Auditoria
    run_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)