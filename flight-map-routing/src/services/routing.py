from typing import Dict, List, Optional, Tuple
from src.graph import FlightGraph
from src.models import Airport
from src.algorithms.bfs import bfs_least_hops
from src.algorithms.dijkstra import dijkstra, WEIGHT_FUNCTIONS


class RouteResult:
    """Holds the result of a route query."""

    def __init__(
        self,
        path: Optional[List[str]],
        cost: float,
        weight: str,
        graph: FlightGraph,
    ) -> None:
        self.path = path
        self.cost = cost
        self.weight = weight
        self._graph = graph

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def found(self) -> bool:
        """True when a valid path was found."""
        return self.path is not None and len(self.path) > 0

    @property
    def hops(self) -> int:
        """Number of flight legs."""
        return len(self.path) - 1 if self.path else -1

    @property
    def airports(self) -> List[Airport]:
        """Return Airport objects for every IATA code in the path."""
        if not self.path:
            return []
        return [
            self._graph.get_airport(iata)
            for iata in self.path
            if self._graph.get_airport(iata) is not None
        ]

    @property
    def label(self) -> str:
        """Human-readable cost label with units."""
        labels = {
            "km":    f"{self.cost:,.0f} km",
            "min":   _format_duration(self.cost),
            "price": f"USD {self.cost:,.2f}",
            "hops":  f"{self.hops} hop(s)",
        }
        return labels.get(self.weight, str(self.cost))

    def __repr__(self) -> str:
        return (
            f"RouteResult(path={self.path}, cost={self.cost}, "
            f"weight='{self.weight}')"
        )


def _format_duration(minutes: float) -> str:
    """Convert a duration in minutes to a ``Xh Ym`` string."""
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h}h {m}m"


class RoutingService:
    """
    High-level service layer for querying routes.

    Separates algorithm logic from UI concerns.
    """

    def __init__(self, graph: FlightGraph) -> None:
        self._graph = graph

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_least_hops(self, origin: str, destination: str) -> RouteResult:
        """Return the path that minimises the number of flight legs (BFS)."""
        path, hops = bfs_least_hops(self._graph, origin, destination)
        cost = float(hops) if hops >= 0 else float("inf")
        return RouteResult(path, cost, "hops", self._graph)

    def find_shortest_distance(
        self, origin: str, destination: str
    ) -> RouteResult:
        """Return the path that minimises total distance (km) via Dijkstra."""
        path, cost = dijkstra(self._graph, origin, destination, weight="km")
        return RouteResult(path, cost, "km", self._graph)

    def find_shortest_time(
        self, origin: str, destination: str
    ) -> RouteResult:
        """Return the path that minimises total flight time via Dijkstra."""
        path, cost = dijkstra(self._graph, origin, destination, weight="min")
        return RouteResult(path, cost, "min", self._graph)

    def find_cheapest(self, origin: str, destination: str) -> RouteResult:
        """Return the path that minimises total ticket price via Dijkstra."""
        path, cost = dijkstra(self._graph, origin, destination, weight="price")
        return RouteResult(path, cost, "price", self._graph)

    def get_all_airports(self) -> List[Airport]:
        """Return a sorted list of all airports in the network."""
        return sorted(self._graph.all_airports(), key=lambda a: a.iata)

    def get_airport(self, iata: str) -> Optional[Airport]:
        """Return the Airport object for *iata*, or None if not found."""
        return self._graph.get_airport(iata)

    def airport_display_options(self) -> Dict[str, str]:
        """
        Return a mapping of ``"IATA – City (Country)"`` → IATA suitable for
        use in UI dropdowns.
        """
        return {
            f"{a.iata} – {a.city_name}, {a.country}": a.iata
            for a in self.get_all_airports()
        }

    def get_segment_details(
        self, path: List[str]
    ) -> List[Dict]:
        """
        Return per-leg details (km, min, price) for every segment in *path*.
        """
        segments = []
        for i in range(len(path) - 1):
            src = path[i]
            dst = path[i + 1]
            src_airport = self._graph.get_airport(src)
            dst_airport = self._graph.get_airport(dst)
            if src_airport is None or dst_airport is None:
                continue
            for route in src_airport.routes:
                if route.iata == dst:
                    segments.append(
                        {
                            "from": src,
                            "to": dst,
                            "from_city": src_airport.city_name,
                            "to_city": dst_airport.city_name,
                            "km": route.km,
                            "min": route.min,
                            "price": route.price,
                            "duration": _format_duration(route.min),
                        }
                    )
                    break
        return segments
