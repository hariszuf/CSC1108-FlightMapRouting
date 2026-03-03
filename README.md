# Flight Map Routing (CSC1108 Project)

## ✈️ A Comprehensive Flight Route Planning System

An advanced flight routing system that demonstrates the practical application of Data Structures & Algorithms in solving real-world transportation network problems. The system finds optimal routes between airports based on different criteria and provides sophisticated network analysis capabilities.

---

## 📑 Table of Contents
- [Core Algorithms Implemented](#core-algorithms-implemented)
- [Advanced Features](#advanced-features)
- [Non-Advanced (Essential) Features](#non-advanced-essential-features)
- [System Architecture](#system-architecture)
- [Setup Instructions](#setup-instructions)
- [Usage Guide](#usage-guide)
- [Performance Comparison](#performance-comparison)
- [Project Structure](#project-structure)

---

## 🧮 Core Algorithms Implemented

### 1. **BFS (Breadth-First Search)**
**Purpose:** Finds route with the fewest connections (minimum hops)

**How it works:** Explores the graph level by level, guaranteeing that the first time we reach the destination, we've taken the path with the fewest edges.

**Time Complexity:** O(V + E) where V = airports, E = routes
**Space Complexity:** O(V)

**Use Case:** When passengers prioritize minimizing layovers over distance or cost.
---

### 2. **Dijkstra's Algorithm**
**Purpose:** Finds shortest path based on weighted criteria (distance, time, or price)

**How it works:** Uses a priority queue to always expand the node with the smallest cumulative cost, guaranteeing optimal paths with non-negative weights.

**Time Complexity:** O((V + E) log V) with binary heap
**Space Complexity:** O(V)

**Variants Implemented:**
- **Shortest Distance** (weight = route kilometers)
- **Fastest Time** (weight = flight minutes)
- **Cheapest Price** (weight = ticket price)
---

### 3. **A* (A-Star) Search**
**Purpose:** Optimized pathfinding using heuristics for better performance

**How it works:** Enhances Dijkstra by adding a heuristic function (great-circle distance) that estimates remaining distance, guiding the search toward the goal more efficiently.

**Heuristic Used:** Haversine formula for great-circle distance between airports

**Time Complexity:** O(E) in best case, O(b^d) in worst case
**Advantage:** 30-50% faster than Dijkstra for long-haul routes
---

### 4. **Bellman-Ford Algorithm**
**Purpose:** Handles negative weights (promotional fares, discounts)

**How it works:** Relaxes all edges V-1 times, can detect negative cycles in the network.

**Time Complexity:** O(V × E)
**Space Complexity:** O(V)

**Advanced Feature:** Detects negative price cycles (arbitrage opportunities in flight pricing)
---

### 5. **Yen's K-Shortest Paths Algorithm**
**Purpose:** Finds multiple alternative routes between airports

**How it works:** Uses Dijkstra to find the first shortest path, then finds deviations (spur paths) from that path to generate alternatives.

**Time Complexity:** O(K × V × (E + V log V))
**Use Case:** Providing travelers with multiple options ranked by preference
---

## 🔧 Advanced Features

### 1. **Multi-City Trip Planner (Traveling Salesman Problem)**
**Purpose:** Plans optimal routes visiting multiple cities

**Algorithm Selection Strategy:**
- **≤ 8 cities:** Held-Karp DP (exact solution, O(n²2ⁿ))
- **9-12 cities:** Branch & Bound (near-optimal with pruning)
- **> 12 cities:** Heuristic approaches (Nearest Neighbor + 2-opt)
- **Very large:** Genetic Algorithm (metaheuristic)


### 2. **Network Analytics & Hub Detection**
**Purpose:** Identifies critically important airports using centrality measures

**Metrics Calculated:**
- **Degree Centrality:** Number of direct connections
- **Betweenness Centrality:** How often an airport lies on shortest paths between others
- **Closeness Centrality:** How quickly you can reach all other airports
- **Eigenvector Centrality:** Connection quality (connections to well-connected airports)
---

### 3. **Route Explorer with Balanced Scoring**
**Purpose:** Finds routes that balance multiple factors
---

### 4. **Intelligent Caching System**
**Purpose:** Optimizes repeated queries for better performance

**Features:**
- TTL-based expiration (1 hour default)
- LRU-like behavior with timestamp tracking
- Automatic cleanup of expired entries
---

### 5. **New Route Suggestion Engine**
**Purpose:** Identifies potentially profitable new flight connections

**Algorithm:**
1. Identify hub airports using centrality measures
2. Check if direct connection exists between hubs
3. Calculate potential demand based on hub sizes
4. Filter by distance and demand threshold
---

### 6. **Data Enhancement Features**
**Purpose:** Adds realism to the flight network

- **Flight Schedules:** Multiple daily flights with realistic timing
- **Seasonal Pricing:** Dynamic pricing based on season
- **Airport Facilities:** Amenities and ratings
- **Price Variations:** Realistic fluctuations
---

## 📋 Non-Advanced (Essential) Features

### 1. **Graph Representation**
- **Adjacency List** implementation for memory efficiency
- **O(1)** neighbor lookup
- Supports weighted edges with multiple attributes

### 2. **Multiple Export Formats**
- **JSON** - Structured data for APIs
- **CSV** - Spreadsheet compatibility
- **Plain Text** - Human-readable reports
- **Shareable Links** - Simple route sharing

### 3. **Route Result Formatting**

### 4. **Airport and Edge Models**
Immutable dataclasses ensuring data integrity
---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│           Dash Web Interface                 │
├─────────────────────────────────────────────┤
│         Unified Interface Layer               │
├─────────────────────────────────────────────┤
│  ┌──────────┬──────────┬──────────────────┐ │
│  │ BFS      │ Dijkstra │ A*               │ │
│  ├──────────┼──────────┼──────────────────┤ │
│  │Bellman-  │ Yen's K- │ Multi-City       │ │
│  │Ford      │ Shortest │ Planner          │ │
│  └──────────┴──────────┴──────────────────┘ │
├─────────────────────────────────────────────┤
│    Cache Manager  │  Export Manager         │
├─────────────────────────────────────────────┤
│         Flight Graph (Adjacency List)       │
├─────────────────────────────────────────────┤
│         JSON Dataset Loader                  │
└─────────────────────────────────────────────┘
```

---

## 🚀 Performance Comparison

| Algorithm | Time Complexity | Space Complexity | Best Use Case |
|-----------|----------------|------------------|---------------|
| BFS | O(V + E) | O(V) | Minimum connections |
| Dijkstra | O((V+E) log V) | O(V) | Weighted shortest path |
| A* | O(E) to O(b^d) | O(V) | Long-haul with heuristic |
| Bellman-Ford | O(V×E) | O(V) | Negative weight detection |
| Yen's K-Shortest | O(K×V×(E+V log V)) | O(K×V) | Multiple alternatives |
| Held-Karp DP | O(n²2ⁿ) | O(n2ⁿ) | Exact TSP (≤8 cities) |

---

## 🐍 Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-url>
cd flight-map-routing
```

### 2️⃣ Create a Virtual Environment
**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Mac / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Install Dependencies
**Windows:**
```bash
pip install -r requirements.txt
pip install dash-bootstrap-components
pip install networkx
```

**Mac:**
```bash
python3 -m pip install -r requirements.txt
pip3 install dash-bootstrap-components
pip3 install networkx
```

### 4️⃣ Dataset Setup
Ensure the dataset exists at: `data/airline_routes.json`

### 5️⃣ Run the Application
```bash
python dash_app_enhanced.py
```

The application will be available at: **http://localhost:8051**

---

## 📊 Usage Guide

### Basic Routing
1. Select departure and arrival airports
2. Choose optimization criteria:
   - 🛬 **Least Connections** (BFS)
   - 📏 **Shortest Distance** (Dijkstra)
   - ⏱️ **Fastest Time** (Dijkstra)
   - 💰 **Cheapest Price** (Dijkstra)
3. View route on interactive map

### Advanced Features
- **Multi-City Planning:** Plan optimal routes visiting multiple cities
- **K-Shortest Paths:** Find alternative routes
- **Network Analytics:** Identify hub airports and connectivity issues
- **Route Suggestions:** Discover potential new flight connections
- **Export Options:** Save routes in multiple formats

---

## 📁 Project Structure

```
flight-map-routing/
├── dash_app_enhanced.py        # Main Dash application
├── requirements.txt            # Dependencies
├── src/
│   ├── graph.py                # Flight graph implementation
│   ├── loader.py               # JSON data loader
│   ├── models.py               # Airport and Edge dataclasses
│   ├── services/
│   │   ├── routing.py          # Basic routing service
│   │   └── unified_interface.py # Unified feature interface
│   ├── algorithms/
│   │   ├── bfs.py              # BFS implementation
│   │   ├── dijkstra.py         # Dijkstra's algorithm
│   │   ├── astar.py            # A* with haversine heuristic
│   │   ├── bellman_ford.py     # Bellman-Ford for negative weights
│   │   └── yen_k_shortest.py   # Yen's K-shortest paths
│   └── features/
│       ├── multi_city_planner.py # TSP solver
│       ├── network_analyzer.py   # NetworkX analytics
│       ├── cache_manager.py      # Query caching
│       ├── export_manager.py     # Multi-format export
│       ├── enhancer.py           # Data enhancement
│       └── route_explorer.py     # Alternative route exploration
├── data/
│   └── airline_routes.json     # Airport and route dataset
└── legacy/
    └── streamlit_app.py        # Legacy prototype (reference only)
```

---

## 🎯 Key Strengths

1. **Comprehensive Algorithm Coverage:** From basic BFS to advanced TSP solvers
2. **Real-world Optimization:** Handles multiple criteria (distance, time, price, connections)
3. **Scalable Architecture:** Different algorithms for different problem sizes
4. **Interactive Visualization:** Real-time map display of routes
5. **Production-ready Features:** Caching, export, error handling
6. **Educational Value:** Demonstrates practical DSA applications

---

## 🔮 Future Enhancements

- Real-time flight data integration
- Machine learning for price prediction
- Airline preference learning
- Mobile app interface
- Weather-aware routing

---

## 📝 License

This project is developed for CSC1108 - Data Structures and Algorithms.

---

**Built with ❤️ using Python, Dash, and advanced algorithms**