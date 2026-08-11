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
    csv_series: dict[str, list[float | None]] | None = None,
) -> dict:
    """Port of Streamlit make_chart — returns Plotly JSON-serializable figure.

    series_dict: display values (incomplete months already nulled).
    csv_series: optional full values incl. provisional incomplete months for CSV.
    """
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

    # CSV includes provisional incomplete-month values when provided
    export_series = csv_series or series_dict
    csv_headers = ["Month"] + list(export_series.keys())
    csv_rows: list[list] = []
    for i, month in enumerate(MONTH_LABELS):
        row: list = [month]
        for yr, data in export_series.items():
            val = data[i] if i < len(data) else None
            display_val = series_dict.get(yr, [None] * 11)
            is_provisional = (
                yr == current_year
                and val is not None
                and (i >= len(display_val) or display_val[i] is None)
            )
            if val is None:
                row.append("")
            elif is_provisional:
                row.append(f"{round(val, 1)} (provisional)")
            else:
                row.append(round(val, 1))
        csv_rows.append(row)

    fig.update_layout(
        title=dict(text=title, font=dict(size=17)),
        yaxis=dict(tickformat=",", range=[y_min, y_max] if y_max else [y_min, None]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=40),
        height=380,
        template="plotly_white",
        hovermode="x unified",
        meta={"csv_export": {"headers": csv_headers, "rows": csv_rows}},
    )
    return fig_to_json(fig)
