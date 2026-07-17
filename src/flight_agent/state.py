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

    # Config efectiva por ruta para esta corrida
    routes_config: Dict = field(default_factory=dict)

    # Reemplazo temporal de las rutas base para una sola corrida
    routes_overrides: Dict = field(default_factory=dict)

    # Overrides temporales de modos globales para una sola corrida
    config_overrides: Dict = field(default_factory=dict)

    # Config global efectiva - base YAML + overrides de la corrida
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

    # Errores registrados durante la ejecucion
    errors: List[Dict] = field(default_factory=list)
