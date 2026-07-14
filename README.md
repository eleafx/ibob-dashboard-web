# IBOB Dashboard Web (Path A)

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
```

## Quick start

### API

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

- Health: http://127.0.0.1:8000/api/health  
- Inbound: http://127.0.0.1:8000/api/inbound  
- Outbound: http://127.0.0.1:8000/api/outbound  
- Docs: http://127.0.0.1:8000/docs  

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 (proxies `/api` → `:8000`).

### Tests

```bash
pytest backend/tests -q
```

## Migration phases

| Phase | Status | Scope |
|-------|--------|--------|
| 0 | Done | Repo scaffold, data + scrapers, standalone layout |
| 1 | Done | Data layer + inbound/outbound API + React shell |
| 2 | Next | Full Plotly combined tables, international PPT section |
| 3 | Todo | Holiday analysis + control-point charts |
| 4 | Todo | Deploy API + static frontend; retire Streamlit |

Details: [docs/migration/PHASES.md](docs/migration/PHASES.md)

## Secrets (PartnerNet scraper)

Set GitHub (or later GitLab) Actions secrets:

- `PARTNERNET_USER`
- `PARTNERNET_PASS`

## GitLab move (later)

This repo is self-contained: copy the whole tree, re-point CI to GitLab CI, keep `data/` + scrapers. No runtime dependency on the old Streamlit remotes.
