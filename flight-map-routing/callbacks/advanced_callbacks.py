import time
import io
import json
from datetime import datetime
from urllib.parse import quote

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
        Output('export-link', 'children'),
        Input('export-json-btn', 'n_clicks'),
        Input('export-csv-btn', 'n_clicks'),
        Input('export-text-btn', 'n_clicks'),
        State('current-route-store', 'data'),
        prevent_initial_call=True
    )
    def export_route(json_clicks, csv_clicks, text_clicks, route_data):
        ctx = callback_context
        if not ctx.triggered or not route_data:
            return no_update, no_update

        trip_type = route_data.get('trip_type', 'oneway')

        # Backward compatibility: old one-way structure
        if 'path' in route_data:
            outbound_path = route_data.get('path', [])
            outbound_km = route_data.get('total_km', 0)
            outbound_minutes = route_data.get('total_minutes', 0)
            outbound_price = route_data.get('total_price', 0)
            return_path = []
            return_km = 0
            return_minutes = 0
            return_price = 0
            trip_type = 'oneway'
        else:
            # New route data structure
            outbound_path = route_data.get('outbound_path', [])
            outbound_km = route_data.get('outbound_km', 0)
            outbound_minutes = route_data.get('outbound_minutes', 0)
            outbound_price = route_data.get('outbound_price', 0)
            return_path = route_data.get('return_path', [])
            return_km = route_data.get('return_km', 0)
            return_minutes = route_data.get('return_minutes', 0)
            return_price = route_data.get('return_price', 0)

        if not outbound_path:
            return no_update, html.Div("No route data available to export", className="info-message")

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        path_str = '_'.join(outbound_path)
        filename_base = f"route_{path_str}"

        total_connections = max(len(outbound_path) - 1, 0) + max(len(return_path) - 1, 0)
        total_km = outbound_km + return_km
        total_minutes = outbound_minutes + return_minutes
        total_price = outbound_price + return_price

        share_route = '-'.join(outbound_path)
        if trip_type == 'roundtrip' and return_path:
            share_route = f"{share_route}--{'-'.join(return_path)}"
        share_link = f"https://flightroute.pro/share/{quote(share_route)}"

        export_notice = html.Div([
            html.Div("Export completed", className="success-message", style={'padding': '10px', 'marginBottom': '8px'}),
            html.A("Share this route", href=share_link, target="_blank", style={'color': '#60a5fa', 'textDecoration': 'underline'})
        ])

        try:
            if button_id == 'export-json-btn':
                content = json.dumps({
                    'trip_type': trip_type,
                    'outbound': {
                        'path': outbound_path,
                        'from': outbound_path[0],
                        'to': outbound_path[-1],
                        'connections': max(len(outbound_path) - 1, 0),
                        'distance_km': round(outbound_km, 2),
                        'minutes': round(outbound_minutes, 2),
                        'price': round(outbound_price, 2)
                    },
                    'return': {
                        'path': return_path,
                        'from': return_path[0] if return_path else None,
                        'to': return_path[-1] if return_path else None,
                        'connections': max(len(return_path) - 1, 0),
                        'distance_km': round(return_km, 2),
                        'minutes': round(return_minutes, 2),
                        'price': round(return_price, 2)
                    } if return_path else None,
                    'totals': {
                        'connections': total_connections,
                        'distance_km': round(total_km, 2),
                        'minutes': round(total_minutes, 2),
                        'price': round(total_price, 2)
                    },
                    'share_link': share_link,
                    'export_date': datetime.now().isoformat()
                }, indent=2)
                return dcc.send_string(content, f"{filename_base}.json"), export_notice

            elif button_id == 'export-csv-btn':
                import csv
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['Field', 'Value'])
                writer.writerow(['Trip Type', trip_type])
                writer.writerow(['Outbound Route', ' → '.join(outbound_path)])
                writer.writerow(['Outbound From', outbound_path[0]])
                writer.writerow(['Outbound To', outbound_path[-1]])
                writer.writerow(['Outbound Connections', max(len(outbound_path) - 1, 0)])
                writer.writerow(['Outbound Distance (km)', round(outbound_km, 2)])
                writer.writerow(['Outbound Time (minutes)', round(outbound_minutes, 2)])
                writer.writerow(['Outbound Price ($)', round(outbound_price, 2)])
                if return_path:
                    writer.writerow(['Return Route', ' → '.join(return_path)])
                    writer.writerow(['Return From', return_path[0]])
                    writer.writerow(['Return To', return_path[-1]])
                    writer.writerow(['Return Connections', max(len(return_path) - 1, 0)])
                    writer.writerow(['Return Distance (km)', round(return_km, 2)])
                    writer.writerow(['Return Time (minutes)', round(return_minutes, 2)])
                    writer.writerow(['Return Price ($)', round(return_price, 2)])
                writer.writerow(['Total Connections', total_connections])
                writer.writerow(['Total Distance (km)', round(total_km, 2)])
                writer.writerow(['Total Time (minutes)', round(total_minutes, 2)])
                writer.writerow(['Total Price ($)', round(total_price, 2)])
                writer.writerow(['Share Link', share_link])
                writer.writerow(['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                return dcc.send_string(output.getvalue(), f"{filename_base}.csv"), export_notice

            elif button_id == 'export-text-btn':
                return_section = ""
                if return_path:
                    return_section = f"""

Return Route:
------------
Route: {' → '.join(return_path)}
From: {return_path[0]}
To: {return_path[-1]}
Number of Connections: {max(len(return_path) - 1, 0)}
📏 Distance: {round(return_km, 2)} km
⏱️  Time: {format_duration(return_minutes)} ({round(return_minutes, 2)} minutes)
💰 Price: ${round(return_price, 2)}
"""

                content = f"""========================================
           FLIGHT ROUTE REPORT
========================================

Route Details:
-------------
Trip Type: {trip_type}
Outbound Route: {' → '.join(outbound_path)}
From: {outbound_path[0]}
To: {outbound_path[-1]}
Number of Connections: {max(len(outbound_path) - 1, 0)}
{return_section}

Journey Metrics:
---------------
📏 Total Distance: {round(total_km, 2)} km
⏱️  Total Time: {format_duration(total_minutes)} ({round(total_minutes, 2)} minutes)
💰 Total Price: ${round(total_price, 2)}
🔗 Share Link: {share_link}

Export Information:
------------------
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
========================================"""
                return dcc.send_string(content, f"{filename_base}.txt"), export_notice

        except Exception as e:
            import traceback
            traceback.print_exc()
            return no_update, html.Div(f"Export failed: {str(e)}", className="error-message")

        return no_update, no_update
