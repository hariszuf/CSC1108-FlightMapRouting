import json
import os
from src.models import Airport, Route
from src.graph import FlightGraph


def load_graph(data_path: str) -> FlightGraph:
    """
    Load airports and routes from a JSON file and return a FlightGraph.

    Expected JSON structure::

        {
            "<IATA>": {
                "iata": "SIN",
                "name": "...",
                "city_name": "...",
                "country": "...",
                "latitude": 1.36,
                "longitude": 103.99,
                "routes": [
                    {"iata": "KUL", "km": 350, "min": 55, "price": 80},
                    ...
                ]
            },
            ...
        }
    """
    if not os.path.isfile(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(data_path, "r", encoding="utf-8") as fh:
        raw: dict = json.load(fh)

    graph = FlightGraph()

    for iata_code, data in raw.items():
        routes = [
            Route(
                iata=r["iata"],
                km=float(r["km"]),
                min=float(r["min"]),
                price=float(r.get("price", 0.0)),
            )
            for r in data.get("routes", [])
        ]
        airport = Airport(
            iata=data.get("iata", iata_code),
            name=data["name"],
            city_name=data["city_name"],
            country=data["country"],
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            routes=routes,
        )
        graph.add_airport(airport)

    return graph
