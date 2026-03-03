import networkx as nx
import plotly.express as px
import plotly.graph_objects as go

class FlightNetworkAnalyzer:
    def __init__(self, graph: FlightGraph):
        self.graph = graph
        self.nx_graph = self._build_networkx_graph()
    
    def _build_networkx_graph(self):
        """Convert to NetworkX for advanced analytics"""
        G = nx.Graph()
        for code, airport in self.graph.airports.items():
            G.add_node(code, lat=airport.lat, lon=airport.lon, 
                      city=airport.city, country=airport.country)
        
        for src in self.graph.adj:
            for edge in self.graph.adj[src]:
                G.add_edge(src, edge.dst, weight=edge.km)
        return G
    
    def get_hub_airports(self, top_n: int = 10) -> pd.DataFrame:
        """Identify hub airports using centrality measures"""
        degree_centrality = nx.degree_centrality(self.nx_graph)
        betweenness = nx.betweenness_centrality(self.nx_graph)
        closeness = nx.closeness_centrality(self.nx_graph)
        
        hubs = []
        for node in self.nx_graph.nodes:
            if node in self.graph.airports:
                airport = self.graph.airports[node]
                hubs.append({
                    'airport': node,
                    'city': airport.city,
                    'country': airport.country,
                    'degree_centrality': degree_centrality[node],
                    'betweenness': betweenness[node],
                    'closeness': closeness[node],
                    'connections': self.nx_graph.degree[node]
                })
        
        df = pd.DataFrame(hubs)
        df['hub_score'] = (df['degree_centrality'] + df['betweenness'] + df['closeness']) / 3
        return df.sort_values('hub_score', ascending=False).head(top_n)
    
    def find_isolated_airports(self) -> List[str]:
        """Find airports with poor connectivity"""
        components = list(nx.connected_components(self.nx_graph))
        isolated = [node for comp in components if len(comp) < 5 for node in comp]
        return isolated
    
    def suggest_new_routes(self, threshold: float = 0.7) -> List[Dict]:
        """Suggest potentially profitable new routes"""
        suggestions = []
        
        # Get hub airports
        hubs = self.get_hub_airports(20)['airport'].tolist()
        
        for i, hub1 in enumerate(hubs):
            for hub2 in hubs[i+1:]:
                # Check if direct flight exists
                has_direct = any(e.dst == hub2 for e in self.graph.neighbors(hub1))
                
                if not has_direct:
                    # Calculate great-circle distance
                    a1 = self.graph.airports[hub1]
                    a2 = self.graph.airports[hub2]
                    distance = haversine(a1.lat, a1.lon, a2.lat, a2.lon)
                    
                    # Calculate potential demand (based on centrality)
                    demand = (self.nx_graph.degree[hub1] * 
                             self.nx_graph.degree[hub2]) / 100
                    
                    if distance < 10000 and demand > threshold:
                        suggestions.append({
                            'from': hub1,
                            'to': hub2,
                            'distance': round(distance, 2),
                            'estimated_demand': round(demand, 2),
                            'potential_price': estimate_price(distance)
                        })
        
        return sorted(suggestions, key=lambda x: x['estimated_demand'], reverse=True)