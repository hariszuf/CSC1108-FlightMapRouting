import time
import io
import json
from datetime import datetime

import pandas as pd
from dash import html, dcc, Output, Input, State, no_update, callback_context
from dash import dash_table

from utils.helpers import format_duration


def register_advanced_callbacks(app, graph, flight_system, yen_available, comparator_available, cache_available):

    # --- Multi-City Trip Planner ---
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
            algorithm_map = {'auto': 'auto', 'heuristic': 'heuristic', 'exact': 'exact', 'bnb': 'bnb', 'genetic': 'genetic'}
            result = flight_system.multi_city_planner.plan_optimal_route(
                cities,
                algorithm=algorithm_map.get(method, 'auto')
            )

            if not result or not result.route:
                return html.Div("No valid route found", className="error-message")

            route = result.route
            total_dist = result.total_distance
            algorithm_used = result.algorithm_used
            optimality = result.optimality_guarantee
            time_ms = result.computation_time_ms

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
                            'padding': '15px', 'borderRadius': '12px',
                            'fontSize': '1.1em', 'fontWeight': '500',
                            'color': '#ffffff', 'marginBottom': '15px',
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
                        html.Div([html.Strong("Algorithm: ", style={'color': '#a5b4fc'}),
                                  html.Span(algorithm_used, style={'color': '#e5e9f0'})]),
                        html.Div([html.Strong("Optimality: ", style={'color': '#a5b4fc'}),
                                  html.Span(optimality, style={'color': '#e5e9f0'})]),
                        html.Div([html.Strong("Computation Time: ", style={'color': '#a5b4fc'}),
                                  html.Span(f"{time_ms:.2f} ms", style={'color': '#e5e9f0'})]) if time_ms > 0 else html.Div(),
                    ], style={'background': 'rgba(0,0,0,0.2)', 'padding': '12px', 'borderRadius': '8px', 'fontSize': '0.95em'}),
                    html.Div([
                        html.H6("Segment Details:", style={'color': '#a5b4fc', 'marginTop': '15px', 'marginBottom': '10px'}),
                        html.Div([
                            html.Div([
                                html.Div(f"{seg['from']} → {seg['to']}", style={'fontWeight': '500', 'color': '#ffffff'}),
                                html.Div(f"{seg['distance']:.2f} km", style={'color': '#8f9bb3', 'fontSize': '0.9em'})
                            ], style={
                                'padding': '8px 12px', 'background': 'rgba(255,255,255,0.05)',
                                'borderRadius': '6px', 'marginBottom': '5px'
                            }) for seg in result.segments[:5]
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

    # --- K-Shortest Paths ---
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

        if not yen_available or not flight_system:
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

            return html.Div([html.H4(f"Found {len(paths)} paths:"), *results])
        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="error-message")

    # --- Algorithm Comparison ---
    @app.callback(
        Output('comparison-results', 'children'),
        Input('compare-algos-btn', 'n_clicks'),
        [State('compare-from', 'value'),
         State('compare-to', 'value')]
    )
    def compare_algorithms(n_clicks, src, dst):
        if not n_clicks or not src or not dst:
            return None

        if not comparator_available or not flight_system:
            results = []
            from src.services.routing import find_route
            for mode in ['hops', 'distance', 'time', 'price']:
                s = time.time()
                route = find_route(graph, src, dst, mode)
                e = time.time()
                results.append({'Mode': mode, 'Found': '✓' if route else '✗', 'Time (ms)': f"{(e-s)*1000:.2f}"})

            df = pd.DataFrame(results)
            return html.Div([
                html.H5("Basic Comparison:"),
                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'color': '#e5e9f0', 'backgroundColor': '#1e2b4a', 'textAlign': 'center', 'border': '1px solid rgba(255,255,255,0.08)'},
                    style_header={'backgroundColor': '#2d3b5e', 'color': '#ffffff', 'fontWeight': 'bold', 'border': '1px solid rgba(165,180,252,0.3)'}
                )
            ])

        try:
            results = flight_system.compare_algorithms(src, dst)
            if not results:
                return html.Div("No comparison results", className="info-message")

            data = [{
                'Algorithm': name,
                'Found': '✓',
                'Cost': f"{info['cost']:.2f}",
                'Path': ' → '.join(info['path'][:3]) + ('...' if len(info['path']) > 3 else '')
            } for name, info in results.items()]

            return html.Div([
                dash_table.DataTable(
                    data=data,
                    columns=[{'name': i, 'id': i} for i in ['Algorithm', 'Found', 'Cost', 'Path']],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px', 'color': '#e5e9f0', 'backgroundColor': '#1e2b4a', 'border': '1px solid rgba(255,255,255,0.08)'},
                    style_data={'color': '#e5e9f0', 'backgroundColor': '#1e2b4a'},
                    style_header={'backgroundColor': '#2d3b5e', 'color': '#ffffff', 'fontWeight': 'bold', 'border': '1px solid rgba(165,180,252,0.3)'}
                )
            ])
        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="error-message")

    # --- Route Explorer ---
    @app.callback(
        Output('explore-results', 'children'),
        Input('explore-routes-btn', 'n_clicks'),
        State('explorer-from', 'value'),
        State('explorer-to', 'value')
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

            return html.Div([html.H4(f"Found {len(results)} alternatives:"), *results])
        except Exception as e:
            return html.Div(f"Error: {str(e)}", className="error-message")

    # --- Cache Status ---
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

    # --- Export Route ---
    @app.callback(
        Output('download-data', 'data'),
        Input('export-json-btn', 'n_clicks'),
        Input('export-csv-btn', 'n_clicks'),
        Input('export-text-btn', 'n_clicks'),
        State('current-route-store', 'data'),
        prevent_initial_call=True
    )
    def export_route(json_clicks, csv_clicks, text_clicks, route_data):
        ctx = callback_context
        if not ctx.triggered or not route_data:
            return no_update

        required_fields = ['path', 'total_km', 'total_minutes', 'total_price']
        if not all(field in route_data for field in required_fields):
            return no_update

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        path_str = '_'.join(route_data['path'])
        filename_base = f"route_{path_str}"

        try:
            if button_id == 'export-json-btn':
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
                return dcc.send_string(content, f"{filename_base}.json")

            elif button_id == 'export-csv-btn':
                import csv
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['Field', 'Value'])
                writer.writerow(['Route', ' → '.join(route_data['path'])])
                writer.writerow(['From', route_data['path'][0]])
                writer.writerow(['To', route_data['path'][-1]])
                writer.writerow(['Connections', len(route_data['path']) - 1])
                writer.writerow(['Total Distance (km)', round(route_data['total_km'], 2)])
                writer.writerow(['Total Time (minutes)', round(route_data['total_minutes'], 2)])
                writer.writerow(['Total Price ($)', round(route_data['total_price'], 2)])
                writer.writerow(['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                return dcc.send_string(output.getvalue(), f"{filename_base}.csv")

            elif button_id == 'export-text-btn':
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
                return dcc.send_string(content, f"{filename_base}.txt")

        except Exception as e:
            import traceback
            traceback.print_exc()
            return no_update

        return no_update
