from typing import Optional, Literal
from ..graph import FlightGraph
from ..models import RouteResult
from ..algorithms.bfs import bfs_least_hops
from ..algorithms.dijkstra import dijkstra

Mode = Literal["hops", "distance", "time", "price"]

def find_route(graph: FlightGraph, src: str, dst: str, mode: Mode) -> Optional[RouteResult]:
    if not (graph.has(src) and graph.has(dst)):
        return None

    if mode == "hops":
        path = bfs_least_hops(graph, src, dst)
    elif mode == "distance":
        path = dijkstra(graph, src, dst, lambda e: e.km)
    elif mode == "time":
        path = dijkstra(graph, src, dst, lambda e: e.minutes)
    else:
        path = dijkstra(graph, src, dst, lambda e: e.price)

    if not path:
        return None

    total_km = 0.0
    total_minutes = 0
    total_price = 0.0

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge = next((e for e in graph.neighbors(u) if e.dst == v), None)
        if edge is None:
            # If this happens, the path references an edge we can't find (data inconsistency)
            return None

        total_km += float(edge.km)
        total_minutes += int(edge.minutes)
        total_price += float(edge.price)

    return RouteResult(path, round(total_km, 2), total_minutes, round(total_price, 2))