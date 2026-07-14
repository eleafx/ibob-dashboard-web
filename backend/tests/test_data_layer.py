"""Smoke tests for local data load + process_raw + Phase 2 payloads."""
from __future__ import annotations

from backend.app.data.load import load_daily_csv, load_international_csv, process_raw
from backend.app.metrics.international import build_ppt_summary
from backend.app.metrics.monthly import get_monthly, get_series, resolve_display_years
from backend.app.services.dashboard import (
    build_inbound_payload,
    build_international_payload,
    get_status,
)


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
    assert "summary_figure" in payload
    assert payload["summary_figure"]["data"]
    assert "2018" in payload["series"]
    assert len(payload["yoy_rows"]) >= 1


def test_international_csv():
    df, meta = load_international_csv()
    assert df is not None, meta
    assert "Australia" in df.columns


def test_ppt_summary():
    df, _ = load_international_csv()
    rows, styles, meta = build_ppt_summary(df)
    assert rows is not None and styles is not None and meta is not None
    assert len(rows) == len(styles)
    assert "period_label" in meta
    assert any(r.get("Market") == "Total" for r in rows)


def test_international_payload():
    payload = build_international_payload()
    assert payload["ok"] is True
    assert payload["monthly_figure"] is not None
    assert payload["ppt_summary"]["rows"]
    assert payload["yoy_figure"] is not None
    assert payload["monthly_yoy_table"] is not None


def test_holiday_options():
    from backend.app.services.dashboard import get_holiday_options

    opts = get_holiday_options()
    assert "Mainland" in opts["contexts"]
    assert "CNY" in opts["holidays_by_region"]["CN"]


def test_holiday_payload():
    from backend.app.services.dashboard import build_holiday_payload

    payload = build_holiday_payload(
        context="Mainland",
        holiday="CNY",
        direction="inbound",
        segment="All tourists",
        variant="Official Days",
    )
    assert payload["tracker"]
    if payload["ok"]:
        assert payload["overview_figure"] is not None or payload.get("message")
        assert payload["daily_figure"] is not None
