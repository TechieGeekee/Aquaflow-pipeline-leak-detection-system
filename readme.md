# AquaFlow – Rural Water O&M Copilot 🚰⚡

> Empowering Gram Panchayats with low-cost, real-time leak detection and water quality monitoring tools. (Problem Statement ID: 25241, Ministry of Jal Shakti)

![Hero Placeholder](docs/images/img1.png)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3-000000?logo=flask&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase-RTDB-FFCA28?logo=firebase&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Prototype-blue)

---

## Table of Contents
- [Overview](#overview)
- [Problem Statement](#problem-statement-ministry-of-jal-shakti)
- [Highlights](#highlights)
- [Leak Detection Logic](#leak-detection-logic-segment-isolation)
- [Architecture](#architecture)
- [Data Model (Firebase)](#data-model-firebase-rtdb)
- [Setup (Local)](#setup-local-windows)
- [Usage Guide](#usage-guide)
- [Operations Runbook](#operations-runbook)
- [Roadmap](#roadmap)
- [Screens & Media](#screens--media-placeholders)
- [License](#license)
- [Credits](#credits)

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
pip install -r requirements.txt
pip install -r water-monitoring-dashboard/requirements.txt

# 4) Firebase Setup - REQUIRED FOR BOTH APPS
# Both simulation and dashboard need Firebase credentials to sync data.
# Follow these detailed steps to add your own Firebase project credentials.
#
# ─── STEP A: Create a Firebase Project (if you don't have one) ───
# 1. Go to https://console.firebase.google.com
# 2. Click "Add project" → enter project name → Create
# 3. Enable Realtime Database:
#    - In left menu, click "Realtime Database"
#    - Click "Create Database" → US region → Test mode → Create
# 4. Note the database URL (looks like: https://PROJECT-ID-default-rtdb.firebaseio.com)
#
# ─── STEP B: Generate Service Account Key ───
# 1. In Firebase Console, top-left menu → "Project Settings"
# 2. Click "Service Accounts" tab
# 3. Under "Firebase Admin SDK" section, click "Generate New Private Key"
# 4. JSON file downloads (contains all credentials needed)
#
# ─── STEP C: Copy Key Values into Placeholder Files ───
# The downloaded JSON file contains these fields you'll need:
#   - "type": "service_account"
#   - "project_id": YOUR_PROJECT_ID
#   - "private_key_id": YOUR_KEY_ID
#   - "private_key": YOUR_LONG_PRIVATE_KEY (multiline, starts with -----BEGIN...)
#   - "client_email": firebase-adminsdk-XXXXX@PROJECT_ID.iam.gserviceaccount.com
#   - "client_id": YOUR_CLIENT_ID
#   - "auth_uri": https://accounts.google.com/o/oauth2/auth
#   - "token_uri": https://oauth2.googleapis.com/token
#   - "auth_provider_x509_cert_url": https://www.googleapis.com/oauth2/v1/certs
#   - "client_x509_cert_url": YOUR_CERT_URL
#   - "universe_domain": googleapis.com
#
# ─── STEP D: Update Placeholder Files ───
# Option 1 (RECOMMENDED): Copy entire JSON
#   1. Open downloaded JSON file with text editor
#   2. Copy ALL contents (Ctrl+A, Ctrl+C)
#   3. Open: serviceAccountKey.json (at repo root)
#   4. Paste (replace all placeholder text): Ctrl+A, Ctrl+V
#   5. Save file
#   6. Repeat steps 3-5 for: water-monitoring-dashboard/serviceAccountKey.json
#
# Option 2 (Manual): Replace individual placeholder values
#   1. Open downloaded JSON file
#   2. Open: serviceAccountKey.json (at repo root)
#   3. Find and replace each YOUR_* placeholder:
#      - Replace YOUR_FIREBASE_PROJECT_ID with "project_id" value from downloaded JSON
#      - Replace YOUR_PRIVATE_KEY_ID with "private_key_id" value
#      - Replace YOUR_PRIVATE_KEY with full "private_key" value (keep the quotes and \\n)
#      - Replace YOUR_CLIENT_EMAIL with "client_email" value
#      - Replace YOUR_CLIENT_ID with "client_id" value
#      - Replace YOUR_CERT_URL with "client_x509_cert_url" value
#   4. Save file
#   5. Repeat for: water-monitoring-dashboard/serviceAccountKey.json
#
# ─── File Locations (both must be updated) ───
#   serviceAccountKey.json               ← at repo root, for simulation
#   water-monitoring-dashboard/serviceAccountKey.json  ← for dashboard
#
# ─── Verify Setup ───
# After updating files, both apps will:
#   - Load credentials automatically on startup
#   - Output: "Firebase initialized successfully"
#   - Begin syncing with your Firebase Realtime Database
#
# ─── Alternative: Environment Variable (Optional) ───
# If you prefer not to use files, set:
#   $env:FIREBASE_DB_URL = "https://YOUR-PROJECT-default-rtdb.firebaseio.com"
# Note: Key files method is simpler and recommended for local development

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

## Firebase Configuration Guide

### Finding Your Firebase Credentials

Once you've generated a service account key from Firebase Console, here's what each field maps to:

| Placeholder | Location in Downloaded JSON | Example |
|-------------|---------------------------|---------|
| `YOUR_FIREBASE_PROJECT_ID` | `project_id` | `"myproject-12345"` |
| `YOUR_PRIVATE_KEY_ID` | `private_key_id` | `"abc123def456..."` |
| `YOUR_PRIVATE_KEY` | `private_key` | `"-----BEGIN PRIVATE KEY-----\nMIIEvQ..."` |
| `YOUR_CLIENT_EMAIL` | `client_email` | `"firebase-adminsdk-fbsvc@myproject.iam.gserviceaccount.com"` |
| `YOUR_CLIENT_ID` | `client_id` | `"123456789012345678"` |
| `YOUR_CERT_URL` | `client_x509_cert_url` | `"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk..."` |

### Checking Credentials Are Loaded

After updating the credential files, run:
```powershell
. .\.venv\Scripts\Activate.ps1
cd simulation
python -c "from firebase_config import initialize_firebase; print('✓ Firebase ready')"
```

Expected output:
```
Found service account key: ../serviceAccountKey.json
Firebase initialized successfully
✓ Firebase ready
```

### Troubleshooting Firebase Issues

**Problem**: "serviceAccountKey.json not found"
- **Solution**: Ensure file exists at repo root AND in `water-monitoring-dashboard/` folder (both required)

**Problem**: "Invalid JSON in serviceAccountKey.json"
- **Solution**: Check that the entire JSON is valid (use https://jsonlint.com to validate)

**Problem**: "Firebase: Permission denied"
- **Solution**: Your database rules may be too restrictive. In Firebase Console:
  - Go to "Realtime Database" → "Rules"
  - Set to test mode (allows all reads/writes) for development:
    ```json
    {
      "rules": {
        ".read": true,
        ".write": true
      }
    }
    ```
  - For production, implement proper security rules

**Problem**: "Simula only runs in mock Firebase mode"
- **Solution**: Credentials are invalid or missing. Check console output for "Found service account key"

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
