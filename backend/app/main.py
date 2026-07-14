"""FastAPI entrypoint for IBOB dashboard API."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Allow `uvicorn backend.app.main:app` from repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.app.config import FRONTEND_DIST, cors_allow_origins, serve_frontend
from backend.app.data.load import load_international_csv, refresh_daily_from_gov
from backend.app.services.dashboard import (
    build_holiday_payload,
    build_inbound_payload,
    build_international_payload,
    build_outbound_payload,
    clear_cache,
    get_holiday_options,
    get_status,
)

app = FastAPI(
    title="IBOB Dashboard API",
    description="Path A migration — Pandas processing, React frontend",
    version="0.1.0",
)

_origins = cors_allow_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials="*" not in _origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", **get_status()}


@app.get("/api/inbound")
def inbound():
    payload = build_inbound_payload()
    if payload.get("series") and not any(
        k != "2018" for k in payload["series"]
    ):
        # still return 2018 baseline even if years empty; only fail if no daily data
        status = get_status()
        if not status["ok"]:
            raise HTTPException(status_code=503, detail=status["source"])
    return payload


@app.get("/api/outbound")
def outbound():
    status = get_status()
    if not status["ok"]:
        raise HTTPException(status_code=503, detail=status["source"])
    return build_outbound_payload()


@app.get("/api/international/meta")
def international_meta():
    df, meta = load_international_csv()
    if df is None:
        raise HTTPException(status_code=503, detail=meta)
    years = sorted(int(y) for y in df["year"].dropna().unique())
    return {
        "meta": meta,
        "years": years,
        "rows": int(len(df)),
        "columns": list(df.columns),
    }


@app.get("/api/international")
def international():
    payload = build_international_payload()
    if not payload.get("ok"):
        raise HTTPException(status_code=503, detail=payload.get("meta", "unavailable"))
    return payload


@app.get("/api/holiday/options")
def holiday_options_route():
    return get_holiday_options()


@app.get("/api/holiday")
def holiday(
    context: str = "Mainland",
    holiday: str = "CNY",
    direction: str | None = None,
    segment: str | None = None,
    variant: str = "Official Days",
):
    if context not in ("Mainland", "HK", "CN"):
        raise HTTPException(status_code=400, detail="context must be Mainland or HK")
    if direction is not None and direction not in ("inbound", "outbound"):
        raise HTTPException(status_code=400, detail="direction must be inbound or outbound")
    payload = build_holiday_payload(
        context=context,
        holiday=holiday,
        direction=direction,
        segment=segment,
        variant=variant,
    )
    return payload


@app.post("/api/refresh")
def refresh(from_gov: bool = False):
    """Clear in-memory cache; optionally re-download IMMD CSV into data/."""
    detail = None
    if from_gov:
        _, detail = refresh_daily_from_gov(save=True)
    clear_cache()
    return {"refreshed": True, "gov_fetch": detail, "status": get_status()}


def _mount_frontend() -> None:
    if not serve_frontend():
        return
    assets = FRONTEND_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index = FRONTEND_DIST / "index.html"

    @app.get("/")
    def spa_index():
        return FileResponse(index)

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # API routes are registered above; this only catches non-API GETs
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


_mount_frontend()
