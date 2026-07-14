"""Load and process passenger traffic CSVs (local-first)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests
import urllib3

from backend.app.config import (
    DAILY_CSV_PATH,
    GOV_DATA_URL,
    INTL_CSV_PATH,
    LAST_UPDATED_PATH,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_HKT = timezone(timedelta(hours=8))
_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def _now_hkt_label(source: str) -> str:
    hkt = datetime.now(_HKT)
    return f"{hkt.strftime('%Y-%m-%d %H:%M')} HKT ({source})"


def read_last_updated() -> str | None:
    if not LAST_UPDATED_PATH.exists():
        return None
    return LAST_UPDATED_PATH.read_text(encoding="utf-8").strip()


def load_daily_csv(path: Path | None = None) -> tuple[pd.DataFrame | None, str]:
    """Load daily passenger CSV from local data/ (standalone source of truth)."""
    csv_path = path or DAILY_CSV_PATH
    if not csv_path.exists():
        return None, f"Missing local file: {csv_path}"
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    if len(df) < 100:
        return None, f"Local CSV too small ({len(df)} rows): {csv_path}"
    return df, _now_hkt_label(f"local:{csv_path.name}")


def load_international_csv(path: Path | None = None) -> tuple[pd.DataFrame | None, str]:
    """Load international visitors CSV from local data/."""
    csv_path = path or INTL_CSV_PATH
    if not csv_path.exists():
        return None, f"Missing local file: {csv_path}"
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    if df.empty or "year" not in df.columns:
        return None, f"Invalid international CSV: {csv_path}"
    return df, _now_hkt_label(f"local:{csv_path.name}")


def refresh_daily_from_gov(save: bool = True) -> tuple[pd.DataFrame | None, str]:
    """Optional live refresh from IMMD open data (writes into data/)."""
    try:
        r = requests.get(GOV_DATA_URL, headers=_FETCH_HEADERS, timeout=60, verify=False)
        if r.status_code != 200 or len(r.text) <= 5000:
            return None, f"Gov fetch failed: HTTP {r.status_code}"
        df = pd.read_csv(StringIO(r.text), encoding="utf-8-sig")
        if len(df) < 100:
            return None, "Gov CSV too small"
        if save:
            DAILY_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
            DAILY_CSV_PATH.write_text(r.text, encoding="utf-8")
            LAST_UPDATED_PATH.write_text(
                f"Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"Rows: {len(df)}\n"
                f"Source: {GOV_DATA_URL}\n",
                encoding="utf-8",
            )
        return df, _now_hkt_label("gov website")
    except Exception as exc:  # noqa: BLE001 — surface fetch errors as message
        return None, f"Gov fetch error: {exc}"


def process_raw(
    df: pd.DataFrame | None,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None, pd.DataFrame | None]:
    """Process raw CSV into daily inbound/outbound (+ arrival/departure detail)."""
    if df is None:
        return None, None, None, None

    df = df.copy()
    df.columns = df.columns.str.strip()
    df.rename(columns={df.columns[0]: "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
    if df["Date"].isna().all():
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"])

    for col in ["Hong Kong Residents", "Mainland Visitors", "Other Visitors", "Total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in ["Hong Kong Residents", "Mainland Visitors", "Other Visitors"]:
        if col not in df.columns:
            df[col] = 0

    if "Total" not in df.columns:
        residency_cols = [
            c
            for c in ("Hong Kong Residents", "Mainland Visitors", "Other Visitors")
            if c in df.columns
        ]
        df["Total"] = df[residency_cols].sum(axis=1) if residency_cols else 0

    arrivals = df[df["Arrival / Departure"] == "Arrival"].copy()
    departures = df[df["Arrival / Departure"] == "Departure"].copy()

    arrivals["tourist_total"] = arrivals["Mainland Visitors"] + arrivals["Other Visitors"]
    daily_in = arrivals.groupby("Date", as_index=False).agg(
        total_arrival=("Total", "sum"),
        tourist_arrival=("tourist_total", "sum"),
        mainland_arrival=("Mainland Visitors", "sum"),
        international_arrival=("Other Visitors", "sum"),
    )
    daily_in["Year"] = daily_in["Date"].dt.year
    daily_in["Month"] = daily_in["Date"].dt.month

    departures["tourist_total"] = (
        departures["Mainland Visitors"] + departures["Other Visitors"]
    )
    daily_out = departures.groupby("Date", as_index=False).agg(
        total_departure=("Total", "sum"),
        hk_departure=("Hong Kong Residents", "sum"),
        tourist_departure=("tourist_total", "sum"),
        mainland_departure=("Mainland Visitors", "sum"),
        international_departure=("Other Visitors", "sum"),
    )
    daily_out["Year"] = daily_out["Date"].dt.year
    daily_out["Month"] = daily_out["Date"].dt.month

    return daily_in, daily_out, arrivals, departures
