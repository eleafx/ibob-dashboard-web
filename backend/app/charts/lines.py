"""Build Plotly figure dicts for monthly trend charts."""
from __future__ import annotations

import plotly.graph_objects as go

from backend.app.charts import fig_to_json
from backend.app.config import BASELINE_COLOR, MONTH_LABELS, get_year_colors


def make_line_figure(
    title: str,
    series_dict: dict[str, list[float | None]],
    colors: dict[str, str] | None = None,
    y_min: float = 0,
    y_max: float | None = None,
    current_year: str | None = None,
) -> dict:
    """Port of Streamlit make_chart — returns Plotly JSON-serializable figure."""
    if colors is None:
        years = [int(y) for y in series_dict if y.isdigit()]
        colors = {**get_year_colors(years), "2018": BASELINE_COLOR}
    if current_year is None:
        numeric = [int(y) for y in series_dict if y.isdigit()]
        current_year = str(max(numeric)) if numeric else None

    fig = go.Figure()
    for yr, data in series_dict.items():
        valid = [d if d else None for d in data]
        fig.add_trace(
            go.Scatter(
                x=MONTH_LABELS,
                y=valid,
                name=yr,
                mode="lines",
                line=dict(
                    color=colors.get(yr, "#333"),
                    width=3 if yr == current_year else 2.5,
                    dash="dash" if yr == "2018" else "solid",
                    shape="spline",
                    smoothing=1.0,
                ),
                hovertemplate="%{x}<br>" + yr + ": <b>%{customdata}K</b><extra></extra>",
                customdata=[int(round(v / 1000)) if v else 0 for v in valid],
                connectgaps=False,
            )
        )
    fig.update_layout(
        title=dict(text=title, font=dict(size=17)),
        yaxis=dict(tickformat=",", range=[y_min, y_max] if y_max else [y_min, None]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=40),
        height=380,
        template="plotly_white",
        hovermode="x unified",
    )
    return fig_to_json(fig)
