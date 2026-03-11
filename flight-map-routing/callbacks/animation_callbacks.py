from dash import Output, Input, State


def register_animation_callbacks(app):

    @app.callback(
        Output("plane-anim", "n_intervals"),
        Input("current-route-store", "data")
    )
    def reset_plane_animation(route_data):
        return 0

    @app.callback(
        Output("plane-marker", "position"),
        Input("plane-anim", "n_intervals"),
        State("current-route-store", "data")
    )
    def animate_plane(n, route_data):
        if not route_data or "coords" not in route_data:
            return [0, 0]

        coords = route_data["coords"]
        if len(coords) < 2:
            return coords[0]

        steps_per_segment = 15
        total_steps = (len(coords) - 1) * steps_per_segment
        step = n % total_steps

        segment = step // steps_per_segment
        progress = (step % steps_per_segment) / steps_per_segment

        lat1, lon1 = coords[segment]
        lat2, lon2 = coords[segment + 1]

        return [lat1 + (lat2 - lat1) * progress, lon1 + (lon2 - lon1) * progress]

    @app.callback(
        Output("animated-route", "positions"),
        Input("plane-anim", "n_intervals"),
        State("current-route-store", "data")
    )
    def animate_route(n, route_data):
        if not route_data or "coords" not in route_data:
            return []

        coords = route_data["coords"]
        if len(coords) < 2:
            return coords

        steps_per_segment = 40
        total_steps = (len(coords) - 1) * steps_per_segment
        step = n % total_steps

        segment = step // steps_per_segment
        progress = (step % steps_per_segment) / steps_per_segment

        route_so_far = list(coords[:segment + 1])

        lat1, lon1 = coords[segment]
        lat2, lon2 = coords[segment + 1]

        route_so_far.append([
            lat1 + (lat2 - lat1) * progress,
            lon1 + (lon2 - lon1) * progress
        ])

        return route_so_far
