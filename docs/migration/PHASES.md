# Migration phases (Path A)

## Phase 0 — Standalone repo ✅

- [x] New repo `eleafx/ibob-dashboard-web`
- [x] Copy `data/*.csv` into this repo (source of truth)
- [x] Copy IMMD + PartnerNet scrapers + Actions workflow
- [x] Keep Streamlit app as `docs/reference/app.py` only

## Phase 1 — Data API + UI shell ✅

- [x] FastAPI loads **local** CSVs (not Streamlit GitHub raw)
- [x] Port `process_raw`, monthly series, recovery / YoY
- [x] `/api/inbound` + `/api/outbound` return series + Plotly JSON
- [x] React shell renders inbound/outbound charts
- [x] Pytest smoke tests on real fixtures

## Phase 2 — International + table figures ✅

- [x] Port `build_ppt_summary` + PPT HTML → React table
- [x] International monthly / YoY charts
- [x] Port `make_combined_figure` table traces (YoY + recovery under chart)

## Phase 3 — Holiday module ✅

- [x] Port `HOLIDAY_PERIODS` + variant helpers
- [x] Port `get_holiday_data` + multi-year / CP charts
- [x] Holiday UI controls (region, holiday, segment, tabs)

## Phase 4 — Cutover ✅ (scaffold) / ⏳ (ops)

- [x] Deploy packaging: Dockerfile + compose; FastAPI serves `frontend/dist`
- [x] Cutover runbook: [CUTOVER.md](CUTOVER.md)
- [x] GitLab CI scaffold: `.gitlab-ci.yml` (fetch + optional image)
- [ ] Mirror PartnerNet secrets on deploy/CI host *(ops)*
- [ ] Point users at new URL; freeze Streamlit *(ops)*
- [ ] Optional: push GitLab mirror + enable schedules *(ops)*
