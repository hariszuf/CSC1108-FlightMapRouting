from collections import deque
from typing import Dict, List, Optional, Tuple
from src.graph import FlightGraph


def bfs_least_hops(
    graph: FlightGraph,
    origin: str,
    destination: str,
) -> Tuple[Optional[List[str]], int]:
    """
    Find the path with the fewest stops (hops) between two airports using BFS.

    Parameters
    ----------
    graph       : FlightGraph  – the loaded flight network
    origin      : str          – IATA code of the departure airport
    destination : str          – IATA code of the arrival airport

    Returns
    -------
    (path, hops)
        path – ordered list of IATA codes from origin to destination,
               or None if no path exists.
        hops – number of flights taken (len(path) - 1), or -1 if unreachable.
    """
    if origin not in graph:
        raise ValueError(f"Origin airport '{origin}' not found in graph.")
    if destination not in graph:
        raise ValueError(f"Destination airport '{destination}' not found in graph.")

    if origin == destination:
        return [origin], 0

    # BFS queue: each element is (current_iata, path_so_far)
    queue: deque = deque()
    queue.append((origin, [origin]))

    visited: set = {origin}

    while queue:
        current, path = queue.popleft()

        for route in graph.get_neighbors(current):
            neighbour = route.iata
            if neighbour == destination:
                full_path = path + [neighbour]
                return full_path, len(full_path) - 1
            if neighbour not in visited and neighbour in graph:
                visited.add(neighbour)
                queue.append((neighbour, path + [neighbour]))

    return None, -1
