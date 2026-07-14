"""Assemble inbound / outbound / international dashboard payloads."""
from __future__ import annotations

from functools import lru_cache
from time import time

import pandas as pd

from backend.app.charts.combined import make_combined_figure
from backend.app.charts.holiday import (
    build_cp_table,
    make_holiday_bar_figure,
    make_holiday_cp_figure,
    make_holiday_daily_figure,
    make_multiyear_holiday_chart,
)
from backend.app.charts.international import (
    build_intl_monthly_chart,
    build_intl_monthly_yoy_chart,
)
from backend.app.charts.lines import make_line_figure
from backend.app.config import (
    BASELINE_COLOR,
    BASELINE_YEAR,
    CACHE_TTL_SECONDS,
    INBOUND_2018,
    INTERNATIONAL_2018,
    MAINLAND_2018,
    MONTH_LABELS,
    OUTBOUND_2018,
    get_year_colors,
)
from backend.app.data.load import (
    load_daily_csv,
    load_international_csv,
    process_raw,
    read_last_updated,
)
from backend.app.metrics.holiday import (
    build_proximity_tracker,
    get_holiday_data,
    get_hk_holiday_meta,
    holiday_options,
    resolve_region,
)
from backend.app.metrics.international import build_monthly_yoy_table, build_ppt_summary
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
def _load_processed() -> tuple[
    pd.DataFrame | None,
    pd.DataFrame | None,
    pd.DataFrame | None,
    pd.DataFrame | None,
    str,
]:
    df, meta = load_daily_csv()
    daily_in, daily_out, arrivals, departures = process_raw(df)
    return daily_in, daily_out, arrivals, departures, meta


def get_status() -> dict:
    daily_in, _, _, _, meta = _load_processed()
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


def _metric_table_rows(rows: list[dict]) -> list[list[str]]:
    """Convert [{label, values}] to Plotly table row lists (strip HTML from labels)."""
    out: list[list[str]] = []
    for row in rows:
        label = str(row["label"]).replace("<b>", "").replace("</b>", "")
        out.append([label] + list(row["values"]))
    return out


def build_inbound_payload() -> dict:
    def _build():
        daily_in, _, _, _, meta = _load_processed()
        years = resolve_display_years(daily_in)
        colors = {**get_year_colors(years), "2018": BASELINE_COLOR}
        current_year = years[-1] if years else 2026
        return _assemble_flow(
            flow="inbound",
            title="Daily Tourist Arrivals by Month",
            summary_title="Inbound YoY & Recovery Summary",
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
        _, daily_out, _, _, meta = _load_processed()
        years = resolve_display_years(daily_out)
        colors = {**get_year_colors(years), "2018": BASELINE_COLOR}
        current_year = years[-1] if years else 2026
        return _assemble_flow(
            flow="outbound",
            title="Daily HK Resident Departures by Month",
            summary_title="Outbound YoY & Recovery Summary",
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
            extra_height=30,
        )

    return _cached("outbound", _build)


def build_international_payload() -> dict:
    def _build():
        df, meta = load_international_csv()
        if df is None:
            return {"ok": False, "meta": meta}

        df_c = df.copy()
        df_c["year"] = pd.to_numeric(df_c["year"], errors="coerce").astype("Int64")
        df_c["month"] = pd.to_numeric(df_c["month"], errors="coerce").astype("Int64")
        available_years = sorted(int(y) for y in df_c["year"].dropna().unique())
        if not available_years:
            return {"ok": False, "meta": "No years in international CSV"}

        curr_year = int(available_years[-1])
        curr_months = sorted(
            int(m)
            for m in df_c.loc[df_c["year"] == curr_year, "month"].dropna().unique()
        )
        curr_month = int(curr_months[-1]) if curr_months else 1

        year_columns = [curr_year]
        for y in [curr_year - 1, curr_year - 2]:
            if y in available_years:
                year_columns.append(y)
        if BASELINE_YEAR in available_years and BASELINE_YEAR not in year_columns:
            year_columns.append(BASELINE_YEAR)

        monthly_figure = build_intl_monthly_chart(df)
        summary_rows, row_styles, ppt_meta = build_ppt_summary(
            df_c,
            target_year=curr_year,
            target_month=curr_month,
            year_columns=year_columns,
        )

        prev_year = curr_year - 1
        yoy_figure = None
        monthly_yoy_table = None
        if prev_year in available_years and row_styles is not None:
            yoy_figure = build_intl_monthly_yoy_chart(
                df_c, curr_year, prev_year, curr_month
            )
            monthly_yoy_table = build_monthly_yoy_table(
                df_c, curr_year, prev_year, curr_month, row_styles
            )

        return {
            "ok": True,
            "meta": meta,
            "rows": int(len(df)),
            "available_years": available_years,
            "curr_year": curr_year,
            "curr_month": curr_month,
            "year_columns": year_columns,
            "monthly_figure": monthly_figure,
            "ppt_summary": {
                "columns": (ppt_meta or {}).get("columns", []),
                "rows": summary_rows or [],
                "row_styles": row_styles or [],
                "meta": ppt_meta,
            },
            "yoy_figure": yoy_figure,
            "monthly_yoy_table": monthly_yoy_table,
        }

    return _cached("international", _build)


def get_holiday_options() -> dict:
    return holiday_options()


def build_holiday_payload(
    *,
    context: str = "Mainland",
    holiday: str = "CNY",
    direction: str | None = None,
    segment: str | None = None,
    variant: str = "Official Days",
) -> dict:
    cache_key = f"holiday:{context}:{holiday}:{direction}:{segment}:{variant}"

    def _build():
        daily_in, daily_out, arrivals, departures, meta = _load_processed()
        years = resolve_display_years(daily_in)
        colors = {**get_year_colors(years), "2018": BASELINE_COLOR}
        current_year = str(years[-1] if years else 2026)
        region = resolve_region(context)

        al_fallback = variant in ("Extended Leave Days", "extended_al") and region == "HK"
        hd = get_holiday_data(
            arrivals,
            departures,
            daily_in,
            daily_out,
            holiday,
            context=context,
            variant=variant,
            al_fallback=al_fallback,
            direction=direction,
            segment=segment,
        )
        if not hd or not hd.get("avg"):
            return {
                "ok": False,
                "meta": meta,
                "message": "No data available for the selected holiday period.",
                "tracker": build_proximity_tracker(context, holiday),
                "hk_meta": {
                    str(y): {
                        "al_applicable": m.get("al_applicable"),
                        "al_reason": m.get("al_reason"),
                    }
                    for y, m in get_hk_holiday_meta(region, holiday).items()
                }
                if region == "HK"
                else {},
                "region": region,
            }

        daily_df = daily_in if hd["direction"] == "inbound" else daily_out
        overview = make_multiyear_holiday_chart(
            daily_df,
            hd["value_col"],
            hd["periods"],
            f"Daily {hd['flow_label']} — {variant}",
            colors,
        )
        # Serialize periods for JSON (int keys → str)
        periods_json = {
            str(y): {k: v for k, v in p.items() if k != "bridge_note" or v}
            for y, p in hd["periods"].items()
        }

        return {
            "ok": True,
            "meta": meta,
            "region": region,
            "context": context,
            "holiday": holiday,
            "holiday_label": hd["holiday_label"],
            "variant": variant,
            "direction": hd["direction"],
            "segment": hd["segment"],
            "flow_label": hd["flow_label"],
            "avg": hd["avg"],
            "total": hd["total"],
            "days": hd["days"],
            "growth": hd["growth"],
            "total_growth": hd["total_growth"],
            "day_labels": hd.get("day_labels", []),
            "periods": periods_json,
            "overview_figure": overview,
            "daily_figure": make_holiday_daily_figure(hd, colors),
            "bar_total_figure": make_holiday_bar_figure(
                hd, colors, current_year, "Period total"
            ),
            "bar_avg_figure": make_holiday_bar_figure(
                hd, colors, current_year, "Daily average"
            ),
            "cp_figure": make_holiday_cp_figure(hd),
            "cp_table": build_cp_table(hd),
            "tracker": build_proximity_tracker(context, holiday),
            "hk_meta": {
                str(y): {
                    "al_applicable": m.get("al_applicable"),
                    "al_reason": m.get("al_reason"),
                }
                for y, m in get_hk_holiday_meta(region, holiday).items()
            }
            if region == "HK"
            else {},
            "al_warnings": [
                f"{yr}: {m['al_reason']}"
                for yr, m in sorted(get_hk_holiday_meta(region, holiday).items())
                if not m.get("al_applicable") and m.get("al_reason")
            ]
            if region == "HK" and al_fallback
            else [],
        }

    return _cached(cache_key, _build)


def _assemble_flow(
    *,
    flow: str,
    title: str,
    summary_title: str,
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
    extra_height: int = 0,
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

    month_headers = MONTH_LABELS + ["FY"]
    summary_figure = make_combined_figure(
        summary_title,
        table1_rows=_metric_table_rows(yoy_rows),
        table1_header=["YoY Growth Rate"] + month_headers,
        table2_rows=_metric_table_rows(rec_rows),
        table2_header=["Recovery Rate vs 2018"] + month_headers,
        extra_height=extra_height,
        colors=colors,
        current_year=str(current_year),
    )

    return {
        "flow": flow,
        "meta": meta,
        "display_years": years,
        "month_labels": month_headers,
        "series": {
            yr: [None if v is None else round(float(v), 2) for v in vals]
            for yr, vals in series_dict.items()
        },
        "figure": figure,
        "summary_figure": summary_figure,
        "yoy_rows": yoy_rows,
        "recovery_rows": rec_rows,
    }
