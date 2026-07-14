"""Smoke tests for local data load + process_raw."""
from __future__ import annotations

from backend.app.data.load import load_daily_csv, load_international_csv, process_raw
from backend.app.metrics.monthly import get_monthly, get_series, resolve_display_years
from backend.app.services.dashboard import build_inbound_payload, get_status


def test_load_daily_csv():
    df, meta = load_daily_csv()
    assert df is not None, meta
    assert len(df) > 1000
    assert "local:" in meta


def test_process_raw_shapes():
    df, _ = load_daily_csv()
    daily_in, daily_out, arrivals, departures = process_raw(df)
    assert daily_in is not None and daily_out is not None
    assert "tourist_arrival" in daily_in.columns
    assert "hk_departure" in daily_out.columns
    assert len(arrivals) > 0 and len(departures) > 0


def test_monthly_series_length():
    df, _ = load_daily_csv()
    daily_in, _, _, _ = process_raw(df)
    monthly = get_monthly(daily_in, "tourist_arrival")
    years = resolve_display_years(daily_in)
    series = get_series(monthly, years[-1])
    assert len(series) == 11


def test_inbound_payload():
    status = get_status()
    assert status["ok"] is True
    payload = build_inbound_payload()
    assert "figure" in payload
    assert "2018" in payload["series"]
    assert len(payload["yoy_rows"]) >= 1


def test_international_csv():
    df, meta = load_international_csv()
    assert df is not None, meta
    assert "Australia" in df.columns
