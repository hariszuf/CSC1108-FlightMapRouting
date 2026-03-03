# src/features/enhancer.py
import random
from datetime import datetime, timedelta
from src.models import Edge

class DataEnhancer:
    """Add enhanced features to the flight graph"""
    
    def __init__(self, graph):
        self.graph = graph
    
    def add_flight_schedules(self):
        """Add realistic flight schedules with multiple daily flights"""
        for src in self.graph.airports:
            edges = self.graph.neighbors(src)
            for i, edge in enumerate(edges):
                # Add multiple daily flights with different times
                num_flights = random.randint(1, 5)
                flights = []
                
                base_time = datetime.now().replace(hour=0, minute=0)
                
                for _ in range(num_flights):
                    departure = base_time + timedelta(
                        hours=random.randint(0, 23),
                        minutes=random.choice([0, 15, 30, 45])
                    )
                    
                    flight_time = edge.minutes + random.randint(-10, 10)  # Small variation
                    arrival = departure + timedelta(minutes=max(1, flight_time))
                    
                    flights.append({
                        'flight_number': f"{src}{random.randint(100, 999)}",
                        'departure': departure.strftime("%H:%M"),
                        'arrival': arrival.strftime("%H:%M"),
                        'duration': flight_time,
                        'price': edge.price * random.uniform(0.9, 1.1),  # Price variation
                        'aircraft': random.choice(['B737', 'A320', 'B787', 'A350'])
                    })
                
                # Since Edge is frozen, we need to create a new Edge with flights
                # But that's complex - let's use object.__setattr__ as a workaround
                object.__setattr__(edge, 'flights', sorted(flights, key=lambda x: x['departure']))
    
    def add_airport_facilities(self):
        """Add amenities and facilities for each airport"""
        facilities = ['lounge', 'wifi', 'restaurants', 'shopping', 'hotel', 
                     'parking', 'car_rental', 'public_transport']
        
        for code in self.graph.airports:
            airport = self.graph.airports[code]
            # Use object.__setattr__ for frozen dataclass
            object.__setattr__(airport, 'facilities', 
                              random.sample(facilities, random.randint(3, len(facilities))))
            object.__setattr__(airport, 'rating', round(random.uniform(3.5, 5.0), 1))
    
    def add_seasonal_pricing(self):
        """Add dynamic pricing based on season"""
        for src in self.graph.airports:
            for edge in self.graph.neighbors(src):
                seasonal_prices = {
                    'summer': edge.price * random.uniform(1.1, 1.3),
                    'winter': edge.price * random.uniform(0.9, 1.1),
                    'spring': edge.price * random.uniform(0.8, 1.0),
                    'fall': edge.price * random.uniform(0.8, 1.0)
                }
                object.__setattr__(edge, 'seasonal_prices', seasonal_prices)