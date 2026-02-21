import streamlit as st
from streamlit_folium import st_folium
import folium
from pathlib import Path

from src.loader import load_graph
from src.services.routing import find_route

# --- Robust dataset path (works on any machine) ---
ROOT = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    ROOT / "data" / "airline_routes.json",
    ROOT / "data" / "airline_routes - Copy.json",
]

def get_data_path() -> str:
    for p in DATA_CANDIDATES:
        if p.exists():
            return str(p)
    raise FileNotFoundError("Dataset not found in ./data/")

@st.cache_resource
def get_graph():
    return load_graph(get_data_path())

def draw_map(graph, path):
    coords = [(graph.airports[c].lat, graph.airports[c].lon) for c in path]
    m = folium.Map(location=coords[0], zoom_start=3)

    for c in path:
        a = graph.airports[c]
        folium.Marker([a.lat, a.lon], tooltip=f"{c} - {a.city}, {a.country}").add_to(m)

    folium.PolyLine(coords).add_to(m)
    return m

def main():
    st.set_page_config(page_title="Flight Map Routing Prototype", layout="wide")
    st.title("✈️ Flight Map Routing Prototype")

    graph = get_graph()
    st.caption(f"Loaded {len(graph.airports)} airports")

    # --- Persist outputs across reruns ---
    if "result" not in st.session_state:
        st.session_state.result = None
    if "error" not in st.session_state:
        st.session_state.error = None

    # --- Form prevents constant reruns while typing ---
    with st.form("route_form"):
        src = st.text_input("Source airport (e.g. SIN)").strip().upper()
        dst = st.text_input("Destination airport (e.g. HND)").strip().upper()
        mode = st.selectbox("Optimise for", ["hops", "distance", "time", "price"])
        submitted = st.form_submit_button("Find Route")

    if submitted:
        if not src or not dst:
            st.session_state.result = None
            st.session_state.error = "Please enter both source and destination airport codes."
        else:
            with st.spinner("Finding route..."):
                try:
                    res = find_route(graph, src, dst, mode)
                    if res is None:
                        st.session_state.result = None
                        st.session_state.error = "No route found (or invalid airport code). Try another pair."
                    else:
                        st.session_state.result = res
                        st.session_state.error = None
                except Exception as e:
                    st.session_state.result = None
                    st.session_state.error = f"Error while computing route: {e}"

    # --- Render from state (stable, no disappearing) ---
    if st.session_state.error:
        st.error(st.session_state.error)

    if st.session_state.result:
        result = st.session_state.result
        st.success(result.pretty())
        st.write({
            "hops": result.hops,
            "km": result.total_km,
            "minutes": result.total_minutes,
            "price": result.total_price
        })

        m = draw_map(graph, result.path)
        st_folium(m, width=900, height=520, key="map")

if __name__ == "__main__":
    main()