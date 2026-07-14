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

## Phase 2 — International + table figures

- [ ] Port `build_ppt_summary` + PPT HTML → React table
- [ ] International monthly / YoY charts
- [ ] Port `make_combined_figure` table traces (YoY + recovery under chart)

## Phase 3 — Holiday module

- [ ] Port `HOLIDAY_PERIODS` + variant helpers
- [ ] Port `get_holiday_data` + multi-year / CP charts
- [ ] Holiday UI controls (region, holiday, segment, tabs)

## Phase 4 — Cutover

- [ ] Deploy API + frontend
- [ ] Mirror PartnerNet secrets on new host
- [ ] Point users at new URL; freeze Streamlit
- [ ] Optional: mirror repo to GitLab; switch CI
