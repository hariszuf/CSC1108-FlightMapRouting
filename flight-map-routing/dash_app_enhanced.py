# dash_app_enhanced.py  ← main entry point
from pathlib import Path
from dash import Dash, html, dcc

# Local imports - core
from src.loader import load_graph

# Feature availability flags
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

# --- Dataset path ---
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

# --- Local module imports (after GRAPH is ready) ---
from utils.helpers import get_airport_options, count_routes
from layout.basic_routing import create_basic_routing_tab
from layout.advanced_features import create_advanced_features_tab
from callbacks.routing_callbacks import register_routing_callbacks
from callbacks.advanced_callbacks import register_advanced_callbacks
from callbacks.animation_callbacks import register_animation_callbacks

# --- App initialisation ---
ASSETS_PATH = Path(__file__).parent / "src" / "assets"

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

# --- Layout ---
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.I(className="fas fa-globe-americas",
                   style={'fontSize': '3em', 'color': '#a5b4fc', 'marginRight': '20px'})
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

    # Main Tabs
    dcc.Tabs(id='main-tabs', value='basic-routing', children=[
        create_basic_routing_tab(GRAPH, get_airport_options),
        create_advanced_features_tab(GRAPH, get_airport_options, YEN_AVAILABLE, CACHE_AVAILABLE),
    ]),

    # Shared stores / downloads / intervals
    dcc.Store(id='current-route-store'),
    dcc.Download(id='download-data'),
    dcc.Interval(id="plane-anim", interval=900, n_intervals=0),
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

# --- Register all callbacks ---
register_routing_callbacks(app, GRAPH, flight_system)
register_advanced_callbacks(app, GRAPH, flight_system, YEN_AVAILABLE, COMPARATOR_AVAILABLE, CACHE_AVAILABLE)
register_animation_callbacks(app)

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
