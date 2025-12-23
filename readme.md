# AquaFlow – Rural Water O&M Copilot

> Empowering Gram Panchayats with low-cost, real-time leak detection and water quality monitoring tools (Problem Statement ID: 25241, Ministry of Jal Shakti).

![Hero Placeholder](docs/images/hero-placeholder.png)

## Why This Matters
Rural piped water schemes often struggle with leak visibility, delayed repairs, and sparse water-quality data. AquaFlow pairs a simulation-driven sensor twin with a live web dashboard to give Panchayats simple, actionable insights for daily operations and maintenance.

## Problem Statement (Summary)
- **Challenge**: Empower Gram Panchayats to manage daily O&M of rural piped water supply using low-cost digital tools.
- **Needs**: Easy tracking of infrastructure, early leak detection, data-led decisions, community accountability.
- **Expected Outcomes**: Simple rural-ready tools for routine checks (pump hours, valve status, leaks, water quality), predictive insights from flow patterns, digital water-quality logs, and empowered local ownership.
- **Origin**: Ministry of Jal Shakti (Swachh Bharat Mission Gramin, DDWS) — Clean & Green Technology theme.

## Core Features
- Real-time leak detection and alerting with mechanic auto-assignment.
- Dual dashboards: **Admin** (oversight, assignments, history) and **Mechanic** (my tasks, acknowledgements).
- Live sensor twin: water level, pH, turbidity, salinity, flow, valve/tap states.
- Tkinter simulation app to model the network and push live data to Firebase.
- Server-Sent Events (SSE) for instant dashboard updates.
- Offline-safe simulation with mock Firebase fallback.
- Extensible roadmap for deployment (container/WSGI ready) and media (screens, demos).

## How Leak Detection Works (Step-by-Step Logic)
Each pipe segment is bounded by sensor nodes (circles in the simulation). To localize a leak:
1. **Isolate upstream**: Treat node `A` as the source, close valve at node `B`. Any detected loss between `A` and `B` signals a leak in that segment.
2. **Narrow further**: Now close `C` (next node) while `B` is blocked. If loss persists between `B` and `C`, the leak lies there. Otherwise proceed downstream.
3. **Iterate to the end**: Continue hop-by-hop isolation until the terminal node. Each isolation window updates active leak flags in Firebase.
4. **Assign and notify**: Detected leaks are auto-assigned round-robin to mechanics; dashboard alerts show pipe name, severity, assignee, and status.
5. **Resolve**: When the segment shows no loss, alerts auto-resolve and assignments clear.

## Architecture at a Glance
- **simulation/tkinder.py**: Tkinter-based network simulator; pushes valves, taps, sensors, leaks, and water flow to Firebase. Works online (serviceAccountKey*.json) or offline (mock Firebase).
- **water-monitoring-dashboard/app.py**: Flask + Flask-Login web app with SSE streams, role-based dashboards, mechanic assignment, alert history, and simulated leak endpoints for testing.
- **Firebase (RTDB)**: Single source of truth for `/water_system` data (valves, taps, sensors, active_leaks, water_level, water_flow, alerts).

## Quickstart (Local, Windows)
```powershell
# 1) Clone and enter
# git clone <your-fork-url>
cd "water-sim 4/water-sim"

# 2) Create & activate venv
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# 3) Install deps (root + dashboard)
pip install -r requirements.txt
pip install -r water-monitoring-dashboard/requirements.txt

# 4) Place Firebase service account key
# Put serviceAccountKey.json at project root (already present) or adjust FIREBASE_DB_URL

# 5) Run simulation (Tkinter GUI)
cd simulation
python tkinder.py

# 6) Run dashboard (Flask, port 5050)
cd ..\water-monitoring-dashboard
python app.py
```

### Environment
- `FIREBASE_DB_URL` (optional): Override the default RTDB URL.
- `SECRET_KEY` (optional): Flask secret key.

### Logins
- **Admin**: `admin` / `WaterMonitor2024!`
- **Mechanics**: `M001`/`mechanic001`, `M002`/`mechanic002`, `M003`/`mechanic003`

## Usage Flow
1. Launch Tkinter simulation → adjust valves, taps, water level, and add/remove leaks on pipes.
2. Data syncs to Firebase (or mock offline fallback); active leaks flagged.
3. Flask dashboard streams updates via SSE → shows system state, alerts, and assignments.
4. Mechanics log in, view assigned leaks, acknowledge, and resolve; admin can reassign or resolve all.

## Tech Stack
- Python, Flask, Flask-Login, gevent (SSE), Firebase Admin SDK, Tkinter
- Frontend: HTML/CSS/JS (dashboard), SSE for realtime

## Project Structure
- `simulation/tkinder.py` — network simulator + Firebase sync
- `water-monitoring-dashboard/app.py` — Flask app (admin + mechanic dashboards)
- `water-monitoring-dashboard/static/` — CSS/JS assets
- `water-monitoring-dashboard/templates/` — Jinja2 templates

## Screenshots & Demo (Placeholders)
- Dashboard Overview: `docs/images/dashboard.png`
- Alert & Assignment Flow: `docs/images/alerts.png`
- Simulation Canvas: `docs/images/simulation.png`
- Demo Video: `docs/videos/demo.mp4`

## Roadmap
- Containerized deployment (Gunicorn/WSGI + reverse proxy)
- Mobile-friendly mechanic interface
- Predictive leak scoring from flow anomalies
- Image/video capture of field repairs

## License
MIT License — see LICENSE (planned). Feel free to fork and build.

## Credits
- Built by **TechieGeekee**
- LinkedIn: https://www.linkedin.com/in/abhinavkoolath

## Contributing
PRs welcome: open an issue with context, then submit a focused PR.

## Inspiration
Aligned with the Ministry of Jal Shakti problem statement to equip Gram Panchayats with low-cost, digital O&M tooling for sustainable rural water supply.
