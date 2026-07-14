# IBOB Dashboard Web

Standalone FastAPI + React migration of the Streamlit [IBOB dashboard](https://github.com/van0805/ibob-dashboard).

**Data lives in this repo** (`data/`) so the app does not depend on the Streamlit GitHub cache. Scrapers + Actions keep CSVs up to date here — ready to move to GitLab later as a self-contained project.

## Architecture

```
data/                  # source of truth CSVs
backend/               # FastAPI + Pandas (ported from app.py)
frontend/              # Vite + React + react-plotly.js
scraper.py             # IMMD weekly fetch
international_visitors_scraper.py
docs/reference/app.py  # original Streamlit app (port checklist)
Dockerfile             # multi-stage: build UI + run API
```

## Quick start

### API (dev)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend (dev)

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 (proxies `/api` → `:8000`).

### Production-style (one port, no Docker)

```powershell
powershell -ExecutionPolicy Bypass -File .\start-local.ps1
```

Builds the React app and serves it from FastAPI at http://127.0.0.1:8000

### Dev (two ports, hot reload)

```powershell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

Or Docker:

```bash
docker compose up --build
```

Open http://127.0.0.1:8000 (local/Docker) or http://127.0.0.1:5173 (Vite dev)
### API routes

- Health: `/api/health`
- Inbound / outbound / international / holiday under `/api/*`
- OpenAPI: `/docs`

### Tests

```bash
pytest backend/tests -q
```

## Secrets (PartnerNet scraper)

Set GitHub or GitLab CI secrets/variables:

- `PARTNERNET_USER`
- `PARTNERNET_PASS`

## GitLab move

This repo is self-contained. Use `.gitlab-ci.yml` for IMMD/PartnerNet fetch + optional image build, then disable GitHub Actions schedules. See cutover doc.
