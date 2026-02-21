from dataclasses import dataclass, field
from typing import List


@dataclass
class Route:
    """Represents a direct flight route from one airport to another."""
    iata: str        # Destination airport IATA code
    km: float        # Distance in kilometres
    min: float       # Flight duration in minutes
    price: float     # Ticket price in USD


@dataclass
class Airport:
    """Represents an airport node in the flight network."""
    iata: str
    name: str
    city_name: str
    country: str
    latitude: float
    longitude: float
    routes: List[Route] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Airport({self.iata}, {self.city_name}, {self.country})"
