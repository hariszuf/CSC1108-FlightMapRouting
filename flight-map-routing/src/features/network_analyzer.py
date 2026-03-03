from typing import List, Dict, Any
import pandas as pd
import networkx as nx
import numpy as np
from src.graph import FlightGraph
from src.algorithms.astar import haversine

class FlightNetworkAnalyzer:
    """Analyze flight network properties and identify key airports"""
    
    def __init__(self, graph: FlightGraph):
        self.graph = graph
        self.nx_graph = self._build_networkx_graph()
    
    def _build_networkx_graph(self):
        """Convert FlightGraph to NetworkX graph for advanced analytics"""
        G = nx.Graph()
        
        # Add nodes with attributes
        for code, airport in self.graph.airports.items():
            G.add_node(code, 
                      lat=airport.lat, 
                      lon=airport.lon,
                      city=airport.city, 
                      country=airport.country)
        
        # Add edges
        for src in self.graph.adj:
            for edge in self.graph.adj[src]:
                G.add_edge(src, edge.dst, 
                          weight=edge.km,
                          time=edge.minutes,
                          price=edge.price)
        
        return G
    
    def get_hub_airports(self, top_n: int = 10) -> pd.DataFrame:
        """Identify hub airports using multiple centrality measures"""
        
        # Calculate different centrality measures
        degree_cent = nx.degree_centrality(self.nx_graph)
        betweenness_cent = nx.betweenness_centrality(self.nx_graph)
        closeness_cent = nx.closeness_centrality(self.nx_graph)
        eigenvector_cent = nx.eigenvector_centrality(self.nx_graph, max_iter=1000, tol=1e-06)
        
        hubs = []
        for node in self.nx_graph.nodes():
            if node in self.graph.airports:
                airport = self.graph.airports[node]
                
                # Combined hub score (normalized)
                hub_score = (
                    degree_cent.get(node, 0) * 0.4 +
                    betweenness_cent.get(node, 0) * 0.3 +
                    closeness_cent.get(node, 0) * 0.2 +
                    eigenvector_cent.get(node, 0) * 0.1
                )
                
                hubs.append({
                    'airport': node,
                    'city': airport.city,
                    'country': airport.country,
                    'connections': self.nx_graph.degree(node),
                    'degree_centrality': round(degree_cent.get(node, 0), 4),
                    'betweenness': round(betweenness_cent.get(node, 0), 4),
                    'closeness': round(closeness_cent.get(node, 0), 4),
                    'hub_score': round(hub_score, 4)
                })
        
        df = pd.DataFrame(hubs)
        return df.sort_values('hub_score', ascending=False).head(top_n)
    
    def find_isolated_airports(self, min_connections: int = 3) -> List[str]:
        """Find airports with poor connectivity"""
        isolated = []
        for node in self.nx_graph.nodes():
            if self.nx_graph.degree(node) < min_connections:
                if node in self.graph.airports:
                    isolated.append(node)
        return isolated
    
    def suggest_new_routes(self, threshold: float = 0.5) -> List[Dict]:
        """Suggest potentially profitable new routes between hubs"""
        suggestions = []
        
        # Get top hubs
        hubs_df = self.get_hub_airports(30)
        hub_codes = hubs_df['airport'].tolist()
        
        for i, hub1 in enumerate(hub_codes):
            for hub2 in hub_codes[i+1:]:
                # Check if direct flight exists
                has_direct = False
                for edge in self.graph.neighbors(hub1):
                    if edge.dst == hub2:
                        has_direct = True
                        break
                
                if not has_direct:
                    # Calculate great-circle distance
                    a1 = self.graph.airports[hub1]
                    a2 = self.graph.airports[hub2]
                    distance = haversine(a1.lat, a1.lon, a2.lat, a2.lon)
                    
                    # Calculate potential demand based on hub sizes
                    demand = (self.nx_graph.degree(hub1) * 
                             self.nx_graph.degree(hub2)) / 100
                    
                    # Only suggest if distance is reasonable and demand is high enough
                    if distance < 10000 and demand > threshold:
                        # Estimate price based on distance
                        est_price = 30 + 0.12 * distance
                        
                        suggestions.append({
                            'from': hub1,
                            'to': hub2,
                            'distance': round(distance, 2),
                            'estimated_demand': round(demand, 2),
                            'potential_price': round(est_price, 2),
                            'from_connections': self.nx_graph.degree(hub1),
                            'to_connections': self.nx_graph.degree(hub2)
                        })
        
        return sorted(suggestions, key=lambda x: x['estimated_demand'], reverse=True)
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get comprehensive network statistics"""
        return {
            'airports': len(self.graph.airports),
            'routes': sum(len(edges) for edges in self.graph.adj.values()),
            'countries': len(set(a.country for a in self.graph.airports.values())),
            'avg_connections': self._avg_connections(),
            'density': self._network_density(),
            'diameter': self._network_diameter(),
            'avg_path_length': self._avg_path_length(),
            'clustering_coefficient': nx.average_clustering(self.nx_graph)
        }
    
    def _avg_connections(self) -> float:
        """Calculate average connections per airport"""
        total = sum(len(self.graph.neighbors(code)) for code in self.graph.airports)
        return round(total / len(self.graph.airports), 2)
    
    def _network_density(self) -> float:
        """Calculate network density"""
        n = len(self.graph.airports)
        if n < 2:
            return 0
        max_possible = n * (n - 1)
        actual = sum(len(self.graph.neighbors(code)) for code in self.graph.airports)
        return round(actual / max_possible, 4)
    
    def _network_diameter(self) -> float:
        """Calculate network diameter (longest shortest path)"""
        try:
            if nx.is_connected(self.nx_graph):
                return nx.diameter(self.nx_graph)
            else:
                # Get largest component
                components = nx.connected_components(self.nx_graph)
                largest = max(components, key=len)
                subgraph = self.nx_graph.subgraph(largest)
                return nx.diameter(subgraph)
        except:
            return float('inf')
    
    def _avg_path_length(self) -> float:
        """Calculate average shortest path length"""
        try:
            if nx.is_connected(self.nx_graph):
                return nx.average_shortest_path_length(self.nx_graph)
            else:
                # Get largest component
                components = nx.connected_components(self.nx_graph)
                largest = max(components, key=len)
                subgraph = self.nx_graph.subgraph(largest)
                return nx.average_shortest_path_length(subgraph)
        except:
            return float('inf')