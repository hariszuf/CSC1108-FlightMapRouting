from dataclasses import dataclass
from time import perf_counter
from typing import Dict, List, Optional
import pandas as pd
from ..graph import FlightGraph
from ..models import Edge

@dataclass
class AlgorithmMetrics:
    name: str
    path: Optional[List[str]]
    cost: float
    time_ms: float
    nodes_explored: int
    memory_usage_mb: float

class AlgorithmComparator:
    def __init__(self, graph: FlightGraph):
        self.graph = graph
        self.results: Dict[str, AlgorithmMetrics] = {}
    
    def compare_all(self, src: str, dst: str) -> pd.DataFrame:
        algorithms = {
            "BFS (Least Hops)": (bfs_least_hops, lambda e: 1),
            "Dijkstra (Distance)": (lambda s,d: dijkstra(self.graph, s, d, lambda e: e.km), lambda e: e.km),
            "Dijkstra (Time)": (lambda s,d: dijkstra(self.graph, s, d, lambda e: e.minutes), lambda e: e.minutes),
            "Dijkstra (Price)": (lambda s,d: dijkstra(self.graph, s, d, lambda e: e.price), lambda e: e.price),
            "A* (Distance)": (lambda s,d: astar_shortest_path(self.graph, s, d, lambda e: e.km), lambda e: e.km),
            "A* (Time)": (lambda s,d: astar_shortest_path(self.graph, s, d, lambda e: e.minutes), lambda e: e.minutes),
            "A* (Price)": (lambda s,d: astar_shortest_path(self.graph, s, d, lambda e: e.price), lambda e: e.price),
        }
        
        for name, (algo_func, cost_func) in algorithms.items():
            # Measure performance
            start_time = perf_counter()
            import tracemalloc
            tracemalloc.start()
            
            path = algo_func(src, dst)
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            end_time = perf_counter()
            
            if path:
                cost = calculate_path_cost(self.graph, path, cost_func)
            else:
                cost = float('inf')
            
            self.results[name] = AlgorithmMetrics(
                name=name,
                path=path,
                cost=cost,
                time_ms=(end_time - start_time) * 1000,
                nodes_explored=len(path) if path else 0,
                memory_usage_mb=peak / 10**6
            )
        
        # Create comparison dataframe
        data = []
        for name, metrics in self.results.items():
            data.append({
                'Algorithm': name,
                'Found Route': '✓' if metrics.path else '✗',
                'Cost': round(metrics.cost, 2) if metrics.path != float('inf') else 'N/A',
                'Time (ms)': round(metrics.time_ms, 3),
                'Nodes': metrics.nodes_explored,
                'Memory (MB)': round(metrics.memory_usage_mb, 3)
            })
        
        return pd.DataFrame(data)