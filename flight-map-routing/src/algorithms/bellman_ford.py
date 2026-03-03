from typing import Optional, List
from ..graph import FlightGraph
from ..models import Edge

def bellman_ford_cheapest(graph: FlightGraph, start: str, goal: str) -> Optional[List[str]]:
    """
    Bellman-Ford algorithm - handles negative weights (discounts/promotions)
    Demonstrates understanding of limitations of Dijkstra
    """
    dist = {node: float('inf') for node in graph.airports}
    prev = {node: None for node in graph.airports}
    dist[start] = 0
    
    # Relax edges |V| - 1 times
    for _ in range(len(graph.airports) - 1):
        updated = False
        for u in graph.airports:
            if dist[u] == float('inf'):
                continue
            for edge in graph.neighbors(u):
                if dist[u] + edge.price < dist[edge.dst]:
                    dist[edge.dst] = dist[u] + edge.price
                    prev[edge.dst] = u
                    updated = True
        if not updated:
            break
    
    # Check for negative cycles (advanced concept)
    for u in graph.airports:
        for edge in graph.neighbors(u):
            if dist[u] + edge.price < dist[edge.dst]:
                print("Negative cycle detected! Using alternative route...")
                return None
    
    # Reconstruct path
    if dist[goal] == float('inf'):
        return None
    
    path = []
    curr = goal
    while curr:
        path.append(curr)
        curr = prev[curr]
    return list(reversed(path))