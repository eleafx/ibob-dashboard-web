"""International visitors PPT summary + monthly YoY metrics."""
from __future__ import annotations

import calendar
from typing import Any

import pandas as pd

from backend.app.config import (
    ASEAN_MARKETS,
    BASELINE_YEAR,
    G7_MARKETS,
    INTERNATIONAL_MARKETS,
    MARKET_GROUP_MAP,
    MONTH_ABBR,
    PPT_LISTED_MARKETS,
    PPT_SUMMARY_ROWS,
)


def _international_year_totals(
    df: pd.DataFrame, year: int, months: list[int] | None = None
) -> dict[str, int]:
    yd = df[df["year"] == year].copy()
    if yd.empty:
        return {}
    if months is not None:
        yd = yd[yd["month"].isin(months)]
    totals: dict[str, int] = {}
    for market in INTERNATIONAL_MARKETS:
        if market not in yd.columns:
            continue
        vals = pd.to_numeric(yd[market], errors="coerce")
        if vals.notna().any():
            totals[market] = int(vals.sum())
    return totals


def _international_row_total(market_totals: dict[str, int], markets: list[str]) -> int:
    return sum(market_totals.get(m, 0) for m in markets)


def _international_others4_total(market_totals: dict[str, int]) -> int:
    return sum(v for m, v in market_totals.items() if m not in PPT_LISTED_MARKETS)


def _days_in_period(year: int, months: list[int]) -> int:
    if not months:
        return 0
    return sum(calendar.monthrange(int(year), int(m))[1] for m in months)


def _period_market_totals(
    df: pd.DataFrame, year: int, months: list[int]
) -> tuple[dict[str, int], int]:
    totals = _international_year_totals(df, year, months=months)
    return totals, _days_in_period(year, months)


def _period_daily_avg(
    totals: dict[str, int],
    period_days: int,
    markets: list[str] | str,
) -> float | None:
    if not totals or period_days <= 0:
        return None
    if markets == "others4":
        total_val = _international_others4_total(totals)
    elif isinstance(markets, list):
        total_val = _international_row_total(totals, markets)
    else:
        return None
    return total_val / period_days


def _pct_change(current_k: float | None, baseline_k: float | None) -> float | None:
    if current_k is None or baseline_k in (None, 0):
        return None
    return (current_k - baseline_k) / baseline_k


def _fmt_pct(pct: float | None) -> str:
    if pct is None:
        return "—"
    if abs(pct) < 0.005:
        return "0%"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.0%}"


def _fmt_daily_avg(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{int(round(value)):,}"


def _resolve_markets(spec: list[str] | str) -> list[str] | str:
    if spec == "asean_total":
        return list(ASEAN_MARKETS)
    if spec == "g7_total":
        return list(G7_MARKETS)
    if spec == "others4":
        return "others4"
    if spec == "grand_total":
        return list(INTERNATIONAL_MARKETS)
    return spec


def _row_kind(spec: list[str] | str, category: str) -> str:
    if spec == "asean_total":
        return "asean_total"
    if spec == "g7_total":
        return "g7_total"
    if spec == "grand_total":
        return "grand_total"
    if category:
        return "group_child"
    return "default"


def build_ppt_summary(
    df: pd.DataFrame | None,
    target_year: int | None = None,
    target_month: int | None = None,
    year_columns: list[int] | None = None,
) -> tuple[list[dict[str, str]] | None, list[dict[str, str]] | None, dict | None]:
    """Build international visitors summary with daily averages and inline YoY growth."""
    if df is None or df.empty:
        return None, None, None

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
    available_years = sorted(int(y) for y in df["year"].dropna().unique())
    if not available_years:
        return None, None, None

    if target_year is None:
        target_year = int(available_years[-1])
    year_months = sorted(
        int(m) for m in df.loc[df["year"] == target_year, "month"].dropna().unique()
    )
    if not year_months:
        return None, None, None

    if target_month is None:
        target_month = int(year_months[-1])
    target_month = int(target_month)
    target_months = [m for m in year_months if int(m) <= target_month]
    if not target_months:
        return None, None, None

    period_label = f"YTD {target_year}"

    if year_columns is None:
        year_columns = [target_year]

    year_totals: dict[int, dict[str, int]] = {}
    year_days: dict[int, int] = {}
    for yr in year_columns:
        totals, days = _period_market_totals(df, int(yr), target_months)
        year_totals[int(yr)] = totals
        year_days[int(yr)] = days

    rows: list[dict[str, str]] = []
    row_styles: list[dict[str, str]] = []
    yr_list = [int(y) for y in year_columns]
    yr0 = yr_list[0]
    yr1 = yr_list[1] if len(yr_list) > 1 else None
    yr2 = yr_list[2] if len(yr_list) > 2 else None
    yr_base = yr_list[-1]

    growth_cols: set[str] = set()
    if yr1:
        growth_cols.add(f"{yr0 % 100} v {yr1 % 100}")
    if yr2:
        growth_cols.add(f"{yr1 % 100} v {yr2 % 100}")
    growth_cols.add(f"{yr0 % 100} v {yr_base % 100}")

    for category, label, spec in PPT_SUMMARY_ROWS:
        markets = _resolve_markets(spec)
        daily_vals: dict[int, float | None] = {}
        for yr in yr_list:
            daily_vals[yr] = _period_daily_avg(year_totals[yr], year_days[yr], markets)

        row: dict[str, str] = {"Category": category, "Market": label}
        row[f"{yr0} YTD Daily Avg"] = _fmt_daily_avg(daily_vals[yr0])
        if yr1:
            if daily_vals.get(yr0) and daily_vals.get(yr1):
                row[f"{yr0 % 100} v {yr1 % 100}"] = _fmt_pct(
                    _pct_change(daily_vals[yr0], daily_vals[yr1])
                )
            else:
                row[f"{yr0 % 100} v {yr1 % 100}"] = "—"
            row[f"{yr1} YTD Daily Avg"] = _fmt_daily_avg(daily_vals[yr1])
        if yr2:
            if daily_vals.get(yr1) and daily_vals.get(yr2):
                row[f"{yr1 % 100} v {yr2 % 100}"] = _fmt_pct(
                    _pct_change(daily_vals[yr1], daily_vals[yr2])
                )
            else:
                row[f"{yr1 % 100} v {yr2 % 100}"] = "—"
            row[f"{yr2} YTD Daily Avg"] = _fmt_daily_avg(daily_vals[yr2])
        if daily_vals.get(yr0) and daily_vals.get(yr_base):
            row[f"{yr0 % 100} v {yr_base % 100}"] = _fmt_pct(
                _pct_change(daily_vals[yr0], daily_vals[yr_base])
            )
        else:
            row[f"{yr0 % 100} v {yr_base % 100}"] = "—"
        row[f"{yr_base} YTD Daily Avg"] = _fmt_daily_avg(daily_vals[yr_base])

        rows.append(row)
        row_styles.append({"kind": _row_kind(spec, category)})

    categories = [row.get("Category", "") for row in rows]
    n = len(categories)
    for i, cat in enumerate(categories):
        if not cat:
            row_styles[i]["category_cell"] = "none"
            continue
        prev_same = i > 0 and categories[i - 1] == cat
        next_same = i < n - 1 and categories[i + 1] == cat
        if not prev_same and next_same:
            row_styles[i]["category_cell"] = "start"
        elif prev_same and next_same:
            row_styles[i]["category_cell"] = "middle"
        elif prev_same and not next_same:
            row_styles[i]["category_cell"] = "end"
        else:
            row_styles[i]["category_cell"] = "single"

    prev_category = None
    for row in rows:
        cat = row.get("Category", "")
        if cat and cat == prev_category:
            row["Category"] = ""
        elif cat:
            prev_category = cat
        else:
            prev_category = None

    columns = list(rows[0].keys()) if rows else ["Category", "Market"]
    return rows, row_styles, {
        "target_year": target_year,
        "target_month": target_month,
        "year_columns": yr_list,
        "months": target_months,
        "period_label": period_label,
        "growth_cols": sorted(growth_cols),
        "columns": columns,
    }


def precompute_monthly_avgs(
    df: pd.DataFrame, year: int, months: list[int]
) -> dict[str, dict[int, float]]:
    """Return {market: {month: daily_avg}} for all markets in a year."""
    result: dict[str, dict[int, float]] = {}
    for market in INTERNATIONAL_MARKETS:
        if market not in df.columns:
            continue
        result[market] = {}
        for m in months:
            mask = (df["year"] == year) & (df["month"] == m)
            row = df[mask]
            if row.empty:
                result[market][m] = 0.0
            else:
                val = pd.to_numeric(row[market], errors="coerce").fillna(0).sum()
                days = calendar.monthrange(int(year), int(m))[1]
                result[market][m] = int(val) / days
    return result


def group_monthly_avg(
    pre: dict[str, dict[int, float]],
    month: int,
    markets: list[str] | str,
) -> float:
    """Daily avg for a market-group spec in a given month."""
    if markets == "asean_total":
        mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "ASEAN"]
    elif markets == "g7_total":
        mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "G7"]
    elif markets == "others4":
        mkts = [m for m in INTERNATIONAL_MARKETS if m not in PPT_LISTED_MARKETS]
    elif markets == "grand_total":
        mkts = list(INTERNATIONAL_MARKETS)
    else:
        mkts = list(markets)
    return sum(pre.get(m, {}).get(month, 0) for m in mkts)


def build_monthly_yoy_table(
    df: pd.DataFrame,
    curr_year: int,
    prev_year: int,
    curr_month: int,
    row_styles: list[dict[str, str]],
) -> dict[str, Any]:
    """Structured monthly YoY table (PPT market rows × month columns)."""
    months = list(range(1, curr_month + 1))
    month_labels = [MONTH_ABBR[m] for m in months]
    curr_pre = precompute_monthly_avgs(df, curr_year, months)
    prev_pre = precompute_monthly_avgs(df, prev_year, months)

    def _fmt_yoy_cell(pct: float | None) -> tuple[str, str]:
        if pct is None:
            return ("—", "#111")
        sign = "+" if pct >= 0 else ""
        color = "#2e7d32" if pct > 0 else ("#8b2942" if pct < 0 else "#111")
        return (f"{sign}{pct:.0%}", color)

    rows: list[dict[str, Any]] = []
    for category, label, spec in PPT_SUMMARY_ROWS:
        yoy_cells: list[float | None] = []
        for m in months:
            curr_avg = group_monthly_avg(curr_pre, m, spec)
            prev_avg = group_monthly_avg(prev_pre, m, spec)
            if prev_avg and prev_avg > 0:
                yoy_cells.append((curr_avg - prev_avg) / prev_avg)
            else:
                yoy_cells.append(None)

        curr_total = sum(
            group_monthly_avg(curr_pre, m, spec)
            * calendar.monthrange(int(curr_year), int(m))[1]
            for m in months
        )
        prev_total = sum(
            group_monthly_avg(prev_pre, m, spec)
            * calendar.monthrange(int(prev_year), int(m))[1]
            for m in months
        )
        curr_days = sum(calendar.monthrange(int(curr_year), int(m))[1] for m in months)
        prev_days = sum(calendar.monthrange(int(prev_year), int(m))[1] for m in months)
        curr_ytd_avg = curr_total / curr_days if curr_days > 0 else 0
        prev_ytd_avg = prev_total / prev_days if prev_days > 0 else 0
        ytd_yoy = (
            (curr_ytd_avg - prev_ytd_avg) / prev_ytd_avg if prev_ytd_avg > 0 else None
        )

        rows.append(
            {
                "category": category,
                "label": label,
                "spec": spec if isinstance(spec, str) else label,
                "yoy_cells": [_fmt_yoy_cell(p) for p in yoy_cells],
                "ytd_yoy": _fmt_yoy_cell(ytd_yoy),
            }
        )

    prev_cat = None
    for row in rows:
        cat = row["category"]
        if cat and cat == prev_cat:
            row["category"] = ""
        elif cat:
            prev_cat = cat
        else:
            prev_cat = None

    return {
        "columns": ["Category", "Market"] + month_labels + ["YTD"],
        "rows": rows,
        "row_styles": row_styles,
        "curr_year": curr_year,
        "prev_year": prev_year,
    }
