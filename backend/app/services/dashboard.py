"""Assemble inbound / outbound dashboard payloads."""
from __future__ import annotations

from functools import lru_cache
from time import time

import pandas as pd

from backend.app.charts.lines import make_line_figure
from backend.app.config import (
    BASELINE_COLOR,
    CACHE_TTL_SECONDS,
    INBOUND_2018,
    INTERNATIONAL_2018,
    MAINLAND_2018,
    MONTH_LABELS,
    OUTBOUND_2018,
    get_year_colors,
)
from backend.app.data.load import load_daily_csv, process_raw, read_last_updated
from backend.app.metrics.monthly import (
    calc_recovery,
    calc_yoy,
    get_monthly,
    get_series,
    resolve_display_years,
)

_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, builder):
    now = time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    value = builder()
    _cache[key] = (now, value)
    return value


def clear_cache() -> None:
    _cache.clear()
    _load_processed.cache_clear()


@lru_cache(maxsize=1)
def _load_processed() -> tuple[pd.DataFrame | None, pd.DataFrame | None, str]:
    df, meta = load_daily_csv()
    daily_in, daily_out, _, _ = process_raw(df)
    return daily_in, daily_out, meta


def get_status() -> dict:
    daily_in, _, meta = _load_processed()
    last = read_last_updated()
    years = resolve_display_years(daily_in)
    return {
        "ok": daily_in is not None,
        "source": meta,
        "last_updated_file": last,
        "display_years": years,
        "daily_in_rows": 0 if daily_in is None else int(len(daily_in)),
    }


def _baseline_series(baseline: dict[int, int]) -> list[float]:
    return [(baseline[1] + baseline[2]) / 2] + [baseline[m] for m in range(3, 13)]


def build_inbound_payload() -> dict:
    def _build():
        daily_in, _, meta = _load_processed()
        years = resolve_display_years(daily_in)
        colors = {**get_year_colors(years), "2018": BASELINE_COLOR}
        current_year = years[-1] if years else 2026
        return _assemble_flow(
            flow="inbound",
            title="Daily Tourist Arrivals by Month",
            daily=daily_in,
            value_col="tourist_arrival",
            mainland_col="mainland_arrival",
            intl_col="international_arrival",
            baseline_overall=INBOUND_2018,
            baseline_mainland=MAINLAND_2018,
            baseline_intl=INTERNATIONAL_2018,
            years=years,
            colors=colors,
            current_year=current_year,
            meta=meta,
            y_max=300_000,
        )

    return _cached("inbound", _build)


def build_outbound_payload() -> dict:
    def _build():
        _, daily_out, meta = _load_processed()
        years = resolve_display_years(daily_out)
        colors = {**get_year_colors(years), "2018": BASELINE_COLOR}
        current_year = years[-1] if years else 2026
        return _assemble_flow(
            flow="outbound",
            title="Daily HK Resident Departures by Month",
            daily=daily_out,
            value_col="hk_departure",
            mainland_col=None,
            intl_col=None,
            baseline_overall=OUTBOUND_2018,
            baseline_mainland=None,
            baseline_intl=None,
            years=years,
            colors=colors,
            current_year=current_year,
            meta=meta,
            y_max=500_000,
        )

    return _cached("outbound", _build)


def _assemble_flow(
    *,
    flow: str,
    title: str,
    daily: pd.DataFrame | None,
    value_col: str,
    mainland_col: str | None,
    intl_col: str | None,
    baseline_overall: dict[int, int],
    baseline_mainland: dict[int, int] | None,
    baseline_intl: dict[int, int] | None,
    years: list[int],
    colors: dict[str, str],
    current_year: int,
    meta: str,
    y_max: float,
) -> dict:
    monthly = get_monthly(daily, value_col)
    series_dict: dict[str, list[float | None]] = {
        "2018": _baseline_series(baseline_overall),
    }
    for yr in years:
        series_dict[str(yr)] = get_series(monthly, yr)

    figure = make_line_figure(
        title,
        series_dict,
        colors=colors,
        y_max=y_max,
        current_year=str(current_year),
    )

    monthly_mainland = get_monthly(daily, mainland_col) if mainland_col else None
    monthly_intl = get_monthly(daily, intl_col) if intl_col else None

    yoy_rows: list[dict] = []
    rec_rows: list[dict] = []
    for yr in years[-2:]:
        if flow == "inbound":
            yoy_rows.append(
                {"label": f"{yr} Overall", "values": calc_yoy(monthly, yr, yr - 1)}
            )
            yoy_rows.append(
                {"label": "  Mainland", "values": calc_yoy(monthly_mainland, yr, yr - 1)}
            )
            yoy_rows.append(
                {
                    "label": "  International",
                    "values": calc_yoy(monthly_intl, yr, yr - 1),
                }
            )
            rec_rows.append(
                {
                    "label": f"{yr} Overall",
                    "values": calc_recovery(monthly, baseline_overall, yr),
                }
            )
            rec_rows.append(
                {
                    "label": "  Mainland",
                    "values": calc_recovery(
                        monthly_mainland, baseline_mainland or {}, yr
                    ),
                }
            )
            rec_rows.append(
                {
                    "label": "  International",
                    "values": calc_recovery(monthly_intl, baseline_intl or {}, yr),
                }
            )
        else:
            yoy_rows.append(
                {
                    "label": f"{yr} vs {yr - 1}",
                    "values": calc_yoy(monthly, yr, yr - 1),
                }
            )
            rec_rows.append(
                {
                    "label": f"{yr} vs 2018",
                    "values": calc_recovery(monthly, baseline_overall, yr),
                }
            )

    return {
        "flow": flow,
        "meta": meta,
        "display_years": years,
        "month_labels": MONTH_LABELS + ["FY"],
        "series": {
            yr: [None if v is None else round(float(v), 2) for v in vals]
            for yr, vals in series_dict.items()
        },
        "figure": figure,
        "yoy_rows": yoy_rows,
        "recovery_rows": rec_rows,
    }
