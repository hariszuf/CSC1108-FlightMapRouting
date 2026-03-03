# src/features/multi_city_planner.py
from typing import List, Dict, Optional, Tuple, Set
from itertools import permutations, combinations
import heapq
import math
import random
from dataclasses import dataclass, field
from src.algorithms.dijkstra import dijkstra

@dataclass
class TSPResult:
    """Structured result for TSP solutions"""
    route: List[str]
    total_distance: float
    segments: List[Dict]
    algorithm_used: str
    computation_time_ms: float
    optimality_guarantee: str  # "exact", "near-optimal", "heuristic"
    
    def __str__(self) -> str:
        return f"{' → '.join(self.route)} ({self.total_distance:.2f} km)"

class MultiCityPlanner:
    """
    Multi-city trip planner with multiple algorithms for different scales.
    
    Problem: Traveling Salesman Problem (TSP) - finding shortest route visiting all cities.
    
    Algorithm Selection:
    - ≤ 8 cities: Exact DP (Held-Karp) - Guaranteed optimal
    - 9-12 cities: Branch and Bound - Near-optimal with pruning
    - > 12 cities: Heuristics (Nearest Neighbor + 2-opt) - Fast, good enough
    """
    
    def __init__(self, graph: FlightGraph):
        self.graph = graph
        self.distance_cache: Dict[str, float] = {}  # Cache distances between cities
        self.path_cache: Dict[str, List[str]] = {}  # Cache actual paths
    
    def _get_cache_key(self, city1: str, city2: str) -> str:
        """Create cache key for city pair (order independent)"""
        return f"{min(city1, city2)}:{max(city1, city2)}"
    
    def _get_distance_and_path(self, city1: str, city2: str) -> Tuple[float, List[str]]:
        """
        Get shortest distance and path between two cities.
        Uses caching for performance.
        """
        cache_key = self._get_cache_key(city1, city2)
        
        # Check cache
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key], self.path_cache[cache_key]
        
        # Find shortest path
        path = dijkstra(self.graph, city1, city2, lambda e: e.km)
        
        if not path:
            return float('inf'), []
        
        # Calculate total distance
        distance = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            for edge in self.graph.neighbors(u):
                if edge.dst == v:
                    distance += edge.km
                    break
        
        # Cache both distance and path
        self.distance_cache[cache_key] = distance
        self.path_cache[cache_key] = path
        return distance, path
    
    def _build_distance_matrix(self, cities: List[str]) -> Tuple[List[List[float]], List[List[List[str]]]]:
        """
        Build distance matrix and path matrix between all pairs.
        Returns:
            dist_matrix: n x n matrix of distances
            path_matrix: n x n matrix of paths (for reconstruction)
        """
        n = len(cities)
        dist_matrix = [[0.0] * n for _ in range(n)]
        path_matrix = [[[] for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                dist, path = self._get_distance_and_path(cities[i], cities[j])
                dist_matrix[i][j] = dist
                dist_matrix[j][i] = dist
                path_matrix[i][j] = path
                path_matrix[j][i] = list(reversed(path)) if path else []
        
        return dist_matrix, path_matrix
    
    def plan_optimal_route(self, cities: List[str], start_city: Optional[str] = None, 
                          algorithm: str = 'auto') -> TSPResult:
        """
        Plan optimal route visiting all cities.
        
        Args:
            cities: List of city codes to visit
            start_city: Optional starting city (defaults to first city)
            algorithm: 'auto', 'exact', 'bnb', 'heuristic', 'genetic'
            
        Returns:
            TSPResult with route details
        """
        import time
        
        if len(cities) < 2:
            return TSPResult(
                route=cities,
                total_distance=0,
                segments=[],
                algorithm_used="trivial",
                computation_time_ms=0,
                optimality_guarantee="exact"
            )
        
        # Handle start city
        if start_city and start_city not in cities:
            cities = [start_city] + [c for c in cities if c != start_city]
        elif not start_city:
            start_city = cities[0]
        
        start_time = time.time()
        
        # Select algorithm based on problem size
        n = len(cities)
        
        if algorithm == 'auto':
            if n <= 8:
                algorithm = 'exact'
            elif n <= 12:
                algorithm = 'bnb'
            else:
                algorithm = 'heuristic'
        
        # Execute selected algorithm
        if algorithm == 'exact':
            result = self._solve_exact_dp(cities)
            result.algorithm_used = "Held-Karp DP (exact)"
            result.optimality_guarantee = "exact"
        elif algorithm == 'bnb':
            result = self._solve_branch_and_bound(cities)
            result.algorithm_used = "Branch & Bound (near-optimal)"
            result.optimality_guarantee = "near-optimal"
        elif algorithm == 'heuristic':
            result = self._solve_heuristic_2opt(cities)
            result.algorithm_used = "Nearest Neighbor + 2-opt (heuristic)"
            result.optimality_guarantee = "heuristic"
        elif algorithm == 'genetic':
            result = self._solve_genetic(cities)
            result.algorithm_used = "Genetic Algorithm (metaheuristic)"
            result.optimality_guarantee = "heuristic"
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Add computation time
        result.computation_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _solve_exact_dp(self, cities: List[str]) -> TSPResult:
        """
        Exact solution using Held-Karp DP algorithm.
        Time: O(n²2ⁿ) - optimal for n ≤ 8
        """
        n = len(cities)
        start_idx = 0  # Start from first city
        
        # Build distance matrix
        dist_matrix, path_matrix = self._build_distance_matrix(cities)
        
        # DP state: (mask, last_city_index) -> (distance, parent)
        dp = {}
        parent = {}
        
        # Initialize: start from first city
        dp[(1 << start_idx, start_idx)] = 0
        
        # Fill DP table
        for mask in range(1 << n):
            for last in range(n):
                if (mask, last) not in dp:
                    continue
                
                for nxt in range(n):
                    if mask & (1 << nxt):
                        continue
                    
                    new_mask = mask | (1 << nxt)
                    new_dist = dp[(mask, last)] + dist_matrix[last][nxt]
                    
                    if (new_mask, nxt) not in dp or new_dist < dp[(new_mask, nxt)]:
                        dp[(new_mask, nxt)] = new_dist
                        parent[(new_mask, nxt)] = last
        
        # Find best route (return to start to complete cycle)
        full_mask = (1 << n) - 1
        best_dist = float('inf')
        best_last = -1
        
        for last in range(n):
            if (full_mask, last) in dp:
                total_dist = dp[(full_mask, last)]  # Don't add return distance for open loop
                if total_dist < best_dist:
                    best_dist = total_dist
                    best_last = last
        
        if best_last == -1:
            return TSPResult(
                route=[], total_distance=float('inf'), segments=[],
                algorithm_used="exact_dp", computation_time_ms=0,
                optimality_guarantee="exact"
            )
        
        # Reconstruct path
        path_indices = []
        mask = full_mask
        last = best_last
        
        while mask:
            path_indices.append(last)
            new_last = parent.get((mask, last), -1)
            mask &= ~(1 << last)
            last = new_last
        
        path_indices.reverse()
        
        # Convert indices to city codes
        route = [cities[i] for i in path_indices]
        
        # Get segment details
        segments = self._get_segment_details(route, path_matrix, cities)
        
        return TSPResult(
            route=route,
            total_distance=round(best_dist, 2),
            segments=segments,
            algorithm_used="Held-Karp DP (exact)",
            computation_time_ms=0,
            optimality_guarantee="exact"
        )
    
    def _solve_branch_and_bound(self, cities: List[str]) -> TSPResult:
        """
        Branch and Bound algorithm for medium-sized problems (9-12 cities).
        Uses bounding to prune suboptimal branches.
        """
        n = len(cities)
        dist_matrix, path_matrix = self._build_distance_matrix(cities)
        
        best_route = None
        best_distance = float('inf')
        
        def bound(current_idx: int, visited: Set[int], current_dist: float) -> float:
            """Calculate lower bound for remaining path"""
            # Simple bound: minimum spanning tree of unvisited nodes
            unvisited = [i for i in range(n) if i not in visited]
            
            if not unvisited:
                return current_dist
            
            # Minimum distance from current to any unvisited
            min_out = min(dist_matrix[current_idx][j] for j in unvisited)
            
            # For each unvisited, minimum connection
            remaining_sum = 0
            for i in unvisited:
                # Minimum edge from this unvisited node
                min_edge = min(dist_matrix[i][j] for j in range(n) if j != i)
                remaining_sum += min_edge
            
            return current_dist + min_out + remaining_sum / 2  # Each edge counted twice
        
        def branch(visited: Set[int], current_route: List[int], current_dist: float):
            nonlocal best_route, best_distance
            
            current_idx = current_route[-1]
            
            if len(visited) == n:
                # Complete route
                if current_dist < best_distance:
                    best_distance = current_dist
                    best_route = current_route.copy()
                return
            
            # Prune if bound is worse than best found
            if bound(current_idx, visited, current_dist) >= best_distance:
                return
            
            # Try all unvisited cities
            for nxt in range(n):
                if nxt not in visited:
                    visited.add(nxt)
                    current_route.append(nxt)
                    
                    branch(visited, current_route, 
                          current_dist + dist_matrix[current_idx][nxt])
                    
                    visited.remove(nxt)
                    current_route.pop()
        
        # Start from each possible start city
        for start in range(n):
            branch({start}, [start], 0)
        
        if not best_route:
            return self._solve_heuristic_2opt(cities)  # Fallback
        
        route = [cities[i] for i in best_route]
        segments = self._get_segment_details(route, path_matrix, cities)
        
        return TSPResult(
            route=route,
            total_distance=round(best_distance, 2),
            segments=segments,
            algorithm_used="Branch & Bound (near-optimal)",
            computation_time_ms=0,
            optimality_guarantee="near-optimal"
        )
    
    def _solve_heuristic_2opt(self, cities: List[str]) -> TSPResult:
        """
        Nearest neighbor heuristic with 2-opt improvement.
        Good for large problems (n > 12).
        """
        n = len(cities)
        dist_matrix, path_matrix = self._build_distance_matrix(cities)
        
        # Try multiple starts for better results
        best_route = None
        best_distance = float('inf')
        
        for start in range(min(5, n)):  # Try first 5 cities as start
            # Nearest neighbor construction
            route = self._nearest_neighbor_construction(dist_matrix, start)
            distance = self._calculate_route_distance(route, dist_matrix)
            
            # 2-opt improvement
            improved_route, improved_distance = self._two_opt(route, dist_matrix)
            
            if improved_distance < best_distance:
                best_distance = improved_distance
                best_route = improved_route
        
        if not best_route:
            return TSPResult(
                route=[], total_distance=float('inf'), segments=[],
                algorithm_used="heuristic", computation_time_ms=0,
                optimality_guarantee="heuristic"
            )
        
        route = [cities[i] for i in best_route]
        segments = self._get_segment_details(route, path_matrix, cities)
        
        return TSPResult(
            route=route,
            total_distance=round(best_distance, 2),
            segments=segments,
            algorithm_used="Nearest Neighbor + 2-opt (heuristic)",
            computation_time_ms=0,
            optimality_guarantee="heuristic (typically 5-10% from optimal)"
        )
    
    def _solve_genetic(self, cities: List[str], population_size: int = 100, 
                      generations: int = 500) -> TSPResult:
        """
        Genetic algorithm for very large problems.
        Provides good solutions for n > 20.
        """
        n = len(cities)
        dist_matrix, path_matrix = self._build_distance_matrix(cities)
        
        # Create initial population
        population = []
        for _ in range(population_size):
            # Mix of nearest neighbor and random starts
            if _ < population_size // 4:
                # Use nearest neighbor for some starting points
                start = _ % n
                route = self._nearest_neighbor_construction(dist_matrix, start)
            else:
                # Random permutation for diversity
                route = list(range(n))
                random.shuffle(route)
            population.append(route)
        
        def fitness(route: List[int]) -> float:
            return 1.0 / (self._calculate_route_distance(route, dist_matrix) + 1)
        
        # Evolution loop
        for gen in range(generations):
            # Evaluate fitness
            fitness_scores = [fitness(route) for route in population]
            
            # Select parents (tournament selection)
            new_population = []
            
            # Elitism - keep best routes
            elite_count = max(2, population_size // 10)
            elite_indices = np.argsort(fitness_scores)[-elite_count:]
            for idx in elite_indices:
                new_population.append(population[idx].copy())
            
            # Generate offspring
            while len(new_population) < population_size:
                # Select parents
                parent1 = self._tournament_select(population, fitness_scores)
                parent2 = self._tournament_select(population, fitness_scores)
                
                # Crossover (Ordered crossover for permutations)
                child = self._ordered_crossover(parent1, parent2)
                
                # Mutation
                if random.random() < 0.1:  # 10% mutation rate
                    self._mutate(child)
                
                new_population.append(child)
            
            population = new_population
        
        # Find best route
        best_route = max(population, key=lambda r: fitness(r))
        best_distance = self._calculate_route_distance(best_route, dist_matrix)
        
        route = [cities[i] for i in best_route]
        segments = self._get_segment_details(route, path_matrix, cities)
        
        return TSPResult(
            route=route,
            total_distance=round(best_distance, 2),
            segments=segments,
            algorithm_used="Genetic Algorithm (metaheuristic)",
            computation_time_ms=0,
            optimality_guarantee="heuristic (good for very large problems)"
        )
    
    # ========== HELPER METHODS FOR HEURISTICS ==========
    
    def _nearest_neighbor_construction(self, dist_matrix: List[List[float]], 
                                       start_idx: int) -> List[int]:
        """Construct route using nearest neighbor heuristic"""
        n = len(dist_matrix)
        visited = {start_idx}
        route = [start_idx]
        
        while len(visited) < n:
            current = route[-1]
            # Find nearest unvisited
            nearest = min(
                ((j, dist_matrix[current][j]) for j in range(n) if j not in visited),
                key=lambda x: x[1]
            )[0]
            route.append(nearest)
            visited.add(nearest)
        
        return route
    
    def _two_opt(self, route: List[int], dist_matrix: List[List[float]]) -> Tuple[List[int], float]:
        """
        Improve route using 2-opt local search.
        Removes crossings and improves route quality.
        """
        improved = True
        best_route = route.copy()
        best_distance = self._calculate_route_distance(best_route, dist_matrix)
        
        while improved:
            improved = False
            n = len(best_route)
            
            for i in range(1, n - 2):
                for j in range(i + 1, n):
                    if j - i == 1:
                        continue
                    
                    # Try reversing segment i..j
                    new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                    new_distance = self._calculate_route_distance(new_route, dist_matrix)
                    
                    if new_distance < best_distance - 1e-6:  # Improvement threshold
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
                        break
                if improved:
                    break
        
        return best_route, best_distance
    
    def _tournament_select(self, population: List[List[int]], 
                          fitness_scores: List[float], k: int = 3) -> List[int]:
        """Tournament selection for genetic algorithm"""
        selected = random.sample(range(len(population)), k)
        best_idx = max(selected, key=lambda i: fitness_scores[i])
        return population[best_idx].copy()
    
    def _ordered_crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Ordered crossover for permutation-based TSP"""
        n = len(parent1)
        start, end = sorted(random.sample(range(n), 2))
        
        child = [-1] * n
        child[start:end+1] = parent1[start:end+1]
        
        pos = (end + 1) % n
        for gene in parent2:
            if gene not in child:
                child[pos] = gene
                pos = (pos + 1) % n
        
        return child
    
    def _mutate(self, route: List[int]):
        """Swap mutation"""
        i, j = random.sample(range(len(route)), 2)
        route[i], route[j] = route[j], route[i]
    
    def _calculate_route_distance(self, route: List[int], dist_matrix: List[List[float]]) -> float:
        """Calculate total distance of a route given by indices"""
        distance = 0.0
        for i in range(len(route) - 1):
            distance += dist_matrix[route[i]][route[i + 1]]
        return distance
    
    def _get_segment_details(self, route: List[str], path_matrix: List[List[List[str]]], 
                            cities: List[str]) -> List[Dict]:
        """Get detailed information for each segment"""
        segments = []
        
        # Create mapping from city code to index
        city_to_idx = {city: i for i, city in enumerate(cities)}
        
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            u_idx = city_to_idx[u]
            v_idx = city_to_idx[v]
            
            path = path_matrix[u_idx][v_idx]
            
            if path:
                distance, _ = self._get_distance_and_path(u, v)
                segments.append({
                    'from': u,
                    'to': v,
                    'distance': distance,
                    'path': path
                })
        
        return segments


# Example usage and documentation
"""
Example:
    planner = MultiCityPlanner(graph)
    
    # Small set - exact optimal
    result = planner.plan_optimal_route(['SIN', 'HND', 'LHR', 'JFK'])
    print(result.algorithm_used)  # "Held-Karp DP (exact)"
    print(f"Optimal route: {result}")
    
    # Medium set - branch and bound
    cities = ['SIN', 'HND', 'LHR', 'JFK', 'CDG', 'FRA', 'DXB', 'SYD', 'LAX', 'PEK']
    result = planner.plan_optimal_route(cities, algorithm='bnb')
    print(f"Near-optimal route: {result}")
    
    # Large set - heuristic
    cities = ['SIN', 'HND', 'LHR', 'JFK', 'CDG', 'FRA', 'DXB', 'SYD', 'LAX', 
              'PEK', 'NRT', 'ICN', 'BKK', 'KUL', 'MEL']
    result = planner.plan_optimal_route(cities)
    print(f"Heuristic route: {result}")
    print(f"Optimality guarantee: {result.optimality_guarantee}")
"""