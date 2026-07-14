"""Holiday period helpers + get_holiday_data (ported from Streamlit)."""
from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.config_holidays import (
    CNY_FIRST_DAY,
    CONTEXT_DIRECTION,
    CONTEXT_TO_REGION,
    CP_TYPE_MAP,
    HOLIDAY_DISPLAY,
    HOLIDAY_INBOUND_SEGMENTS,
    HOLIDAY_OUTBOUND_SEGMENTS,
    HOLIDAY_PERIODS,
    HOLIDAY_VARIANTS,
    HOLIDAYS_BY_REGION,
    LUNAR_LABELS,
    VARIANT_TO_KEY,
)


def resolve_region(context: str) -> str:
    return CONTEXT_TO_REGION.get(context, context)


def format_period_note(start_str: str, end_str: str) -> str:
    start = pd.to_datetime(start_str)
    end = pd.to_datetime(end_str)
    n_days = (end - start).days + 1
    return f"{n_days}d  {start.strftime('%b %d (%a)')} – {end.strftime('%b %d (%a)')}"


def cny_lunar_offset(start_str: str, year: int) -> int:
    first_day = CNY_FIRST_DAY.get(int(year))
    if not first_day:
        return 0
    return (pd.to_datetime(start_str) - pd.to_datetime(first_day)).days


def list_holidays_for_context(context: str) -> list[str]:
    region = resolve_region(context)
    return list(HOLIDAYS_BY_REGION.get(region, []))


def enrich_period(period: dict, holiday_key: str, year: int) -> dict:
    period = dict(period)
    period["note"] = format_period_note(period["start"], period["end"])
    if holiday_key == "CNY":
        period["lunar_offset"] = cny_lunar_offset(period["start"], year)
    return period


def bridge_leave_weekdays(official: dict, extended: dict) -> list:
    off_start = pd.to_datetime(official["start"])
    off_end = pd.to_datetime(official["end"])
    ext_start = pd.to_datetime(extended["start"])
    ext_end = pd.to_datetime(extended["end"])
    off_dates = set(pd.date_range(off_start, off_end, freq="D"))
    bridge = []
    for d in pd.date_range(ext_start, ext_end, freq="D"):
        if d not in off_dates and d.weekday() < 5:
            bridge.append(d)
    return bridge


def normalize_hk_holiday(cfg: dict, holiday_key: str, year: int) -> dict:
    official = enrich_period(cfg["official"], holiday_key, year)
    if "extended_al" not in cfg:
        return {
            "official": official,
            "extended_al": None,
            "al_applicable": False,
            "al_reason": "No annual leave bridge defined for this holiday.",
        }

    extended_raw = cfg["extended_al"]
    if (
        official["start"] == extended_raw["start"]
        and official["end"] == extended_raw["end"]
    ):
        return {
            "official": official,
            "extended_al": None,
            "al_applicable": False,
            "al_reason": "No annual leave bridge — official holiday only.",
        }

    bridge_days = bridge_leave_weekdays(official, extended_raw)
    if not bridge_days:
        merged = {
            "start": min(official["start"], extended_raw["start"]),
            "end": max(official["end"], extended_raw["end"]),
        }
        merged = enrich_period(merged, holiday_key, year)
        return {
            "official": merged,
            "extended_al": None,
            "al_applicable": False,
            "al_reason": (
                "Weekend link only — counted under Official View "
                "(no annual leave required)."
            ),
        }

    extended = enrich_period(extended_raw, holiday_key, year)
    extended["bridge_note"] = ", ".join(d.strftime("%d %b (%a)") for d in bridge_days)
    return {
        "official": official,
        "extended_al": extended,
        "al_applicable": True,
        "al_reason": None,
    }


def get_hk_holiday_meta(region: str, holiday_key: str) -> dict[int, dict]:
    meta: dict[int, dict] = {}
    for year, holidays in sorted(HOLIDAY_PERIODS.get(region, {}).items()):
        cfg = holidays.get(holiday_key)
        if not cfg:
            continue
        meta[int(year)] = normalize_hk_holiday(cfg, holiday_key, int(year))
    return meta


def get_holiday_periods(
    context: str,
    holiday_key: str,
    variant: str,
    al_fallback: bool = False,
) -> dict[int, dict]:
    region = resolve_region(context)
    variant_key = VARIANT_TO_KEY.get(variant, variant)
    periods: dict[int, dict] = {}

    for year, holidays in sorted(HOLIDAY_PERIODS.get(region, {}).items()):
        cfg = holidays.get(holiday_key)
        if not cfg:
            continue
        year_i = int(year)

        if region == "CN":
            if variant_key != "official":
                continue
            periods[year_i] = enrich_period(cfg["official"], holiday_key, year_i)
            continue

        norm = normalize_hk_holiday(cfg, holiday_key, year_i)
        if variant_key == "official" and norm["official"]:
            periods[year_i] = norm["official"]
        elif variant_key == "extended_al":
            if al_fallback:
                continue
            if norm["extended_al"]:
                periods[year_i] = norm["extended_al"]

    return periods


def build_hk_al_view_periods(holiday_key: str) -> dict[int, dict]:
    official = get_holiday_periods("HK", holiday_key, "Official Days")
    extended = get_holiday_periods("HK", holiday_key, "Extended Leave Days")
    periods: dict[int, dict] = {}
    for year, off in official.items():
        if year in extended:
            periods[year] = extended[year]
        else:
            periods[year] = dict(off)
            periods[year]["official_fallback"] = True
    return periods


def holiday_segment_config(
    direction: str, segment: str
) -> tuple[str, list[str] | None, str]:
    if direction == "inbound":
        configs = {
            "All tourists": (
                "tourist_arrival",
                ["Mainland Visitors", "Other Visitors"],
                "Tourist Arrivals",
            ),
            "Mainland": (
                "mainland_arrival",
                ["Mainland Visitors"],
                "Mainland Visitor Arrivals",
            ),
            "International": (
                "international_arrival",
                ["Other Visitors"],
                "International Visitor Arrivals",
            ),
        }
        return configs.get(segment, configs["All tourists"])
    configs = {
        "All": ("total_departure", None, "Total Departures"),
        "HK Residents": (
            "hk_departure",
            ["Hong Kong Residents"],
            "HK Resident Departures",
        ),
        "Tourists": (
            "tourist_departure",
            ["Mainland Visitors", "Other Visitors"],
            "Visitor Departures",
        ),
    }
    return configs.get(segment, configs["HK Residents"])


def cp_segment_values(cp_subset: pd.DataFrame, cp_cols: list[str] | None) -> pd.Series:
    if cp_cols is None:
        return cp_subset["Total"]
    if len(cp_cols) == 1:
        return cp_subset[cp_cols[0]]
    return cp_subset[cp_cols].sum(axis=1)


def get_holiday_data(
    raw_arrivals_df: pd.DataFrame | None,
    raw_departures_df: pd.DataFrame | None,
    daily_in: pd.DataFrame | None,
    daily_out: pd.DataFrame | None,
    holiday_key: str,
    context: str = "Mainland",
    variant: str = "Official Days",
    al_fallback: bool = False,
    direction: str | None = None,
    segment: str | None = None,
) -> dict[str, Any] | None:
    region = resolve_region(context)
    if direction is None:
        direction = CONTEXT_DIRECTION.get(region, "inbound")
    if segment is None:
        segment = (
            HOLIDAY_INBOUND_SEGMENTS[0]
            if direction == "inbound"
            else HOLIDAY_OUTBOUND_SEGMENTS[1]
        )
    value_col, cp_cols, flow_label = holiday_segment_config(direction, segment)

    if direction == "inbound":
        if raw_arrivals_df is None or daily_in is None:
            return None
        daily_df = daily_in
        cp_df = raw_arrivals_df
    else:
        if raw_departures_df is None or daily_out is None:
            return None
        daily_df = daily_out
        cp_df = raw_departures_df

    if region == "HK" and VARIANT_TO_KEY.get(variant, variant) == "extended_al" and al_fallback:
        periods = build_hk_al_view_periods(holiday_key)
    else:
        periods = get_holiday_periods(
            region, holiday_key, variant, al_fallback=al_fallback
        )
    if not periods:
        return None

    result: dict[str, Any] = {
        "avg": {},
        "total": {},
        "days": {},
        "daily": {},
        "cp_data": {},
        "cp_total": {},
        "periods": periods,
        "flow_label": flow_label,
        "value_col": value_col,
        "segment": segment,
        "direction": direction,
        "holiday_key": holiday_key,
        "holiday_label": HOLIDAY_DISPLAY.get(holiday_key, holiday_key),
        "variant": variant,
        "region": region,
        "context": context,
    }

    if not pd.api.types.is_datetime64_any_dtype(cp_df["Date"]):
        cp_df = cp_df.copy()
        cp_df["Date"] = pd.to_datetime(cp_df["Date"], errors="coerce")

    for year, p in periods.items():
        start, end = pd.to_datetime(p["start"]), pd.to_datetime(p["end"])
        mask = (daily_df["Date"] >= start) & (daily_df["Date"] <= end)
        subset = daily_df[mask]
        if subset.empty:
            continue

        n_days = len(subset)
        total_vol = int(subset[value_col].sum())
        avg = subset[value_col].mean()
        daily_vals = subset[value_col].tolist()

        result["avg"][str(year)] = int(avg)
        result["total"][str(year)] = total_vol
        result["days"][str(year)] = n_days
        result["daily"][str(year)] = [int(v) for v in daily_vals]

        cp_mask = (cp_df["Date"] >= start) & (cp_df["Date"] <= end)
        cp_subset = cp_df[cp_mask].copy()
        if cp_subset.empty or "Control Point" not in cp_subset.columns:
            continue
        cp_subset["_segment_val"] = cp_segment_values(cp_subset, cp_cols)
        cp_daily = cp_subset.groupby("Control Point")["_segment_val"].sum() / n_days
        result["cp_data"][str(year)] = {k: float(v) for k, v in cp_daily.to_dict().items()}
        cp_total = cp_subset.groupby("Control Point")["_segment_val"].sum()
        result["cp_total"][str(year)] = {k: int(v) for k, v in cp_total.to_dict().items()}

    years_avail = sorted(result["avg"].keys())
    growth: list[str] = []
    total_growth: list[str] = []
    for i in range(len(years_avail) - 1):
        y1, y2 = years_avail[i], years_avail[i + 1]
        if result["avg"][y1] > 0:
            pct = (result["avg"][y2] - result["avg"][y1]) / result["avg"][y1]
            growth.append(f"+{pct:.0%}" if pct >= 0 else f"{pct:.0%}")
        else:
            growth.append("—")
        if result["total"][y1] > 0:
            pct_t = (result["total"][y2] - result["total"][y1]) / result["total"][y1]
            total_growth.append(f"+{pct_t:.0%}" if pct_t >= 0 else f"{pct_t:.0%}")
        else:
            total_growth.append("—")
    result["growth"] = growth
    result["total_growth"] = total_growth

    cp_growth: dict[str, list[str]] = {}
    for cp_name in CP_TYPE_MAP:
        cp_rates: list[str] = []
        for i in range(len(years_avail) - 1):
            y1, y2 = years_avail[i], years_avail[i + 1]
            v1 = result["cp_data"].get(y1, {}).get(cp_name, 0)
            v2 = result["cp_data"].get(y2, {}).get(cp_name, 0)
            if v1 and v1 > 0:
                pct = (v2 - v1) / v1
                cp_rates.append(f"+{pct:.0%}" if pct >= 0 else f"{pct:.0%}")
            else:
                cp_rates.append("—")
        cp_growth[cp_name] = cp_rates
    result["cp_growth"] = cp_growth

    if years_avail:
        has_lunar = any(
            "lunar_offset" in periods.get(int(yr), {}) for yr in years_avail
        )
        if has_lunar:
            min_lunar = min(
                periods[int(yr)].get("lunar_offset", 0) for yr in years_avail
            )
            max_lunar_end = max(
                periods[int(yr)].get("lunar_offset", 0)
                + len(result["daily"].get(yr, []))
                - 1
                for yr in years_avail
                if result["daily"].get(yr)
            )
            n_total = max_lunar_end - min_lunar + 1
            for yr in years_avail:
                offset = periods[int(yr)].get("lunar_offset", 0) - min_lunar
                raw = result["daily"].get(yr, [])
                padded: list[int | None] = [None] * n_total
                for j, v in enumerate(raw):
                    padded[offset + j] = v
                result["daily"][yr] = padded
            result["day_labels"] = [
                LUNAR_LABELS.get(min_lunar + i, f"Day{i + 1}") for i in range(n_total)
            ]
        else:
            max_len = max(
                (len(result["daily"].get(yr, [])) for yr in years_avail), default=0
            )
            result["day_labels"] = [f"Day {i + 1}" for i in range(max_len)]

    return result


def build_calendar_days(
    start_date_str: str,
    end_date_str: str,
    official_start_str: str,
    official_end_str: str,
) -> list[dict[str, Any]]:
    """Structured mini-calendar days for React (official / weekend / leave)."""
    start_dt = pd.to_datetime(start_date_str)
    end_dt = pd.to_datetime(end_date_str)
    display_start = start_dt - pd.Timedelta(days=start_dt.weekday())
    display_end = end_dt + pd.Timedelta(days=(6 - end_dt.weekday()))
    off_start = pd.to_datetime(official_start_str)
    off_end = pd.to_datetime(official_end_str)

    days: list[dict[str, Any]] = []
    for d in pd.date_range(display_start, display_end):
        is_wknd = d.weekday() in (5, 6)
        is_off = off_start <= d <= off_end
        is_leave = (start_dt <= d <= end_dt) and not is_off and not is_wknd
        if is_off:
            kind = "official"
        elif is_wknd:
            kind = "weekend"
        elif is_leave:
            kind = "leave"
        else:
            kind = "plain"
        days.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "weekday": d.strftime("%a")[:2],
                "day": int(d.day),
                "month": d.strftime("%b"),
                "kind": kind,
            }
        )
    return days


def build_proximity_tracker(context: str, holiday_key: str) -> list[dict[str, Any]]:
    region = resolve_region(context)
    official_periods = get_holiday_periods(region, holiday_key, "Official Days")
    extended_periods = get_holiday_periods(region, holiday_key, "Extended Leave Days")
    hk_meta = get_hk_holiday_meta(region, holiday_key) if region == "HK" else {}

    rows: list[dict[str, Any]] = []
    for yr in sorted(official_periods.keys()):
        cfg_off = official_periods.get(yr)
        if not cfg_off:
            continue
        off_days = (
            pd.to_datetime(cfg_off["end"]) - pd.to_datetime(cfg_off["start"])
        ).days + 1

        if region == "HK":
            meta = hk_meta.get(yr, {})
            if not meta.get("al_applicable"):
                rows.append(
                    {
                        "year": yr,
                        "label": f"{off_days} holiday day{'s' if off_days != 1 else ''}",
                        "al_applicable": False,
                        "al_reason": meta.get("al_reason"),
                        "days": build_calendar_days(
                            cfg_off["start"],
                            cfg_off["end"],
                            cfg_off["start"],
                            cfg_off["end"],
                        ),
                    }
                )
            else:
                cfg_ext = extended_periods.get(yr) or cfg_off
                ext_days = (
                    pd.to_datetime(cfg_ext["end"]) - pd.to_datetime(cfg_ext["start"])
                ).days + 1
                rows.append(
                    {
                        "year": yr,
                        "label": f"{off_days} official · {ext_days} incl. AL bridge",
                        "al_applicable": True,
                        "al_reason": None,
                        "days": build_calendar_days(
                            cfg_ext["start"],
                            cfg_ext["end"],
                            cfg_off["start"],
                            cfg_off["end"],
                        ),
                    }
                )
        else:
            rows.append(
                {
                    "year": yr,
                    "label": f"{off_days} holiday day{'s' if off_days != 1 else ''}",
                    "al_applicable": False,
                    "al_reason": None,
                    "days": build_calendar_days(
                        cfg_off["start"],
                        cfg_off["end"],
                        cfg_off["start"],
                        cfg_off["end"],
                    ),
                }
            )
    return rows


def holiday_options() -> dict[str, Any]:
    return {
        "contexts": ["Mainland", "HK"],
        "directions": ["inbound", "outbound"],
        "inbound_segments": list(HOLIDAY_INBOUND_SEGMENTS),
        "outbound_segments": list(HOLIDAY_OUTBOUND_SEGMENTS),
        "variants": list(HOLIDAY_VARIANTS),
        "holidays_by_region": HOLIDAYS_BY_REGION,
        "holiday_display": HOLIDAY_DISPLAY,
        "default_direction": CONTEXT_DIRECTION,
    }
