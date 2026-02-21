"""
Flight Map Routing – Streamlit UI
==================================
Run with:
    cd flight-map-routing
    streamlit run src/ui/app.py
"""

import os
import sys

# Ensure the project root (flight-map-routing/) is on the path so that
# ``src.*`` imports work regardless of where Streamlit is launched from.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st

from src.loader import load_graph
from src.services.routing import RoutingService

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Flight Map Routing",
    page_icon="✈️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Load data (cached so it only runs once per session)
# ---------------------------------------------------------------------------
DATA_PATH = os.path.join(_ROOT, "data", "airports.json")


@st.cache_resource(show_spinner="Loading flight network…")
def get_service() -> RoutingService:
    graph = load_graph(DATA_PATH)
    return RoutingService(graph)


service = get_service()
options = service.airport_display_options()  # "IATA – City, Country" -> "IATA"
option_labels = list(options.keys())

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("✈️ Flight Router")
st.sidebar.markdown("Find routes between airports using BFS or Dijkstra.")

origin_label = st.sidebar.selectbox("Origin", option_labels, index=0)
dest_label = st.sidebar.selectbox(
    "Destination",
    option_labels,
    index=min(1, len(option_labels) - 1),
)

algorithm = st.sidebar.radio(
    "Optimise for",
    options=["Fewest Stops (BFS)", "Distance (km)", "Duration (min)", "Cheapest (USD)"],
)

find_btn = st.sidebar.button("Find Route", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("✈️ Flight Map Routing System")
st.caption(
    "Powered by BFS (fewest hops) & Dijkstra (distance · time · price) "
    "– no external graph libraries used."
)

if not find_btn:
    st.info("Select an origin, destination and optimisation strategy, then click **Find Route**.")
    st.stop()

origin = options[origin_label]
destination = options[dest_label]

if origin == destination:
    st.warning("Origin and destination are the same airport.")
    st.stop()

# ---------------------------------------------------------------------------
# Run the selected algorithm
# ---------------------------------------------------------------------------
with st.spinner("Computing route…"):
    if algorithm == "Fewest Stops (BFS)":
        result = service.find_least_hops(origin, destination)
    elif algorithm == "Distance (km)":
        result = service.find_shortest_distance(origin, destination)
    elif algorithm == "Duration (min)":
        result = service.find_shortest_time(origin, destination)
    else:
        result = service.find_cheapest(origin, destination)

# ---------------------------------------------------------------------------
# Display result
# ---------------------------------------------------------------------------
if not result.found:
    st.error(f"No route found between **{origin}** and **{destination}**.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Stops", result.hops)
col2.metric("Algorithm", algorithm.split(" ")[0])
col3.metric("Total cost", result.label)

st.divider()

# Path visualisation
st.subheader("Route Path")
path_str = "  →  ".join(
    [
        f"**{iata}** ({service.get_airport(iata).city_name})"
        for iata in result.path
    ]
)
st.markdown(path_str)

st.divider()

# Per-segment table
segments = service.get_segment_details(result.path)
if segments:
    st.subheader("Leg Details")

    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "From": f"{s['from']} ({s['from_city']})",
                "To": f"{s['to']} ({s['to_city']})",
                "Distance (km)": f"{s['km']:,.0f}",
                "Duration": s["duration"],
                "Price (USD)": f"{s['price']:,.2f}",
            }
            for s in segments
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Totals row
    total_km = sum(s["km"] for s in segments)
    total_min = sum(s["min"] for s in segments)
    total_price = sum(s["price"] for s in segments)

    st.divider()
    t1, t2, t3 = st.columns(3)
    t1.metric("Total Distance", f"{total_km:,.0f} km")

    h = int(total_min) // 60
    m = int(total_min) % 60
    t2.metric("Total Duration", f"{h}h {m}m")
    t3.metric("Total Price", f"USD {total_price:,.2f}")

# ---------------------------------------------------------------------------
# Airport info
# ---------------------------------------------------------------------------
st.divider()
with st.expander("Airport Details"):
    for airport in result.airports:
        st.markdown(
            f"**{airport.iata}** – {airport.name}  \n"
            f"📍 {airport.city_name}, {airport.country}  \n"
            f"🌐 Lat {airport.latitude:.4f}, Lon {airport.longitude:.4f}"
        )
        st.write("")
