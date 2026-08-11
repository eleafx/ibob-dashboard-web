"""Monthly aggregation and recovery / YoY metrics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

_HKT = timezone(timedelta(hours=8))

# Days per month for baseline conversion (2018 was not a leap year).
_DAYS_IN_MONTH = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


def make_baseline_series(baseline: dict[int, int], mode: str = "daily_avg") -> list[float]:
    """Return 11-value baseline series: [Jan&Feb, Mar, ..., Dec] in daily-avg or monthly-total units."""
    if mode == "monthly":
        return [
            float(baseline[1] * _DAYS_IN_MONTH[1] + baseline[2] * _DAYS_IN_MONTH[2]),
            float(baseline[3] * _DAYS_IN_MONTH[3]),
            float(baseline[4] * _DAYS_IN_MONTH[4]),
            float(baseline[5] * _DAYS_IN_MONTH[5]),
            float(baseline[6] * _DAYS_IN_MONTH[6]),
            float(baseline[7] * _DAYS_IN_MONTH[7]),
            float(baseline[8] * _DAYS_IN_MONTH[8]),
            float(baseline[9] * _DAYS_IN_MONTH[9]),
            float(baseline[10] * _DAYS_IN_MONTH[10]),
            float(baseline[11] * _DAYS_IN_MONTH[11]),
            float(baseline[12] * _DAYS_IN_MONTH[12]),
        ]
    return [(baseline[1] + baseline[2]) / 2] + [float(baseline[m]) for m in range(3, 13)]


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


def get_series(
    monthly: pd.DataFrame | None,
    year: int,
    include_jf: bool = True,
    mode: str = "daily_avg",
    mask_incomplete: bool = True,
) -> list[float | None]:
    """Return [Jan&Feb avg, Mar, ..., Dec] for a year.

    When mask_incomplete=True (default), incomplete current-year months → None
    (for chart display). Pass False to retain provisional values for CSV export.
    """
    del include_jf  # kept for API compatibility with Streamlit port
    if monthly is None:
        return [None] * 11
    yd = monthly[monthly["Year"] == year]
    if yd.empty:
        return [None] * 11

    value_col = "total" if mode == "monthly" else "daily_avg"

    jan = yd[yd["Month"] == 1][value_col].values
    feb = yd[yd["Month"] == 2][value_col].values
    jv = float(jan[0]) if len(jan) else None
    fv = float(feb[0]) if len(feb) else None
    # monthly mode: sum Jan+Feb; daily_avg mode: average of the two averages
    jf = (jv + fv) if mode == "monthly" else ((jv + fv) / 2 if jv is not None and fv is not None else (jv or fv))

    current_year = datetime.now(_HKT).year
    if mask_incomplete and year == current_year:
        if not is_month_complete(year, 1) or not is_month_complete(year, 2):
            jf = None

    result: list[float | None] = [jf]
    for m in range(3, 13):
        v = yd[yd["Month"] == m][value_col].values
        val = float(v[0]) if len(v) else None
        if mask_incomplete and year == current_year and not is_month_complete(year, m):
            val = None
        result.append(val)
    return result


def calc_recovery(
    monthly_data: pd.DataFrame | None,
    baseline_dict: dict[int, int],
    year: int,
    mode: str = "daily_avg",
) -> list[str]:
    """Recovery rate for each month vs 2018 (+ FY average)."""
    if monthly_data is None:
        return ["—"] * 12
    series = get_series(monthly_data, year, mode=mode)
    baseline_series = make_baseline_series(baseline_dict, mode=mode)
    rates: list[str] = []
    for i, val in enumerate(series):
        base_val = baseline_series[i]
        if val and base_val and base_val > 0:
            rates.append(f"{val / base_val:.0%}")
        else:
            rates.append("—")
    valid = [v for v in series if v]
    base_valid = [b for b, v in zip(baseline_series, series) if v]
    if valid and base_valid:
        rates.append(f"{sum(valid) / sum(base_valid):.0%}")
    else:
        rates.append("—")
    return rates


def calc_yoy(
    monthly_data: pd.DataFrame | None,
    curr_year: int,
    prev_year: int,
    mode: str = "daily_avg",
) -> list[str]:
    """YoY growth for each month + FY average."""
    if monthly_data is None:
        return ["—"] * 12
    curr_s = get_series(monthly_data, curr_year, mode=mode)
    prev_s = get_series(monthly_data, prev_year, mode=mode)
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
