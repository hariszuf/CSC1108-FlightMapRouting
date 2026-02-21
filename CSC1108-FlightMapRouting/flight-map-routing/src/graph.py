from typing import Dict, List
from .models import Airport, Edge

class FlightGraph:
    def __init__(self):
        self.airports: Dict[str, Airport] = {}
        self.adj: Dict[str, List[Edge]] = {}

    def add_airport(self, airport: Airport):
        self.airports[airport.code] = airport
        self.adj.setdefault(airport.code, [])

    def add_edge(self, edge: Edge):
        self.adj.setdefault(edge.src, []).append(edge)

    def neighbors(self, code: str) -> List[Edge]:
        return self.adj.get(code, [])

    def has(self, code: str) -> bool:
        return code in self.airports