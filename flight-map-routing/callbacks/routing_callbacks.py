import math
import time
from dash import html, dcc, Output, Input, State, no_update, callback_context
import dash_leaflet as dl
import plotly.graph_objects as go

from utils.helpers import path_to_coords, get_airport_options, format_duration
from utils.charts import create_route_analysis, create_performance_comparison


def make_curved_path(coords, arc_height=8, points_per_segment=30):
    if len(coords) < 2:
        return coords

    curved = []

    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]

        for j in range(points_per_segment):
            t = j / points_per_segment

            lat = lat1 + (lat2 - lat1) * t
            lon = lon1 + (lon2 - lon1) * t

            curve_offset = math.sin(t * math.pi) * arc_height
            lat += curve_offset

            curved.append([lat, lon])

    curved.append(coords[-1])
    return curved


def register_routing_callbacks(app, graph, flight_system):

    # --- Trip type toggle ---
    @app.callback(
        [Output('trip-oneway', 'className'),
         Output('trip-roundtrip', 'className'),
         Output('trip-type-store', 'data')],
        [Input('trip-oneway', 'n_clicks'),
         Input('trip-roundtrip', 'n_clicks')]
    )
    def toggle_trip_type(n1, n2):
        ctx = callback_context
        base = "trip-type-btn"
        active = "trip-type-btn trip-type-active"
        if not ctx.triggered or ctx.triggered[0]['prop_id'] == '.':
            return active, base, 'oneway'
        
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        trip_type = 'oneway'
        if triggered_id == 'trip-roundtrip':
            trip_type = 'roundtrip'
        
        return (
            active if triggered_id == 'trip-oneway' else base,
            active if triggered_id == 'trip-roundtrip' else base,
            trip_type
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
         State('optimization-mode', 'value'),
         State('trip-type-store', 'data')]
    )
    def find_route(n_clicks, src, dst, mode, trip_type):
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

        trip_type = trip_type or 'oneway'
        start_time = time.time()
        outbound_route = None
        return_route = None

        # Find outbound route
        if flight_system and flight_system.cache_manager:
            outbound_route = flight_system.cache_manager.get_shortest_path(src, dst, mode)

        if not outbound_route:
            if flight_system:
                outbound_route = flight_system.find_route(src, dst, mode)
            else:
                from src.services.routing import find_route as basic_find_route
                outbound_route = basic_find_route(graph, src, dst, mode)

            if outbound_route and flight_system and flight_system.cache_manager:
                flight_system.cache_manager.cache_route(src, dst, mode, outbound_route)

        # Find return route if round trip
        if trip_type == 'roundtrip' and outbound_route:
            if flight_system and flight_system.cache_manager:
                return_route = flight_system.cache_manager.get_shortest_path(dst, src, mode)

            if not return_route:
                if flight_system:
                    return_route = flight_system.find_route(dst, src, mode)
                else:
                    from src.services.routing import find_route as basic_find_route
                    return_route = basic_find_route(graph, dst, src, mode)

                if return_route and flight_system and flight_system.cache_manager:
                    flight_system.cache_manager.cache_route(dst, src, mode, return_route)

        elapsed_time = (time.time() - start_time) * 1000

        if not outbound_route:
            return (
                html.Div([
                    html.I(className="fas fa-exclamation-triangle"),
                    f" No route found between {src} and {dst}"
                ], className="error-message"),
                [], empty_fig, empty_fig, None
            )

        # Build trip summary with tabs for round trips
        trip_label = "Round Trip" if trip_type == 'roundtrip' else "One Way"
        total_price = outbound_route.total_price
        total_km = outbound_route.total_km
        total_minutes = outbound_route.total_minutes
        
        # Outbound flight card content
        outbound_content = html.Div([
            html.H4(f"{src} → {dst}", style={'color': '#667eea', 'marginBottom': '12px', 'fontSize': '1em'}),
            html.Div([
                html.Div(f"{outbound_route.pretty()}", style={'fontSize': '0.85em', 'color': '#94a3b8', 'marginBottom': '12px'}),
                html.Div([
                    html.Div([
                        html.Div("Connections", className="metric-label"),
                        html.Div(f"{outbound_route.hops}", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Distance", className="metric-label"),
                        html.Div(f"{outbound_route.total_km:.0f} km", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Duration", className="metric-label"),
                        html.Div(format_duration(outbound_route.total_minutes), className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Price", className="metric-label"),
                        html.Div(f"${outbound_route.total_price:.2f}", className="metric-value")
                    ], className="metric-box"),
                ], className="metric-grid")
            ])
        ])

        # Build summary based on trip type
        if trip_type == 'roundtrip' and return_route:
            total_price += return_route.total_price
            total_km += return_route.total_km
            total_minutes += return_route.total_minutes

            # Return flight card content
            return_content = html.Div([
                html.H4(f"{dst} → {src}", style={'color': '#667eea', 'marginBottom': '12px', 'fontSize': '1em'}),
                html.Div([
                    html.Div(f"{return_route.pretty()}", style={'fontSize': '0.85em', 'color': '#94a3b8', 'marginBottom': '12px'}),
                    html.Div([
                        html.Div([
                            html.Div("Connections", className="metric-label"),
                            html.Div(f"{return_route.hops}", className="metric-value")
                        ], className="metric-box"),
                        html.Div([
                            html.Div("Distance", className="metric-label"),
                            html.Div(f"{return_route.total_km:.0f} km", className="metric-value")
                        ], className="metric-box"),
                        html.Div([
                            html.Div("Duration", className="metric-label"),
                            html.Div(format_duration(return_route.total_minutes), className="metric-value")
                        ], className="metric-box"),
                        html.Div([
                            html.Div("Price", className="metric-label"),
                            html.Div(f"${return_route.total_price:.2f}", className="metric-value")
                        ], className="metric-box"),
                    ], className="metric-grid")
                ])
            ])

            # Total summary card content
            total_content = html.Div([
                html.H4("Trip Summary", style={'color': '#22c55e', 'marginBottom': '12px', 'fontSize': '1em'}),
                html.Div([
                    html.Div([
                        html.Div("Total Connections", className="metric-label"),
                        html.Div(f"{outbound_route.hops + return_route.hops}", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Total Distance", className="metric-label"),
                        html.Div(f"{total_km:.0f} km", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Total Duration", className="metric-label"),
                        html.Div(format_duration(total_minutes), className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Total Price", className="metric-label"),
                        html.Div(f"${total_price:.2f}", className="metric-value", 
                                style={'color': '#22c55e', 'fontWeight': 'bold'})
                    ], className="metric-box"),
                ], className="metric-grid")
            ])

            # Use tabbed interface for round trip
            tab_style = {
                'backgroundColor': '#0f172a',
                'color': '#94a3b8',
                'border': '1px solid rgba(255, 255, 255, 0.08)',
                'borderBottom': 'none',
                'padding': '8px 12px',
                'fontSize': '0.85em'
            }
            tab_selected_style = {
                'backgroundColor': 'rgba(59, 130, 246, 0.18)',
                'color': '#e2e8f0',
                'border': '1px solid rgba(59, 130, 246, 0.35)',
                'borderBottom': '2px solid #3b82f6',
                'padding': '8px 12px',
                'fontSize': '0.85em',
                'fontWeight': '600'
            }

            summary = html.Div([
                html.Div(f"✓ {trip_label} route found in {elapsed_time:.2f}ms", className="success-message", style={'marginBottom': '12px'}),
                dcc.Tabs(id='flight-details-tabs', value='outbound-tab', children=[
                    dcc.Tab(label='Outbound', value='outbound-tab', children=[outbound_content], className='flight-detail-tab', style=tab_style, selected_style=tab_selected_style),
                    dcc.Tab(label='Return', value='return-tab', children=[return_content], className='flight-detail-tab', style=tab_style, selected_style=tab_selected_style),
                    dcc.Tab(label='Total', value='total-tab', children=[total_content], className='flight-detail-tab', style=tab_style, selected_style=tab_selected_style),
                ], style={'marginTop': '0px'})
            ])
        else:
            # For one-way trips, show without tabs
            summary = html.Div([
                html.Div(f"✓ {trip_label} route found in {elapsed_time:.2f}ms", className="success-message"),
                html.H4(f"{src} → {dst}", style={'color': '#667eea', 'marginTop': '12px', 'marginBottom': '12px', 'fontSize': '1.1em'}),
                html.Div(f"{outbound_route.pretty()}", style={'fontSize': '0.85em', 'color': '#94a3b8', 'marginBottom': '12px'}),
                html.Div([
                    html.Div([
                        html.Div("Connections", className="metric-label"),
                        html.Div(f"{outbound_route.hops}", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Distance", className="metric-label"),
                        html.Div(f"{outbound_route.total_km:.0f} km", className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Duration", className="metric-label"),
                        html.Div(format_duration(outbound_route.total_minutes), className="metric-value")
                    ], className="metric-box"),
                    html.Div([
                        html.Div("Price", className="metric-label"),
                        html.Div(f"${outbound_route.total_price:.2f}", className="metric-value")
                    ], className="metric-box"),
                ], className="metric-grid")
            ])

        # Build map layers for both routes
        coords_outbound = path_to_coords(graph, outbound_route.path)
        curved_coords_outbound = make_curved_path(coords_outbound)
        markers = []

        # Outbound route markers
        for i, code in enumerate(outbound_route.path):
            airport = graph.airports[code]
            if i == 0:
                color = "#22c55e"
                radius = 10
            elif i == len(outbound_route.path) - 1:
                color = "#ef4444" if trip_type != 'roundtrip' else "#3b82f6"
                radius = 10
            else:
                color = "#60a5fa"
                radius = 7
            markers.append(
                dl.CircleMarker(
                    center=(airport.lat, airport.lon),
                    radius=radius,
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.9,
                    weight=2,
                    children=[
                        dl.Tooltip(f"{code} - {airport.city}")
                    ]
                )
            )

        glow_line_outbound = dl.Polyline(
            positions=curved_coords_outbound,
            color="#3b82f6",
            weight=10,
            opacity=0.18
        )

        route_line_outbound = dl.Polyline(
            positions=curved_coords_outbound,
            color="#67e8f9",
            weight=4,
            opacity=0.95
        )

        plane_outbound = dl.Marker(
            id="plane-marker",
            position=curved_coords_outbound[0],
            icon={
                "iconUrl": "https://cdn-icons-png.flaticon.com/512/7893/7893979.png",
                "iconSize": [40, 40],
                "iconAnchor": [20, 20],
                "className": "plane-icon"
            }
        )

        map_layers = [glow_line_outbound, route_line_outbound] + markers + [plane_outbound]

        # Add return route to map if round trip
        if trip_type == 'roundtrip' and return_route:
            coords_return = path_to_coords(graph, return_route.path)
            curved_coords_return = make_curved_path(coords_return)

            # Return route markers
            for i, code in enumerate(return_route.path):
                airport = graph.airports[code]
                if i == 0:
                    color = "#3b82f6"
                    radius = 10
                elif i == len(return_route.path) - 1:
                    color = "#ef4444"
                    radius = 10
                else:
                    color = "#60a5fa"
                    radius = 7
                markers.append(
                    dl.CircleMarker(
                        center=(airport.lat, airport.lon),
                        radius=radius,
                        color=color,
                        fill=True,
                        fillColor=color,
                        fillOpacity=0.9,
                        weight=2,
                        children=[
                            dl.Tooltip(f"{code} - {airport.city} (Return)")
                        ]
                    )
                )

            glow_line_return = dl.Polyline(
                positions=curved_coords_return,
                color="#ef4444",
                weight=10,
                opacity=0.18
            )

            route_line_return = dl.Polyline(
                positions=curved_coords_return,
                color="#f87171",
                weight=4,
                opacity=0.95,
                dashArray="5, 5"
            )

            plane_return = dl.Marker(
                position=curved_coords_return[0],
                icon={
                    "iconUrl": "https://cdn-icons-png.flaticon.com/512/7893/7893979.png",
                    "iconSize": [40, 40],
                    "iconAnchor": [20, 20],
                    "className": "plane-icon"
                }
            )

            map_layers.extend([glow_line_return, route_line_return, plane_return])

        analysis_fig = create_route_analysis(graph, outbound_route.path)
        performance_fig = create_performance_comparison(graph, src, dst, mode)

        route_data = {
            'outbound_path': outbound_route.path,
            'outbound_km': outbound_route.total_km,
            'outbound_minutes': outbound_route.total_minutes,
            'outbound_price': outbound_route.total_price,
            'outbound_coords': curved_coords_outbound,
            'trip_type': trip_type
        }
        
        if trip_type == 'roundtrip' and return_route:
            route_data['return_path'] = return_route.path
            route_data['return_km'] = return_route.total_km
            route_data['return_minutes'] = return_route.total_minutes
            route_data['return_price'] = return_route.total_price
            route_data['return_coords'] = curved_coords_return

        return summary, map_layers, analysis_fig, performance_fig, route_data
