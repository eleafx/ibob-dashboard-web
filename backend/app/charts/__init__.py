"""Shared chart helpers."""
from __future__ import annotations

import json

import plotly.graph_objects as go


def fig_to_json(fig: go.Figure) -> dict:
    """Convert Plotly Figure to JSON-serializable dict.

    Uses a JSON roundtrip because fig.to_plotly_json() can leak numpy arrays
    (e.g. datetime64 in trace x/y) on some Plotly versions.
    """
    return json.loads(fig.to_json())
