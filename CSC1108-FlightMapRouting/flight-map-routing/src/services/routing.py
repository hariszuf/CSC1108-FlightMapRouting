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

    total_km = total_minutes = total_price = 0

    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        edge = next(e for e in graph.neighbors(u) if e.dst == v)
        total_km += edge.km
        total_minutes += edge.minutes
        total_price += edge.price

    return RouteResult(path, round(total_km,2), total_minutes, round(total_price,2))