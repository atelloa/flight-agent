import sqlite3
from datetime import datetime
from state import Flight


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