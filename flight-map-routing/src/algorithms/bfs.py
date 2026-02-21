from collections import deque
from typing import Dict, List, Optional
from ..graph import FlightGraph

def bfs_least_hops(graph: FlightGraph, start: str, goal: str) -> Optional[List[str]]:
    if start == goal:
        return [start]

    q = deque([start])
    prev: Dict[str, str] = {start: ""}

    while q:
        u = q.popleft()
        for e in graph.neighbors(u):
            v = e.dst
            if v not in prev:
                prev[v] = u
                if v == goal:
                    q.clear()
                    break
                q.append(v)

    if goal not in prev:
        return None

    path = [goal]
    cur = goal
    while cur != start:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return path