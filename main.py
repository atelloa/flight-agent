from src.flight_agent.runner import AgentRunResult, run_agent


def print_summary(run_result: AgentRunResult) -> None:
    print(f"\n[RUN {run_result.run_id}] status={run_result.status} duracion_total={run_result.duration_seconds:.2f}s")

    if run_result.status == "failed":
        print(f"Error fatal: {run_result.error_message}")
        return

    result = run_result.result
    if result is None:
        print("No se genero resultado final.")
        return

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


if __name__ == "__main__":
    run_result = run_agent(raise_on_error=False)
    print_summary(run_result)

    if run_result.status == "failed":
        raise SystemExit(1)
