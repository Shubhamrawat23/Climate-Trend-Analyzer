# Climate Hazard Trend Analyzer

A full-stack web application for analyzing historical heatwave trends at a chosen location and time period. It retrieves daily maximum temperatures from the Open-Meteo Historical Weather API, detects heatwave events with a percentile-based threshold, calculates annual metrics, fits a linear trend, and presents the results as charts and plain-language insights.

Built with a **FastAPI** backend, **MongoDB** caching, and a **React + Tailwind CSS** frontend.

---

## Features

- **Flexible location input:** type a city or state, enter latitude and longitude, or click a point on the map.
- **Date range selection:** choose a start and end date with a calendar picker (`yyyy-mm-dd`). Future dates are disabled.
- **Heatwave detection:** a 95th-percentile threshold from the 1991–2020 reference period, with a minimum run of three consecutive days.
- **Annual metrics and trend analysis:** event frequency, total heatwave days, average event duration, and a linear-regression trend.
- **Visualizations and insights:** frequency and duration charts, plus auto-generated key insights (trend direction, rate of change, peak year).
- **Caching:** MongoDB stores thresholds, daily temperatures, and finished analyses so repeat requests are fast.
- **Report export:** export the results (annual metrics, insights) as a spreadsheet.
- **Error handling:** clear messages for invalid input, unknown places, unreachable APIs, and timeouts. A newer request cancels any request still in flight.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Recharts, Leaflet / React-Leaflet |
| Backend | Python, FastAPI, Pydantic, NumPy |
| Database | MongoDB |
| Data sources | Open-Meteo Historical Weather API, Open-Meteo Geocoding API, OpenStreetMap tiles |

---

## Project Structure

```text
Climate Analyzer/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   │   └── db_connection.py      # MongoDB connection and collections
│   │   ├── modules/
│   │   │   ├── climate_router.py     # API routes
│   │   │   ├── climate_schema.py     # Pydantic request/response models
│   │   │   └── climate_service.py    # fetching, detection, metrics, trend, insights
│   │   └── main.py                   # FastAPI app entry point
│   ├── .env
│   ├── .gitignore
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── ClimateCharts.jsx     # frequency and duration charts
│   │   │   ├── FilterPanel.jsx       # region, map, and date-range inputs
│   │   │   ├── Header.jsx
│   │   │   ├── KeyInsights.jsx       # auto-generated insights
│   │   │   └── MapPicker.jsx         # Leaflet map for picking a point
│   │   ├── App.jsx                   # state, API call, layout, export
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .env
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## Architecture

```text
React Frontend
      │  user picks a location and date range
      ▼
FastAPI endpoint  (POST /api/analysis)
      ▼
Climate service
      ├──────► MongoDB cache (analysis, threshold, daily temperatures)
      └──────► Open-Meteo APIs (geocoding, historical weather)
      ▼
Heatwave detection
      ▼
Annual metrics and trend analysis
      ▼
JSON response
      ▼
Charts, insights, and export
```

### Frontend
- **Component-driven:** separate components for the header, filters, charts, insights, and map.
- **Inverse data flow:** `MapPicker` captures map clicks with Leaflet's `useMapEvents` and passes the coordinates up to `FilterPanel` through callback props.
- **Request handling:** `App.jsx` owns the API call. It uses an `AbortController`, so only the newest request can update the screen, and it applies a request timeout. It turns every failure into one readable message.
- **Visualization:** Recharts plots annual event frequency and average duration.

### Backend
- **Layered design:** router (`climate_router.py`), schemas (`climate_schema.py`), business logic (`climate_service.py`), and database access (`db_connection.py`) are kept separate.
- **Validation:** Pydantic requires either a region name or both `lat` and `lon`, valid coordinate ranges, and `start_date <= end_date`.
- **Caching:** the service checks three MongoDB collections before calling Open-Meteo: finished analyses, reference-period thresholds, and daily temperatures.

---

## API

`POST /api/analysis`

```json
{
  "region": "mumbai",
  "lat": null,
  "lon": null,
  "start_date": "2020-01-01",
  "end_date": "2025-12-31"
}
```

Send either `region`, or both `lat` and `lon`. Interactive documentation is at `/docs` when enabled.

**Response (abridged)**

```json
{
  "name": "Mumbai",
  "latitude": 19.07283,
  "longitude": 72.88261,
  "start_date": "2020-01-01",
  "end_date": "2025-12-31",
  "reference_period": "1991-2020",
  "threshold_percentile": 95,
  "threshold_val": 33.9,
  "hazard_type": "heatwave",
  "annual_metrics": [
    { "year": 2020, "event_count": 2, "total_heatwave_days": 6, "avg_event_duration_days": 3.0 }
  ],
  "trend": {
    "frequency_trend": { "slope": 1.0857, "direction": "increasing", "percentage_change": 237.5 },
    "heatwave_days_trend": { "slope": 9.8, "direction": "increasing", "percentage_change": 773.68 }
  },
  "insights": {
    "frequency_trend": "Heatwave frequency shows an increasing linear trend over the selected period. ...",
    "heatwave_days_trend": "Annual heatwave days shows an increasing linear trend over the selected period. ...",
    "peak_year_insight": "The highest annual number of heatwave days occurred in 2023, with 52 days."
  }
}
```

**Errors** (returned as `{ "detail": "..." }`)

| Status | Meaning |
|---|---|
| 422 | Invalid input: missing region or coordinates, bad dates, or coordinates out of range |
| 404 | Region not found by the geocoding service |
| 502 | The weather provider failed or returned incomplete data |
| 500 | Heatwave detection, metrics, or trend calculation failed |

---

## Data Source

- **Weather:** [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), using the daily maximum temperature (`temperature_2m_max`) for the chosen latitude and longitude.
- **Place names:** [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api) converts a city or state name into coordinates (first match is used).
- **Map tiles:** OpenStreetMap, shown through Leaflet.

Results depend on the completeness and quality of the provider's data. If any day in the requested range is missing, the request fails instead of returning partial results.

---

## Heatwave Detection Logic

1. **Reference period:** 1991–2020.
2. **Threshold:** the 95th percentile of all daily maximum temperatures in the reference period for the selected location, rounded to two decimals.
3. **Hot day:** a day is hot when its maximum temperature is **strictly greater than** the threshold.
4. **Heatwave event:** a run of **at least three consecutive hot days**. Shorter runs are ignored. Each event records its start date, end date, and duration.
5. **Annual metrics**, for every year in the selected range:
   - `event_count`: events that **start** in that year
   - `total_heatwave_days`: heatwave days falling in that calendar year (an event that crosses New Year is split between the two years)
   - `avg_event_duration_days`: average duration of events starting that year
6. **Trend:** a straight line (`y = mx + c`) is fitted by least squares to `event_count` and to `total_heatwave_days` against year. The slope gives the rate of change per year, and the direction is increasing, decreasing, or stable. The percentage change compares the fitted values at the first and last year, and it is `null` when the starting value is below 1 or fewer than two years are available.
7. **Insights:** the trend numbers and the peak year are turned into short sentences automatically.

A regression trend describes the pattern in the analyzed data. It does not establish a cause and does not guarantee future conditions.

---

## Assumptions and Limitations

- The scope is heatwaves only. Other hazards are not included yet.
- The 1991–2020 period is the fixed baseline for the threshold.
- **One threshold for the whole year.** The percentile is calculated from all days of the year, not separately for each calendar day or season. Warm-season days are therefore more likely to count as hot, and events can appear in months that are not the hottest of the year.
- A location is a single geographic point, not a whole city or administrative area. City names resolve to the first geocoding match, so ambiguous names (for example "Springfield") may not be the place the user intended. Results should not be generalized to a larger area.
- Start date must be on or before the end date. Future dates are disabled, and the archive lags real time by several days, so very recent dates may be unavailable.
- Linear regression summarizes the trend but does not establish causation. With a short range (a few years), the trend and percentage change are sensitive to single years.
- MongoDB caching reduces repeated work. Cache expiry and invalidation are not implemented and should be added if the application is extended.
- Export formatting follows the data shown on screen, with a title block and clean table headers for spreadsheet software such as Excel or Google Sheets.

---

## Local Setup

### Prerequisites
- Python 3.14.5
- Node.js 22.20, with npm
- A MongoDB instance, either local or hosted

### 1. Clone the repository
```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd "Climate Analyzer"
```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv .venv

# Windows
.venv\scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env` and set the MongoDB connection using the variable names that `app/db/db_connection.py` reads. Do not commit credentials or other secrets.

Start the server from the `backend/` directory:
```bash
uvicorn app.main:app --reload --port 8000
```
The API is at `http://127.0.0.1:8000`, and the docs are at `http://127.0.0.1:8000/docs`.

### 3. Frontend (React + Vite)
Open a second terminal:
```bash
cd frontend
npm install
```

Create `frontend/.env`:
```env
VITE_API_URL=http://127.0.0.1:8000
```

Run the dev server:
```bash
npm run dev
```
Open the local URL Vite prints, usually `http://localhost:5173`.

---

## Deployment

- **Frontend:** `<ADD_DEPLOYED_FRONTEND_URL>`
- **Backend API:** `<ADD_DEPLOYED_BACKEND_URL>`
- **API docs:** `<ADD_DEPLOYED_BACKEND_URL>/docs` (if enabled)

For the deployed app to work:
- Set `VITE_API_URL` on the frontend to the deployed backend URL.
- The backend must be able to reach the configured MongoDB instance.
- The backend must allow the frontend's origin through CORS.

---

## Future Improvements

**Analysis**
- Add a significance test (such as Mann-Kendall) alongside the linear trend.
- Support more hazards, such as drought and heavy rainfall.
- Compare two locations side by side.

**Frontend**
- Export a visual PDF report with live charts and insight cards.
- Add skeleton loaders and transitions for smoother loading feedback.

**Backend**
- Add cache expiry (TTL indexes) and a way to invalidate stale analyses.
- Replace blocking `requests` calls with an async HTTP client so slow upstream calls don't hold up the server.
- Add rate limiting and structured logging.
- Add `pytest` unit tests for detection, metrics, and trend logic, plus integration tests for the API.
- Provide a Docker setup so the backend and MongoDB start with one command.