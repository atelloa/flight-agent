import sqlite3
from datetime import datetime
from src.flight_agent.state import Flight


DB_PATH = "data/flight_agent.sqlite"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Crea las tablas si no existen"""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            id          TEXT,
            flight_number TEXT,
            route       TEXT,
            price       REAL,
            date        TEXT,
            airline     TEXT,
            stops       INTEGER,
            searched_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            flight_id   TEXT,
            route       TEXT,
            price       REAL,
            tipo        TEXT,
            mensaje     TEXT,
            decided_at  TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS review_queue (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id   TEXT,
            flight_number TEXT,
            route       TEXT,
            price       REAL,
            airline     TEXT,
            stops       INTEGER,
            motivo      TEXT,
            estado      TEXT DEFAULT 'pendiente',
            created_at  TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL UNIQUE,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            duration_seconds REAL,
            fetch_mode TEXT,
            claude_mode TEXT,
            telegram_enabled INTEGER,
            flights_found INTEGER DEFAULT 0,
            alerts_generated INTEGER DEFAULT 0,
            error_message TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_flights(flights: list, searched_at: datetime):
    """Guarda vuelos encontrados en esta ejecucion"""
    conn = get_connection()
    for vuelo in flights:
        conn.execute("""
            INSERT INTO flights VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vuelo.id,
            vuelo.flight_number,
            vuelo.route,
            vuelo.price,
            str(vuelo.date),
            vuelo.airline,
            vuelo.stops,
            str(searched_at),
        ))
    conn.commit()
    conn.close()


def save_decisions(alerts: list, decided_at: datetime):
    """Guarda decisiones tomadas en esta ejecucion"""
    conn = get_connection()
    for alerta in alerts:
        vuelo = alerta["vuelo"]
        conn.execute("""
            INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?)
        """, (
            vuelo.id,
            vuelo.route,
            vuelo.price,
            alerta["tipo"],
            alerta["mensaje"],
            str(decided_at),
        ))
    conn.commit()
    conn.close()


def get_price_history(route: str) -> list:
    """Lee historico de precios de una ruta"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT price, searched_at
        FROM flights
        WHERE route = ?
        ORDER BY searched_at DESC
        LIMIT 30
    """, (route,)).fetchall()
    conn.close()
    return [{"price": r["price"], "searched_at": r["searched_at"]} for r in rows]

def save_review_queue(alerts: list, created_at: datetime):
    """Guarda vuelos que necesitan revision humana"""
    conn = get_connection()
    for alerta in alerts:
        vuelo = alerta["vuelo"]
        conn.execute("""
            INSERT INTO review_queue 
            (flight_id, flight_number, route, price, airline, stops, motivo, estado, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente', ?)
        """, (
            vuelo.id,
            vuelo.flight_number,
            vuelo.route,
            vuelo.price,
            vuelo.airline,
            vuelo.stops,
            alerta["mensaje"],
            str(created_at),
        ))
    conn.commit()
    conn.close()


def get_review_queue() -> list:
    """Lee vuelos pendientes de revision humana"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT *
        FROM review_queue
        WHERE estado = 'pendiente'
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_flights_snapshot() -> list:
    """Lee los vuelos del ultimo snapshot guardado"""
    conn = get_connection()

    last_snapshot = conn.execute("""
        SELECT searched_at
        FROM flights
        ORDER BY searched_at DESC
        LIMIT 1
    """).fetchone()

    if not last_snapshot:
        conn.close()
        return []

    rows = conn.execute("""
        SELECT id, flight_number, route, price, date, airline, stops
        FROM flights
        WHERE searched_at = ?
    """, (last_snapshot["searched_at"],)).fetchall()

    conn.close()

    return [
        Flight(
            id=row["id"],
            flight_number=row["flight_number"],
            route=row["route"],
            price=row["price"],
            date=datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S"),
            airline=row["airline"],
            stops=row["stops"],
        )
        for row in rows
    ]

def save_agent_run(
    run_id: str,
    started_at: str,
    finished_at: str,
    status: str,
    duration_seconds: float,
    fetch_mode: str = None,
    claude_mode: str = None,
    telegram_enabled: bool = None,
    flights_found: int = 0,
    alerts_generated: int = 0,
    error_message: str = None,
):
    """Guarda el resumen de una ejecucion del agente"""
    conn = get_connection()

    conn.execute("""
        INSERT INTO agent_runs (
            run_id,
            started_at,
            finished_at,
            status,
            duration_seconds,
            fetch_mode,
            claude_mode,
            telegram_enabled,
            flights_found,
            alerts_generated,
            error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        started_at,
        finished_at,
        status,
        duration_seconds,
        fetch_mode,
        claude_mode,
        int(telegram_enabled) if telegram_enabled is not None else None,
        flights_found,
        alerts_generated,
        error_message,
    ))

    conn.commit()
    conn.close()