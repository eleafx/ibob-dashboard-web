"""International visitor Plotly charts."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from backend.app.charts import fig_to_json
from backend.app.config import INTERNATIONAL_MARKETS, MARKET_GROUP_MAP, MONTH_ABBR
from backend.app.metrics.international import group_monthly_avg, precompute_monthly_avgs


def build_intl_monthly_chart(df: pd.DataFrame | None) -> dict | None:
    """Monthly trend chart: international visitors by market group, 2024–present."""
    if df is None or df.empty:
        return None

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")

    asean_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "ASEAN"]
    g7_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "G7"]
    other_mkts = [
        m
        for m in INTERNATIONAL_MARKETS
        if MARKET_GROUP_MAP.get(m) not in ("ASEAN", "G7")
    ]

    for m in INTERNATIONAL_MARKETS:
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0)

    df["ASEAN"] = df[[m for m in asean_mkts if m in df.columns]].sum(axis=1)
    df["G7"] = df[[m for m in g7_mkts if m in df.columns]].sum(axis=1)
    df["Other Markets"] = df[[m for m in other_mkts if m in df.columns]].sum(axis=1)
    df["Total"] = df[["ASEAN", "G7", "Other Markets"]].sum(axis=1)

    df = df[df["year"] >= 2024].sort_values(["year", "month"])
    if df.empty:
        return None

    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

    fig = go.Figure()
    groups = [
        ("Total", "#111111", 2.8, "solid"),
        ("ASEAN", "#2E7D5E", 2.0, "solid"),
        ("G7", "#8B2942", 2.0, "solid"),
        ("Other Markets", "#B9A779", 1.8, "dash"),
    ]
    for name, color, width, dash in groups:
        if name not in df.columns:
            continue
        mask = df[name].notna() & (df[name] > 0)
        fig.add_trace(
            go.Scatter(
                x=df.loc[mask, "date"],
                y=df.loc[mask, name],
                name=name,
                mode="lines",
                line=dict(color=color, width=width, dash=dash),
                hovertemplate=f"{name}: <b>%{{y:,.0f}}</b><br>%{{x|%b %Y}}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(
            text="Monthly International Visitor Arrivals by Market Group",
            font=dict(size=15),
        ),
        xaxis=dict(dtick="M1", tickformat="%b<br>%Y", ticklabelstep=2),
        yaxis=dict(tickformat=",", title="Monthly Arrivals"),
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
) -> dict:
    """Line chart: monthly YoY % for Total, ASEAN, G7, Other Markets vs prev year."""
    months = list(range(1, curr_month + 1))
    month_labels = [MONTH_ABBR[m] for m in months]

    curr_pre = precompute_monthly_avgs(df, curr_year, months)
    prev_pre = precompute_monthly_avgs(df, prev_year, months)

    asean_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "ASEAN"]
    g7_mkts = [m for m in INTERNATIONAL_MARKETS if MARKET_GROUP_MAP.get(m) == "G7"]
    other_mkts = [
        m
        for m in INTERNATIONAL_MARKETS
        if MARKET_GROUP_MAP.get(m) not in ("ASEAN", "G7")
    ]

    groups = [
        ("Total", INTERNATIONAL_MARKETS, "#111111", 2.8, "solid"),
        ("ASEAN", asean_mkts, "#2E7D5E", 2.0, "solid"),
        ("G7", g7_mkts, "#8B2942", 2.0, "solid"),
        ("Other Markets", other_mkts, "#B9A779", 1.8, "dash"),
    ]

    fig = go.Figure()
    for name, mkts, color, width, dash in groups:
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
                hovertemplate=f"{name}: <b>%{{y:+.1f}}%</b><extra></extra>",
                connectgaps=False,
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="#999", line_width=1)
    fig.update_layout(
        title=dict(
            text=f"{curr_year} vs {prev_year} Monthly YoY — Daily Avg Arrivals",
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
