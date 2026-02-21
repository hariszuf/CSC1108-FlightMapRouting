import json
from .graph import FlightGraph
from .models import Airport, Edge

def to_float(x, default=0.0):
    if x is None:
        return float(default)
    try:
        return float(x)
    except (TypeError, ValueError):
        return float(default)

def estimate_price(km: float) -> float:
    return round(30 + 0.12 * km, 2)

def load_graph(path: str) -> FlightGraph:
    g = FlightGraph()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # -----------------------
    # AIRPORT CREATION LOOP
    # -----------------------
    for code, info in data.items():

        lat = to_float(info.get("latitude"), 0.0)
        lon = to_float(info.get("longitude"), 0.0)

        # Skip airports with invalid coordinates
        if lat == 0.0 and lon == 0.0:
            continue  

        airport = Airport(
            code=info.get("iata", code),
            name=info.get("name", code),
            city=info.get("city_name", ""),
            country=info.get("country", ""),
            lat=lat,
            lon=lon,
        )

        g.add_airport(airport)

    # -----------------------
    # EDGE CREATION LOOP
    # -----------------------
    for src, info in data.items():

        if not g.has(src):
            continue

        for r in info.get("routes", []):
            dst = r.get("iata")

            if not dst or not g.has(dst):
                continue

            km = to_float(r.get("km"), 0.0)
            minutes = int(to_float(r.get("min"), 0.0))

            if km <= 0 or minutes <= 0:
                continue

            g.add_edge(Edge(
                src=src,
                dst=dst,
                km=km,
                minutes=minutes,
                price=estimate_price(km)
            ))

    return g