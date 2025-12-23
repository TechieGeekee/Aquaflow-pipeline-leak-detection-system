# AquaFlow – Rural Water O&M Copilot 🚰⚡

> Empowering Gram Panchayats with low-cost, real-time leak detection and water quality monitoring tools. (Problem Statement ID: 25241, Ministry of Jal Shakti)

![Hero Placeholder](docs/images/hero-placeholder.png)

---

## Table of Contents
- Overview
- Problem Statement
- Highlights
- Leak Detection Logic
- Architecture
- Data Model (Firebase)
- Setup (Local)
- Usage Guide
- Operations Runbook
- Roadmap
- Screens & Media
- License
- Credits

---

## Overview
AquaFlow pairs a simulation-driven sensor twin (Tkinter) with a live Flask dashboard to give Panchayats simple, actionable insight into rural piped water networks. It surfaces leaks, assigns mechanics automatically, streams real-time sensor data, and keeps admins in control with clear, role-based dashboards.

## Problem Statement (Ministry of Jal Shakti)
- **Title**: Empowering Gram Panchayats to manage daily O&M of Rural Piped Water Supply Systems using low-cost digital tools for routine monitoring.
- **Gaps**: Delayed repairs, undetected leakages, limited water-quality visibility, and low tooling for routine O&M.
- **Expected Outcomes**:
	- Rural-ready digital tools for routine checks (pump hours, valve status, leaks, water quality).
	- Predictive insights from flow patterns for early fault detection.
	- Digital water-quality logs; community accountability and ownership.

## Highlights
- 🔴 Real-time leak alerts with auto mechanic assignment and history.
- 🎛️ Dual dashboards: **Admin** (oversight, assignments, history) and **Mechanic** (my tasks, acknowledgements).
- 🌊 Sensor twin: water level, pH, turbidity, salinity, flow, valve/tap states.
- 🔄 SSE-driven updates for instant dashboard refresh.
- 🧪 Tkinter simulation to model the network, inject leaks, and push data to Firebase.
- 🛡️ Offline-safe simulation via mock Firebase when keys are absent.

## Leak Detection Logic (Segment Isolation)
```
Source A ---- B ---- C ---- D
				 [1] close B, check A-B segment
				 [2] close C (B closed), check B-C segment
				 [3] close D (B,C closed), check C-D segment
```
Step-by-step:
1) **Isolate upstream**: Treat `A` as source, close at `B`. Loss between `A` and `B` → leak in that span.
2) **Narrow further**: Close `C` while `B` stays blocked. If loss persists, leak is between `B` and `C`.
3) **Iterate**: Continue hop-by-hop until the terminal node; each isolation updates `active_leaks` in Firebase.
4) **Assign**: Round-robin mechanic assignment with workload balancing; alerts carry pipe name, severity, assignee, status.
5) **Resolve**: When flow loss clears, alerts auto-resolve and assignments are released.

## Architecture
- **simulation/tkinder.py** — Tkinter network simulator; pushes valves, taps, sensors, leaks, water_flow, water_level to Firebase. Uses serviceAccountKey*.json or mock offline Firebase.
- **water-monitoring-dashboard/app.py** — Flask + Flask-Login + SSE; admin/mechanic dashboards, alert history, leak simulation API, assignments.
- **Firebase RTDB** — `/water_system` is the single source of truth for state and alerts.

### High-Level Flow
```
[Tkinter Simulation] --(Firebase Admin SDK)--> [Firebase RTDB] --(SSE/REST)--> [Flask Dashboard]
					 ^                                               |
					 |-----------------------------------------------|
								 (read-back for live state & alerts)
```

## Data Model (Firebase RTDB)
- `/water_system/valves` — `{TANK_VALVE: 0/1, VALVE_A: 0/1}`
- `/water_system/taps` — tap states 0/1
- `/water_system/sensors` — `{pH, turbidity, salinity, flow}`
- `/water_system/water_level` — percent int
- `/water_system/leaks` — configured leaks 0/1
- `/water_system/active_leaks` — computed active leaks 0/1 (flow present)
- `/water_system/water_flow` — per-pipe flow flags
- `/water_system/leak_report` — summary payload for active/inactive leaks

## Setup (Local, Windows)
```powershell
# 1) Clone
# git clone <your-fork-url>
cd "water-sim 4/water-sim"

# 2) Create & activate venv
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# 3) Install deps (root + dashboard)

pip install -r water-monitoring-dashboard/requirements.txt

# 4) Firebase key
# Place serviceAccountKey.json at project root (already present) or set FIREBASE_DB_URL

# 5) Run simulation (Tkinter)
cd simulation
python tkinder.py

# 6) Run dashboard (Flask, port 5050)
cd ..\water-monitoring-dashboard
python app.py
```

### Environment
| Name | Purpose |
| ---- | ------- |
| FIREBASE_DB_URL | Override default RTDB URL (optional) |
| SECRET_KEY | Flask secret key (optional) |

### Logins
- Admin: `admin` / `WaterMonitor2024!`
- Mechanics: `M001`/`mechanic001`, `M002`/`mechanic002`, `M003`/`mechanic003`

## Usage Guide
1) Launch Tkinter simulation → adjust valves, taps, water level; add/remove leaks on pipes.
2) State syncs to Firebase (or mock offline); `active_leaks` computed and published.
3) Flask dashboard streams updates via SSE → system state, alerts, assignments.
4) Mechanics log in to view/ack/resolve; admin can reassign or resolve all.

## Operations Runbook
- **Start simulation**: `python simulation/tkinder.py`
- **Start dashboard**: `python water-monitoring-dashboard/app.py`
- **Firebase key**: Keep `serviceAccountKey.json` at repo root (sim) and `/water-monitoring-dashboard` (dashboard already finds root copy).
- **Troubleshoot Firebase**: If offline, the simulator drops to mock Firebase; dashboard requires a real key for RTDB.
- **Ports**: Dashboard default `5050`; update `PORT` env to override.

## Roadmap
- Containerized deployment (Gunicorn/WSGI + reverse proxy)
- Mobile-friendly mechanic interface
- Predictive leak scoring from flow anomalies
- Image/video capture for field repairs

## Screens & Media (placeholders)
- docs/images/dashboard.png — Dashboard overview
- docs/images/alerts.png — Alert & assignment flow
- docs/images/simulation.png — Simulation canvas
- docs/videos/demo.mp4 — Demo walk-through

## License
MIT License — see LICENSE (planned). Feel free to fork and build.

## Credits
- Built by **TechieGeekee**
- LinkedIn: https://www.linkedin.com/in/abhinavkoolath

## Contributing
PRs welcome: open an issue with context, then submit a focused PR.

## Inspiration
Aligned with the Ministry of Jal Shakti challenge to equip Gram Panchayats with low-cost, digital O&M tooling for sustainable rural water supply.
