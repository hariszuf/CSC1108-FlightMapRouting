from typing import Dict, List, Optional
from src.models import Airport, Route


class FlightGraph:
    """
    Adjacency-list graph representation of the flight network.

    Each node is an airport (keyed by IATA code).
    Each edge is a direct route stored inside the source Airport's route list.
    """

    def __init__(self) -> None:
        self._airports: Dict[str, Airport] = {}

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_airport(self, airport: Airport) -> None:
        """Add an airport node to the graph."""
        self._airports[airport.iata] = airport

    def add_route(self, source_iata: str, route: Route) -> None:
        """Append a route edge to an existing source airport."""
        if source_iata not in self._airports:
            raise KeyError(f"Airport '{source_iata}' not found in graph.")
        self._airports[source_iata].routes.append(route)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_airport(self, iata: str) -> Optional[Airport]:
        """Return the Airport object for *iata*, or None if not found."""
        return self._airports.get(iata)

    def get_neighbors(self, iata: str) -> List[Route]:
        """Return the list of outgoing routes from airport *iata*."""
        airport = self._airports.get(iata)
        return airport.routes if airport else []

    def all_airports(self) -> List[Airport]:
        """Return all airports in the graph (unordered)."""
        return list(self._airports.values())

    def all_iata_codes(self) -> List[str]:
        """Return all IATA codes present in the graph."""
        return list(self._airports.keys())

    def __contains__(self, iata: str) -> bool:
        return iata in self._airports

    def __len__(self) -> int:
        return len(self._airports)

    def __repr__(self) -> str:
        return f"FlightGraph(airports={len(self._airports)})"
