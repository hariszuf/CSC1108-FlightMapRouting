from typing import List, Optional, Dict
from src.algorithms.dijkstra import dijkstra
from src.algorithms.bfs import bfs_least_hops
from src.models import Edge

class RouteExplorer:
    def __init__(self, graph: FlightGraph):
        self.graph = graph
        self.route_cache = {}
    
    def explore_alternatives(self, src: str, dst: str):
        """Generate multiple route options with different trade-offs"""
        alternatives = []
        
        # 1. Shortest distance
        alternatives.append({
            'name': 'Shortest Distance',
            'path': dijkstra(self.graph, src, dst, lambda e: e.km),
            'type': 'distance'
        })
        
        # 2. Least hops
        alternatives.append({
            'name': 'Least Connections',
            'path': bfs_least_hops(self.graph, src, dst),
            'type': 'hops'
        })
        
        # 3. Fastest time
        alternatives.append({
            'name': 'Fastest',
            'path': dijkstra(self.graph, src, dst, lambda e: e.minutes),
            'type': 'time'
        })
        
        # 4. Cheapest
        alternatives.append({
            'name': 'Cheapest',
            'path': dijkstra(self.graph, src, dst, lambda e: e.price),
            'type': 'price'
        })
        
        # 5. Balanced (composite score)
        alternatives.append({
            'name': 'Balanced (Recommended)',
            'path': self.find_balanced_route(src, dst),
            'type': 'balanced'
        })
        
        return [alt for alt in alternatives if alt['path']]
    
    def find_balanced_route(self, src: str, dst: str) -> Optional[List[str]]:
        """Find route that balances all factors using normalized scoring"""
        def composite_score(edge: Edge) -> float:
            # Normalize each metric to 0-1 scale
            max_km = 15000  # Longest possible flight
            max_min = 1200   # 20 hours
            max_price = 2000
            
            norm_dist = edge.km / max_km
            norm_time = edge.minutes / max_min
            norm_price = edge.price / max_price
            
            # Weighted combination (customizable)
            return (0.3 * norm_dist + 0.3 * norm_time + 0.4 * norm_price)
        
        return dijkstra(self.graph, src, dst, composite_score)