# CSC1108-FlightMapRouting
# ✈️ Flight Map Routing (CSC1108 Project)

A flight routing system built using Data Structures & Algorithms.

- Graph representation using adjacency list
- BFS (least hops search)
- Dijkstra’s algorithm (shortest distance / time / price)
- Interactive map visualisation using Streamlit + Folium

---

# 📦 Project Structure
flight-map-routing/
│
├── app.py
├── data/
│ └── airline_routes.json
│
├── src/
│ ├── loader.py
│ ├── graph.py
│ ├── models.py
│ ├── algorithms/
│ │ ├── bfs.py
│ │ └── dijkstra.py
│ └── services/
│ └── routing.py
│
├── requirements.txt
└── README.md


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

If `requirements.txt` does not exist:
pip install streamlit folium streamlit-folium
---

# ▶️ Running the Application

From the project root:
streamlit run app.py

You should see:
Local URL: http://localhost:8501
Open that link in your browser.

---
# 🧪 Example Test Routes

Try:

- SIN → HND
- LHR → JFK
- SFO → NRT

---

# 📂 Dataset Requirement

Make sure the dataset exists at:


data/airline_routes.json


If your file is named:


airline_routes - Copy.json


Rename it to:


airline_routes.json


---

# 🔁 Daily Workflow (Team Members)

Each time you work:

### Windows

git pull
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py


### Mac / Linux

git pull
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py


---

# 🧠 Algorithms Implemented

- **BFS** → Least number of hops  
- **Dijkstra** → Shortest distance / time / price  

---

# ⚠️ Notes

- Do NOT commit the `.venv` folder
- Do NOT commit `__pycache__`
- Always run the app from the project root folder
- If you get import errors, ensure the virtual environment is activated

---
