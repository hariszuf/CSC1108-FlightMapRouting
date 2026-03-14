import time
from dash import html, Output, Input, State, no_update, callback_context
import dash_leaflet as dl
import plotly.graph_objects as go

from utils.helpers import path_to_coords, get_airport_options, format_duration
from utils.charts import create_route_analysis, create_performance_comparison


def register_routing_callbacks(app, graph, flight_system):

    # --- Trip type toggle (visual only) ---
    @app.callback(
        [Output('trip-oneway', 'className'),
         Output('trip-roundtrip', 'className'),
         Output('trip-multicity', 'className')],
        [Input('trip-oneway', 'n_clicks'),
         Input('trip-roundtrip', 'n_clicks'),
         Input('trip-multicity', 'n_clicks')]
    )
    def toggle_trip_type(n1, n2, n3):
        ctx = callback_context
        base = "trip-type-btn"
        active = "trip-type-btn trip-type-active"
        if not ctx.triggered or ctx.triggered[0]['prop_id'] == '.':
            return active, base, base
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        return (
            active if triggered_id == 'trip-oneway' else base,
            active if triggered_id == 'trip-roundtrip' else base,
            active if triggered_id == 'trip-multicity' else base,
        )

    # --- Swap airports ---
    @app.callback(
        [Output('src-dropdown', 'value'),
         Output('dst-dropdown', 'value')],
        Input('swap-airports-btn', 'n_clicks'),
        [State('src-dropdown', 'value'),
         State('dst-dropdown', 'value')],
        prevent_initial_call=True
    )
    def swap_airports(n_clicks, src, dst):
        return dst, src

    # --- Autocomplete: source dropdown ---
    @app.callback(
        Output('src-dropdown', 'options'),
        Input('src-dropdown', 'search_value')
    )
    def filter_src_options(search_value):
        return get_airport_options(graph, search_value or "")

    # --- Autocomplete: destination dropdown ---
    @app.callback(
        Output('dst-dropdown', 'options'),
        [Input('dst-dropdown', 'search_value'),
         Input('src-dropdown', 'value')]
    )
    def filter_dst_options(search_value, src_value):
        opts = get_airport_options(graph, search_value or "")
        if src_value:
            opts = [o for o in opts if o['value'] != src_value]
        return opts

    # --- Main route finder ---
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
                'text': 'Select airports and click Search flights',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False
            }],
            height=500
        )

        if not n_clicks or not src or not dst:
            return (
                html.P("Select airports and click 'Search flights'", style={'color': '#666'}),
                [], empty_fig, empty_fig, None
            )

        start_time = time.time()
        route_result = None

        if flight_system and flight_system.cache_manager:
            route_result = flight_system.cache_manager.get_shortest_path(src, dst, mode)

        if not route_result:
            if flight_system:
                route_result = flight_system.find_route(src, dst, mode)
            else:
                from src.services.routing import find_route as basic_find_route
                route_result = basic_find_route(graph, src, dst, mode)

            if route_result and flight_system and flight_system.cache_manager:
                flight_system.cache_manager.cache_route(src, dst, mode, route_result)

        elapsed_time = (time.time() - start_time) * 1000

        if not route_result:
            return (
                html.Div([
                    html.I(className="fas fa-exclamation-triangle"),
                    f" No route found between {src} and {dst}"
                ], className="error-message"),
                [], empty_fig, empty_fig, None
            )

        route_data = {
            'path': route_result.path,
            'total_km': route_result.total_km,
            'total_minutes': route_result.total_minutes,
            'total_price': route_result.total_price
        }

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

        coords = path_to_coords(graph, route_result.path)
        markers = []

        for i, code in enumerate(route_result.path):
            airport = graph.airports[code]
            color = 'green' if i == 0 else 'red' if i == len(route_result.path) - 1 else 'blue'
            markers.append(
                dl.Marker(
                    position=(airport.lat, airport.lon),
                    children=[dl.Tooltip(f"{code} - {airport.city}")],
                    icon={
                        'iconUrl': f'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-{color}.png',
                        'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
                        'iconSize': [20, 32],
                        'iconAnchor': [12, 41]
                    }
                )
            )

        plane = dl.Marker(
            id="plane-marker",
            position=coords[0],
            icon={
                "iconUrl": "https://cdn-icons-png.flaticon.com/512/7893/7893979.png",
                "iconSize": [40, 40],
                "iconAnchor": [20, 20],
                "className": "plane-icon"
            }
        )

        route_line = dl.Polyline(
            positions=coords,
            color="#3bffef",
            weight=3,
            opacity=0.9
        )

        map_layers = [route_line] + markers + [plane]
        analysis_fig = create_route_analysis(graph, route_result.path)
        performance_fig = create_performance_comparison(graph, src, dst, mode)

        route_data["coords"] = coords
        return summary, map_layers, analysis_fig, performance_fig, route_data
