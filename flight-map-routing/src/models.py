# src/models.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    country: str
    lat: float
    lon: float
    
    # These will be added by enhancer - using field with default
    facilities: List[str] = field(default_factory=list, compare=False)
    rating: float = 0.0

@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    km: float
    minutes: int
    price: float
    
    # These will be added by enhancer - using field with default
    flights: List[Dict] = field(default_factory=list, compare=False, hash=False)
    seasonal_prices: Dict[str, float] = field(default_factory=dict, compare=False, hash=False)

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