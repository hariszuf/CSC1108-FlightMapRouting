import streamlit as st
from streamlit_folium import st_folium
import folium

from src.loader import load_graph
from src.services.routing import find_route

DATA_PATH = "data/airline_routes.json"

@st.cache_resource
def get_graph():
    return load_graph(DATA_PATH)

def draw_map(graph, path):
    coords = [(graph.airports[c].lat, graph.airports[c].lon) for c in path]
    m = folium.Map(location=coords[0], zoom_start=3)

    for c in path:
        a = graph.airports[c]
        folium.Marker([a.lat, a.lon], tooltip=c).add_to(m)

    folium.PolyLine(coords).add_to(m)
    return m

def main():
    st.title("✈️ Flight Map Routing")

    graph = get_graph()

    src = st.text_input("Source airport (e.g. SIN)").upper()
    dst = st.text_input("Destination airport (e.g. HND)").upper()
    mode = st.selectbox("Optimise for", ["hops","distance","time","price"])

    if st.button("Find Route"):
        result = find_route(graph, src, dst, mode)
        if not result:
            st.error("No route found")
            return

        st.success(result.pretty())
        st.write({
            "hops": result.hops,
            "km": result.total_km,
            "minutes": result.total_minutes,
            "price": result.total_price
        })

        m = draw_map(graph, result.path)
        st_folium(m, width=800)

if __name__ == "__main__":
    main()