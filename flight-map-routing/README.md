# Flight Map Routing — CSC1108

A flight route planning web app built for the CSC1108 Data Structures & Algorithms module. It finds optimal paths between airports using five graph algorithms and wraps them in an interactive Dash dashboard with live map visualisation.

---

## Table of Contents

- [Algorithms](#algorithms)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the App](#running-the-app)
- [Usage Guide](#usage-guide)
- [Algorithm Performance Reference](#algorithm-performance-reference)

---

## Algorithms

### BFS — Breadth-First Search
Finds the route with the fewest stopovers by exploring the graph level by level. The first time the destination is reached, it is guaranteed to be via the minimum number of edges.

- **Time:** O(V + E) &nbsp; **Space:** O(V)
- **Best for:** Passengers who want the least connections regardless of distance or cost.

---

### Dijkstra's Algorithm
Finds the shortest weighted path using a min-priority queue. Always expands the node with the lowest cumulative cost, guaranteeing optimality when edge weights are non-negative.

Three weight modes are implemented:
- **Shortest Distance** — kilometres
- **Fastest Time** — flight minutes
- **Cheapest Price** — ticket price

- **Time:** O((V + E) log V) &nbsp; **Space:** O(V)

---

### A\* Search
Extends Dijkstra with a heuristic that estimates remaining distance using the **Haversine formula** (great-circle distance). This guides the search toward the goal and reduces unnecessary exploration.

- **Time:** O(E) best case, O(b^d) worst case &nbsp; **Space:** O(V)
- **Advantage:** Typically 30–50% faster than Dijkstra on long-haul routes.

---

### Bellman-Ford
Handles negative edge weights (e.g. promotional fares or discounts) by relaxing all edges V−1 times. Also detects negative cycles in the pricing network.

- **Time:** O(V × E) &nbsp; **Space:** O(V)
- **Use case:** Routes involving discounted or dynamic pricing.

---

### Yen's K-Shortest Paths
Returns the K best routes between two airports. Runs Dijkstra to find the primary shortest path, then generates alternative "spur" paths as deviations from it.

- **Time:** O(K × V × (E + V log V)) &nbsp; **Space:** O(K × V)
- **Use case:** Giving travellers a ranked list of route options.

---

## Features

### Advanced

| Feature | Description |
|---|---|
| **Multi-City Trip Planner** | Solves a Travelling Salesman Problem variant. Uses Held-Karp DP (≤8 cities), Branch & Bound (9–12 cities), Nearest Neighbour + 2-opt (>12 cities), or Genetic Algorithm for very large inputs. |
| **Network Analytics & Hub Detection** | Calculates degree, betweenness, closeness, and eigenvector centrality to identify the most critical airports in the network. |
| **Route Explorer** | Finds balanced routes that trade off distance, time, price, and number of connections simultaneously. |
| **Intelligent Caching** | TTL-based query cache (1-hour default) with LRU-style eviction and automatic cleanup of stale entries. |
| **New Route Suggestion Engine** | Identifies hub pairs with no direct connection and high estimated demand, surfacing potentially profitable new routes. |
| **Data Enhancement** | Adds realistic flight schedules, seasonal pricing, airport facilities, and price variation to the base dataset. |

### Essential

| Feature | Description |
|---|---|
| **Graph Representation** | Adjacency-list structure with O(1) neighbour lookup and multi-attribute weighted edges. |
| **Multi-Format Export** | Export route results as JSON, CSV, plain text, or a shareable link. |
| **Airport & Edge Models** | Immutable dataclasses enforcing data integrity throughout the pipeline. |
| **Interactive Map** | Live Plotly/Dash map that renders routes, stopovers, and airport markers in real time. |

---

## System Architecture

```
┌──────────────────────────────────────────────────┐
│              Dash Web Interface                   │
│         dash_app_enhanced.py  (port 8051)        │
├────────────────────┬─────────────────────────────┤
│   layout/          │   callbacks/                 │
│   basic_routing.py │   routing_callbacks.py       │
│   advanced_        │   advanced_callbacks.py      │
│   features.py      │   animation_callbacks.py     │
├────────────────────┴─────────────────────────────┤
│              utils/  (charts, helpers)            │
├──────────────────────────────────────────────────┤
│           src/services/unified_interface.py       │
├───────────┬───────────┬──────────────────────────┤
│ bfs.py    │dijkstra.py│ astar.py                 │
│bellman_   │yen_k_     │ (src/algorithms/)         │
│ford.py    │shortest.py│                           │
├───────────┴───────────┴──────────────────────────┤
│  features: multi_city_planner · network_analyzer  │
│            cache_manager · export_manager         │
│            enhancer · route_explorer              │
├──────────────────────────────────────────────────┤
│     src/graph.py  (adjacency list)               │
│     src/loader.py (JSON parser)                  │
│     src/models.py (Airport, Edge dataclasses)    │
├──────────────────────────────────────────────────┤
│          data/airline_routes.json                │
└──────────────────────────────────────────────────┘
```

---

## Project Structure

```
CSC1108-FlightMapRouting/
├── README.md
├── requirements.txt                  # Root-level pinned deps
└── flight-map-routing/
    ├── dash_app_enhanced.py          # Entry point — runs on port 8051
    ├── requirements.txt              # App-level deps (same pins)
    ├── data/
    │   └── airline_routes.json       # Airport and route dataset (~22 MB)
    ├── src/
    │   ├── graph.py                  # Adjacency-list flight graph
    │   ├── loader.py                 # JSON dataset loader
    │   ├── models.py                 # Airport and Edge dataclasses
    │   ├── algorithms/
    │   │   ├── bfs.py
    │   │   ├── dijkstra.py
    │   │   ├── astar.py
    │   │   ├── bellman_ford.py
    │   │   └── yen_k_shortest.py
    │   ├── services/
    │   │   ├── routing.py            # Basic routing service
    │   │   └── unified_interface.py  # Single interface for all features
    │   ├── features/
    │   │   ├── multi_city_planner.py
    │   │   ├── network_analyzer.py
    │   │   ├── algorithm_comparator.py
    │   │   ├── cache_manager.py
    │   │   ├── export_manager.py
    │   │   ├── enhancer.py
    │   │   └── route_explorer.py
    │   └── assets/
    │       ├── css/style.css
    │       ├── logo.svg
    │       └── plane.jpg / plane1.png
    ├── layout/
    │   ├── basic_routing.py          # Basic routing tab layout
    │   └── advanced_features.py      # Advanced features tab layout
    ├── callbacks/
    │   ├── routing_callbacks.py
    │   ├── advanced_callbacks.py
    │   └── animation_callbacks.py
    ├── utils/
    │   ├── charts.py                 # Plotly chart helpers
    │   └── helpers.py
    └── legacy/
        └── app.py                    # Original Streamlit prototype (reference only)
```

---

## Setup

### Prerequisites

- Python 3.10 or higher
- `pip`

### 1. Clone the repository and navigate to the app directory

```bash
git clone <your-repo-url>
cd CSC1108-FlightMapRouting/flight-map-routing
```

> **Note:** All subsequent commands must be run from inside the `flight-map-routing/` directory.

### 2. Create a virtual environment

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** If you hit any issues on macOS with `numpy` or `pandas`, try `pip install --upgrade pip` first.

### 4. Verify the dataset

Confirm that `data/airline_routes.json` exists inside `flight-map-routing/`. This file is ~22 MB and must be present before the app will start.

---

## Running the App

```bash
python dash_app_enhanced.py
```

Then open **http://localhost:8051** in your browser.

On startup the console prints a summary of loaded airports, routes, countries, and which optional modules loaded successfully.

---

## Usage Guide

### Basic Routing

1. Go to the **Basic Routing** tab.
2. Select a departure and arrival airport.
3. Choose an optimisation mode:
   - **Least Connections** — BFS
   - **Shortest Distance** — Dijkstra (km)
   - **Fastest Time** — Dijkstra (minutes)
   - **Cheapest Price** — Dijkstra (price)
4. The route appears on the map with a breakdown of stops, distance, time, and cost.

### Advanced Features

- **K-Shortest Paths** — Enter source, destination, and K to get ranked alternative routes.
- **Multi-City Planner** — Add multiple cities; the planner selects the appropriate TSP algorithm based on city count.
- **Network Analytics** — View centrality rankings to identify the busiest and most critical hub airports.
- **Route Suggestions** — Discover airport pairs with high demand and no existing direct connection.
- **Export** — Download any result as JSON, CSV, or plain text from the results panel.

---

## Algorithm Performance Reference

| Algorithm | Time Complexity | Space | Best Use Case |
|---|---|---|---|
| BFS | O(V + E) | O(V) | Fewest connections |
| Dijkstra | O((V + E) log V) | O(V) | Weighted shortest path |
| A* | O(E) | O(V) | Faster with heuristic |
| Bellman-Ford | O(VE) | O(V) | Negative weights |
| Yen's KSP | O(K (E + V log V)) | O(KV) | Multiple paths |
| Held-Karp DP | O(n² 2ⁿ) | O(n 2ⁿ) | Small TSP |

---