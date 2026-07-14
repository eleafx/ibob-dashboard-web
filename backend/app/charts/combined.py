"""Combined Plotly figure: line chart + table traces (ported from Streamlit)."""
from __future__ import annotations

import plotly.graph_objects as go

from backend.app.config import BASELINE_COLOR, MONTH_LABELS, get_year_colors


def make_combined_figure(
    title: str,
    series_dict: dict[str, list[float | None]] | None = None,
    table1_rows: list[list[str]] | None = None,
    table1_header: list[str] | None = None,
    table2_rows: list[list[str]] | None = None,
    table2_header: list[str] | None = None,
    table3_rows: list[list[str]] | None = None,
    table3_header: list[str] | None = None,
    table3_is_yoy: bool = False,
    y_min: float = 0,
    y_max: float | None = None,
    extra_height: int = 0,
    colors: dict[str, str] | None = None,
    current_year: str | None = None,
) -> dict:
    """Return Plotly JSON with optional chart + stacked table traces."""
    x_positions = list(range(11))
    fig = go.Figure()
    has_chart = series_dict is not None and len(series_dict) > 0

    if colors is None and has_chart:
        years = [int(y) for y in series_dict if str(y).isdigit()]
        colors = {**get_year_colors(years), "2018": BASELINE_COLOR}
    if colors is None:
        colors = {}
    if current_year is None and has_chart:
        numeric = [int(y) for y in series_dict if str(y).isdigit()]
        current_year = str(max(numeric)) if numeric else None

    if has_chart:
        for yr, data in series_dict.items():
            valid = [d if d else None for d in data]
            fig.add_trace(
                go.Scatter(
                    x=x_positions,
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
                    hovertemplate="%{customdata}<br>"
                    + yr
                    + ": <b>%{y:,.0f}</b><extra></extra>",
                    customdata=MONTH_LABELS,
                    connectgaps=False,
                )
            )

    num_tables = (
        (1 if table1_rows else 0)
        + (1 if table2_rows else 0)
        + (1 if table3_rows else 0)
    )

    if num_tables == 0:
        title_font = 17 if has_chart else 14
        fig.update_layout(
            title=dict(text=title, font=dict(size=title_font)),
            xaxis=dict(
                domain=[0, 1],
                range=[-0.5, 10.5],
                tickmode="array",
                tickvals=x_positions,
                ticktext=MONTH_LABELS,
            ),
            yaxis=dict(tickformat=",", range=[y_min, y_max]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=50, b=35),
            height=380,
            template="plotly_white",
            hovermode="x unified",
        )
        return fig.to_plotly_json()

    header_px = 35
    row_px = 30
    gap_px = 8
    chart_px = 380 if has_chart else 0
    chart_table_gap_px = 32 if has_chart else 0

    tables: list[tuple[list[list[str]], list[str] | None, bool]] = []
    if table3_rows:
        tables.append((table3_rows, table3_header, table3_is_yoy))
    if table2_rows:
        tables.append((table2_rows, table2_header, False))
    if table1_rows:
        tables.append((table1_rows, table1_header, True))

    table_px = sum(header_px + len(t[0]) * row_px for t in tables)
    inter_table_gap_px = gap_px * max(len(tables) - 1, 0)
    chart_table_gap = chart_table_gap_px if has_chart and tables else 0
    total_px = chart_px + table_px + inter_table_gap_px + chart_table_gap
    fig_height = total_px + 80 + extra_height

    table_domains: list[
        tuple[list[list[str]], list[str] | None, bool, list[float]]
    ] = []
    cursor_px = 0.0
    for t_rows, t_header, t_is_yoy in tables:
        t_px = header_px + len(t_rows) * row_px
        table_domains.append(
            (
                t_rows,
                t_header,
                t_is_yoy,
                [
                    round(cursor_px / total_px, 4),
                    round((cursor_px + t_px) / total_px, 4),
                ],
            )
        )
        cursor_px += t_px + gap_px

    chart_domain = None
    if has_chart:
        top_table_top_px = cursor_px - gap_px
        chart_start_px = top_table_top_px + chart_table_gap
        chart_domain = [round(chart_start_px / total_px, 4), 1.0]

    def _build_table(
        table_rows: list[list[str]],
        table_header: list[str] | None,
        domain_y: list[float],
        is_yoy: bool = False,
    ) -> None:
        if not table_rows:
            return
        columns = list(zip(*table_rows))
        n_rows = len(table_rows)
        n_cols = len(columns)

        font_colors: list[list[str]] = []
        for col_idx, col in enumerate(columns):
            if col_idx == 0:
                font_colors.append(["#111"] * len(col))
            else:
                col_colors: list[str] = []
                for val in col:
                    if is_yoy and isinstance(val, str) and val != "—":
                        try:
                            num = float(val.replace("%", "").replace("+", ""))
                            if num > 0:
                                col_colors.append("#2e7d32")
                            elif num < 0:
                                col_colors.append("#8b2942")
                            else:
                                col_colors.append("#111")
                        except ValueError:
                            col_colors.append("#111")
                    else:
                        col_colors.append("#111")
                font_colors.append(col_colors)

        row_fills: list[str] = []
        for i in range(n_rows):
            label = str(table_rows[i][0]).lower()
            if "overall" in label or " vs " in label:
                row_fills.append("#f0f0f0")
            else:
                row_fills.append("#ffffff")
        fill_colors = [[row_fills[i] for i in range(n_rows)] for _ in range(n_cols)]

        if n_cols == 12:
            columnwidth = [16] + [11] * 11
        elif n_cols == 13:
            columnwidth = [14] + [10] * 11 + [10]
        elif n_cols == 4:
            columnwidth = [16] + [13] * 3
        else:
            columnwidth = None

        fig.add_trace(
            go.Table(
                header=dict(
                    values=table_header or [""] * n_cols,
                    fill=dict(color="#B9A779"),
                    font=dict(color="white", size=12, family="Arial"),
                    align="center",
                    line=dict(color="#d4d4d4", width=1),
                ),
                cells=dict(
                    values=columns,
                    font=dict(color=font_colors, size=11, family="Arial"),
                    fill=dict(color=fill_colors),
                    align=["left"] + ["center"] * (n_cols - 1),
                    line=dict(color="#d4d4d4", width=1),
                    height=25,
                ),
                domain=dict(x=[0, 1], y=domain_y),
                columnwidth=columnwidth,
            )
        )

    for t_rows, t_header, t_is_yoy, t_domain in table_domains:
        _build_table(t_rows, t_header, t_domain, is_yoy=t_is_yoy)

    if has_chart:
        fig.update_layout(
            title=dict(text=title, font=dict(size=13)),
            xaxis=dict(
                domain=[0, 1],
                range=[-0.5, 10.5],
                tickmode="array",
                tickvals=x_positions,
                ticktext=MONTH_LABELS,
            ),
            yaxis=dict(domain=chart_domain, tickformat=",", range=[y_min, y_max]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=60, b=35),
            height=fig_height,
            template="plotly_white",
            hovermode="x unified",
        )
    else:
        fig.update_layout(
            title=dict(text=title, font=dict(size=14)),
            margin=dict(l=10, r=10, t=45, b=20),
            height=fig_height,
            template="plotly_white",
        )

    return fig.to_plotly_json()
