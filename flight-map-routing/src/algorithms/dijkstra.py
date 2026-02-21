import heapq
from typing import Callable, Dict, List, Optional, Tuple
from ..graph import FlightGraph
from ..models import Edge

def dijkstra(graph: FlightGraph, start: str, goal: str,
             weight: Callable[[Edge], float]) -> Optional[List[str]]:

    dist: Dict[str, float] = {start: 0.0}
    prev: Dict[str, Tuple[str, Edge]] = {}
    pq = [(0.0, start)]

    while pq:
        d, u = heapq.heappop(pq)
        if u == goal:
            break
        if d != dist.get(u):
            continue

        for e in graph.neighbors(u):
            v = e.dst
            nd = d + weight(e)
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = (u, e)
                heapq.heappush(pq, (nd, v))

    if goal not in dist:
        return None

    path = [goal]
    cur = goal
    while cur != start:
        cur = prev[cur][0]
        path.append(cur)
    path.reverse()
    return path