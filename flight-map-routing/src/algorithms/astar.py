# src/algorithms/astar.py
import heapq
from typing import Callable, Dict, List, Optional, Tuple
from math import radians, sin, cos, sqrt, atan2

from ..graph import FlightGraph
from ..models import Edge

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine formula for great-circle distance heuristic"""
    R = 6371  # Earth's radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def astar_shortest_path(graph: FlightGraph, start: str, goal: str, 
                        weight: Callable[[Edge], float]) -> Optional[List[str]]:
    """A* algorithm with haversine heuristic - more efficient than Dijkstra"""
    
    def heuristic(node: str) -> float:
        # Estimate remaining distance using great-circle distance
        if node not in graph.airports or goal not in graph.airports:
            return 0
        a1 = graph.airports[node]
        a2 = graph.airports[goal]
        return haversine(a1.lat, a1.lon, a2.lat, a2.lon)
    
    # Implementation with f = g + h
    g_score: Dict[str, float] = {start: 0.0}
    f_score: Dict[str, float] = {start: heuristic(start)}
    prev: Dict[str, str] = {}
    open_set = [(f_score[start], start)]
    closed_set = set()
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current == goal:
            # Reconstruct path
            path = [goal]
            while current in prev:
                current = prev[current]
                path.append(current)
            return list(reversed(path))
        
        if current in closed_set:
            continue
            
        closed_set.add(current)
        
        for edge in graph.neighbors(current):
            neighbor = edge.dst
            tentative_g = g_score[current] + weight(edge)
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                prev[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None