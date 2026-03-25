from dash import html, dcc
from utils.helpers import get_airport_options  # Add this import
from src.graph import FlightGraph

def create_advanced_features_tab(graph, get_airport_options, yen_available, cache_available):
    airport_options = get_airport_options(graph, "")
    return dcc.Tab(label='Advanced Features', value='advanced', children=[
        html.Div([
            # Left Column
            html.Div([
                # Multi-City Planning
                html.Div([
                    html.Div("Multi-City Trip Planner", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                            id='multi-city-selector',
                            options=get_airport_options(graph),
                            placeholder="Select cities to visit",
                            multi=True,
                            value=['SIN', 'HND', 'LHR'] if all(
                                c in graph.airports for c in ['SIN', 'HND', 'LHR']) else [],
                            searchable=True
                        ),
                        html.Div([
                            dcc.RadioItems(
                                id='tsp-method',
                                options=[
                                    {'label': 'Auto (DP for ≤8 cities)',
                                     'value': 'auto'},
                                    {'label': 'Heuristic (Nearest Neighbor)',
                                     'value': 'heuristic'},
                                ],
                                value='auto',
                                className="opt-radio",
                                labelStyle={'display': 'inline-block',
                                            'marginRight': '20px'}
                            ),
                        ], style={'marginTop': '12px'}),
                        html.Button("Plan Optimal Route",
                                    id='plan-multi-city-btn',
                                    className="btn-primary", n_clicks=0,
                                    style={'marginTop': '12px'}),
                        html.Div(id='multi-city-results',
                                 style={'marginTop': '15px'})
                    ])
                ], className="card adv-card"),

                # K-Shortest Paths
                html.Div([
                    html.Div(
                        f"K-Shortest Paths {'' if yen_available else '(Not Available)'}",
                        className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                            id='ksp-from',
                            options=get_airport_options(graph),
                            placeholder="From...",
                            searchable=True
                        ),
                        dcc.Dropdown(
                            id='ksp-to',
                            options=get_airport_options(graph),
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
                                    {'label': 'Distance', 'value': 'distance'},
                                    {'label': 'Time', 'value': 'time'},
                                    {'label': 'Price', 'value': 'price'},
                                ],
                                value='distance',
                                inline=True,
                                className="opt-radio"
                            ),
                        ], style={'marginTop': '10px', 'display': 'flex',
                                  'alignItems': 'center'}),
                        html.Button("Find K Paths", id='find-k-paths-btn',
                                    className="btn-primary",
                                    n_clicks=0,
                                    disabled=not yen_available,
                                    style={'marginTop': '12px'}),
                        html.Div(id='k-paths-results')
                    ])
                ], className="card adv-card"),

                # Algorithm Comparison
                html.Div([
                    html.Div("Algorithm Comparison", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                            id='compare-from',
                            options=get_airport_options(graph),
                            placeholder="From...",
                            searchable=True,
                            clearable=True
                        ),
                        dcc.Dropdown(
                            id='compare-to',
                            options=get_airport_options(graph),
                            placeholder="To...",
                            searchable=True,
                            clearable=True
                        ),
                        html.Button("Compare All Algorithms",
                                    id='compare-algos-btn',
                                    className="btn-primary", n_clicks=0,
                                    style={'marginTop': '12px'}),
                        html.Div(id='comparison-results')
                    ])
                ], className="card adv-card"),

            ], className="adv-col"),

            # Right Column
            html.Div([
                # Export Options
                html.Div([
                    html.Div("Export & Share", className="card-header"),
                    html.Div([
                        html.Div([
                            html.Button("Export JSON", id='export-json-btn',
                                        className="download-btn", n_clicks=0),
                            html.Button("Export CSV", id='export-csv-btn',
                                        className="download-btn", n_clicks=0),
                            html.Button("Export Text", id='export-text-btn',
                                        className="download-btn", n_clicks=0),
                        ], className="export-btn-group"),
                        html.Div(id='export-link', style={'marginTop': '15px'})
                    ])
                ], className="card adv-card"),

                # Seasonal Pricing with Bellman-Ford
                html.Div([
                    html.H4("📅 Seasonal Pricing with Bellman-Ford", className="card-header"),
                    html.P("See how Bellman-Ford finds cheaper routes during off-peak seasons", 
                        style={'color': '#94a3b8', 'marginBottom': '15px'}),
                    
                    html.Div([
                        html.Div([
                            html.Label("From", className="field-label"),
                            dcc.Dropdown(
                                id='seasonal-src',
                                options=airport_options,
                                value='JFK',
                                className="airport-dd"
                            ),
                        ], className="field-group"),
                        
                        html.Div([
                            html.Label("To", className="field-label"),
                            dcc.Dropdown(
                                id='seasonal-dst',
                                options=airport_options,
                                value='LAX',
                                className="airport-dd"
                            ),
                        ], className="field-group"),
                        
                        html.Button("Compare Seasonal Prices", id='demo-seasonal-bf-btn', 
                                className="btn-primary", style={'marginTop': '10px', 'width': '100%'}),
                        
                    ]),
                    
                    html.Div(id='seasonal-bf-result', style={'marginTop': '20px'}),
                    
                ], className="card adv-card", style={'marginTop': '20px'}),

                # Route Explorer
                html.Div([
                    html.Div("Route Explorer", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                            id='explorer-from',
                            options=get_airport_options(graph),
                            placeholder="From...",
                            searchable=True,
                            clearable=True
                        ),
                        dcc.Dropdown(
                            id='explorer-to',
                            options=get_airport_options(graph),
                            placeholder="To...",
                            searchable=True,
                            clearable=True
                        ),
                        html.Button("Explore Alternatives",
                                    id='explore-routes-btn',
                                    className="btn-primary", n_clicks=0,
                                    style={'marginTop': '12px'}),
                        html.Div(id='explore-results')
                    ])
                ], className="card adv-card"),

                # Cache Status
                html.Div([
                    html.Div("Cache Status", className="card-header"),
                    html.Div(id='cache-status', children=[
                        html.P(
                            f"Cache Manager: {'Active' if cache_available else 'Not Available'}",
                            style={'color': '#64748b'})
                    ]),
                    html.Button("Clear Cache", id='clear-cache-btn',
                                className="btn-secondary", n_clicks=0,
                                disabled=not cache_available,
                                style={'marginTop': '12px'}),
                ], className="card adv-card"),

            ], className="adv-col"),
        ], className="adv-layout"),
    ])
