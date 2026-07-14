# Phase 4 — Cutover checklist

Deploy the FastAPI + React app, keep scrapers updating `data/`, then point users at the new URL and freeze Streamlit.

## 1. Deploy API + frontend

### Local Docker (parity with production)

```bash
cd C:\Users\Averyxie19\Downloads\ibob-dashboard-web
docker compose up --build
```

Open http://127.0.0.1:8000 — API under `/api/*`, UI from `frontend/dist`.

### Manual (no Docker)

```bash
cd frontend && npm ci && npm run build && cd ..
pip install -r backend/requirements.txt
set SERVE_FRONTEND=1
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Hosting notes

- One process serves both API and static UI (`SERVE_FRONTEND=1`).
- Mount/persist `data/` so Actions or scrapers can refresh CSVs without rebuilding the image.
- Optional: `CORS_ALLOW_ORIGINS=https://your.domain` (default allows local Vite; Docker compose defaults to `*`).
- Health check: `GET /api/health`.

## 2. Mirror PartnerNet secrets

On the **new** GitHub (or GitLab) project, add the same secrets used by the Streamlit repo:

| Secret | Purpose |
|--------|---------|
| `PARTNERNET_USER` | HKTB PartnerNet login |
| `PARTNERNET_PASS` | HKTB PartnerNet password |

Confirm `.github/workflows/fetch_data.yml` (or `.gitlab-ci.yml` fetch jobs) runs and commits into `data/`.

## 3. Point users + freeze Streamlit

- [ ] Smoke-test production URL: inbound, international, holiday, outbound
- [ ] Share new URL with stakeholders
- [ ] On Streamlit Cloud (or wherever Streamlit is hosted): stop redeploys / unschedule; leave a banner or redirect note pointing to the new URL
- [ ] Keep Streamlit repo read-only for a cooldown window before archive

## 4. Optional — GitLab mirror + CI

- [ ] Create GitLab project; push mirror (`git remote add gitlab … && git push gitlab main`)
- [ ] Copy CI variables: `PARTNERNET_USER`, `PARTNERNET_PASS`
- [ ] Enable schedules for `.gitlab-ci.yml` (weekly IMMD / monthly PartnerNet)
- [ ] Disable GitHub Actions once GitLab fetch jobs are green

## Exit criteria

- [ ] Production URL loads dashboard + holiday controls
- [ ] `/api/health` returns `ok: true` with recent `source`
- [ ] PartnerNet secrets present on the active CI host
- [ ] Users notified; Streamlit frozen or redirected
