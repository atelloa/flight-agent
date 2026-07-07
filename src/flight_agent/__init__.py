AIRLINE_CATALOG = {
    "easyjet": {"airline_type": "low_cost", "source": "manual_reference"},
    "flybondi": {"airline_type": "low_cost", "source": "manual_reference"},
    "french bee": {"airline_type": "low_cost", "source": "manual_reference"},
    "frontier": {"airline_type": "low_cost", "source": "manual_reference"},
    "frontier airlines": {"airline_type": "low_cost", "source": "manual_reference"},
    "iberia express": {"airline_type": "low_cost", "source": "manual_reference"},
    "jet smart": {"airline_type": "low_cost", "source": "manual_reference"},
    "jetsmart": {"airline_type": "low_cost", "source": "manual_reference"},
    "level": {"airline_type": "low_cost", "source": "manual_reference"},
    "norse atlantic": {"airline_type": "low_cost", "source": "manual_reference"},
    "norse atlantic airways": {"airline_type": "low_cost", "source": "manual_reference"},
    "norwegian": {"airline_type": "low_cost", "source": "manual_reference"},
    "play": {"airline_type": "low_cost", "source": "manual_reference"},
    "ryanair": {"airline_type": "low_cost", "source": "manual_reference"},
    "sky": {"airline_type": "low_cost", "source": "manual_reference"},
    "sky airline": {"airline_type": "low_cost", "source": "manual_reference"},
    "sky airlines": {"airline_type": "low_cost", "source": "manual_reference"},
    "spirit": {"airline_type": "low_cost", "source": "manual_reference"},
    "spirit airlines": {"airline_type": "low_cost", "source": "manual_reference"},
    "viva aerobus": {"airline_type": "low_cost", "source": "manual_reference"},
    "viva air": {"airline_type": "low_cost", "source": "manual_reference"},
    "volaris": {"airline_type": "low_cost", "source": "manual_reference"},
    "vueling": {"airline_type": "low_cost", "source": "manual_reference"},
    "wizz air": {"airline_type": "low_cost", "source": "manual_reference"},
}


def normalize_airline_name(airline: str | None) -> str:
    if airline is None:
        return ""

    return " ".join(airline.strip().lower().split())


def get_airline_metadata(airline: str | None) -> dict:
    normalized_airline = normalize_airline_name(airline)

    default_metadata = {
        "airline_type": "standard_or_unknown",
        "source": "not_found_in_catalog",
    }

    return AIRLINE_CATALOG.get(normalized_airline, default_metadata)


def enrich_offer_with_airline_metadata(offer: dict) -> dict:
    enriched_offer = dict(offer)
    metadata = get_airline_metadata(enriched_offer.get("airline"))
    airline_type = metadata["airline_type"]

    enriched_offer["airline_type"] = airline_type
    enriched_offer["airline_type_source"] = metadata["source"]
    enriched_offer["is_low_cost"] = airline_type == "low_cost"

    return enriched_offer
