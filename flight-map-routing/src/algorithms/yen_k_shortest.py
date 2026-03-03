from typing import List, Optional, Set, Tuple, Dict, Callable, Any
import heapq
from copy import deepcopy

from src.graph import FlightGraph
from src.algorithms.dijkstra import dijkstra
from src.models import Edge

def calculate_path_cost(graph: FlightGraph, path: List[str], weight_func: Callable[[Edge], float]) -> float:
    """Calculate the total cost of a path using the given weight function"""
    if not path or len(path) < 2:
        return float('inf')
    
    total = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for edge in graph.neighbors(u):
            if edge.dst == v:
                total += weight_func(edge)
                break
    return total

class GraphModifier:
    """Helper class to temporarily modify a graph for Yen's algorithm"""
    
    def __init__(self, graph: FlightGraph):
        self.original_graph = graph
        self.removed_edges: Set[Tuple[str, str]] = set()
        self.disabled_nodes: Set[str] = set()
        self.modified_adj: Dict[str, List[Edge]] = {}
        
    def remove_edge_temporarily(self, u: str, v: str) -> bool:
        """Temporarily remove an edge from the graph"""
        self.removed_edges.add((u, v))
        return True
    
    def disable_node_temporarily(self, node: str) -> bool:
        """Temporarily disable a node (remove all edges to/from it)"""
        self.disabled_nodes.add(node)
        return True
    
    def restore_all(self):
        """Restore all removed edges and disabled nodes"""
        self.removed_edges.clear()
        self.disabled_nodes.clear()
        self.modified_adj.clear()
    
    def get_neighbors(self, node: str) -> List[Edge]:
        """Get neighbors considering temporary removals"""
        if node in self.disabled_nodes:
            return []
        
        # Check if we have cached modified neighbors
        if node in self.modified_adj:
            return self.modified_adj[node]
        
        # Get original neighbors and filter
        original = self.original_graph.neighbors(node)
        filtered = []
        
        for edge in original:
            # Skip if edge is removed
            if (node, edge.dst) in self.removed_edges:
                continue
            # Skip if destination is disabled
            if edge.dst in self.disabled_nodes:
                continue
            filtered.append(edge)
        
        self.modified_adj[node] = filtered
        return filtered


def yen_k_shortest_paths(graph: FlightGraph, start: str, goal: str, 
                         K: int, weight_func: Callable[[Edge], float]) -> List[List[str]]:
    """
    Yen's algorithm for finding K shortest loopless paths between two nodes.
    
    Args:
        graph: The flight graph
        start: Source airport code
        goal: Destination airport code
        K: Number of shortest paths to find
        weight_func: Function to extract weight from an edge
        
    Returns:
        List of up to K shortest paths, each as a list of airport codes
    """
    if start == goal:
        return [[start]]
    
    # List of shortest paths found
    A: List[List[str]] = []
    
    # Priority queue of candidate paths (cost, path)
    B: List[Tuple[float, List[str]]] = []
    
    # Get the first shortest path using Dijkstra
    first_path = dijkstra(graph, start, goal, weight_func)
    if not first_path:
        return []  # No path exists
    
    A.append(first_path)
    
    # Create graph modifier for temporary changes
    modifier = GraphModifier(graph)
    
    # Find K-1 more paths
    for k in range(1, K):
        # The spur node ranges from the first node to the node before goal in previous (k-1) path
        for i in range(len(A[k-1]) - 1):
            # Spur node is the current node in the path
            spur_node = A[k-1][i]
            
            # Root path is the sequence from start to spur node
            root_path = A[k-1][:i+1]
            
            # Remove edges that are part of previous paths that share the same root path
            modifier.restore_all()  # Start fresh
            
            # Remove edges used in previously found paths that have the same root path
            for path in A:
                if len(path) > i and root_path == path[:i+1]:
                    # Remove the edge from path[i] to path[i+1]
                    u = path[i]
                    v = path[i+1]
                    modifier.remove_edge_temporarily(u, v)
            
            # Remove nodes in root path (except spur node) to avoid cycles
            for node in root_path[:-1]:
                if node != spur_node:
                    modifier.disable_node_temporarily(node)
            
            # Create a modified view of the graph for spur path calculation
            class ModifiedGraph:
                def __init__(self, original_graph, modifier):
                    self.original = original_graph
                    self.modifier = modifier
                
                def neighbors(self, node):
                    return self.modifier.get_neighbors(node)
                
                @property
                def airports(self):
                    return self.original.airports
            
            modified_graph = ModifiedGraph(graph, modifier)
            
            # Find spur path from spur node to goal
            spur_path = dijkstra(modified_graph, spur_node, goal, weight_func)
            
            if spur_path:
                # Combine root path and spur path (excluding spur node to avoid duplication)
                total_path = root_path[:-1] + spur_path
                
                # Check if path already exists in A or B
                path_exists = False
                for p in A:
                    if p == total_path:
                        path_exists = True
                        break
                if not path_exists:
                    for _, p in B:
                        if p == total_path:
                            path_exists = True
                            break
                
                if not path_exists:
                    # Calculate total path cost
                    cost = calculate_path_cost(graph, total_path, weight_func)
                    heapq.heappush(B, (cost, total_path))
        
        if not B:
            # No more candidate paths
            break
        
        # Add the best path from B to A
        best_cost, best_path = heapq.heappop(B)
        
        # Filter out any paths that might have been added that are the same
        if best_path not in A:
            A.append(best_path)
    
    return A[:K]  # Return up to K paths