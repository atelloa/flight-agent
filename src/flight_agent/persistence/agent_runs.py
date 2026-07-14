from src.flight_agent.persistence.db import get_connection


FINAL_RUN_STATUSES = {"completed", "failed"}


def migrate_legacy_agent_run_statuses() -> None:
    """Normaliza corridas historicas que usaban el estado success."""
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


def start_agent_run(run_id: str, started_at: str) -> None:
    """Registra una corrida como running antes de ejecutar LangGraph.

    Si en el futuro la corrida ya existe como queued, la transiciona a
    running conservando el mismo run_id.
    """
    conn = get_connection()

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
                recoverable_errors_count
            )
            VALUES (?, ?, NULL, 'running', NULL, NULL, NULL, NULL, 0, 0, NULL, 0)
            """,
            (run_id, started_at),
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
                error_message = NULL
            WHERE run_id = ?
            """,
            (started_at, run_id),
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
) -> None:
    """Finaliza una corrida existente como completed o failed."""
    if status not in FINAL_RUN_STATUSES:
        raise ValueError("status final debe ser 'completed' o 'failed'")

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
            recoverable_errors_count = ?
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
            run_id,
        ),
    )

    if cursor.rowcount != 1:
        conn.close()
        raise ValueError(f"No existe agent_run para run_id {run_id}")

    conn.commit()
    conn.close()
