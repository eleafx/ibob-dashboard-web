"""Holiday Plotly chart builders (ported from Streamlit render helpers)."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from backend.app.config_holidays import (
    CP_COLORS,
    CP_DISPLAY_NAME,
    CP_TYPE_MAP,
    HOLIDAY_MARGIN_BAR,
    HOLIDAY_MARGIN_OVERVIEW,
    HOLIDAY_MARGIN_PANEL,
    TOP_CONTROL_POINTS,
)


def format_volume_label(value: float) -> str:
    if value >= 1_000_000:
        return f"<b>{value / 1_000_000:.2f}M</b>"
    if value >= 1_000:
        return f"<b>{value / 1_000:.1f}K</b>"
    return f"<b>{value:,}</b>"


def _yoy_display(newer_val: float | None, older_val: float | None) -> str:
    if older_val and older_val > 0 and newer_val is not None:
        pct = (newer_val - older_val) / older_val
        return f"+{pct:.0%}" if pct >= 0 else f"{pct:.0%}"
    return "—"


def _growth_pct_color(val: str) -> str:
    if not isinstance(val, str) or val == "—":
        return "#111111"
    if val.startswith("+"):
        return "#2e7d32"
    if val.startswith("-"):
        return "#8b2942"
    return "#111111"


def _add_cp_direct_labels(fig: go.Figure, endpoints: list[dict]) -> None:
    if not endpoints:
        return
    endpoints = sorted(endpoints, key=lambda e: e["y"], reverse=True)
    max_y = max(ep["y"] for ep in endpoints)
    y_range = max_y if max_y > 0 else 1
    min_gap_y = y_range * 0.045
    last_x = max(ep["x"] for ep in endpoints)
    label_x = last_x + 0.35
    prev_y = None
    for ep in endpoints:
        y_pos = float(ep["y"])
        if prev_y is not None and (prev_y - y_pos) < min_gap_y:
            y_pos = prev_y - min_gap_y
        prev_y = y_pos
        fig.add_annotation(
            x=label_x,
            y=y_pos,
            xref="x",
            yref="y",
            text=ep["text"],
            showarrow=False,
            font=dict(size=11, color=ep["color"]),
            bgcolor="rgba(255,255,255,0.85)",
            borderpad=2,
            xanchor="left",
        )


def make_multiyear_holiday_chart(
    daily_df: pd.DataFrame | None,
    value_col: str,
    periods: dict,
    title: str,
    colors: dict[str, str],
) -> dict | None:
    if daily_df is None or daily_df.empty:
        return None

    fig = go.Figure()
    ref_year = 2024
    years_sorted = sorted(periods.keys(), key=lambda y: int(y))

    period_info = []
    for year in years_sorted:
        yr_int = int(year)
        p = periods.get(year) or periods.get(yr_int) or periods.get(str(year), {})
        if not p:
            continue
        h_start = pd.to_datetime(p["start"])
        h_end = pd.to_datetime(p["end"])
        norm_start = pd.Timestamp(year=ref_year, month=h_start.month, day=h_start.day)
        norm_end = pd.Timestamp(year=ref_year, month=h_end.month, day=h_end.day)
        color = colors.get(str(year), "#3A7976")
        n_days = (h_end - h_start).days + 1
        period_info.append(
            (
                str(year),
                norm_start,
                norm_end,
                color,
                h_start.strftime("%d %b"),
                h_end.strftime("%d %b"),
                n_days,
            )
        )

    unique_windows = {(ns, ne) for _, ns, ne, _, _, _, _ in period_info}
    single_window = len(unique_windows) == 1

    plotted = False
    for year in years_sorted:
        yr_int = int(year)
        yr_data = daily_df[daily_df["Date"].dt.year == yr_int].sort_values("Date")
        if yr_data.empty:
            continue
        norm_dates = yr_data["Date"].apply(
            lambda d: pd.Timestamp(year=ref_year, month=d.month, day=d.day)
        )
        color = colors.get(str(year), "#3A7976")
        fig.add_trace(
            go.Scatter(
                x=norm_dates,
                y=yr_data[value_col],
                mode="lines",
                name=str(year),
                line=dict(color=color, width=1.8),
                hovertemplate=f"{year} · %{{x|%d %b}}<br><b>%{{y:,}}</b><extra></extra>",
            )
        )
        plotted = True

    for yr, ns, ne, color, start_lbl, end_lbl, _n_days in period_info:
        del yr, start_lbl, end_lbl, _n_days
        fig.add_vrect(
            x0=ns,
            x1=ne + pd.Timedelta(days=1),
            fillcolor=color,
            opacity=0.12,
            line_width=0,
            layer="below",
        )

    if single_window and period_info:
        _, ns, ne, color, start_lbl, end_lbl, n_days = period_info[0]
        mid = ns + (ne - ns) / 2
        fig.add_annotation(
            x=mid,
            yref="paper",
            y=1.02,
            text=f"<b>{start_lbl} – {end_lbl}</b> · {n_days}d",
            showarrow=False,
            font=dict(color=color, size=11),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=color,
            borderwidth=1,
            borderpad=4,
            xanchor="center",
        )
    elif not single_window:
        for i, (yr, ns, ne, color, start_lbl, end_lbl, n_days) in enumerate(period_info):
            mid = ns + (ne - ns) / 2
            fig.add_annotation(
                x=mid,
                yref="paper",
                y=1.02 - i * 0.06,
                text=f"<b>{yr}</b>  {start_lbl} – {end_lbl} · {n_days}d",
                showarrow=False,
                font=dict(color=color, size=10),
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor=color,
                borderwidth=1,
                borderpad=3,
                xanchor="center",
            )

    if not plotted:
        return None

    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        yaxis=dict(tickformat=","),
        xaxis=dict(dtick="M1", tickformat="%b", title=""),
        margin=HOLIDAY_MARGIN_OVERVIEW,
        height=520,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig.to_plotly_json()


def make_holiday_daily_figure(hd: dict, colors: dict[str, str]) -> dict | None:
    years_avail = sorted(hd.get("avg", {}).keys())
    if not years_avail:
        return None
    day_labels = list(hd.get("day_labels") or [])
    max_len = max((len(hd["daily"].get(yr, [])) for yr in years_avail), default=0)
    if not day_labels and max_len:
        day_labels = [f"Day {j + 1}" for j in range(max_len)]
    x_idx = list(range(len(day_labels)))

    fig = go.Figure()
    for yr in years_avail:
        data = hd["daily"].get(yr, [])
        if not data:
            continue
        fig.add_trace(
            go.Scatter(
                x=x_idx[: len(data)],
                y=data,
                name=yr,
                mode="lines+markers",
                line=dict(
                    color=colors.get(yr, "#999"),
                    width=3 if yr == years_avail[-1] else 2,
                    dash="dash" if yr == years_avail[0] else "solid",
                    shape="spline",
                ),
                marker=dict(size=6),
                hovertemplate=yr + ": <b>%{customdata}K</b><extra></extra>",
                customdata=[int(round(v / 1000)) if v is not None else 0 for v in data],
                connectgaps=False,
            )
        )
    for i in range(max_len):
        fig.add_vline(x=i, line_width=1, line_dash="dot", line_color="#e0e0e0")
    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=x_idx, ticktext=day_labels),
        yaxis=dict(tickformat=",", range=[0, None]),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=HOLIDAY_MARGIN_PANEL,
        height=380,
        template="plotly_white",
    )
    return fig.to_plotly_json()


def make_holiday_bar_figure(
    hd: dict,
    colors: dict[str, str],
    current_year: str,
    volume_basis: str = "Period total",
) -> dict | None:
    years_avail = sorted(hd.get("avg", {}).keys())
    if not years_avail:
        return None

    def _period_for_year(year: str) -> dict:
        periods = hd.get("periods") or {}
        return periods.get(int(year)) or periods.get(year) or {}

    bar_colors = [
        colors.get(yr, "#B9A779") if yr == str(current_year) else "#c8c8c8"
        for yr in years_avail
    ]
    bar_labels = [
        f"{yr}<br>{hd['days'][yr]}d"
        + ("*" if _period_for_year(yr).get("official_fallback") else "")
        for yr in years_avail
    ]

    if volume_basis == "Period total":
        bar_vals = [hd["total"][yr] for yr in years_avail]
        growth_vals = hd.get("total_growth", [])
        text_labels = [format_volume_label(v) for v in bar_vals]
    else:
        bar_vals = [hd["avg"][yr] for yr in years_avail]
        growth_vals = hd.get("growth", [])
        text_labels = [f"<b>{int(v / 1000)}K</b>" for v in bar_vals]

    fig = go.Figure(
        go.Bar(
            x=bar_labels,
            y=bar_vals,
            marker_color=bar_colors,
            text=text_labels,
            textposition="outside",
        )
    )
    for i, g in enumerate(growth_vals):
        fig.add_annotation(
            x=(i + i + 1) / 2,
            y=(bar_vals[i] + bar_vals[i + 1]) / 2,
            text=f"<b>{g}</b>",
            showarrow=False,
            font=dict(size=12, color="#333"),
            bgcolor="#fff",
            bordercolor="#555",
            borderwidth=1.5,
            borderpad=4,
        )
    fig.update_layout(
        yaxis=dict(visible=False),
        showlegend=False,
        margin=HOLIDAY_MARGIN_BAR,
        height=380,
        template="plotly_white",
    )
    return fig.to_plotly_json()


def make_holiday_cp_figure(hd: dict) -> dict | None:
    cp_years = sorted(hd.get("cp_data", {}).keys())
    if not cp_years:
        return None

    fig = go.Figure()
    cp_x_idx = list(range(len(cp_years)))
    cp_endpoints: list[dict] = []

    for cp in TOP_CONTROL_POINTS:
        pts = []
        for yr in cp_years:
            val = hd["cp_data"].get(yr, {}).get(cp, 0)
            pts.append(int(val) if val and val > 500 else None)
        cp_label = CP_DISPLAY_NAME.get(cp, cp)
        cp_color = CP_COLORS.get(
            cp, CP_COLORS.get(CP_TYPE_MAP.get(cp, "other"), "#A6A6A6")
        )
        short_label = (
            cp_label.replace("Lok Ma Chau Spur Line", "LMC Spur Line")
            .replace("Express Rail Link West Kowloon", "XRL West Kowloon")
            .replace("Hong Kong-Zhuhai-Macao Bridge", "HZMB")
        )
        fig.add_trace(
            go.Scatter(
                x=cp_x_idx,
                y=pts,
                name=cp_label,
                showlegend=False,
                mode="lines+markers",
                line=dict(color=cp_color, width=2.5),
                marker=dict(size=7, color=cp_color),
                hovertemplate=f"{cp_label}<br>Avg Daily: <b>%{{y:,}}</b><extra></extra>",
            )
        )
        visible_pts = [(i, p) for i, p in enumerate(pts) if p is not None]
        if visible_pts:
            last_idx, last_val = visible_pts[-1]
            cp_endpoints.append(
                {
                    "x": last_idx,
                    "y": last_val,
                    "text": short_label,
                    "color": cp_color,
                }
            )

    others_pts = []
    for yr in cp_years:
        yr_data = hd["cp_data"].get(yr, {})
        others_val = sum(v for k, v in yr_data.items() if k not in TOP_CONTROL_POINTS)
        others_pts.append(int(others_val) if others_val > 0 else None)
    others_color = "#888888"
    fig.add_trace(
        go.Scatter(
            x=cp_x_idx,
            y=others_pts,
            name="Others",
            showlegend=False,
            mode="lines+markers",
            line=dict(color=others_color, width=1.5, dash="dash"),
            marker=dict(size=5, color=others_color),
            hovertemplate="Others<br>Avg Daily: <b>%{y:,}</b><extra></extra>",
        )
    )
    others_visible = [(i, p) for i, p in enumerate(others_pts) if p is not None]
    if others_visible:
        last_idx, last_val = others_visible[-1]
        cp_endpoints.append(
            {
                "x": last_idx,
                "y": last_val,
                "text": "<i>Others</i>",
                "color": others_color,
            }
        )

    _add_cp_direct_labels(fig, cp_endpoints)
    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=cp_x_idx,
            ticktext=[str(yr) for yr in cp_years],
            range=[-0.3, len(cp_years) - 0.3],
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            tickformat=",",
            range=[0, None],
            tickfont=dict(size=12),
            title=dict(text="Avg. Daily Visitors", font=dict(size=12, color="#555")),
        ),
        showlegend=False,
        margin=dict(l=60, r=140, t=75, b=60),
        height=480,
        template="plotly_white",
    )
    return fig.to_plotly_json()


def build_cp_table(hd: dict) -> dict[str, Any] | None:
    cp_years = sorted(hd.get("cp_total", {}).keys())
    if not cp_years:
        return None

    years_desc = sorted(cp_years, key=lambda y: int(y), reverse=True)
    columns = ["Control Point"]
    for i, yr in enumerate(years_desc):
        columns.append(str(yr))
        if i < len(years_desc) - 1:
            older = years_desc[i + 1]
            columns.append(f"YoY {str(yr)[-2:]}→{str(older)[-2:]}")

    rows: list[dict[str, Any]] = []
    for cp in TOP_CONTROL_POINTS + ["Others"]:
        cp_label = "Others" if cp == "Others" else CP_DISPLAY_NAME.get(cp, cp)
        year_map: dict[str, int | None] = {}
        for yr in cp_years:
            if cp == "Others":
                yr_data = hd["cp_total"].get(yr, {})
                tv = sum(v for k, v in yr_data.items() if k not in TOP_CONTROL_POINTS)
            else:
                tv = hd["cp_total"].get(yr, {}).get(cp, 0)
            year_map[str(yr)] = int(tv) if tv else None

        record: dict[str, Any] = {"Control Point": cp_label}
        for i, yr in enumerate(years_desc):
            record[str(yr)] = year_map.get(str(yr))
            if i < len(years_desc) - 1:
                older = years_desc[i + 1]
                yoy_key = f"YoY {str(yr)[-2:]}→{str(older)[-2:]}"
                record[yoy_key] = _yoy_display(
                    year_map.get(str(yr)), year_map.get(str(older))
                )
                record[f"{yoy_key}__color"] = _growth_pct_color(record[yoy_key])
        rows.append(record)

    latest = str(years_desc[0]) if years_desc else None
    if latest:
        rows.sort(
            key=lambda r: (r.get(latest) is None, -(r.get(latest) or 0)),
        )

    return {
        "columns": columns,
        "rows": rows,
        "yoy_columns": [c for c in columns if c.startswith("YoY")],
    }
