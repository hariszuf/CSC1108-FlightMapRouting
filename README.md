# CSC1108-FlightMapRouting
# ✈️ Flight Map Routing (CSC1108 Project)

A flight routing system built using Data Structures & Algorithms.

Current app (official): **Dash + dash-leaflet**
Legacy prototype: **Streamlit** (kept for reference)


- Graph representation using adjacency list
- BFS (least hops search)
- Dijkstra’s algorithm (shortest distance / time / price)
- Interactive map visualisation using Streamlit + Folium

---

# 🐍 Setup Instructions

## 1️⃣ Clone the Repository

git clone <your-repo-url>
cd flight-map-routing

---

## 2️⃣ Create a Virtual Environment

### Windows
python -m venv .venv
.venv\Scripts\activate

### Mac / Linux
python3 -m venv .venv
source .venv/bin/activate


If activated successfully, you should see:
(.venv) in your terminal.

---

## 3️⃣ Install Dependencies
pip install -r requirements.txt

---

📂 Dataset

Ensure the dataset exists at:

data/airline_routes.json

If your dataset is named airline_routes - Copy.json, rename it:

# Windows PowerShell
Rename-Item "data\airline_routes - Copy.json" "airline_routes.json"
▶️ Run the Dash App (Official)

From the project root:

python dash_app.py

Dash will print a local URL (typically):

http://127.0.0.1:8050/
🧪 (Optional) Run Legacy Streamlit Prototype

The Streamlit prototype is kept for reference only.

streamlit run legacy/streamlit_app.py

Note: Streamlit dependencies are not included by default anymore.
If you want to run this legacy prototype, install:
pip install streamlit folium streamlit-folium

🧠 Algorithms Implemented

BFS → least number of hops

Dijkstra → shortest distance / time / price

⚠️ Notes

Do NOT commit .venv/ or __pycache__/

Always run commands from the project root


---

## 5) Update `.gitignore` (if you haven’t already)
Make sure it includes:

```gitignore
.venv/
__pycache__/
*.pyc
.streamlit/
