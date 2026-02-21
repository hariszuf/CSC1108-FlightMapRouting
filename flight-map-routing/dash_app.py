from __future__ import annotations

from pathlib import Path

from dash import Dash, html, dcc, Input, Output, State
import dash_leaflet as dl

from src.loader import load_graph
from src.services.routing import find_route


# --- robust dataset path ---
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

# Load once (Dash keeps process running)
GRAPH = load_graph(get_data_path())

def airport_options(graph):
    # small, safe list for dropdown; can be huge, so keep simple for prototype
    # If you want all airports, just return them all (may be heavy).
    codes = sorted(graph.airports.keys())
    return [{"label": c, "value": c} for c in codes]

def path_to_latlon(graph, path):
    return [(graph.airports[c].lat, graph.airports[c].lon) for c in path]

app = Dash(__name__)
app.title = "Flight Map Routing (Dash)"

app.layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "16px"},
    children=[
        html.H2("✈️ Flight Map Routing Prototype (Dash)"),
        html.Div(f"Loaded {len(GRAPH.airports)} airports", style={"opacity": 0.7, "marginBottom": "12px"}),

        html.Div(
            style={"display": "flex", "gap": "12px", "flexWrap": "wrap"},
            children=[
                html.Div(
                    style={"minWidth": "260px"},
                    children=[
                        html.Label("Source"),
                        dcc.Dropdown(
                            id="src",
                            options=airport_options(GRAPH),
                            placeholder="Select source (e.g., SIN)",
                            searchable=True,
                            clearable=True,
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "260px"},
                    children=[
                        html.Label("Destination"),
                        dcc.Dropdown(
                            id="dst",
                            options=airport_options(GRAPH),
                            placeholder="Select destination (e.g., HND)",
                            searchable=True,
                            clearable=True,
                        ),
                    ],
                ),
                html.Div(
                    style={"minWidth": "220px"},
                    children=[
                        html.Label("Optimise for"),
                        dcc.Dropdown(
                            id="mode",
                            options=[
                                {"label": "Least hops (BFS)", "value": "hops"},
                                {"label": "Shortest distance (Dijkstra)", "value": "distance"},
                                {"label": "Fastest time (Dijkstra)", "value": "time"},
                                {"label": "Cheapest price (Dijkstra)", "value": "price"},
                            ],
                            value="distance",
                            clearable=False,
                        ),
                    ],
                ),
                html.Div(
                    style={"alignSelf": "end"},
                    children=[
                        html.Button("Find route", id="run", n_clicks=0, style={"padding": "10px 14px"}),
                    ],
                ),
            ],
        ),

        html.Hr(),

        html.Div(id="status", style={"marginBottom": "10px"}),

        html.Div(
            style={"display": "flex", "gap": "14px", "flexWrap": "wrap", "marginBottom": "12px"},
            children=[
                html.Div(id="metric_route", style={"padding": "10px 12px", "border": "1px solid #ddd", "borderRadius": "10px"}),
                html.Div(id="metric_stats", style={"padding": "10px 12px", "border": "1px solid #ddd", "borderRadius": "10px"}),
            ],
        ),

        dl.Map(
            id="map",
            center=(1.3521, 103.8198),  # Singapore default
            zoom=3,
            style={"width": "100%", "height": "560px", "borderRadius": "12px"},
            children=[
                dl.TileLayer(),
                dl.LayerGroup(id="route_layer"),
            ],
        ),
    ],
)

@app.callback(
    Output("status", "children"),
    Output("metric_route", "children"),
    Output("metric_stats", "children"),
    Output("route_layer", "children"),
    Input("run", "n_clicks"),
    State("src", "value"),
    State("dst", "value"),
    State("mode", "value"),
)
def on_run(n_clicks, src, dst, mode):
    if not n_clicks:
        return "Pick source & destination, then click Find route.", "", "", []

    if not src or not dst:
        return "⚠️ Please select both source and destination.", "", "", []

    res = find_route(GRAPH, src, dst, mode)
    if res is None:
        return "❌ No route found (try another pair).", "", "", []

    coords = path_to_latlon(GRAPH, res.path)

    # Markers
    markers = []
    for code in res.path:
        a = GRAPH.airports[code]
        markers.append(dl.Marker(position=(a.lat, a.lon), children=[dl.Tooltip(f"{code} - {a.city}, {a.country}")]))
    # Polyline
    poly = dl.Polyline(positions=coords)

    route_text = html.Div([
        html.Div("Route", style={"fontWeight": 700}),
        html.Div(res.pretty()),
    ])

    stats_text = html.Div([
        html.Div("Totals", style={"fontWeight": 700}),
        html.Ul([
            html.Li(f"Hops: {res.hops}"),
            html.Li(f"Distance (km): {res.total_km}"),
            html.Li(f"Duration (min): {res.total_minutes}"),
            html.Li(f"Price: {res.total_price}"),
        ], style={"margin": 0}),
    ])

    return "✅ Route computed.", route_text, stats_text, [poly, *markers]

if __name__ == "__main__":
    app.run(debug=True)