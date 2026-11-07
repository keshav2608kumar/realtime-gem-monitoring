# GeM BidWatch — Production Deployment & Operation Guide

This document describes the Render.com web service configuration, domestic Indian scanner execution, background worker management, and rollback procedures.

---

## 1. Production Architecture Overview

The deployed system consists of two coordinated components:

1. **Render Cloud Web Service (`realtime-gem-monitoring.onrender.com`):**
   - **Runtime:** Python 3.12+ with Uvicorn.
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Persistence:** SQLite database (`gem_bidwatch.db`).
   - **Auto-Migration:** Runs automatically on application startup via `init_db()`.
2. **Domestic Scanner Agent (`local_scanner.py`):**
   - Runs on any computer in India (home or office).
   - Direct connection to GeM portal endpoints (`search-bids` and `all-bids-data`).
   - Syncs verified newly found bids to the cloud backend via `POST /bids/batch-sync`.

---

## 2. Render Deployment Instructions

Because Render is connected to the GitHub repository:

### Method 1: Git Push (Automatic Deployment)
Any commit pushed to `main` triggers a GitHub Actions APK build. If Render Auto-Deploy is enabled on your service, Render pulls and builds the latest commit.

### Method 2: Manual Deploy (Recommended for Immediate Reflection)
If Render Auto-Deploy webhook is not active:
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click on the **`gem-bidwatch`** (or `realtime-gem-monitoring`) service.
3. In the top right corner, click **"Manual Deploy"**.
4. Select **"Deploy latest commit"**.
5. Render will build and deploy the application in 2–3 minutes with zero downtime.

---

## 3. Environment Variables Configuration

| Variable | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.12.0` | Production Python runtime |
| `MONITOR_ENABLED` | `true` | Enables background APScheduler worker |
| `GEM_POLL_INTERVAL_SECONDS` | `300` | Real polling interval (5 minutes) |
| `APP_HOST` | `0.0.0.0` | Server binding address |
| `APP_PORT` | `$PORT` (assigned by Render) | Listening port |

---

## 4. Rollback Plan

If an unexpected production defect occurs:
1. Identify the last stable commit SHA on `main`.
2. In the Render Dashboard, go to **"Deploys"**.
3. Locate the previous successful build and click **"Rollback to this deploy"**.
4. Render immediately switches traffic to the previous build artifact.
