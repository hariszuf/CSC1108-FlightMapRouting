from dash import html, dcc
import dash_leaflet as dl


def create_basic_routing_tab(graph, get_airport_options):
    return dcc.Tab(label='Basic Routing', value='basic-routing', children=[
        html.Div([
            # Left Column - Route Configuration
            html.Div([
                html.Div([
                    html.Div("Route Configuration", className="card-header"),

                    # Trip type selector
                    html.Div([
                        html.Button("One way", className="trip-type-btn trip-type-active",
                                    id='trip-oneway'),
                        html.Button("Round trip", className="trip-type-btn",
                                    id='trip-roundtrip'),
                        html.Button("Multi-city", className="trip-type-btn",
                                    id='trip-multicity'),
                    ], className="trip-type-group"),

                    html.Div([
                        html.Div([
                            html.Label("Origin", className="field-label"),
                            dcc.Dropdown(
                                id='src-dropdown',
                                options=get_airport_options(graph),
                                placeholder="Select departure airport",
                                value='SIN' if 'SIN' in graph.airports else None,
                                searchable=True,
                                clearable=True,
                                className="airport-dd"
                            ),
                        ], className="field-group"),

                        html.Div([
                            html.Button("⇅", id='swap-airports-btn',
                                        className="swap-icon", n_clicks=0),
                        ], className="swap-container"),

                        html.Div([
                            html.Label("Destination", className="field-label"),
                            dcc.Dropdown(
                                id='dst-dropdown',
                                options=get_airport_options(graph),
                                placeholder="Select arrival airport",
                                value='HND' if 'HND' in graph.airports else None,
                                searchable=True,
                                clearable=True,
                                className="airport-dd"
                            ),
                        ], className="field-group"),
                    ], className="origin-dest-section"),

                    html.Div([
                        html.Label("Optimize for", className="field-label"),
                        dcc.RadioItems(
                            id='optimization-mode',
                            options=[
                                {'label': 'Least hops', 'value': 'hops'},
                                {'label': 'Shortest distance', 'value': 'distance'},
                                {'label': 'Fastest time', 'value': 'time'},
                                {'label': 'Cheapest price', 'value': 'price'},
                            ],
                            value='distance',
                            className="opt-radio opt-radio-grid",
                        ),
                    ], className="optimize-section"),

                    html.Button("Search flights", id='find-route-btn',
                                className="btn-primary", n_clicks=0),

                ], className="card"),
            ], className="layout-panel layout-left"),

            # Center Column - Map & Charts
            html.Div([
                dcc.Tabs(id='results-tabs', value='map-tab', children=[

                    dcc.Tab(label='Route Map', value='map-tab', children=[
                        dl.Map(
                            id='flight-map',
                            center=[20, 0],
                            zoom=2,
                            minZoom=2,
                            maxZoom=12,
                            bounceAtZoomLimits=False,
                            preferCanvas=True,
                            inertia=True,
                            maxBounds=[[-85, -180], [85, 180]],
                            maxBoundsViscosity=0.3,
                            worldCopyJump=True,
                            zoomSnap=0.25,
                            zoomDelta=0.5,
                            style={'width': '100%', 'height': '420px',
                                   'borderRadius': '12px'},
                            children=[
                                dl.ScaleControl(position="bottomleft"),
                                dl.LayersControl([
                                    dl.BaseLayer(
                                        dl.TileLayer(
                                            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                                            noWrap=True
                                        ),
                                        name="Dark",
                                        checked=True
                                    ),
                                    dl.BaseLayer(
                                        dl.TileLayer(
                                            url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                                            noWrap=True
                                        ),
                                        name="Map",
                                        checked=False
                                    ),
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
                                dl.LayerGroup(id='map-layers')
                            ]
                        )
                    ]),

                    dcc.Tab(label='Route Analysis', value='analysis-tab',
                            children=[dcc.Graph(id='route-analysis',
                                                style={'height': '520px'})]),

                    dcc.Tab(label='Performance', value='performance-tab',
                            children=[dcc.Graph(id='performance-metrics',
                                                style={'height': '520px'})])
                ])
            ], className="layout-panel layout-center"),

            # Right Column - Route Summary
            html.Div([
                html.Div("Flight Details", className="card-header"),
                html.Div(id='route-summary', children=[
                    html.P("Select airports and click 'Search flights'",
                           style={'color': '#8f9bb3', 'textAlign': 'center',
                                  'padding': '40px 20px'})
                ])
            ], className="card layout-panel layout-right"),

        ], className="main-responsive-layout"),
    ])
