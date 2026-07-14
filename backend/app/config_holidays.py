"""Holiday calendar constants (ported from Streamlit app)."""
from __future__ import annotations

LUNAR_LABELS = {
    -3: "廿七",
    -2: "廿八",
    -1: "除夕",
    0: "初一",
    1: "初二",
    2: "初三",
    3: "初四",
    4: "初五",
    5: "初六",
    6: "初七",
    7: "初八",
    8: "初九",
    9: "初十",
}

CONTEXT_TO_REGION = {"Mainland": "CN", "CN": "CN", "HK": "HK"}
CONTEXT_DIRECTION = {"CN": "inbound", "Mainland": "inbound", "HK": "outbound"}

HOLIDAY_VARIANTS = ("Official Days", "Extended Leave Days")
VARIANT_TO_KEY = {
    "Official Days": "official",
    "Extended Leave Days": "extended_al",
    "official": "official",
    "extended_al": "extended_al",
}

HOLIDAY_DISPLAY = {
    "CNY": "CNY (春节)",
    "Qingming": "Qingming (清明)",
    "Labour_Day": "Labour Day (劳动节)",
    "Dragon_Boat": "Dragon Boat (端午)",
    "Mid_Autumn": "Mid-Autumn (中秋)",
    "National_Day": "National Day (国庆)",
    "Easter": "Easter (复活节)",
    "Christmas": "Christmas (圣诞)",
}

HOLIDAYS_BY_REGION = {
    "CN": [
        "CNY",
        "Qingming",
        "Labour_Day",
        "Dragon_Boat",
        "Mid_Autumn",
        "National_Day",
    ],
    "HK": [
        "CNY",
        "Easter",
        "Labour_Day",
        "Dragon_Boat",
        "National_Day",
        "Christmas",
    ],
}

CNY_FIRST_DAY = {2024: "2024-02-10", 2025: "2025-01-29", 2026: "2026-02-17"}

HOLIDAY_MARGIN_OVERVIEW = dict(l=50, r=20, t=100, b=65)
HOLIDAY_MARGIN_PANEL = dict(l=50, r=20, t=75, b=60)
HOLIDAY_MARGIN_BAR = dict(l=20, r=20, t=85, b=60)

HOLIDAY_INBOUND_SEGMENTS = ("All tourists", "Mainland", "International")
HOLIDAY_OUTBOUND_SEGMENTS = ("All", "HK Residents", "Tourists")

HOLIDAY_PERIODS: dict = {
    "CN": {
        2024: {
            "CNY": {"official": {"start": "2024-02-10", "end": "2024-02-17"}},
            "Qingming": {"official": {"start": "2024-04-04", "end": "2024-04-06"}},
            "Labour_Day": {"official": {"start": "2024-05-01", "end": "2024-05-05"}},
            "Dragon_Boat": {"official": {"start": "2024-06-08", "end": "2024-06-10"}},
            "Mid_Autumn": {"official": {"start": "2024-09-15", "end": "2024-09-17"}},
            "National_Day": {"official": {"start": "2024-10-01", "end": "2024-10-07"}},
        },
        2025: {
            "CNY": {"official": {"start": "2025-01-28", "end": "2025-02-04"}},
            "Qingming": {"official": {"start": "2025-04-04", "end": "2025-04-06"}},
            "Labour_Day": {"official": {"start": "2025-05-01", "end": "2025-05-05"}},
            "Dragon_Boat": {"official": {"start": "2025-05-31", "end": "2025-06-02"}},
            "Mid_Autumn": {"official": {"start": "2025-10-06", "end": "2025-10-08"}},
            "National_Day": {"official": {"start": "2025-10-01", "end": "2025-10-08"}},
        },
        2026: {
            "CNY": {"official": {"start": "2026-02-15", "end": "2026-02-23"}},
            "Qingming": {"official": {"start": "2026-04-04", "end": "2026-04-06"}},
            "Labour_Day": {"official": {"start": "2026-05-01", "end": "2026-05-05"}},
            "Dragon_Boat": {"official": {"start": "2026-06-19", "end": "2026-06-21"}},
            "Mid_Autumn": {"official": {"start": "2026-09-25", "end": "2026-09-27"}},
            "National_Day": {"official": {"start": "2026-10-01", "end": "2026-10-07"}},
        },
    },
    "HK": {
        2024: {
            "CNY": {
                "official": {"start": "2024-02-10", "end": "2024-02-13"},
                "extended_al": {"start": "2024-02-10", "end": "2024-02-13"},
            },
            "Easter": {
                "official": {"start": "2024-03-29", "end": "2024-04-01"},
                "extended_al": {"start": "2024-03-29", "end": "2024-04-01"},
            },
            "Labour_Day": {
                "official": {"start": "2024-05-01", "end": "2024-05-01"},
                "extended_al": {"start": "2024-05-01", "end": "2024-05-01"},
            },
            "Dragon_Boat": {
                "official": {"start": "2024-06-10", "end": "2024-06-10"},
                "extended_al": {"start": "2024-06-08", "end": "2024-06-10"},
            },
            "National_Day": {
                "official": {"start": "2024-10-01", "end": "2024-10-01"},
                "extended_al": {"start": "2024-09-28", "end": "2024-10-01"},
            },
            "Christmas": {
                "official": {"start": "2024-12-25", "end": "2024-12-26"},
                "extended_al": {"start": "2024-12-25", "end": "2024-12-29"},
            },
        },
        2025: {
            "CNY": {
                "official": {"start": "2025-01-29", "end": "2025-01-31"},
                "extended_al": {"start": "2025-01-29", "end": "2025-02-02"},
            },
            "Easter": {
                "official": {"start": "2025-04-18", "end": "2025-04-21"},
                "extended_al": {"start": "2025-04-18", "end": "2025-04-21"},
            },
            "Labour_Day": {
                "official": {"start": "2025-05-01", "end": "2025-05-01"},
                "extended_al": {"start": "2025-05-01", "end": "2025-05-04"},
            },
            "Dragon_Boat": {
                "official": {"start": "2025-05-31", "end": "2025-05-31"},
                "extended_al": {"start": "2025-05-31", "end": "2025-06-01"},
            },
            "National_Day": {
                "official": {"start": "2025-10-01", "end": "2025-10-01"},
                "extended_al": {"start": "2025-10-01", "end": "2025-10-01"},
            },
            "Christmas": {
                "official": {"start": "2025-12-25", "end": "2025-12-26"},
                "extended_al": {"start": "2025-12-25", "end": "2025-12-28"},
            },
        },
        2026: {
            "CNY": {
                "official": {"start": "2026-02-17", "end": "2026-02-19"},
                "extended_al": {"start": "2026-02-14", "end": "2026-02-22"},
            },
            "Easter": {
                "official": {"start": "2026-04-03", "end": "2026-04-06"},
                "extended_al": {"start": "2026-04-03", "end": "2026-04-06"},
            },
            "Labour_Day": {
                "official": {"start": "2026-05-01", "end": "2026-05-01"},
                "extended_al": {"start": "2026-05-01", "end": "2026-05-03"},
            },
            "Dragon_Boat": {
                "official": {"start": "2026-06-19", "end": "2026-06-19"},
                "extended_al": {"start": "2026-06-19", "end": "2026-06-21"},
            },
            "National_Day": {
                "official": {"start": "2026-10-01", "end": "2026-10-01"},
                "extended_al": {"start": "2026-10-01", "end": "2026-10-04"},
            },
            "Christmas": {
                "official": {"start": "2026-12-25", "end": "2026-12-26"},
                "extended_al": {"start": "2026-12-25", "end": "2026-12-27"},
            },
        },
    },
}

CP_COLORS = {
    "Lok Ma Chau Spur Line": "#0F6B55",
    "Express Rail Link West Kowloon": "#2B8A8E",
    "Lo Wu": "#66B8B0",
    "Shenzhen Bay": "#A0720A",
    "Heung Yuen Wai": "#CC8800",
    "Hong Kong-Zhuhai-Macao Bridge": "#CD853F",
    "Lok Ma Chau": "#E8C547",
    "Airport": "#CF9E9A",
    "Others": "#A6A6A6",
}

CP_DISPLAY_NAME = {
    "Lok Ma Chau": "Lok Ma Chau (皇岗口岸)",
}

CP_TYPE_MAP = {
    "Lok Ma Chau Spur Line": "rail",
    "Express Rail Link West Kowloon": "rail",
    "Lo Wu": "rail",
    "Shenzhen Bay": "car",
    "Heung Yuen Wai": "car",
    "Hong Kong-Zhuhai-Macao Bridge": "car",
    "Lok Ma Chau": "car",
    "Airport": "air",
}

TOP_CONTROL_POINTS = [
    "Lok Ma Chau Spur Line",
    "Express Rail Link West Kowloon",
    "Lo Wu",
    "Shenzhen Bay",
    "Heung Yuen Wai",
    "Hong Kong-Zhuhai-Macao Bridge",
    "Lok Ma Chau",
    "Airport",
]
