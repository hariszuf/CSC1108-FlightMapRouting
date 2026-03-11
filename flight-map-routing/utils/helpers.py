def path_to_coords(graph, path):
    """Convert path to list of coordinates"""
    return [(graph.airports[c].lat, graph.airports[c].lon) for c in path]


def get_airport_options(graph, search_term=""):
    """Get airport options with optional search filtering"""
    options = []
    for code in sorted(graph.airports.keys())[:10000]:
        airport = graph.airports[code]
        label = f"{code} - {airport.city}, {airport.country}"
        if search_term.lower() in label.lower() or not search_term:
            options.append({'label': label, 'value': code})
    return options


def count_routes(graph):
    """Count total routes in graph"""
    count = 0
    for src in graph.adj:
        count += len(graph.adj[src])
    return count


def format_duration(minutes):
    """Format minutes to hours and minutes"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"
