import heapq
from typing import Callable, Dict, List, Optional, Tuple
from src.graph import FlightGraph
from src.models import Route


# Weight extractors – each receives a Route and returns a numeric cost.
WEIGHT_FUNCTIONS: Dict[str, Callable[[Route], float]] = {
    "km": lambda r: r.km,
    "min": lambda r: r.min,
    "price": lambda r: r.price,
}


def dijkstra(
    graph: FlightGraph,
    origin: str,
    destination: str,
    weight: str = "km",
) -> Tuple[Optional[List[str]], float]:
    """
    Find the lowest-cost path between two airports using Dijkstra's algorithm.

    Parameters
    ----------
    graph       : FlightGraph – the loaded flight network
    origin      : str         – IATA code of the departure airport
    destination : str         – IATA code of the arrival airport
    weight      : str         – optimisation metric: ``"km"``, ``"min"``, or
                                ``"price"``  (default: ``"km"``)

    Returns
    -------
    (path, total_cost)
        path       – ordered list of IATA codes from origin to destination,
                     or None if no path exists.
        total_cost – accumulated cost along the optimal path, or inf if
                     unreachable.
    """
    if weight not in WEIGHT_FUNCTIONS:
        raise ValueError(
            f"Unknown weight '{weight}'. Choose from: {list(WEIGHT_FUNCTIONS)}"
        )
    if origin not in graph:
        raise ValueError(f"Origin airport '{origin}' not found in graph.")
    if destination not in graph:
        raise ValueError(f"Destination airport '{destination}' not found in graph.")

    if origin == destination:
        return [origin], 0.0

    get_cost = WEIGHT_FUNCTIONS[weight]

    # dist[iata] = best known cumulative cost to reach that airport
    dist: Dict[str, float] = {iata: float("inf") for iata in graph.all_iata_codes()}
    dist[origin] = 0.0

    # prev[iata] = predecessor IATA on the optimal path
    prev: Dict[str, Optional[str]] = {iata: None for iata in graph.all_iata_codes()}

    # Min-heap: (cost, iata)
    heap: List[Tuple[float, str]] = [(0.0, origin)]

    visited: set = set()

    while heap:
        current_cost, current = heapq.heappop(heap)

        if current in visited:
            continue
        visited.add(current)

        if current == destination:
            break

        for route in graph.get_neighbors(current):
            neighbour = route.iata
            if neighbour not in graph:
                continue
            new_cost = current_cost + get_cost(route)
            if new_cost < dist[neighbour]:
                dist[neighbour] = new_cost
                prev[neighbour] = current
                heapq.heappush(heap, (new_cost, neighbour))

    if dist[destination] == float("inf"):
        return None, float("inf")

    # Reconstruct path by walking backwards through prev
    path: List[str] = []
    node: Optional[str] = destination
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()

    return path, dist[destination]
