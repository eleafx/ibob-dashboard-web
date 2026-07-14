"""Monthly aggregation and recovery / YoY metrics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

_HKT = timezone(timedelta(hours=8))


def get_monthly(daily_df: pd.DataFrame | None, value_col: str) -> pd.DataFrame | None:
    """Aggregate daily to monthly."""
    if daily_df is None:
        return None
    monthly = (
        daily_df.groupby(["Year", "Month"])
        .agg(days=("Date", "count"), total=(value_col, "sum"))
        .reset_index()
    )
    monthly["daily_avg"] = monthly["total"] / monthly["days"]
    return monthly


def is_month_complete(year: int, month: int) -> bool:
    """True if month has ended (today >= first day of next month in HKT)."""
    today = datetime.now(_HKT)
    if month == 12:
        next_month = datetime(year + 1, 1, 1, tzinfo=_HKT)
    else:
        next_month = datetime(year, month + 1, 1, tzinfo=_HKT)
    return today >= next_month


def get_series(monthly: pd.DataFrame | None, year: int, include_jf: bool = True) -> list[float | None]:
    """Return [Jan&Feb avg, Mar, ..., Dec] for a year (incomplete current months → None)."""
    del include_jf  # kept for API compatibility with Streamlit port
    if monthly is None:
        return [None] * 11
    yd = monthly[monthly["Year"] == year]
    if yd.empty:
        return [None] * 11

    jan = yd[yd["Month"] == 1]["daily_avg"].values
    feb = yd[yd["Month"] == 2]["daily_avg"].values
    jv = float(jan[0]) if len(jan) else None
    fv = float(feb[0]) if len(feb) else None
    jf = (jv + fv) / 2 if jv is not None and fv is not None else (jv or fv)

    current_year = datetime.now(_HKT).year
    if year == current_year:
        if not is_month_complete(year, 1) or not is_month_complete(year, 2):
            jf = None

    result: list[float | None] = [jf]
    for m in range(3, 13):
        v = yd[yd["Month"] == m]["daily_avg"].values
        val = float(v[0]) if len(v) else None
        if year == current_year and not is_month_complete(year, m):
            val = None
        result.append(val)
    return result


def calc_recovery(
    monthly_data: pd.DataFrame | None,
    baseline_dict: dict[int, int],
    year: int,
) -> list[str]:
    """Recovery rate for each month vs 2018 (+ FY average)."""
    if monthly_data is None:
        return ["—"] * 12
    series = get_series(monthly_data, year)
    rates: list[str] = []
    for i, val in enumerate(series):
        if i == 0:
            base_val = (baseline_dict[1] + baseline_dict[2]) / 2
        else:
            base_val = baseline_dict.get(i + 2)
        if val and base_val and base_val > 0:
            rates.append(f"{val / base_val:.0%}")
        else:
            rates.append("—")
    valid = [v for v in series if v]
    base_valid = [(baseline_dict[1] + baseline_dict[2]) / 2] + [
        baseline_dict.get(m, 0) for m in range(3, 13)
    ]
    base_valid = [b for b, v in zip(base_valid, series) if v]
    if valid and base_valid:
        rates.append(f"{sum(valid) / sum(base_valid):.0%}")
    else:
        rates.append("—")
    return rates


def calc_yoy(
    monthly_data: pd.DataFrame | None,
    curr_year: int,
    prev_year: int,
) -> list[str]:
    """YoY growth for each month + FY average."""
    if monthly_data is None:
        return ["—"] * 12
    curr_s = get_series(monthly_data, curr_year)
    prev_s = get_series(monthly_data, prev_year)
    rates: list[str] = []
    for i in range(11):
        if curr_s[i] and prev_s[i] and prev_s[i] > 0:
            pct = (curr_s[i] - prev_s[i]) / prev_s[i]
            rates.append(f"{pct:+.0%}")
        else:
            rates.append("—")
    valid_curr = [v for v in curr_s if v]
    valid_prev = [prev_s[i] for i, v in enumerate(curr_s) if v and prev_s[i]]
    if valid_curr and valid_prev and sum(valid_prev) > 0:
        rates.append(f"{(sum(valid_curr) - sum(valid_prev)) / sum(valid_prev):+.0%}")
    else:
        rates.append("—")
    return rates


def resolve_display_years(daily_in: pd.DataFrame | None) -> list[int]:
    """Latest up to 3 years from 2024+ present in daily data."""
    if daily_in is None or daily_in.empty:
        return [2024, 2025, 2026]
    years = sorted(int(y) for y in daily_in["Year"].unique())
    display = [yr for yr in years if yr >= 2024][-3:]
    return display or [2024, 2025, 2026]
