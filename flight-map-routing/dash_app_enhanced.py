# dash_app_enhanced.py
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import time
import base64
import io
import json
from pathlib import Path
import math
# Dash components
from dash import Dash, html, dcc, Input, Output, State, dash_table, no_update, callback_context
import plotly.graph_objects as go
import plotly.express as px
import dash_leaflet as dl

# Local imports - core
from src.loader import load_graph
from src.models import RouteResult
# Dash components

# Try to import all enhanced features
try:
    from src.services.unified_interface import FlightRouteUnified
    UNIFIED_AVAILABLE = True
except ImportError as e:
    UNIFIED_AVAILABLE = False
    print(f"Unified interface not available: {e}")

try:
    from src.algorithms.astar import astar_shortest_path
    ASTAR_AVAILABLE = True
except ImportError:
    ASTAR_AVAILABLE = False

try:
    from src.algorithms.bellman_ford import bellman_ford_cheapest
    BELLMAN_FORD_AVAILABLE = True
except ImportError:
    BELLMAN_FORD_AVAILABLE = False

try:
    from src.algorithms.yen_k_shortest import yen_k_shortest_paths
    YEN_AVAILABLE = True
except ImportError:
    YEN_AVAILABLE = False

try:
    from src.features.algorithm_comparator import AlgorithmComparator
    COMPARATOR_AVAILABLE = True
except ImportError:
    COMPARATOR_AVAILABLE = False

try:
    from src.features.cache_manager import CacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from src.features.enhancer import DataEnhancer
    ENHANCER_AVAILABLE = True
except ImportError:
    ENHANCER_AVAILABLE = False

# --- Robust dataset path ---
ROOT = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    ROOT / "data" / "airline_routes.json",
    ROOT / "data" / "airline_routes - Copy.json",
]

def get_data_path() -> str:
    for p in DATA_CANDIDATES:
        if p.exists():
            return str(p)
    raise FileNotFoundError("Dataset not found in ./data/")

# Load graph and initialize unified interface
GRAPH = load_graph(get_data_path())

if UNIFIED_AVAILABLE:
    flight_system = FlightRouteUnified(GRAPH)
    print("✅ Unified Flight System initialized with all features")
else:
    flight_system = None
    print("⚠️ Running in basic mode - some features unavailable")

# Helper functions
def path_to_coords(graph, path):
    """Convert path to list of coordinates"""
    return [(graph.airports[c].lat, graph.airports[c].lon) for c in path]

def get_airport_options(graph, search_term=""):
    """Get airport options with optional search filtering"""
    options = []
    for code in sorted(graph.airports.keys())[:10000]:
        airport = graph.airports[code]
        label = f"{code} - {airport.city}, {airport.country}"
        if search_term.lower() in label.lower() or not search_term:
            options.append({'label': label, 'value': code})
    return options

def count_routes(graph):
    """Count total routes in graph"""
    count = 0
    for src in graph.adj:
        count += len(graph.adj[src])
    return count

def format_duration(minutes):
    """Format minutes to hours and minutes"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"

# Get the absolute path to your assets folder
ASSETS_PATH = Path(__file__).parent / "src" / "assets"

# Initialize the app
app = Dash(
    __name__,
    assets_folder=str(ASSETS_PATH),
    suppress_callback_exceptions=True,
    external_stylesheets=[
        "https://unpkg.com/leaflet.fullscreen@1.6.0/Control.FullScreen.css"
    ],
    external_scripts=[
        "https://unpkg.com/leaflet.fullscreen@1.6.0/Control.FullScreen.js"
    ]
)
app.title = "FlightRoute Pro - Complete Flight Routing System"

# Main Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.I(className="fas fa-globe-americas", style={'fontSize': '3em', 'color': '#a5b4fc', 'marginRight': '20px'})
        ], style={'display': 'inline-block', 'verticalAlign': 'middle'}),
        html.Div([
            html.H1("FlightRoute Pro"),
            html.P("Advanced Flight Network Intelligence", 
                   style={'fontSize': '1.2em', 'color': '#8f9bb3', 'fontWeight': '300'}),
        ], style={'display': 'inline-block', 'verticalAlign': 'middle'}),
        
        html.Div([
            html.Span([
                html.I(className="fas fa-plane-departure", style={'marginRight': '8px'}),
                f"{len(GRAPH.airports):,} Airports"
            ], className="stats-badge"),
            html.Span([
                html.I(className="fas fa-route", style={'marginRight': '8px'}),
                f"{count_routes(GRAPH):,} Routes"
            ], className="stats-badge"),
            html.Span([
                html.I(className="fas fa-map-marker-alt", style={'marginRight': '8px'}),
                f"{len(set(a.country for a in GRAPH.airports.values()))} Countries"
            ], className="stats-badge"),
        ], style={'float': 'right', 'marginTop': '20px'})
    ], className="header"),
    
    # Main Tabs - Added margin-top in CSS
    dcc.Tabs(id='main-tabs', value='basic-routing', children=[
        # Basic Routing Tab
        dcc.Tab(label='🎯 Basic Routing', value='basic-routing', children=[
            html.Div([
                # Left Column
            html.Div([

            # ROUTE CONFIG
            html.Div([
                html.Div("Route Configuration", className="card-header"),

                html.Label("From:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='src-dropdown',
                    options=get_airport_options(GRAPH),
                    placeholder="Type to search departure...",
                    value='SIN' if 'SIN' in GRAPH.airports else None,
                    searchable=True,
                    clearable=True,
                    className="airport-dd"
                ),

                html.Label("To:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                dcc.Dropdown(
                    id='dst-dropdown',
                    options=get_airport_options(GRAPH),
                    placeholder="Type to search arrival...",
                    value='HND' if 'HND' in GRAPH.airports else None,
                    searchable=True,
                    clearable=True,
                    className="airport-dd"
                ),

                html.Label("Optimize for:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
               dcc.RadioItems(
                    id='optimization-mode',
                    options=[
                        {'label': '🛬 Least Connections (BFS)', 'value': 'hops'},
                        {'label': '📏 Shortest Distance', 'value': 'distance'},
                        {'label': '⏱️ Fastest Time', 'value': 'time'},
                        {'label': '💰 Cheapest Price', 'value': 'price'},
                    ],
                    value='distance',
                    labelStyle={
                        'display': 'flex',
                        'alignItems': 'center',
                        'gap': '10px',
                        'marginBottom': '12px'
                    }
                ),

                html.Button("🔍 Find Route", id='find-route-btn',
                            className="btn-primary", n_clicks=0,
                            style={'marginTop': '20px'}),

            ], className="card", style={'width':'22%'}),


            # MAP
            html.Div([
                
                dcc.Tabs(id='results-tabs', value='map-tab', children=[
                    
                    dcc.Tab(label='🗺️ Route Map', value='map-tab', children=[
                dl.Map(
                    id='flight-map',
                    center=[20, 0],
                    zoom=2,
                    maxBounds=[[-90, -180], [90, 180]],
                    maxBoundsViscosity=1.0,
                    worldCopyJump=False,
                    style={'width': '100%', 'height': '520px'},
                    children=[
                        dl.LayersControl([
    
                # Normal Map
                dl.BaseLayer(
                    dl.TileLayer(
                        url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                        noWrap=True
                    ),
                    name="Map",
                    checked=True
                ),

                # Satellite Map
                dl.BaseLayer(
                    dl.TileLayer(
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                        noWrap=True
                    ),
                    name="Satellite",
                    checked=False
                )

            ]),
                        dl.FullScreenControl(position="topright"),


                        dl.LayerGroup(id='map-layers'),
                        dl.Polyline(
                            id="animated-route",
                            positions=[],
                            color="#ff3300",
                            weight=6
                        ),

                        # ADD THIS

                    ]
                )
                    ]),

                    dcc.Tab(label='📊 Route Analysis', value='analysis-tab',
                        children=[dcc.Graph(id='route-analysis', style={'height':'520px'})]),

                    dcc.Tab(label='📈 Performance', value='performance-tab',
                        children=[dcc.Graph(id='performance-metrics', style={'height':'520px'})])

                ])
            ], style={'width':'56%'}),


            # ROUTE SUMMARY
            html.Div([
                html.Div("📋 Route Summary", className="card-header"),
                html.Div(id='route-summary', children=[
                    html.P("Select airports and click 'Find Route'",
                        style={'color':'#8f9bb3','textAlign':'center'})
                ])
            ], className="card", style={'width':'22%'}),

        ],
        style={
            'display':'flex',
            'gap':'20px',
            'alignItems':'flex-start'
        }),
                
            ])
        ]),
        
        # Advanced Features Tab
        dcc.Tab(label='🔧 Advanced Features', value='advanced', children=[
            html.Div([
                # Multi-City Planning
                html.Div([
                    html.Div("🗺️ Multi-City Trip Planner", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                                id='multi-city-selector',
                                options=get_airport_options(GRAPH),
                                placeholder="Select cities to visit.",
                                multi=True,
                                value=['SIN', 'HND', 'LHR'] if all(c in GRAPH.airports for c in ['SIN','HND','LHR']) else [],
                                searchable=True
                            ),
                        html.Div([
                            dcc.RadioItems(
                                id='tsp-method',
                                options=[
                                    {'label': ' Auto (DP for ≤8 cities)', 'value': 'auto'},
                                    {'label': ' Heuristic (Nearest Neighbor)', 'value': 'heuristic'},
                                ],
                                value='auto',
                                labelStyle={'display': 'inline-block', 'marginRight': '20px'}
                            ),
                        ], style={'marginTop': '10px'}),
                        html.Button("📋 Plan Optimal Route", id='plan-multi-city-btn', 
                                  className="btn-secondary", n_clicks=0),
                        html.Div(id='multi-city-results', style={'marginTop': '15px'})
                    ])
                ], className="card"),
                
                # K-Shortest Paths
                html.Div([
                    html.Div(f"🔄 K-Shortest Paths {'' if YEN_AVAILABLE else '(Not Available)'}", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                                id='ksp-from',
                                options=get_airport_options(GRAPH),
                                placeholder="From...",
                                searchable=True
                            ),
                        dcc.Dropdown(
                                id='ksp-to',
                                options=get_airport_options(GRAPH),
                                placeholder="To...",
                                searchable=True
                            ),
                        html.Div([
                            dcc.Input(
                                id='k-value',
                                type='number',
                                min=1,
                                max=10,
                                value=3,
                                className="dash-input",
                                style={'width': '80px', 'marginRight': '10px'}
                            ),
                            dcc.RadioItems(
                                id='k-mode',
                                options=[
                                    {'label': ' Distance', 'value': 'distance'},
                                    {'label': ' Time', 'value': 'time'},
                                    {'label': ' Price', 'value': 'price'},
                                ],
                                value='distance',
                                inline=True
                            ),
                        ], style={'marginTop': '10px', 'display': 'flex', 'alignItems': 'center'}),
                        html.Button("🔍 Find K Paths", id='find-k-paths-btn', 
                                  className="btn-secondary", n_clicks=0, disabled=not YEN_AVAILABLE),
                        html.Div(id='k-paths-results')
                    ])
                ], className="card"),
                
                # Algorithm Comparison
                html.Div([
                    html.Div("⚡ Algorithm Comparison", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                            id='compare-from',
                            options=get_airport_options(GRAPH),
                            placeholder="From...",
                            searchable=True,
                            clearable=True
                        ),

                        dcc.Dropdown(
                            id='compare-to',
                            options=get_airport_options(GRAPH),
                            placeholder="To...",
                            searchable=True,
                            clearable=True
                        ),
                        html.Button("📊 Compare All Algorithms", id='compare-algos-btn', 
                                  className="btn-secondary", n_clicks=0),
                        html.Div(id='comparison-results')
                    ])
                ], className="card"),
            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
            
            # Right column advanced features
            html.Div([
             
                # Export Options
                html.Div([
                    html.Div("📤 Export & Share", className="card-header"),
                    html.Div([
                        html.Button("📄 Export as JSON", id='export-json-btn', 
                                  className="download-btn", n_clicks=0),
                        html.Button("📊 Export as CSV", id='export-csv-btn', 
                                  className="download-btn", n_clicks=0),
                        html.Button("📝 Export as Text", id='export-text-btn', 
                                  className="download-btn", n_clicks=0),
                        html.Div(id='export-link', style={'marginTop': '15px'})
                    ])
                ], className="card"),
                
                # Route Explorer
                html.Div([
                    html.Div("🔄 Route Explorer", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                            id='explorer-from',
                            options=get_airport_options(GRAPH),
                            placeholder="From...",
                            searchable=True,
                            clearable=True
                        ),

                        dcc.Dropdown(
                            id='explorer-to',
                            options=get_airport_options(GRAPH),
                            placeholder="To...",
                            searchable=True,
                            clearable=True
                        ),
                        html.Button("🔍 Explore Alternatives", id='explore-routes-btn', 
                                  className="btn-secondary", n_clicks=0),
                        html.Div(id='explore-results')
                    ])
                ], className="card"),
                
                # Cache Status
                html.Div([
                    html.Div("💾 Cache Status", className="card-header"),
                    html.Div(id='cache-status', children=[
                        html.P(f"Cache Manager: {'✅ Active' if CACHE_AVAILABLE else '❌ Not Available'}", 
                              style={'color': '#e5e9f0'})
                    ]),
                    html.Button("🗑️ Clear Cache", id='clear-cache-btn', 
                              className="btn-secondary", n_clicks=0, disabled=not CACHE_AVAILABLE),
                ], className="card"),
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ]),
    ]),
    
    # Hidden div for storing current route
    dcc.Store(id='current-route-store'),
    dcc.Download(id='download-data'),
    dcc.Interval(
        id="plane-anim",
        interval=300,
        n_intervals=0

    ),

    dcc.Store(id="route-coords"),
    # Footer
    html.Div([
        html.P("© 2025 FlightRoute Pro - Complete Flight Routing System"),
        html.P([
            "Algorithms: BFS | Dijkstra | A*" + (" ✓" if ASTAR_AVAILABLE else "") + 
            " | Bellman-Ford" + (" ✓" if BELLMAN_FORD_AVAILABLE else "") + 
            " | Yen's K-Shortest" + (" ✓" if YEN_AVAILABLE else "")
        ])
    ], className="footer")
        ])


# --- Autocomplete dropdown options (search-as-you-type) ---
@app.callback(
    Output('src-dropdown', 'options'),
    Input('src-dropdown', 'search_value')
)
def filter_src_options(search_value):
    # Limit results for performance
    return get_airport_options(GRAPH, search_value or "")

@app.callback(
    Output('dst-dropdown', 'options'),
    [Input('dst-dropdown', 'search_value'),
     Input('src-dropdown', 'value')]
)
def filter_dst_options(search_value, src_value):
    opts = get_airport_options(GRAPH, search_value or "")
    if src_value:
        opts = [o for o in opts if o['value'] != src_value]
    return opts

# Callbacks

@app.callback(
    [Output('route-summary', 'children'),
     Output('map-layers', 'children'),
     Output('route-analysis', 'figure'),
     Output('performance-metrics', 'figure'),
     Output('current-route-store', 'data')],
    Input('find-route-btn', 'n_clicks'),
    [State('src-dropdown', 'value'),
     State('dst-dropdown', 'value'),
     State('optimization-mode', 'value')]
)
def find_route(n_clicks, src, dst, mode):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="No data to display",
        annotations=[{
            'text': 'Select airports and click Find Route',
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False
        }],
        height=500
    )
    
    if not n_clicks or not src or not dst:
        return html.P("Select airports and click 'Find Route'", style={'color': '#666'}), [], empty_fig, empty_fig, None
    
    start_time = time.time()
    
    if flight_system:
        route_result = flight_system.find_route(src, dst, mode)
    else:
        from src.services.routing import find_route as basic_find_route
        route_result = basic_find_route(GRAPH, src, dst, mode)
    
    elapsed_time = (time.time() - start_time) * 1000
    
    if not route_result:
        return html.Div([
            html.I(className="fas fa-exclamation-triangle"),
            f" No route found between {src} and {dst}"
        ], className="error-message"), [], empty_fig, empty_fig, None
    
    # Store route result as JSON
    route_data = {
        'path': route_result.path,
        'total_km': route_result.total_km,
        'total_minutes': route_result.total_minutes,
        'total_price': route_result.total_price
    }
    
    # Create summary
    summary = html.Div([
        html.Div(f"✓ Route found in {elapsed_time:.2f}ms", className="success-message"),
        html.H4(f"Route: {route_result.pretty()}", style={'color': '#667eea'}),
        html.Div([
            html.Div([
                html.Div("Connections", className="metric-label"),
                html.Div(f"{route_result.hops}", className="metric-value")
            ], className="metric-box"),
            html.Div([
                html.Div("Distance", className="metric-label"),
                html.Div(f"{route_result.total_km:.0f} km", className="metric-value")
            ], className="metric-box"),
            html.Div([
                html.Div("Duration", className="metric-label"),
                html.Div(format_duration(route_result.total_minutes), className="metric-value")
            ], className="metric-box"),
            html.Div([
                html.Div("Price", className="metric-label"),
                html.Div(f"${route_result.total_price:.2f}", className="metric-value")
            ], className="metric-box"),
        ], className="metric-grid")
    ])
    
    # Create map layers
    coords = path_to_coords(GRAPH, route_result.path)
    
    coords = path_to_coords(GRAPH, route_result.path)

    markers = []

    for i, code in enumerate(route_result.path):
        airport = GRAPH.airports[code]
        color = 'green' if i == 0 else 'red' if i == len(route_result.path)-1 else 'blue'

        markers.append(
            dl.Marker(
                position=(airport.lat, airport.lon),
                children=[dl.Tooltip(f"{code} - {airport.city}")],
                icon={
                    'iconUrl': f'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{color}.png',
                    'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                    'iconSize': [25, 41],
                    'iconAnchor': [12, 41]
                }
            )
        )


    plane = dl.Marker(
        id="plane-marker",
        position=coords[0],
        icon={
            "iconUrl": "https://cdn-icons-png.flaticon.com/512/7893/7893979.png",
            "iconSize": [40,40],
            "iconAnchor": [20,20],
            "className": "plane-icon"
        }
    )
    glow1 = dl.Polyline(
        positions=coords,
        color="#ff6b6b",
        weight=14,
        opacity=0.15
    )

    glow2 = dl.Polyline(
        positions=coords,
        color="#ff6b6b",
        weight=8,
        opacity=0.35
    )

    route_line = dl.Polyline(
        positions=coords,
        color="#3bffef",
        weight=5,
        opacity=0.9
    )
  
    map_layers = [glow1, glow2, route_line] + markers + [plane]
    
    # Create analysis figure
    analysis_fig = create_route_analysis(GRAPH, route_result.path)
    
    # Create performance comparison
    performance_fig = create_performance_comparison(GRAPH, src, dst, mode)
    
    route_data["coords"] = coords
    return summary, map_layers, analysis_fig, performance_fig, route_data

# dash_app_enhanced.py (fixed multi-city callback)

# In dash_app_enhanced.py - replace the multi-city callback with this:

@app.callback(
    Output('multi-city-results', 'children'),
    Input('plan-multi-city-btn', 'n_clicks'),
    [State('multi-city-selector', 'value'),
     State('tsp-method', 'value')]
)
def plan_multi_city(n_clicks, cities, method):
    if not n_clicks or not cities or len(cities) < 2:
        return html.P("Select at least 2 cities to plan a route")
    
    if not flight_system or not hasattr(flight_system, 'multi_city_planner') or not flight_system.multi_city_planner:
        return html.Div("Multi-city planning not available", className="info-message")
    
    try:
        # Map UI method to algorithm parameter
        algorithm_map = {
            'auto': 'auto',
            'heuristic': 'heuristic',
            'exact': 'exact',
            'bnb': 'bnb',
            'genetic': 'genetic'
        }
        
        # Call the planner - now returns TSPResult object
        result = flight_system.multi_city_planner.plan_optimal_route(
            cities, 
            algorithm=algorithm_map.get(method, 'auto')
        )
        
        # Check if route exists (TSPResult object attributes)
        if not result or not result.route:
            return html.Div("No valid route found", className="error-message")
        
        # Access attributes directly (not .get())
        route = result.route
        total_dist = result.total_distance
        algorithm_used = result.algorithm_used
        optimality = result.optimality_guarantee
        time_ms = result.computation_time_ms
        
        # Create detailed result display
        return html.Div([
            html.Div([
                html.I(className="fas fa-check-circle", style={'color': '#10b981', 'marginRight': '10px'}),
                html.Span("Route Found Successfully", style={'fontWeight': 'bold', 'fontSize': '1.1em'})
            ], className="success-message", style={'marginBottom': '15px'}),
            
            html.Div([
                html.H5("Optimal Route:", style={'color': '#a5b4fc', 'marginBottom': '10px'}),
                html.Div(
                    ' → '.join(route),
                    style={
                        'background': 'linear-gradient(135deg, #1e2b4a 0%, #151f37 100%)',
                        'padding': '15px',
                        'borderRadius': '12px',
                        'fontSize': '1.1em',
                        'fontWeight': '500',
                        'color': '#ffffff',
                        'marginBottom': '15px',
                        'border': '1px solid rgba(165, 180, 252, 0.2)'
                    }
                ),
                
                html.Div([
                    html.Div([
                        html.Div("Total Distance", className="metric-label"),
                        html.Div(f"{total_dist:.2f} km", className="metric-value")
                    ], className="metric-box", style={'flex': '1'}),
                    
                    html.Div([
                        html.Div("Segments", className="metric-label"),
                        html.Div(f"{len(route)-1}", className="metric-value")
                    ], className="metric-box", style={'flex': '1'}),
                ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '15px'}),
                
                html.Div([
                    html.Div([
                        html.Strong("Algorithm: ", style={'color': '#a5b4fc'}),
                        html.Span(algorithm_used, style={'color': '#e5e9f0'})
                    ]),
                    html.Div([
                        html.Strong("Optimality: ", style={'color': '#a5b4fc'}),
                        html.Span(optimality, style={'color': '#e5e9f0'})
                    ]),
                    html.Div([
                        html.Strong("Computation Time: ", style={'color': '#a5b4fc'}),
                        html.Span(f"{time_ms:.2f} ms", style={'color': '#e5e9f0'})
                    ]) if time_ms > 0 else html.Div(),
                ], style={
                    'background': 'rgba(0,0,0,0.2)',
                    'padding': '12px',
                    'borderRadius': '8px',
                    'fontSize': '0.95em'
                }),
                
                # Show segments if available
                html.Div([
                    html.H6("Segment Details:", style={'color': '#a5b4fc', 'marginTop': '15px', 'marginBottom': '10px'}),
                    html.Div([
                        html.Div([
                            html.Div(f"{seg['from']} → {seg['to']}", 
                                    style={'fontWeight': '500', 'color': '#ffffff'}),
                            html.Div(f"{seg['distance']:.2f} km", 
                                    style={'color': '#8f9bb3', 'fontSize': '0.9em'})
                        ], style={
                            'padding': '8px 12px',
                            'background': 'rgba(255,255,255,0.05)',
                            'borderRadius': '6px',
                            'marginBottom': '5px'
                        }) for seg in result.segments[:5]  # Show first 5 segments
                    ])
                ]) if result.segments else html.Div(),
                
            ])
            
        ], className="card", style={'padding': '20px'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div([
            html.I(className="fas fa-exclamation-triangle", style={'marginRight': '10px'}),
            f"Error planning route: {str(e)}"
        ], className="error-message")

@app.callback(
    Output('k-paths-results', 'children'),
    Input('find-k-paths-btn', 'n_clicks'),
    [State('ksp-from', 'value'),
     State('ksp-to', 'value'),
     State('k-value', 'value'),
     State('k-mode', 'value')]
)
def find_k_paths(n_clicks, src, dst, k, mode):
    if not n_clicks or not src or not dst:
        return None
    
    if not YEN_AVAILABLE or not flight_system:
        return html.Div("Yen's algorithm not available", className="error-message")
    
    try:
        paths = flight_system.find_k_shortest_paths(src, dst, k, mode)
        
        if not paths:
            return html.Div("No paths found", className="info-message")
        
        results = []
        for path_info in paths:
            path = path_info['path']
            cost = path_info['cost']
            results.append(html.Div([
                html.H5(f"Path #{path_info['rank']} - Cost: {cost:.2f}"),
                html.P(f"{' → '.join(path)}"),
                html.Hr()
            ]))
        
        return html.Div([
            html.H4(f"Found {len(paths)} paths:"),
            *results
        ])
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="error-message")

@app.callback(
    Output('comparison-results', 'children'),
    Input('compare-algos-btn', 'n_clicks'),
    [State('compare-from', 'value'),
     State('compare-to', 'value')]
)
def compare_algorithms(n_clicks, src, dst):
    if not n_clicks or not src or not dst:
        return None
    
    if not COMPARATOR_AVAILABLE or not flight_system:
        # Create simple comparison
        results = []
        
        from src.services.routing import find_route
        for mode in ['hops', 'distance', 'time', 'price']:
            s = time.time()
            route = find_route(GRAPH, src, dst, mode)
            e = time.time()
            results.append({
                'Mode': mode,
                'Found': '✓' if route else '✗',
                'Time (ms)': f"{(e-s)*1000:.2f}"
            })
        
        df = pd.DataFrame(results)
        return html.Div([
            html.H5("Basic Comparison:"),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'color': '#e5e9f0',
                    'backgroundColor': '#1e2b4a',
                    'textAlign': 'center',
                    'border': '1px solid rgba(255, 255, 255, 0.08)'
                },
                style_header={
                    'backgroundColor': '#2d3b5e',
                    'color': '#ffffff',
                    'fontWeight': 'bold',
                    'border': '1px solid rgba(165, 180, 252, 0.3)'
                }
            )
        ])
    
    try:
        results = flight_system.compare_algorithms(src, dst)
        
        if not results:
            return html.Div("No comparison results", className="info-message")
        
        data = []
        for name, info in results.items():
            data.append({
                'Algorithm': name,
                'Found': '✓',
                'Cost': f"{info['cost']:.2f}",
                'Path': ' → '.join(info['path'][:3]) + ('...' if len(info['path']) > 3 else '')
            })
        
        return html.Div([
            dash_table.DataTable(
                data=data,
                columns=[{'name': i, 'id': i} for i in ['Algorithm', 'Found', 'Cost', 'Path']],
                style_table={'overflowX': 'auto'},

                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'color': '#e5e9f0',
                    'backgroundColor': '#1e2b4a',
                    'border': '1px solid rgba(255, 255, 255, 0.08)'
                },

                style_data={
                    'color': '#e5e9f0',
                    'backgroundColor': '#1e2b4a'
                },

                style_header={
                    'backgroundColor': '#2d3b5e',
                    'color': '#ffffff',
                    'fontWeight': 'bold',
                    'border': '1px solid rgba(165, 180, 252, 0.3)'
                }
            )
        ])
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="error-message")


def network_analytics(hubs_clicks, isolated_clicks, suggest_clicks):
    ctx = callback_context
    if not ctx.triggered:
        return html.P("Click a button to analyze the network", 
                     style={'color': '#8f9bb3', 'textAlign': 'center'})
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Always return something, even if there's an error
    try:
        if button_id == 'show-hubs-btn':
            # Check if flight_system exists
            if not flight_system:
                return html.Div("Flight system not initialized", className="error-message")
            
            # Try to get hub airports
            try:
                hubs_df = flight_system.get_hub_airports(10)
                print(f"Hub DataFrame type: {type(hubs_df)}")
                print(f"Hub DataFrame content: {hubs_df}")
                
                if hubs_df is None or (isinstance(hubs_df, pd.DataFrame) and hubs_df.empty):
                    return html.Div("No hub data available", className="info-message")
                
                if isinstance(hubs_df, pd.DataFrame):
                    # Create a simple table first to test
                    return html.Div([
                        html.H5("🏆 Top Hub Airports", 
                               style={'color': '#a5b4fc', 'marginBottom': '15px'}),
                        html.Table([
                            html.Thead(html.Tr([html.Th(col) for col in ['Airport', 'City', 'Country', 'Connections', 'Score']])),
                            html.Tbody([
                                html.Tr([
                                    html.Td(str(row.get('airport', 'N/A'))),
                                    html.Td(str(row.get('city', 'N/A'))),
                                    html.Td(str(row.get('country', 'N/A'))),
                                    html.Td(str(row.get('connections', 'N/A'))),
                                    html.Td(f"{float(row.get('hub_score', 0)):.3f}")
                                ]) for _, row in hubs_df.head(10).iterrows()
                            ])
                        ], style={
                            'width': '100%',
                            'borderCollapse': 'collapse',
                            'background': '#1e2b4a',
                            'borderRadius': '8px',
                            'overflow': 'hidden'
                        })
                    ])
                else:
                    return html.Div(f"Unexpected data type: {type(hubs_df)}", className="error-message")
                    
            except Exception as e:
                print(f"Error in get_hub_airports: {str(e)}")
                import traceback
                traceback.print_exc()
                return html.Div(f"Error getting hub airports: {str(e)}", className="error-message")
        
        elif button_id == 'show-isolated-btn':
            if not flight_system:
                return html.Div("Flight system not initialized", className="error-message")
            
            try:
                isolated = flight_system.get_isolated_airports(min_connections=3)
                print(f"Isolated airports: {isolated}")
                
                if isolated is None:
                    return html.Div("Isolation analysis returned None", className="info-message")
                
                if not isolated:
                    return html.Div([
                        html.I(className="fas fa-check-circle", style={'color': '#10b981', 'marginRight': '10px'}),
                        " No isolated airports found - network is well connected!"
                    ], className="success-message")
                
                return html.Div([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle", 
                              style={'color': '#f59e0b', 'marginRight': '10px'}),
                        html.Span(f"Found {len(isolated)} airports with poor connectivity", 
                                 style={'fontWeight': 'bold'})
                    ], style={'marginBottom': '15px'}),
                    html.Div(
                        ', '.join(isolated[:20]) + ('...' if len(isolated) > 20 else ''),
                        style={
                            'background': '#1e2b4a',
                            'padding': '15px',
                            'borderRadius': '8px',
                            'color': '#e5e9f0'
                        }
                    )
                ])
                
            except Exception as e:
                print(f"Error in get_isolated_airports: {str(e)}")
                return html.Div(f"Error finding isolated airports: {str(e)}", className="error-message")
        
        elif button_id == 'suggest-routes-btn':
            if not flight_system:
                return html.Div("Flight system not initialized", className="error-message")
            
            try:
                suggestions = flight_system.suggest_new_routes(threshold=0.3)
                print(f"Suggestions: {suggestions}")
                
                if suggestions is None:
                    return html.Div("Route suggestions returned None", className="info-message")
                
                if not suggestions:
                    return html.Div([
                        html.I(className="fas fa-info-circle", 
                              style={'color': '#60a5fa', 'marginRight': '10px'}),
                        " No profitable route suggestions found"
                    ], className="info-message")
                
                # Create a simple list display
                return html.Div([
                    html.H5("💡 Suggested New Routes", 
                           style={'color': '#a5b4fc', 'marginBottom': '15px'}),
                    html.Div([
                        html.Div([
                            html.Div(f"{s.get('from', 'N/A')} → {s.get('to', 'N/A')}", 
                                    style={'fontWeight': 'bold'}),
                            html.Div(f"Distance: {s.get('distance', 0):.0f} km | "
                                    f"Price: ${s.get('potential_price', 0):.2f} | "
                                    f"Demand: {s.get('estimated_demand', 0):.2f}",
                                    style={'color': '#8f9bb3', 'fontSize': '0.9em'})
                        ], style={
                            'background': '#1e2b4a',
                            'padding': '12px',
                            'borderRadius': '8px',
                            'marginBottom': '8px',
                            'border': '1px solid rgba(165, 180, 252, 0.2)'
                        }) for s in suggestions[:10]
                    ])
                ])
                
            except Exception as e:
                print(f"Error in suggest_new_routes: {str(e)}")
                return html.Div(f"Error generating suggestions: {str(e)}", className="error-message")
    
    except Exception as e:
        print(f"Unexpected error in network_analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        return html.Div([
            html.I(className="fas fa-exclamation-circle", 
                  style={'color': '#ef4444', 'marginRight': '10px'}),
            f" Unexpected error: {str(e)}"
        ], className="error-message")
    
    # Fallback return
    return html.Div("Processing complete", className="info-message")

@app.callback(
    Output('explore-results','children'),
    Input('explore-routes-btn','n_clicks'),
    State('explorer-from','value'),
    State('explorer-to','value')
)
def explore_routes(n_clicks, src, dst):
    if not n_clicks or not src or not dst:
        return None
    
    if not flight_system or not hasattr(flight_system, 'route_explorer') or not flight_system.route_explorer:
        return html.Div("Route explorer not available", className="info-message")
    
    try:
        alternatives = flight_system.explore_alternatives(src, dst)
        
        if not alternatives:
            return html.Div("No alternative routes found", className="info-message")
        
        results = []
        for alt in alternatives:
            if alt.get('path'):
                path = alt['path']
                results.append(html.Div([
                    html.H5(f"{alt['name']}:"),
                    html.P(f"{' → '.join(path)}"),
                    html.P(f"Length: {len(path)-1} connections"),
                    html.Hr()
                ]))
        
        return html.Div([
            html.H4(f"Found {len(results)} alternatives:"),
            *results
        ])
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="error-message")

@app.callback(
    Output('cache-status', 'children'),
    Input('clear-cache-btn', 'n_clicks')
)
def update_cache_status(n_clicks):
    if n_clicks and flight_system and flight_system.cache_manager:
        flight_system.cache_manager.clear_all()
        return html.P("Cache cleared successfully!", className="success-message")
    
    if flight_system and flight_system.cache_manager:
        return html.P("Cache Manager: ✅ Active - Routes are being cached")
    return html.P("Cache Manager: ❌ Not Available")

@app.callback(
    Output('download-data', 'data'),
    Input('export-json-btn', 'n_clicks'),
    Input('export-csv-btn', 'n_clicks'),
    Input('export-text-btn', 'n_clicks'),
    State('current-route-store', 'data'),
    prevent_initial_call=True
)
def export_route(json_clicks, csv_clicks, text_clicks, route_data):
    # Get the callback context
    ctx = callback_context
    if not ctx.triggered:
        print("No button triggered")
        return no_update
    
    if not route_data:
        print("No route data available")
        # You might want to show a notification to the user
        return no_update
    
    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"Export button clicked: {button_id}")
    print(f"Route data received: {route_data}")
    
    # Validate route data structure
    required_fields = ['path', 'total_km', 'total_minutes', 'total_price']
    if not all(field in route_data for field in required_fields):
        print(f"Route data missing required fields. Has: {list(route_data.keys())}")
        return no_update
    
    try:
        # Create filename base
        path_str = '_'.join(route_data['path'])
        filename_base = f"route_{path_str}"
        
        # Handle different export formats
        if button_id == 'export-json-btn':
            # Create JSON content
            content = json.dumps({
                'path': route_data['path'],
                'from': route_data['path'][0],
                'to': route_data['path'][-1],
                'connections': len(route_data['path']) - 1,
                'total_distance_km': round(route_data['total_km'], 2),
                'total_minutes': round(route_data['total_minutes'], 2),
                'total_price': round(route_data['total_price'], 2),
                'export_date': datetime.now().isoformat()
            }, indent=2)
            
            print(f"Returning JSON file: {filename_base}.json")
            return dcc.send_string(content, f"{filename_base}.json")
        
        elif button_id == 'export-csv-btn':
            # Create CSV content
            import csv
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Field', 'Value'])
            writer.writerow(['Route', ' → '.join(route_data['path'])])
            writer.writerow(['From', route_data['path'][0]])
            writer.writerow(['To', route_data['path'][-1]])
            writer.writerow(['Connections', len(route_data['path']) - 1])
            writer.writerow(['Total Distance (km)', round(route_data['total_km'], 2)])
            writer.writerow(['Total Time (minutes)', round(route_data['total_minutes'], 2)])
            writer.writerow(['Total Price ($)', round(route_data['total_price'], 2)])
            writer.writerow(['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            
            content = output.getvalue()
            print(f"Returning CSV file: {filename_base}.csv")
            return dcc.send_string(content, f"{filename_base}.csv")
        
        elif button_id == 'export-text-btn':
            # Create text content
            content = f"""========================================
           FLIGHT ROUTE REPORT
========================================

Route Details:
-------------
Route: {' → '.join(route_data['path'])}
From: {route_data['path'][0]}
To: {route_data['path'][-1]}
Number of Connections: {len(route_data['path']) - 1}

Journey Metrics:
---------------
📏 Total Distance: {round(route_data['total_km'], 2)} km
⏱️  Total Time: {format_duration(route_data['total_minutes'])} ({round(route_data['total_minutes'], 2)} minutes)
💰 Total Price: ${round(route_data['total_price'], 2)}

Export Information:
------------------
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================"""
            
            print(f"Returning TEXT file: {filename_base}.txt")
            return dcc.send_string(content, f"{filename_base}.txt")
        
        else:
            print(f"Unknown button: {button_id}")
            return no_update
            
    except Exception as e:
        print(f"Error in export: {str(e)}")
        import traceback
        traceback.print_exc()
        return no_update


# Helper function for route analysis
def create_route_analysis(graph, path):
    segments = []
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for edge in graph.neighbors(u):
            if edge.dst == v:
                segments.append({
                    'segment': f"{u} → {v}",
                    'distance': edge.km,
                    'time': edge.minutes,
                    'price': edge.price
                })
                break
    
    if not segments:
        return go.Figure()
    
    df = pd.DataFrame(segments)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Distance (km)',
        x=df['segment'],
        y=df['distance'],
        marker_color='#667eea',
        text=df['distance'].round(),
        textposition='auto',
    ))
    
    fig.add_trace(go.Bar(
        name='Time (min)',
        x=df['segment'],
        y=df['time'],
        marker_color='#28a745',
        text=df['time'],
        textposition='auto',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Route Segment Analysis',
        xaxis_title='Flight Segments',
        yaxis=dict(title='Distance (km)', title_font=dict(color='#667eea')),
        yaxis2=dict(title='Time (minutes)', overlaying='y', side='right', 
                   title_font=dict(color='#28a745')),
        barmode='group',
        height=500,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def create_performance_comparison(graph, src, dst, mode):
    algorithms = []
    
    from src.algorithms.bfs import bfs_least_hops
    algorithms.append(('BFS', lambda: bfs_least_hops(graph, src, dst)))
    
    from src.algorithms.dijkstra import dijkstra
    if mode == 'distance':
        weight = lambda e: e.km
    elif mode == 'time':
        weight = lambda e: e.minutes
    elif mode == 'price':
        weight = lambda e: e.price
    else:
        weight = lambda e: 1
    
    algorithms.append(('Dijkstra', lambda: dijkstra(graph, src, dst, weight)))
    
    if ASTAR_AVAILABLE:
        try:
            from src.algorithms.astar import astar_shortest_path
            algorithms.append(('A*', lambda: astar_shortest_path(graph, src, dst, weight)))
        except:
            pass
    
    results = []
    for name, algo_func in algorithms:
        start = time.time()
        try:
            path = algo_func()
            elapsed = (time.time() - start) * 1000
            
            if path:
                results.append({
                    'Algorithm': name,
                    'Time (ms)': round(elapsed, 2),
                    'Path Length': len(path),
                    'Found': '✓'
                })
            else:
                results.append({
                    'Algorithm': name,
                    'Time (ms)': round(elapsed, 2),
                    'Path Length': 0,
                    'Found': '✗'
                })
        except Exception as e:
            results.append({
                'Algorithm': name,
                'Time (ms)': 0,
                'Path Length': 0,
                'Found': '✗'
            })
    
    if not results:
        return go.Figure()
    
    df = pd.DataFrame(results)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Algorithm'],
        y=df['Time (ms)'],
        marker_color=['#667eea', '#28a745', '#ffc107', '#dc3545'][:len(df)],
        text=df['Time (ms)'],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Algorithm Performance Comparison',
        xaxis_title='Algorithm',
        yaxis_title='Time (milliseconds)',
        height=500,
        showlegend=False,
        annotations=[
            dict(
                x=row['Algorithm'],
                y=row['Time (ms)'] + (max(df['Time (ms)']) * 0.05 if max(df['Time (ms)']) > 0 else 5),
                text=f"Found: {row['Found']} | Nodes: {row['Path Length']}",
                showarrow=False,
                font=dict(size=10)
            ) for _, row in df.iterrows()
        ] if not df.empty else []
    )

    
    return fig

@app.callback(
    Output("plane-anim", "n_intervals"),
    Input("current-route-store", "data")
)
def reset_plane_animation(route_data):
    return 0

@app.callback(
    Output("plane-marker", "position"),
    Input("plane-anim", "n_intervals"),
    State("current-route-store", "data")
)

def animate_plane(n, route_data):

    if not route_data or "coords" not in route_data:
        return [0,0], 0   # hide plane

    coords = route_data["coords"]

    if len(coords) < 2:
        return coords[0], 1

    steps_per_segment = 40

    total_steps = (len(coords) - 1) * steps_per_segment
    step = n % total_steps

    segment = step // steps_per_segment
    progress = (step % steps_per_segment) / steps_per_segment

    lat1, lon1 = coords[segment]
    lat2, lon2 = coords[segment + 1]

    lat = lat1 + (lat2 - lat1) * progress
    lon = lon1 + (lon2 - lon1) * progress

    return [lat, lon]

@app.callback(
    Output("animated-route", "positions"),
    Input("plane-anim", "n_intervals"),
    State("current-route-store", "data")
)
def animate_route(n, route_data):

    if not route_data or "coords" not in route_data:
        return []

    coords = route_data["coords"]

    if len(coords) < 2:
        return coords

    steps_per_segment = 40
    total_steps = (len(coords) - 1) * steps_per_segment

    step = n % total_steps

    segment = step // steps_per_segment
    progress = (step % steps_per_segment) / steps_per_segment

    route_so_far = coords[:segment+1]

    lat1, lon1 = coords[segment]
    lat2, lon2 = coords[segment+1]

    lat = lat1 + (lat2 - lat1) * progress
    lon = lon1 + (lon2 - lon1) * progress

    route_so_far.append([lat, lon])

    return route_so_far

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("✨ FlightRoute Pro - Complete Flight Routing System")
    print(f"{'='*60}")
    print(f"📍 Airports: {len(GRAPH.airports):,}")
    print(f"🛫 Routes: {count_routes(GRAPH):,}")
    print(f"🌍 Countries: {len(set(a.country for a in GRAPH.airports.values()))}")
    print(f"\n📦 Feature Status:")
    print(f"   ├─ Unified Interface: {'✅' if UNIFIED_AVAILABLE else '❌'}")
    print(f"   ├─ A* Algorithm: {'✅' if ASTAR_AVAILABLE else '❌'}")
    print(f"   ├─ Bellman-Ford: {'✅' if BELLMAN_FORD_AVAILABLE else '❌'}")
    print(f"   ├─ Yen's K-Shortest: {'✅' if YEN_AVAILABLE else '❌'}")
    print(f"   ├─ Algorithm Comparator: {'✅' if COMPARATOR_AVAILABLE else '❌'}")
    print(f"   ├─ Cache Manager: {'✅' if CACHE_AVAILABLE else '❌'}")
    print(f"   └─ Data Enhancer: {'✅' if ENHANCER_AVAILABLE else '❌'}")
    print(f"\n{'='*60}")
    print("🌐 Open http://localhost:8051 in your browser")
    print(f"{'='*60}\n")
    
    app.run(debug=True, port=8051)