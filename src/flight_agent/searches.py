def build_route_id(origin: str, destination: str) -> str:
    """Devuelve el identificador limpio de la ruta, por ejemplo LIM-CUZ."""
    return f"{origin.strip().upper()}-{destination.strip().upper()}"


def build_search_id(
    origin: str,
    destination: str,
    trip_type: str,
    outbound_date: str,
    return_date: str | None = None,
) -> str:
    """Construye una identidad estable para una consulta de vuelos.

    La ruta identifica el trayecto. La busqueda agrega tipo y fechas, lo que
    permite monitorear el mismo trayecto varias veces sin sobrescribirlo.
    """
    route_id = build_route_id(origin, destination)
    normalized_trip_type = trip_type.strip().lower()

    if normalized_trip_type == "one_way":
        return f"{route_id}__OW__{outbound_date}"

    if normalized_trip_type == "round_trip":
        if not return_date:
            raise ValueError("return_date es obligatorio para round_trip")
        return f"{route_id}__RT__{outbound_date}__{return_date}"

    raise ValueError("trip_type debe ser 'one_way' o 'round_trip'")
