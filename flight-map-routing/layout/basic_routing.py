from dash import html, dcc
import dash_leaflet as dl


def create_basic_routing_tab(graph, get_airport_options):
    return dcc.Tab(label='🎯 Basic Routing', value='basic-routing', children=[
        html.Div([
            # Left Column - Route Configuration
            html.Div([
                html.Div([
                    html.Div("Route Configuration", className="card-header"),

                    html.Label("From:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='src-dropdown',
                        options=get_airport_options(graph),
                        placeholder="Type to search departure...",
                        value='SIN' if 'SIN' in graph.airports else None,
                        searchable=True,
                        clearable=True,
                        className="airport-dd"
                    ),

                    html.Label("To:", style={'fontWeight': 'bold', 'marginTop': '15px'}),
                    dcc.Dropdown(
                        id='dst-dropdown',
                        options=get_airport_options(graph),
                        placeholder="Type to search arrival...",
                        value='HND' if 'HND' in graph.airports else None,
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

                ], className="card layout-panel layout-left"),
            ]),

            # Center Column - Map & Charts
            html.Div([
                dcc.Tabs(id='results-tabs', value='map-tab', children=[

                    dcc.Tab(label='🗺️ Route Map', value='map-tab', children=[
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
                            style={'width': '100%', 'height': '420px', 'borderRadius': '18px'},
                            children=[
                                dl.ScaleControl(position="bottomleft"),
                                dl.LayersControl([
                                    dl.BaseLayer(
                                        dl.TileLayer(
                                            url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                                            noWrap=True
                                        ),
                                        name="Map",
                                        checked=True
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

                    dcc.Tab(label='📊 Route Analysis', value='analysis-tab',
                            children=[dcc.Graph(id='route-analysis', style={'height': '520px'})]),

                    dcc.Tab(label='📈 Performance', value='performance-tab',
                            children=[dcc.Graph(id='performance-metrics', style={'height': '520px'})])
                ])
            ], className="layout-panel layout-center"),

            # Right Column - Route Summary
            html.Div([
                html.Div("📋 Route Summary", className="card-header"),
                html.Div(id='route-summary', children=[
                    html.P("Select airports and click 'Find Route'",
                           style={'color': '#8f9bb3', 'textAlign': 'center'})
                ])
            ], className="card layout-panel layout-right"),

        ], className="main-responsive-layout"),
    ])
