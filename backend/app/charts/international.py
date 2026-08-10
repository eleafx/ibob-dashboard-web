"""International visitor Plotly charts."""
from __future__ import annotations

import calendar

import pandas as pd
import plotly.graph_objects as go

from backend.app.charts import fig_to_json
from backend.app.config import INTERNATIONAL_MARKETS, MARKET_GROUP_MAP, MONTH_ABBR
from backend.app.metrics.international import group_monthly_avg, precompute_monthly_avgs


def build_intl_monthly_chart(df: pd.DataFrame | None, mode: str = "daily_avg") -> dict | None:
    """Trend chart: overall tourist arrivals by market group, 2024–present.

    mode='daily_avg' plots daily averages (CSV totals ÷ days in month).
    mode='monthly' plots raw monthly totals.
    """
    if df is None or df.empty:
        return None

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")

    mainland_mkts = [
        m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "Mainland China"
    ]
    asean_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "ASEAN"]
    g7_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "G7"]
    other_mkts = [
        m
        for m in INTERNATIONAL_MARKETS
        if MARKET_GROUP_MAP.get(m) not in ("Mainland China", "ASEAN", "G7")
    ]

    for m in INTERNATIONAL_MARKETS:
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0)

    df["Mainland"] = df[[m for m in mainland_mkts if m in df.columns]].sum(axis=1)
    df["ASEAN"] = df[[m for m in asean_mkts if m in df.columns]].sum(axis=1)
    df["G7"] = df[[m for m in g7_mkts if m in df.columns]].sum(axis=1)
    df["Other Markets"] = df[[m for m in other_mkts if m in df.columns]].sum(axis=1)
    df["Total"] = df[["Mainland", "ASEAN", "G7", "Other Markets"]].sum(axis=1)

    df = df[df["year"] >= 2024].sort_values(["year", "month"])
    if df.empty:
        return None

    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

    # Convert to daily averages when mode is daily_avg
    if mode == "daily_avg":
        df["days_in_month"] = df.apply(
            lambda row: calendar.monthrange(int(row["year"]), int(row["month"]))[1], axis=1,
        )
        for grp in ["Mainland", "ASEAN", "G7", "Other Markets", "Total"]:
            if grp in df.columns:
                df[grp] = df[grp] / df["days_in_month"]

    chart_title = "Overall Tourist Arrivals by Market Group"
    y_label = "Daily Avg Arrivals" if mode == "daily_avg" else "Monthly Arrivals"
    hovertemplate = "%{y:,.0f}<br>%{x|%b %Y}<extra></extra>"

    fig = go.Figure()
    groups: list[tuple[str, str, float, str, bool, str | None]] = [
        # name, color, width, dash, visible, fill
        ("Total", "#111111", 4.0, "solid", False, "tozeroy"),
        ("Mainland", "#C41E3A", 2.0, "solid", False, None),
        ("ASEAN", "#2E7D5E", 2.0, "solid", True, None),
        ("G7", "#8B2942", 2.0, "solid", True, None),
        ("Other Markets", "#B9A779", 1.8, "dash", True, None),
    ]
    for name, color, width, dash, visible, fill in groups:
        if name not in df.columns:
            continue
        mask = df[name].notna() & (df[name] > 0)
        trace_kwargs: dict = dict(
            x=df.loc[mask, "date"],
            y=df.loc[mask, name],
            name=name,
            mode="lines",
            line=dict(color=color, width=width, dash=dash),
            visible=True if visible else "legendonly",
            hovertemplate=f"{name}: <b>{hovertemplate}</b>",
        )
        if fill:
            trace_kwargs["fill"] = fill
            trace_kwargs["fillcolor"] = "rgba(17, 17, 17, 0.10)"
        fig.add_trace(go.Scatter(**trace_kwargs))

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
    )
    return fig_to_json(fig)


def build_intl_monthly_yoy_chart(
    df: pd.DataFrame,
    curr_year: int,
    prev_year: int,
    curr_month: int,
    mode: str = "daily_avg",
) -> dict:
    """Line chart: monthly YoY % for Total, Mainland, ASEAN, G7, Other Markets vs prev year."""
    months = list(range(1, curr_month + 1))
    month_labels = [MONTH_ABBR[m] for m in months]
    unit_label = "Monthly Total" if mode == "monthly" else "Daily Avg"

    curr_pre = precompute_monthly_avgs(df, curr_year, months, mode=mode)
    prev_pre = precompute_monthly_avgs(df, prev_year, months, mode=mode)

    mainland_mkts = [
        m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "Mainland China"
    ]
    asean_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "ASEAN"]
    g7_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "G7"]
    other_mkts = [
        m
        for m in INTERNATIONAL_MARKETS
        if MARKET_GROUP_MAP.get(m) not in ("Mainland China", "ASEAN", "G7")
    ]

    groups: list[tuple[str, list[str], str, float, str, bool]] = [
        # name, markets, color, width, dash, visible
        ("Total", INTERNATIONAL_MARKETS, "#111111", 4.0, "solid", False),
        ("Mainland", mainland_mkts, "#C41E3A", 2.0, "solid", False),
        ("ASEAN", asean_mkts, "#2E7D5E", 2.0, "solid", True),
        ("G7", g7_mkts, "#8B2942", 2.0, "solid", True),
        ("Other Markets", other_mkts, "#B9A779", 1.8, "dash", True),
    ]

    fig = go.Figure()
    for name, mkts, color, width, dash, visible in groups:
        yoy_vals: list[float | None] = []
        for m in months:
            curr_avg = group_monthly_avg(curr_pre, m, mkts)
            prev_avg = group_monthly_avg(prev_pre, m, mkts)
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
    )
    return fig_to_json(fig)
