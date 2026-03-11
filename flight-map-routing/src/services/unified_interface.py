# src/services/unified_interface.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import json

from src.graph import FlightGraph
from src.models import RouteResult
from src.services.routing import find_route
from src.algorithms.dijkstra import dijkstra
from src.algorithms.bfs import bfs_least_hops

# Optional imports with error handling
try:
    from src.algorithms.astar import astar_shortest_path
    ASTAR_AVAILABLE = True
except ImportError:
    ASTAR_AVAILABLE = False
    print("A* algorithm not available")

try:
    from src.algorithms.bellman_ford import bellman_ford_cheapest
    BELLMAN_FORD_AVAILABLE = True
except ImportError:
    BELLMAN_FORD_AVAILABLE = False
    print("Bellman-Ford algorithm not available")

try:
    from src.algorithms.yen_k_shortest import yen_k_shortest_paths
    YEN_AVAILABLE = True
except ImportError:
    YEN_AVAILABLE = False
    print("Yen's algorithm not available")

try:
    from src.features.route_explorer import RouteExplorer
    ROUTE_EXPLORER_AVAILABLE = True
except ImportError:
    ROUTE_EXPLORER_AVAILABLE = False
    print("RouteExplorer not available")

try:
    from src.features.multi_city_planner import MultiCityPlanner
    MULTI_CITY_AVAILABLE = True
except ImportError:
    MULTI_CITY_AVAILABLE = False
    print("MultiCityPlanner not available")

try:
    from src.features.network_analyzer import FlightNetworkAnalyzer
    NETWORK_ANALYZER_AVAILABLE = True
except ImportError:
    NETWORK_ANALYZER_AVAILABLE = False
    print("FlightNetworkAnalyzer not available")

try:
    from src.features.export_manager import ExportManager
    EXPORT_MANAGER_AVAILABLE = True
except ImportError:
    EXPORT_MANAGER_AVAILABLE = False
    print("ExportManager not available")

try:
    from src.features.cache_manager import CacheManager
    CACHE_MANAGER_AVAILABLE = True
except ImportError as e:
    CACHE_MANAGER_AVAILABLE = False
    print(f"CacheManager not available: {e}")

try:
    from src.features.enhancer import DataEnhancer
    ENHANCER_AVAILABLE = True
except ImportError:
    ENHANCER_AVAILABLE = False
    print("DataEnhancer not available")


class FlightRouteUnified:
    """Unified interface for all flight routing features"""
    
    def __init__(self, graph: FlightGraph):
        self.graph = graph
        
        # Initialize available features
        self.route_explorer = RouteExplorer(graph) if ROUTE_EXPLORER_AVAILABLE else None
        self.multi_city_planner = MultiCityPlanner(graph) if MULTI_CITY_AVAILABLE else None
        self.network_analyzer = FlightNetworkAnalyzer(graph) if NETWORK_ANALYZER_AVAILABLE else None
        self.export_manager = ExportManager() if EXPORT_MANAGER_AVAILABLE else None
        self.cache_manager = CacheManager(use_redis=False) if CACHE_MANAGER_AVAILABLE else None
        
        # Initialize enhancements if available
        if ENHANCER_AVAILABLE:
            self.data_enhancer = DataEnhancer(graph)
            self._initialize_enhancements()
        else:
            self.data_enhancer = None
    
    def _initialize_enhancements(self):
        """Initialize enhanced data features"""
        if self.data_enhancer:
            try:
                self.data_enhancer.add_flight_schedules()
                self.data_enhancer.add_airport_facilities()
                self.data_enhancer.add_seasonal_pricing()
            except Exception as e:
                print(f"Could not initialize enhancements: {e}")
    
    # ========== BASIC ROUTING ==========
    def find_route(self, src: str, dst: str, mode: str = "distance") -> Optional[RouteResult]:
        """Basic route finding with caching"""
        # Check cache first
        if self.cache_manager:
            cached = self.cache_manager.get_shortest_path(src, dst, mode)
            if cached:
                return cached
        
        # Find route
        if mode == 'balanced' and self.route_explorer:
            path = self.route_explorer.find_balanced_route(src, dst)
            if path:
                result = self._path_to_route_result(path)
            else:
                result = None
        else:
            result = find_route(self.graph, src, dst, mode)
        
        # Cache result
        if result and self.cache_manager:
            self.cache_manager.cache_route(src, dst, mode, result)
        
        return result
    
    # ========== MULTIPLE ALGORITHMS ==========
    def compare_algorithms(self, src: str, dst: str) -> Dict[str, Any]:
        """Compare all available algorithms"""
        results = {}
        
        # BFS (least hops)
        path_bfs = bfs_least_hops(self.graph, src, dst)
        if path_bfs:
            results['BFS (Least Hops)'] = {
                'path': path_bfs,
                'cost': len(path_bfs) - 1,
                'algorithm': 'bfs'
            }
        
        # Dijkstra variations
        for name, weight_func, mode in [
            ('Dijkstra (Distance)', lambda e: e.km, 'distance'),
            ('Dijkstra (Time)', lambda e: e.minutes, 'time'),
            ('Dijkstra (Price)', lambda e: e.price, 'price')
        ]:
            path = dijkstra(self.graph, src, dst, weight_func)
            if path:
                results[name] = {
                    'path': path,
                    'cost': self._calculate_path_cost(path, weight_func),
                    'algorithm': 'dijkstra',
                    'mode': mode
                }
        
        # A* variations
        if ASTAR_AVAILABLE:
            for name, weight_func, mode in [
                ('A* (Distance)', lambda e: e.km, 'distance'),
                ('A* (Time)', lambda e: e.minutes, 'time'),
                ('A* (Price)', lambda e: e.price, 'price')
            ]:
                try:
                    path = astar_shortest_path(self.graph, src, dst, weight_func)
                    if path:
                        results[name] = {
                            'path': path,
                            'cost': self._calculate_path_cost(path, weight_func),
                            'algorithm': 'astar',
                            'mode': mode
                        }
                except:
                    pass
        
        # Bellman-Ford (handles negative weights)
        if BELLMAN_FORD_AVAILABLE:
            try:
                path_bf = bellman_ford_cheapest(self.graph, src, dst)
                if path_bf:
                    results['Bellman-Ford (Cheapest)'] = {
                        'path': path_bf,
                        'cost': self._calculate_path_cost(path_bf, lambda e: e.price),
                        'algorithm': 'bellman_ford'
                    }
            except:
                pass
        
        return results
    
    # ========== K-SHORTEST PATHS ==========
    def find_k_shortest_paths(self, src: str, dst: str, K: int = 3, 
                              mode: str = "distance") -> List[Dict[str, Any]]:
        """Find K shortest paths using Yen's algorithm"""
        if not YEN_AVAILABLE:
            return []
        
        weight_func = self._get_weight_function(mode)
        try:
            paths = yen_k_shortest_paths(self.graph, src, dst, K, weight_func)
        except:
            return []
        
        results = []
        for i, path in enumerate(paths):
            cost = self._calculate_path_cost(path, weight_func)
            route_result = self._path_to_route_result(path)
            results.append({
                'rank': i + 1,
                'path': path,
                'cost': cost,
                'details': route_result
            })
        
        return results
    
    # ========== ROUTE EXPLORATION ==========
    def explore_alternatives(self, src: str, dst: str) -> List[Dict[str, Any]]:
        """Get alternative routes with different trade-offs"""
        if not self.route_explorer:
            return []
        return self.route_explorer.explore_alternatives(src, dst)
    
    def find_balanced_route(self, src: str, dst: str) -> Optional[RouteResult]:
        """Find route balanced between distance, time, and price"""
        if not self.route_explorer:
            return None
        path = self.route_explorer.find_balanced_route(src, dst)
        if path:
            return self._path_to_route_result(path)
        return None
    
    # ========== MULTI-CITY PLANNING ==========
    def plan_multi_city_route(self, cities: List[str], start_city: Optional[str] = None,
                         method: str = 'auto') -> Dict[str, Any]:
        if not self.multi_city_planner:
            return {'route': None, 'total_distance': float('inf'), 'error': 'Multi-city planner not available'}
    
        # Call the planner
        result = self.multi_city_planner.plan_optimal_route(cities, start_city, method)
    
    # Convert TSPResult to dictionary for backward compatibility
        return {
            'route': result.route,
            'total_distance': result.total_distance,
            'segments': result.segments,
            'algorithm_used': result.algorithm_used,
            'computation_time_ms': result.computation_time_ms,
            'optimality_guarantee': result.optimality_guarantee
        }
    
    # ========== NETWORK ANALYTICS ==========
    def get_network_stats(self) -> Dict[str, Any]:
        """Get overall network statistics"""
        if self.network_analyzer:
            return self.network_analyzer.get_network_stats()
        
        # Fallback basic stats
        return {
            'airports': len(self.graph.airports),
            'routes': sum(len(edges) for edges in self.graph.adj.values()),
            'countries': len(set(a.country for a in self.graph.airports.values())),
            'avg_connections': self._avg_connections(),
            'density': self._network_density()
        }
    
    def get_hub_airports(self, top_n: int = 10) -> pd.DataFrame:
        """Identify hub airports using centrality measures"""
        if self.network_analyzer:
            return self.network_analyzer.get_hub_airports(top_n)
        
        # Fallback: just return airports sorted by connections
        hubs = []
        for code in self.graph.airports:
            airport = self.graph.airports[code]
            hubs.append({
                'airport': code,
                'city': airport.city,
                'country': airport.country,
                'connections': len(self.graph.neighbors(code)),
                'hub_score': len(self.graph.neighbors(code)) / 100  # Simple normalized score
            })
        
        df = pd.DataFrame(hubs)
        return df.sort_values('hub_score', ascending=False).head(top_n)
    
    def get_isolated_airports(self, min_connections: int = 3) -> List[str]:
        """Find airports with poor connectivity"""
        if self.network_analyzer:
            return self.network_analyzer.find_isolated_airports(min_connections)
        
        # Fallback
        isolated = []
        for code in self.graph.airports:
            if len(self.graph.neighbors(code)) < min_connections:
                isolated.append(code)
        return isolated
    
    def suggest_new_routes(self, threshold: float = 0.5) -> List[Dict]:
        """Suggest potentially profitable new routes"""
        if self.network_analyzer:
            return self.network_analyzer.suggest_new_routes(threshold)
        return []
    
    # ========== EXPORT FUNCTIONALITY ==========
    def export_route(self, route_result: RouteResult, format: str = 'json') -> Any:
        """Export route in various formats"""
        if not self.export_manager:
            if format == 'json':
                return json.dumps({'path': route_result.path}, indent=2)
            elif format == 'text':
                return str(route_result)
            else:
                return None
        
        if format == 'json':
            return self.export_manager.export_as_json(route_result)
        elif format == 'csv':
            return self.export_manager.export_as_csv(route_result)
        elif format == 'text':
            return self.export_manager.export_as_text(route_result)
        elif format == 'pdf':
            return self.export_manager.export_as_pdf(route_result)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def create_shareable_link(self, route_result: RouteResult) -> str:
        """Create shareable link for route"""
        if self.export_manager:
            return self.export_manager.create_shareable_link(route_result)
        
        # Fallback
        route_str = '-'.join(route_result.path)
        return f"https://flightroute.pro/share/{route_str}"
    
    # ========== HELPER METHODS ==========
    def _get_weight_function(self, mode: str):
        """Get weight function based on mode"""
        if mode == 'distance':
            return lambda e: e.km
        elif mode == 'time':
            return lambda e: e.minutes
        elif mode == 'price':
            return lambda e: e.price
        else:
            return lambda e: 1  # hops
    
    def _calculate_path_cost(self, path: List[str], weight_func) -> float:
        """Calculate total cost of a path"""
        if not path or len(path) < 2:
            return float('inf')
        
        total = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            for edge in self.graph.neighbors(u):
                if edge.dst == v:
                    total += weight_func(edge)
                    break
        return total
    
    def _path_to_route_result(self, path: List[str]) -> RouteResult:
        """Convert path list to RouteResult"""
        total_km = 0.0
        total_minutes = 0
        total_price = 0.0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            for edge in self.graph.neighbors(u):
                if edge.dst == v:
                    total_km += edge.km
                    total_minutes += edge.minutes
                    total_price += edge.price
                    break
        
        return RouteResult(path, total_km, total_minutes, total_price)
    
    def _avg_connections(self) -> float:
        """Calculate average connections per airport"""
        total = sum(len(self.graph.neighbors(code)) for code in self.graph.airports)
        return round(total / len(self.graph.airports), 2) if self.graph.airports else 0
    
    def _network_density(self) -> float:
        """Calculate network density"""
        n = len(self.graph.airports)
        if n < 2:
            return 0
        max_possible = n * (n - 1)
        actual = sum(len(self.graph.neighbors(code)) for code in self.graph.airports)
        return round(actual / max_possible, 4)