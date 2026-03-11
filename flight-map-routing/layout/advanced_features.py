from dash import html, dcc


def create_advanced_features_tab(graph, get_airport_options, yen_available, cache_available):
    return dcc.Tab(label='🔧 Advanced Features', value='advanced', children=[
        html.Div([
            # Left Column
            html.Div([
                # Multi-City Planning
                html.Div([
                    html.Div("🗺️ Multi-City Trip Planner", className="card-header"),
                    html.Div([
                        dcc.Dropdown(
                            id='multi-city-selector',
                            options=get_airport_options(graph),
                            placeholder="Select cities to visit.",
                            multi=True,
                            value=['SIN', 'HND', 'LHR'] if all(c in graph.airports for c in ['SIN', 'HND', 'LHR']) else [],
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
                    html.Div(f"🔄 K-Shortest Paths {'' if yen_available else '(Not Available)'}", className="card-header"),
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
                                    {'label': ' Distance', 'value': 'distance'},
                                    {'label': ' Time', 'value': 'time'},
                                    {'label': ' Price', 'value': 'price'},
                                ],
                                value='distance',
                                inline=True
                            ),
                        ], style={'marginTop': '10px', 'display': 'flex', 'alignItems': 'center'}),
                        html.Button("🔍 Find K Paths", id='find-k-paths-btn',
                                    className="btn-secondary", n_clicks=0, disabled=not yen_available),
                        html.Div(id='k-paths-results')
                    ])
                ], className="card"),

                # Algorithm Comparison
                html.Div([
                    html.Div("⚡ Algorithm Comparison", className="card-header"),
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
                        html.Button("📊 Compare All Algorithms", id='compare-algos-btn',
                                    className="btn-secondary", n_clicks=0),
                        html.Div(id='comparison-results')
                    ])
                ], className="card"),

            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),

            # Right Column
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
                        html.Button("🔍 Explore Alternatives", id='explore-routes-btn',
                                    className="btn-secondary", n_clicks=0),
                        html.Div(id='explore-results')
                    ])
                ], className="card"),

                # Cache Status
                html.Div([
                    html.Div("💾 Cache Status", className="card-header"),
                    html.Div(id='cache-status', children=[
                        html.P(f"Cache Manager: {'✅ Active' if cache_available else '❌ Not Available'}",
                               style={'color': '#e5e9f0'})
                    ]),
                    html.Button("🗑️ Clear Cache", id='clear-cache-btn',
                                className="btn-secondary", n_clicks=0, disabled=not cache_available),
                ], className="card"),

            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        ]),
    ])
