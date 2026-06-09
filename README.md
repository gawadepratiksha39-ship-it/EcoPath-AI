# EcoPath AI

An AI-powered climate action platform that helps users choose eco-friendly travel routes and track their carbon footprint.

> **Status:** Full-stack India route planner with rule-based AI sustainability engine, auth, eco scores, and personalized insights.

## Project Structure

```
ecopath-ai/
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   │   ├── Navbar.jsx     # Top navigation
│   │   │   ├── RouteForm.jsx  # Source/destination input → wire to API
│   │   │   ├── MapView.jsx    # Leaflet map → wire to OSM routes
│   │   │   ├── CarbonCard.jsx # Emissions display → wire to calculator
│   │   │   └── Dashboard.jsx  # History summary → wire to /api/carbon/history
│   │   ├── pages/
│   │   │   ├── Home.jsx       # Route planner page
│   │   │   └── History.jsx    # Carbon history page
│   │   ├── services/
│   │   │   └── api.js         # All backend HTTP calls
│   │   ├── App.jsx            # Router + layout
│   │   ├── main.jsx           # React entry point
│   │   └── index.css          # Global styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js         # Dev proxy to Flask on :5000
│
├── backend/                   # Python Flask API
│   ├── routes/
│   │   ├── routes.py          # → Future: POST /api/routes/plan
│   │   └── carbon.py          # → Future: carbon calc + history endpoints
│   ├── services/
│   │   ├── ai_service.py      # → Future: OpenAI recommendations
│   │   ├── carbon_service.py  # CO₂ emission factors & calculation
│   │   └── map_service.py     # Nominatim geocoding + OSRM routing
│   ├── models/
│   │   └── database.py        # SQLite connection + schema
│   ├── app.py                 # Flask entry point + CORS + /api/test
│   ├── requirements.txt
│   └── emissions.db           # SQLite database (auto-created on first run)
│
├── .gitignore
└── README.md
```

## Where to Add Future Features

| Feature | Frontend | Backend |
|---------|----------|---------|
| Route planner | ✅ `RouteForm.jsx`, `MapView.jsx`, `api.js` | ✅ `routes/routes.py`, `services/map_service.py` |
| Carbon calculator | ✅ `CarbonCard.jsx` | ✅ `services/carbon_service.py` |
| AI recommendations | ✅ `AIInsightsCard.jsx`, `RouteComparison.jsx` | ✅ `services/ai_service.py` |
| History dashboard | ✅ `Dashboard.jsx`, `History.jsx` | ✅ `routes/carbon.py` |
| Map (OSM + Leaflet) | ✅ `MapView.jsx` with react-leaflet | ✅ OSRM via `map_service.py` |

---

## Step 1: Install Dependencies

### Backend (Python)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Frontend (Node.js)

```bash
cd frontend
npm install
```

---

## Step 2: Run Backend

From the `backend` directory (with virtual environment activated):

```bash
python app.py
```

The API will start at **http://localhost:5000**.

Test it:

```bash
curl http://localhost:5000/api/test
```

Expected response:

```json
{
  "status": "ok",
  "message": "EcoPath AI backend is running",
  "version": "0.1.0"
}
```

---

## Step 3: Run Frontend

Open a **new terminal**, then:

```bash
cd frontend
npm run dev
```

The app will start at **http://localhost:5173**.

Vite proxies `/api/*` requests to the Flask backend automatically.

---

## Step 4: Verify Project Works

1. Open **http://localhost:5173** in your browser.
2. You should see the EcoPath AI home page with the route planner form.
3. A green badge should show **"EcoPath AI backend is running"** — this confirms frontend ↔ backend connectivity.
4. Navigate to **History** via the navbar to confirm React Router works.
5. Optionally test the API directly: **http://localhost:5000/api/test**

---

## Tech Stack

- **Frontend:** React 18, Vite, React Router, Leaflet (ready to integrate)
- **Backend:** Python Flask, Flask-CORS
- **Database:** SQLite (`emissions.db`)
- **Maps (future):** OpenStreetMap + Leaflet
- **AI:** Rule-based sustainability engine (no paid APIs)

## API Endpoints

| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/api/test` | ✅ Working |
| POST | `/api/auth/register` | ✅ User registration |
| POST | `/api/auth/login` | ✅ JWT login |
| GET | `/api/auth/me` | ✅ Profile + stats |
| POST | `/api/routes/plan` | ✅ Route + carbon + AI insights |
| GET | `/api/routes/suggest` | ✅ Indian city autocomplete |
| GET | `/api/carbon/history` | ✅ Per-user trip history |
| POST | `/api/ai/analyze` | ✅ AI route analysis |
| GET | `/api/ai/insights` | ✅ Personalized sustainability insights |

Emission factors (kg CO₂/km): Car 0.21 · Bus 0.10 · Bicycle/Walking 0 · Train 0.05

---

## AI Module Architecture

The AI sustainability engine is a **rule-based decision system** in `backend/services/ai_service.py`. It requires no external paid APIs and runs entirely on the server using route data, emission factors, and SQLite trip history.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Route Planner  │────▶│   ai_service.py  │────▶│  AI Insights JSON   │
│  (distance,     │     │  Rule Engine     │     │  (score, tips,      │
│   mode, carbon) │     │                  │     │   comparison)       │
└─────────────────┘     └────────┬─────────┘     └─────────────────────┘
                                   │
                          ┌────────▼─────────┐
                          │ carbon_history   │
                          │ (user trip data) │
                          └──────────────────┘
```

### Components

| Function | Purpose |
|----------|---------|
| `analyze_route()` | Full AI analysis after route planning |
| `calculate_eco_score()` | 0–100 score vs car baseline |
| `compare_route_modes()` | Emissions for all 5 transport modes |
| `_generate_recommendations()` | Rule-based eco tips |
| `get_personalized_insights()` | History analytics for dashboard |
| `get_sustainability_badge()` | Bronze → Green Champion badges |

### API Flow

1. User plans a route → `POST /api/routes/plan`
2. Backend calculates distance, time, carbon
3. `analyze_route()` attaches `ai_insights` to the response
4. History page calls `GET /api/ai/insights` for personalized analytics

---

## Recommendation Logic

The engine applies **distance-based rules** combined with **mode comparison**:

| Distance | Ideal Mode | Rule |
|----------|-----------|------|
| ≤ 3 km | Walking | Suggest walking/cycling over motorized transport |
| 3–15 km | Bicycle | Bus or cycle preferred over car |
| 15–100 km | Bus | Public transit over private car |
| 100–300 km | Train | Rail over road for long distances |
| > 300 km | Train | Strong train-over-car recommendation |

Additional rules:
- If current mode ≠ lowest-emission mode → recommend switch with exact kg CO₂ savings
- If user history shows heavy car usage → suggest breaking the car habit
- Each recommendation includes a natural-language **explanation** and priority (`high` / `medium` / `low`)

---

## Eco Score Calculation

```
Eco Score = (1 - current_emissions / car_emissions) × 100
```

| Score | Label | Color | Meaning |
|-------|-------|-------|---------|
| 80–100 | Excellent | Green | Minimal emissions (walk, cycle, train) |
| 60–79 | Good | Light green | Significantly below car baseline |
| 40–59 | Fair | Yellow | Moderate impact |
| 0–39 | Poor | Red | High-emission mode (typically car) |

---

## Sustainability Analytics

`GET /api/ai/insights` analyzes all user trips and returns:

- **Total emissions saved** — sum of (car baseline − actual) for every trip
- **Most-used transport mode** — from trip frequency analysis
- **Weekly performance** — trips, distance, carbon, avg eco score (last 7 days)
- **Monthly summary** — same metrics for last 30 days
- **Sustainability badge** — based on average eco score across all trips

### Badge Tiers

| Badge | Average Eco Score |
|-------|-------------------|
| Green Champion | ≥ 80 |
| Gold | ≥ 60 |
| Silver | ≥ 40 |
| Bronze | < 40 |

---

## Frontend AI Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `AIInsightsCard.jsx` | Route Planner | Eco score, recommendations, explanations |
| `RouteComparison.jsx` | Route Planner | 5-mode emission comparison |
| `SustainabilityInsights.jsx` | History, Profile | Full AI sustainability dashboard |
