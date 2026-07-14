from src.flight_agent.runner import create_run_id, run_agent


def print_summary(result: dict) -> None:
    print(f"\n{'='*50}")
    print("RESUMEN FINAL")
    print(f"{'='*50}")
    print(f"Vuelos encontrados : {len(result['latest_offers'])}")
    print(f"Validos            : {len(result['rule_matches'])}")
    print(f"Rechazados         : {len(result['suspicious_cases'])}")
    print(f"Decisiones         : {len(result['alerts_to_send'])}")

    print(f"Errores recuperables: {len(result['errors'])}")

    if result["errors"]:
        print("\nERRORES RECUPERABLES")
        for error in result["errors"]:
            print(f"- [{error['node']}] {error['type']}: {error['message']}")


def main() -> None:
    run_id = create_run_id()
    print(f"[RUN] run_id: {run_id}")

    try:
        agent_run = run_agent(run_id=run_id)
    except Exception as error:
        print(f"\n[RUN {run_id}] error={error}")
        raise

    print(
        f"\n[RUN {agent_run.run_id}] "
        f"status={agent_run.status} "
        f"duracion_total={agent_run.duration_seconds:.2f}s"
    )

    if agent_run.state:
        print_summary(agent_run.state)


if __name__ == "__main__":
    main()
