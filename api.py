from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.flight_agent.catalogs.airlines import (
    enrich_offer_with_airline_metadata,
    normalize_airline_name,
)
from src.flight_agent.persistence.db import (
    get_agent_runs,
    get_agent_run,
    get_review_queue,
    get_cheapest_offers,
    get_cheapest_offers_for_all_routes,
)
from src.flight_agent.runner import run_agent


class RunOverrides(BaseModel):
    """Temporary configuration overrides for one agent run."""

    model_config = ConfigDict(extra="forbid")

    fetch_mode: Literal["cached", "live"] | None = None
    claude_mode: Literal["mock", "live"] | None = None
    telegram_enabled: bool | None = None
    review_mode: bool | None = None


class RunRequest(BaseModel):
    """Request body for starting one agent run."""

    model_config = ConfigDict(extra="forbid")

    overrides: RunOverrides = Field(default_factory=RunOverrides)


app = FastAPI(title="Flight Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def validate_window(window: str) -> int:
    if window not in ["1d", "7d"]:
        raise HTTPException(
            status_code=400,
            detail="window must be '1d' or '7d'",
        )

    return 1 if window == "1d" else 7


def validate_limit(limit: int) -> None:
    if limit < 1 or limit > 10:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 10",
        )


def apply_offer_filters(offers: list, limit: int, unique_airline: bool) -> list:
    selected_offers = []
    seen_airlines = set()

    for offer in offers:
        if unique_airline:
            airline_key = normalize_airline_name(offer.get("airline"))

            if airline_key in seen_airlines:
                continue

            seen_airlines.add(airline_key)

        selected_offers.append(enrich_offer_with_airline_metadata(offer))

        if len(selected_offers) >= limit:
            break

    return selected_offers


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/runs")
def list_runs():
    return get_agent_runs()


@app.post("/runs")
def create_run(request: RunRequest | None = None):
    overrides = (
        request.overrides.model_dump(exclude_none=True)
        if request is not None
        else {}
    )

    try:
        run_result = run_agent(
            config_overrides=overrides,
            raise_on_error=False,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    response = {
        "run_id": run_result.run_id,
        "status": run_result.status,
        "duration_seconds": run_result.duration_seconds,
        "flights_found": run_result.flights_found,
        "alerts_generated": run_result.alerts_generated,
        "recoverable_errors_count": run_result.recoverable_errors_count,
        "effective_config": run_result.effective_config,
        "error_message": run_result.error_message,
    }

    if run_result.status == "failed":
        return JSONResponse(status_code=500, content=response)

    return response


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
def list_cheapest_offers(
    route_id: str,
    window: str = "7d",
    limit: int = 3,
    unique_airline: bool = False,
):
    window_days = validate_window(window)
    validate_limit(limit)

    candidate_limit = 50 if unique_airline else limit

    offers = get_cheapest_offers(
        route=route_id,
        window_days=window_days,
        limit=candidate_limit,
    )

    filtered_offers = apply_offer_filters(
        offers=offers,
        limit=limit,
        unique_airline=unique_airline,
    )

    return {
        "route": route_id,
        "window": window,
        "limit": limit,
        "unique_airline": unique_airline,
        "offers": filtered_offers,
    }


@app.get("/offers/cheapest")
def list_cheapest_offers_for_all_routes(
    window: str = "7d",
    limit: int = 3,
    unique_airline: bool = False,
):
    window_days = validate_window(window)
    validate_limit(limit)

    candidate_limit = 50 if unique_airline else limit

    routes = get_cheapest_offers_for_all_routes(
        window_days=window_days,
        limit=candidate_limit,
    )

    filtered_routes = []

    for route_group in routes:
        filtered_routes.append({
            "route": route_group["route"],
            "offers": apply_offer_filters(
                offers=route_group["offers"],
                limit=limit,
                unique_airline=unique_airline,
            ),
        })

    return {
        "window": window,
        "limit_per_route": limit,
        "unique_airline": unique_airline,
        "routes": filtered_routes,
    }
