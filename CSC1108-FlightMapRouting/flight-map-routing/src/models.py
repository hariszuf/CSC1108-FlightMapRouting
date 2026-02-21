from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    country: str
    lat: float
    lon: float

@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    km: float
    minutes: int
    price: float

@dataclass
class RouteResult:
    path: List[str]
    total_km: float
    total_minutes: int
    total_price: float

    @property
    def hops(self) -> int:
        return max(0, len(self.path) - 1)

    def pretty(self) -> str:
        return " -> ".join(self.path)