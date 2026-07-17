import json

from src.flight_agent.persistence.db import create_tables, get_connection


FINAL_RUN_STATUSES = {"completed", "failed"}


def ensure_agent_runs_schema() -> None:
    """Asegura la tabla y agrega columnas evolutivas sin recrearla."""
    create_tables()
    conn = get_connection()
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(agent_runs)").fetchall()
    }

    if "routes_json" not in columns:
        conn.execute("ALTER TABLE agent_runs ADD COLUMN routes_json TEXT")

    conn.commit()
    conn.close()


def migrate_legacy_agent_run_statuses() -> None:
    """Normaliza corridas historicas que usaban el estado success."""
    ensure_agent_runs_schema()
    conn = get_connection()
    conn.execute(
        """
        UPDATE agent_runs
        SET status = 'completed'
        WHERE status = 'success'
        """
    )
    conn.commit()
    conn.close()


def serialize_routes(routes: dict | None) -> str | None:
    if routes is None:
        return None
    return json.dumps(routes, ensure_ascii=False, sort_keys=True)


def deserialize_routes(routes_json: str | None) -> dict:
    if not routes_json:
        return {}
    return json.loads(routes_json)


def start_agent_run(
    run_id: str,
    started_at: str,
    requested_routes: dict | None = None,
) -> None:
    """Registra una corrida como running antes de ejecutar LangGraph.

    Si en el futuro la corrida ya existe como queued, la transiciona a
    running conservando el mismo run_id.
    """
    ensure_agent_runs_schema()
    conn = get_connection()
    routes_json = serialize_routes(requested_routes)

    existing_run = conn.execute(
        """
        SELECT status
        FROM agent_runs
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()

    if existing_run is None:
        conn.execute(
            """
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
                error_message,
                recoverable_errors_count,
                routes_json
            )
            VALUES (?, ?, NULL, 'running', NULL, NULL, NULL, NULL, 0, 0, NULL, 0, ?)
            """,
            (run_id, started_at, routes_json),
        )
    elif existing_run["status"] == "queued":
        conn.execute(
            """
            UPDATE agent_runs
            SET
                started_at = ?,
                finished_at = NULL,
                status = 'running',
                duration_seconds = NULL,
                error_message = NULL,
                routes_json = COALESCE(?, routes_json)
            WHERE run_id = ?
            """,
            (started_at, routes_json, run_id),
        )
    else:
        conn.close()
        raise ValueError(
            f"run_id {run_id} ya existe con status {existing_run['status']}"
        )

    conn.commit()
    conn.close()


def finish_agent_run(
    run_id: str,
    finished_at: str,
    status: str,
    duration_seconds: float,
    fetch_mode: str | None = None,
    claude_mode: str | None = None,
    telegram_enabled: bool | None = None,
    flights_found: int = 0,
    alerts_generated: int = 0,
    error_message: str | None = None,
    recoverable_errors_count: int = 0,
    effective_routes: dict | None = None,
) -> None:
    """Finaliza una corrida existente como completed o failed."""
    if status not in FINAL_RUN_STATUSES:
        raise ValueError("status final debe ser 'completed' o 'failed'")

    ensure_agent_runs_schema()
    conn = get_connection()
    cursor = conn.execute(
        """
        UPDATE agent_runs
        SET
            finished_at = ?,
            status = ?,
            duration_seconds = ?,
            fetch_mode = ?,
            claude_mode = ?,
            telegram_enabled = ?,
            flights_found = ?,
            alerts_generated = ?,
            error_message = ?,
            recoverable_errors_count = ?,
            routes_json = COALESCE(?, routes_json)
        WHERE run_id = ?
        """,
        (
            finished_at,
            status,
            duration_seconds,
            fetch_mode,
            claude_mode,
            int(telegram_enabled) if telegram_enabled is not None else None,
            flights_found,
            alerts_generated,
            error_message,
            recoverable_errors_count,
            serialize_routes(effective_routes),
            run_id,
        ),
    )

    if cursor.rowcount != 1:
        conn.close()
        raise ValueError(f"No existe agent_run para run_id {run_id}")

    conn.commit()
    conn.close()


def row_to_agent_run(row) -> dict:
    run = dict(row)
    run["effective_routes"] = deserialize_routes(run.pop("routes_json", None))
    return run


def get_agent_runs() -> list:
    ensure_agent_runs_schema()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
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
            error_message,
            recoverable_errors_count,
            routes_json
        FROM agent_runs
        ORDER BY started_at DESC
        """
    ).fetchall()
    conn.close()
    return [row_to_agent_run(row) for row in rows]


def get_agent_run(run_id: str) -> dict | None:
    ensure_agent_runs_schema()
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
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
            error_message,
            recoverable_errors_count,
            routes_json
        FROM agent_runs
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return row_to_agent_run(row)
