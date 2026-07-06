from fastapi import FastAPI, HTTPException
from src.flight_agent.persistence.db import (
    get_agent_runs,
    get_agent_run,
    get_review_queue,
    get_cheapest_offers,
    get_cheapest_offers_for_all_routes,
)

app = FastAPI(title="Flight Agent API")


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/runs")
def list_runs():
    return  get_agent_runs()

@app.get("/runs/{run_id}")
def get_run(run_id: str):
    run = get_agent_run(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return run

@app.get("/review-queue")
def list_review_queue():
    return get_review_queue()

@app.get("/routes/{route_id}/cheapest-offers")
def list_cheapest_offers(route_id: str, window: str = "7d", limit: int = 3):
    if window not in ["1d", "7d"]:
        raise HTTPException(
            status_code=400,
            detail="window must be '1d' or '7d'",
        )

    if limit < 1 or limit > 10:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 10",
        )

    window_days = 1 if window == "1d" else 7

    offers = get_cheapest_offers(
        route=route_id,
        window_days=window_days,
        limit=limit,
    )

    return {
        "route": route_id,
        "window": window,
        "limit": limit,
        "offers": offers,
    }

@app.get("/offers/cheapest")
def list_cheapest_offers_for_all_routes(window: str = "7d", limit: int = 3):
    if window not in ["1d", "7d"]:
        raise HTTPException(
            status_code=400,
            detail="window must be '1d' or '7d'",
        )

    if limit < 1 or limit > 10:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 10",
        )

    window_days = 1 if window == "1d" else 7

    routes = get_cheapest_offers_for_all_routes(
        window_days=window_days,
        limit=limit,
    )

    return {
        "window": window,
        "limit_per_route": limit,
        "routes": routes,
    }