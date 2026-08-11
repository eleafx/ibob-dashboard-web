"""International visitor Plotly charts."""
from __future__ import annotations

import calendar

import pandas as pd
import plotly.graph_objects as go

from backend.app.charts import fig_to_json
from backend.app.config import INTERNATIONAL_MARKETS, MARKET_GROUP_MAP, MONTH_ABBR
from backend.app.metrics.international import group_monthly_avg, precompute_monthly_avgs
from backend.app.metrics.monthly import is_month_complete

_CORE_GROUPS = ("Mainland China", "ASEAN", "G7", "Greater China")


def _market_lists() -> dict[str, list[str]]:
    return {
        "Mainland": [
            m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "Mainland China"
        ],
        "Greater China": [
            m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "Greater China"
        ],
        "ASEAN": [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "ASEAN"],
        "G7": [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "G7"],
        "Other Markets": [
            m
            for m in INTERNATIONAL_MARKETS
            if MARKET_GROUP_MAP.get(m) not in _CORE_GROUPS
        ],
    }


def _group_order() -> list[str]:
    return ["Total", "Mainland", "Greater China", "ASEAN", "G7", "Other Markets"]


def build_intl_monthly_chart(df: pd.DataFrame | None, mode: str = "daily_avg") -> dict | None:
    """Trend chart: overall tourist arrivals by market group, 2024–present.

    mode='daily_avg' plots daily averages (CSV totals ÷ days in month).
    mode='monthly' plots raw monthly totals.

    Incomplete current-year months are hidden on the chart but included in CSV export.
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")

    mkts = _market_lists()
    for m in INTERNATIONAL_MARKETS:
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0)

    for name, markets in mkts.items():
        cols = [m for m in markets if m in df.columns]
        df[name] = df[cols].sum(axis=1) if cols else 0.0
    df["Total"] = df[["Mainland", "Greater China", "ASEAN", "G7", "Other Markets"]].sum(axis=1)

    df = df[df["year"] >= 2024].sort_values(["year", "month"])
    if df.empty:
        return None

    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    df["date_label"] = df["date"].dt.strftime("%Y-%m")

    # Absolute monthly totals (before daily-avg conversion) for CSV checking
    abs_cols = _group_order()
    abs_frame = df[["date_label", "year", "month"] + abs_cols].copy()

    if mode == "daily_avg":
        df["days_in_month"] = df.apply(
            lambda row: calendar.monthrange(int(row["year"]), int(row["month"]))[1],
            axis=1,
        )
        for grp in abs_cols:
            df[grp] = df[grp] / df["days_in_month"]

    # Display: drop incomplete current-year months
    complete_mask = df.apply(
        lambda row: is_month_complete(int(row["year"]), int(row["month"])),
        axis=1,
    )
    df_plot = df[complete_mask].copy()
    if df_plot.empty:
        df_plot = df.copy()

    chart_title = "Overall Tourist Arrivals by Market Group"
    y_label = "Daily Avg Arrivals" if mode == "daily_avg" else "Monthly Arrivals"
    hovertemplate = "%{y:,.0f}<br>%{x|%b %Y}<extra></extra>"

    fig = go.Figure()
    groups: list[tuple[str, str, float, str, bool, str | None]] = [
        # name, color, width, dash, visible, fill
        ("Total", "#111111", 4.0, "solid", False, "tozeroy"),
        ("Mainland", "#C41E3A", 2.0, "solid", False, None),
        ("Greater China", "#E8A838", 2.0, "solid", True, None),
        ("ASEAN", "#2E7D5E", 2.0, "solid", True, None),
        ("G7", "#8B2942", 2.0, "solid", True, None),
        ("Other Markets", "#B9A779", 1.8, "dash", True, None),
    ]
    # Keep shared x-axis for all traces so CSV export stays aligned
    for name, color, width, dash, visible, fill in groups:
        if name not in df_plot.columns:
            continue
        y_vals = [
            float(v) if pd.notna(v) and float(v) > 0 else None for v in df_plot[name]
        ]
        trace_kwargs: dict = dict(
            x=df_plot["date"],
            y=y_vals,
            name=name,
            mode="lines",
            line=dict(color=color, width=width, dash=dash),
            visible=True if visible else "legendonly",
            hovertemplate=f"{name}: <b>{hovertemplate}</b>",
            connectgaps=False,
        )
        if fill:
            trace_kwargs["fill"] = fill
            trace_kwargs["fillcolor"] = "rgba(17, 17, 17, 0.10)"
        fig.add_trace(go.Scatter(**trace_kwargs))

    # CSV: all months including incomplete + absolute totals + plotted units
    unit_suffix = "Daily Avg" if mode == "daily_avg" else "Monthly"
    csv_headers = ["Date", "Year", "Month", "Complete"]
    for grp in abs_cols:
        csv_headers.append(f"{grp} ({unit_suffix})")
        csv_headers.append(f"{grp} (Absolute)")

    csv_rows: list[list] = []
    for _, row in df.iterrows():
        label = str(row["date_label"])
        yr, mo = int(row["year"]), int(row["month"])
        complete = is_month_complete(yr, mo)
        abs_row = abs_frame.loc[abs_frame["date_label"] == label].iloc[0]
        out: list = [label, yr, mo, "yes" if complete else "no (provisional)"]
        for grp in abs_cols:
            plotted = row[grp]
            out.append("" if pd.isna(plotted) else round(float(plotted), 1))
            out.append(int(round(float(abs_row[grp]))))
        csv_rows.append(out)

    fig.update_layout(
        title=dict(
            text=chart_title,
            font=dict(size=15),
        ),
        xaxis=dict(dtick="M1", tickformat="%b<br>%Y", ticklabelstep=2),
        yaxis=dict(tickformat=",", title=y_label),
        margin=dict(l=60, r=20, t=50, b=50),
        height=420,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        meta={"csv_export": {"headers": csv_headers, "rows": csv_rows}},
    )
    return fig_to_json(fig)


def build_intl_monthly_yoy_chart(
    df: pd.DataFrame,
    curr_year: int,
    prev_year: int,
    curr_month: int,
    mode: str = "daily_avg",
) -> dict:
    """Line chart: monthly YoY % for market groups vs prev year.

    Incomplete current-year months are hidden on the chart but included in CSV export
    with absolute values for checking.
    """
    months_all = list(range(1, curr_month + 1))
    # Display only complete months (keep provisional in CSV)
    months_display = [
        m for m in months_all if is_month_complete(curr_year, m)
    ] or months_all
    month_labels = [MONTH_ABBR[m] for m in months_display]
    unit_label = "Monthly Total" if mode == "monthly" else "Daily Avg"

    curr_pre = precompute_monthly_avgs(df, curr_year, months_all, mode=mode)
    prev_pre = precompute_monthly_avgs(df, prev_year, months_all, mode=mode)
    # Absolute monthly totals for CSV (always monthly totals regardless of mode)
    curr_abs = precompute_monthly_avgs(df, curr_year, months_all, mode="monthly")
    prev_abs = precompute_monthly_avgs(df, prev_year, months_all, mode="monthly")

    mkts = _market_lists()
    groups: list[tuple[str, list[str], str, float, str, bool]] = [
        # name, markets, color, width, dash, visible
        ("Total", INTERNATIONAL_MARKETS, "#111111", 4.0, "solid", False),
        ("Mainland", mkts["Mainland"], "#C41E3A", 2.0, "solid", False),
        ("Greater China", mkts["Greater China"], "#E8A838", 2.0, "solid", True),
        ("ASEAN", mkts["ASEAN"], "#2E7D5E", 2.0, "solid", True),
        ("G7", mkts["G7"], "#8B2942", 2.0, "solid", True),
        ("Other Markets", mkts["Other Markets"], "#B9A779", 1.8, "dash", True),
    ]

    fig = go.Figure()
    for name, markets, color, width, dash, visible in groups:
        yoy_vals: list[float | None] = []
        for m in months_display:
            curr_avg = group_monthly_avg(curr_pre, m, markets)
            prev_avg = group_monthly_avg(prev_pre, m, markets)
            if prev_avg and prev_avg > 0:
                yoy_vals.append(round((curr_avg - prev_avg) / prev_avg * 100, 1))
            else:
                yoy_vals.append(None)
        fig.add_trace(
            go.Scatter(
                x=month_labels,
                y=yoy_vals,
                name=name,
                mode="lines+markers",
                line=dict(color=color, width=width, dash=dash),
                marker=dict(size=6),
                visible=True if visible else "legendonly",
                hovertemplate=f"{name}: <b>%{{y:+.1f}}%</b><extra></extra>",
                connectgaps=False,
            )
        )

    # CSV with YoY % + absolute values for all months (incl. incomplete)
    csv_headers = ["Month", "Complete"]
    for name, _, _, _, _, _ in groups:
        csv_headers.extend(
            [
                f"{name} YoY %",
                f"{name} {curr_year} ({unit_label})",
                f"{name} {prev_year} ({unit_label})",
                f"{name} {curr_year} Absolute",
                f"{name} {prev_year} Absolute",
            ]
        )
    csv_rows: list[list] = []
    for m in months_all:
        complete = is_month_complete(curr_year, m)
        row: list = [
            MONTH_ABBR[m],
            "yes" if complete else "no (provisional)",
        ]
        for name, markets, _, _, _, _ in groups:
            curr_avg = group_monthly_avg(curr_pre, m, markets)
            prev_avg = group_monthly_avg(prev_pre, m, markets)
            if prev_avg and prev_avg > 0:
                yoy = round((curr_avg - prev_avg) / prev_avg * 100, 1)
            else:
                yoy = ""
            row.extend(
                [
                    yoy,
                    round(curr_avg, 1) if curr_avg else 0,
                    round(prev_avg, 1) if prev_avg else 0,
                    int(round(group_monthly_avg(curr_abs, m, markets))),
                    int(round(group_monthly_avg(prev_abs, m, markets))),
                ]
            )
        csv_rows.append(row)

    fig.add_hline(y=0, line_dash="dash", line_color="#999", line_width=1)
    fig.update_layout(
        title=dict(
            text=f"{curr_year} vs {prev_year} Monthly YoY — {unit_label} Arrivals",
            font=dict(size=15),
        ),
        yaxis=dict(title="YoY % Change", ticksuffix="%"),
        margin=dict(l=60, r=20, t=50, b=40),
        height=380,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        meta={"csv_export": {"headers": csv_headers, "rows": csv_rows}},
    )
    return fig_to_json(fig)
