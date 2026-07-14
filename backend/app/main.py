"""FastAPI entrypoint for IBOB dashboard API."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Allow `uvicorn backend.app.main:app` from repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.app.data.load import load_international_csv, refresh_daily_from_gov
from backend.app.services.dashboard import (
    build_inbound_payload,
    build_outbound_payload,
    clear_cache,
    get_status,
)

app = FastAPI(
    title="IBOB Dashboard API",
    description="Path A migration — Pandas processing, React frontend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
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


@app.post("/api/refresh")
def refresh(from_gov: bool = False):
    """Clear in-memory cache; optionally re-download IMMD CSV into data/."""
    detail = None
    if from_gov:
        _, detail = refresh_daily_from_gov(save=True)
    clear_cache()
    return {"refreshed": True, "gov_fetch": detail, "status": get_status()}
