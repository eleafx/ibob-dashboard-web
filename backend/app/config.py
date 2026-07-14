"""Shared constants for IBOB dashboard API (ported from Streamlit app)."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

CACHE_TTL_SECONDS = 604800  # 7 days

# Local-first data sources (standalone — no dependency on Streamlit repo)
DAILY_CSV_PATH = DATA_DIR / "daily_passenger_traffic.csv"
INTL_CSV_PATH = DATA_DIR / "international_visitors.csv"
LAST_UPDATED_PATH = DATA_DIR / "last_updated.txt"

GOV_DATA_URL = (
    "https://www.immd.gov.hk/opendata/eng/transport/immigration_clearance/"
    "statistics_on_daily_passenger_traffic.csv"
)

# Comma-separated origins; empty = same-origin / default local Vite ports
_CORS_DEFAULT = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:3000,http://127.0.0.1:3000"
)


def cors_allow_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOW_ORIGINS", _CORS_DEFAULT).strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def serve_frontend() -> bool:
    """Mount built React app when frontend/dist exists (production / Docker)."""
    flag = os.environ.get("SERVE_FRONTEND", "").strip().lower()
    if flag in ("0", "false", "no"):
        return False
    if flag in ("1", "true", "yes"):
        return FRONTEND_DIST.is_dir()
    return FRONTEND_DIST.is_dir()


_YEAR_PALETTE = ["#CF9E9A", "#B9A779", "#3A7976"]  # oldest → latest
BASELINE_COLOR = "#A6A6A6"
BASELINE_YEAR = 2018

INBOUND_2018 = {
    1: 172050, 2: 188606, 3: 161133, 4: 176720, 5: 159774, 6: 158059,
    7: 176168, 8: 190192, 9: 157285, 10: 189823, 11: 199834, 12: 212460,
}
OUTBOUND_2018 = {
    1: 236056, 2: 236056, 3: 269689, 4: 252022, 5: 247218, 6: 257566,
    7: 250747, 8: 245103, 9: 240199, 10: 249645, 11: 263862, 12: 278927,
}
MAINLAND_2018 = {
    1: 132097, 2: 156357, 3: 117796, 4: 134413, 5: 122709, 6: 120557,
    7: 141419, 8: 154956, 9: 123129, 10: 149308, 11: 153770, 12: 164596,
}
INTERNATIONAL_2018 = {k: INBOUND_2018[k] - MAINLAND_2018[k] for k in INBOUND_2018}

INTERNATIONAL_MARKETS = [
    "Australia", "Canada", "France", "Germany", "India", "Indonesia",
    "Japan", "Macau SAR", "Malaysia", "Netherlands", "Philippines", "Russia",
    "Singapore", "South Korea", "Taiwan", "Thailand", "United Kingdom",
    "USA", "Vietnam", "Middle East",
]

MARKET_GROUP_MAP = {
    "Australia": "Australia",
    "Canada": "G7",
    "France": "G7",
    "Germany": "G7",
    "India": "India",
    "Indonesia": "ASEAN",
    "Japan": "G7",
    "Macau SAR": "Greater China",
    "Mainland": "Mainland China",
    "Malaysia": "ASEAN",
    "Netherlands": "Netherlands",
    "Philippines": "ASEAN",
    "Russia": "Russia",
    "Singapore": "ASEAN",
    "South Korea": "Other Markets",
    "Taiwan": "Greater China",
    "Thailand": "ASEAN",
    "United Kingdom": "G7",
    "USA": "G7",
    "Vietnam": "ASEAN",
    "Middle East": "Middle East",
}

PPT_SUMMARY_ROWS = [
    ("Greater China", "Taiwan", ["Taiwan"]),
    ("Greater China", "Macau SAR", ["Macau SAR"]),
    ("ASEAN", "Philippines", ["Philippines"]),
    ("ASEAN", "Thailand", ["Thailand"]),
    ("ASEAN", "Indonesia", ["Indonesia"]),
    ("ASEAN", "Singapore", ["Singapore"]),
    ("ASEAN", "Malaysia", ["Malaysia"]),
    ("ASEAN", "Vietnam", ["Vietnam"]),
    ("ASEAN", "ASEAN Total", "asean_total"),
    ("G7", "USA", ["USA"]),
    ("G7", "Japan", ["Japan"]),
    ("G7", "United Kingdom", ["United Kingdom"]),
    ("G7", "Canada", ["Canada"]),
    ("G7", "France", ["France"]),
    ("G7", "Germany", ["Germany"]),
    ("G7", "G7 Total", "g7_total"),
    ("Other Markets", "South Korea", ["South Korea"]),
    ("Other Markets", "Australia", ["Australia"]),
    ("Other Markets", "India", ["India"]),
    ("Other Markets", "Middle East", ["Middle East"]),
    ("Other Markets", "Russia", ["Russia"]),
    ("Other Markets", "Netherlands", ["Netherlands"]),
    ("", "Total", "grand_total"),
]

ASEAN_MARKETS = {m for m, g in MARKET_GROUP_MAP.items() if g == "ASEAN"}
G7_MARKETS = {m for m, g in MARKET_GROUP_MAP.items() if g == "G7"}
PPT_LISTED_MARKETS = (
    {
        "South Korea",
        "Taiwan",
        "Macau SAR",
        "Australia",
        "Middle East",
        "India",
        "Russia",
        "Netherlands",
    }
    | ASEAN_MARKETS
    | G7_MARKETS
)

MONTH_ABBR = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

MONTH_LABELS = [
    "Jan&Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def get_year_colors(years: list[int]) -> dict[str, str]:
    """Assign colors by position; latest year gets the bold palette color."""
    return {
        str(yr): _YEAR_PALETTE[i] if i < len(_YEAR_PALETTE) else "#333"
        for i, yr in enumerate(years)
    }
