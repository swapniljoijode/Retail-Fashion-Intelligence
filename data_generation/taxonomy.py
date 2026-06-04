"""
Hand-seeded fashion taxonomy.

All constants here make synthetic records read like a real UK fashion retailer
rather than random strings. Values are deliberately chosen, not generated.
"""

from __future__ import annotations

# ── Product taxonomy ──────────────────────────────────────────────────────────

CATEGORIES: dict[str, dict] = {
    "Tops": {
        "subcategories": ["T-Shirt", "Blouse", "Shirt", "Knit", "Vest"],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "price_range": (15.0, 85.0),
        "margin_range": (0.55, 0.72),
        "season_affinity": {"SS": 1.4, "AW": 0.8},
        "category_weight": 0.25,
    },
    "Bottoms": {
        "subcategories": ["Jeans", "Trousers", "Shorts", "Skirt", "Leggings"],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "price_range": (25.0, 120.0),
        "margin_range": (0.50, 0.68),
        "season_affinity": {"SS": 1.2, "AW": 1.0},
        "category_weight": 0.22,
    },
    "Dresses": {
        "subcategories": [
            "Mini Dress",
            "Midi Dress",
            "Maxi Dress",
            "Shirt Dress",
            "Wrap Dress",
        ],
        "sizes": ["XS", "S", "M", "L", "XL"],
        "price_range": (35.0, 180.0),
        "margin_range": (0.58, 0.75),
        "season_affinity": {"SS": 1.5, "AW": 0.7},
        "category_weight": 0.20,
    },
    "Outerwear": {
        "subcategories": ["Jacket", "Coat", "Blazer", "Puffer Jacket", "Trench Coat"],
        "sizes": ["XS", "S", "M", "L", "XL"],
        "price_range": (80.0, 350.0),
        "margin_range": (0.52, 0.70),
        "season_affinity": {"SS": 0.5, "AW": 1.8},
        "category_weight": 0.12,
    },
    "Footwear": {
        "subcategories": ["Sneakers", "Boots", "Heels", "Sandals", "Loafers"],
        "sizes": ["36", "37", "38", "39", "40", "41", "42"],
        "price_range": (40.0, 250.0),
        "margin_range": (0.45, 0.65),
        "season_affinity": {"SS": 1.1, "AW": 1.1},
        "category_weight": 0.12,
    },
    "Accessories": {
        "subcategories": ["Tote Bag", "Crossbody Bag", "Scarf", "Belt", "Hat"],
        "sizes": ["ONE SIZE"],
        "price_range": (20.0, 200.0),
        "margin_range": (0.60, 0.80),
        "season_affinity": {"SS": 1.0, "AW": 1.2},
        "category_weight": 0.09,
    },
}

BRANDS: list[str] = [
    "Arcwave",
    "Vellura",
    "Novafit",
    "Celeste & Co",
    "Brixton Lane",
    "Thornwood",
    "Solaire",
    "Mira Collective",
    "Hartley",
    "Plume Studio",
]

COLORS: list[str] = [
    "Black",
    "White",
    "Navy",
    "Grey",
    "Beige",
    "Camel",
    "Olive",
    "Burgundy",
    "Blush",
    "Sage",
    "Cobalt",
    "Terracotta",
    "Cream",
    "Charcoal",
    "Forest Green",
    "Rust",
    "Lilac",
    "Ecru",
]

BUYING_SEASONS: list[str] = ["SS24", "AW24", "SS25", "AW25"]

# Retail months belonging to each buying season
SEASON_MONTHS: dict[str, list[int]] = {
    "SS": [2, 3, 4, 5, 6, 7],
    "AW": [8, 9, 10, 11, 12, 1],
}

# Monthly demand multipliers relative to an average month.
# Encodes Black Friday (11), Christmas (12), season launches (3, 9),
# and the mid-August trough between seasons.
MONTHLY_DEMAND: dict[int, float] = {
    1: 0.85,
    2: 0.90,
    3: 1.20,
    4: 1.15,
    5: 1.05,
    6: 1.00,
    7: 1.10,
    8: 0.75,
    9: 1.15,
    10: 1.20,
    11: 1.40,
    12: 1.35,
}

# ── Store geography ───────────────────────────────────────────────────────────

UK_REGIONS: list[tuple[str, float]] = [
    ("Greater London", 0.25),
    ("South East", 0.12),
    ("North West", 0.12),
    ("Yorkshire", 0.09),
    ("West Midlands", 0.09),
    ("South West", 0.08),
    ("East of England", 0.08),
    ("East Midlands", 0.07),
    ("Scotland", 0.06),
    ("Wales", 0.04),
]

UK_CITIES_BY_REGION: dict[str, list[str]] = {
    "Greater London": ["London"],
    "South East": ["Brighton", "Oxford", "Southampton", "Reading", "Guildford"],
    "North West": ["Manchester", "Liverpool", "Preston", "Chester", "Blackpool"],
    "Yorkshire": ["Leeds", "Sheffield", "Bradford", "York", "Harrogate"],
    "West Midlands": ["Birmingham", "Coventry", "Wolverhampton", "Solihull"],
    "South West": ["Bristol", "Bath", "Exeter", "Plymouth", "Cheltenham"],
    "East of England": ["Cambridge", "Norwich", "Ipswich", "Luton", "Peterborough"],
    "East Midlands": ["Nottingham", "Leicester", "Derby", "Lincoln", "Northampton"],
    "Scotland": ["Glasgow", "Edinburgh", "Aberdeen", "Dundee"],
    "Wales": ["Cardiff", "Swansea", "Newport", "Wrexham"],
}

# Weighted so most stores are standard; one flagship and a couple of outlets
STORE_TYPE_POOL: list[str] = [
    "flagship",
    "standard",
    "standard",
    "standard",
    "standard",
    "outlet",
    "pop_up",
]

STORE_SQFT_RANGES: dict[str, tuple[int, int]] = {
    "flagship": (8_000, 20_000),
    "standard": (2_000, 6_000),
    "outlet": (3_000, 8_000),
    "pop_up": (500, 1_500),
}

# ── Customer attributes ───────────────────────────────────────────────────────

CUSTOMER_SEGMENTS: list[str] = ["budget", "mid_market", "premium", "luxury"]
SEGMENT_WEIGHTS: list[float] = [0.30, 0.40, 0.20, 0.10]

LOYALTY_TIERS: list[str] = ["bronze", "silver", "gold", "platinum"]
LOYALTY_WEIGHTS: list[float] = [0.50, 0.30, 0.15, 0.05]

ACQUISITION_CHANNELS: list[str] = [
    "organic",
    "paid_search",
    "social",
    "email",
    "referral",
    "in_store",
]
ACQUISITION_WEIGHTS: list[float] = [0.25, 0.20, 0.25, 0.15, 0.10, 0.05]

# ── Channel seed (7 rows — mirrors dim_channel in the data model) ─────────────

CHANNEL_SEED: list[dict] = [
    {
        "channel_id": "CH01",
        "channel_name": "Own Website",
        "channel_type": "digital",
        "platform": "own_website",
    },
    {
        "channel_id": "CH02",
        "channel_name": "Instagram Shop",
        "channel_type": "digital",
        "platform": "instagram_shop",
    },
    {
        "channel_id": "CH03",
        "channel_name": "Amazon",
        "channel_type": "marketplace",
        "platform": "amazon",
    },
    {
        "channel_id": "CH04",
        "channel_name": "Flagship Store",
        "channel_type": "physical",
        "platform": "own_store",
    },
    {
        "channel_id": "CH05",
        "channel_name": "Standard Store",
        "channel_type": "physical",
        "platform": "own_store",
    },
    {
        "channel_id": "CH06",
        "channel_name": "Outlet Store",
        "channel_type": "physical",
        "platform": "outlet_store",
    },
    {
        "channel_id": "CH07",
        "channel_name": "Pop-Up",
        "channel_type": "physical",
        "platform": "pop_up",
    },
]

# ── Promotions ────────────────────────────────────────────────────────────────

# (name, type, peak_month, discount_pct | None, duration_days)
NAMED_PROMOTIONS: list[tuple] = [
    ("Spring Sale", "pct_off", 3, 0.20, 14),
    ("Summer Sale", "pct_off", 7, 0.30, 21),
    ("End of Season AW", "pct_off", 1, 0.40, 28),
    ("End of Season SS", "pct_off", 8, 0.35, 21),
    ("Black Friday", "pct_off", 11, 0.25, 4),
    ("Cyber Monday", "pct_off", 11, 0.20, 2),
    ("Boxing Day", "pct_off", 12, 0.30, 7),
    ("New Year Sale", "pct_off", 1, 0.25, 14),
    ("Bank Holiday", "pct_off", 5, 0.15, 3),
    ("Student Discount", "pct_off", 9, 0.10, 30),
    ("Free Shipping Week", "free_shipping", 4, None, 7),
    ("Buy 2 Get 1", "buy_x_get_y", 6, 0.33, 10),
    ("Bundle Deal", "bundle", 10, 0.15, 14),
    ("Loyalty Reward", "pct_off", 12, 0.15, 30),
    ("Flash Sale", "pct_off", 2, 0.20, 2),
    ("Referral Bonus", "pct_off", 7, 0.10, 30),
    ("Birthday Month", "pct_off", 6, 0.15, 30),
    ("VIP Preview", "pct_off", 9, 0.20, 5),
    ("Clearance", "pct_off", 8, 0.50, 28),
    ("Pay Day Deal", "pct_off", 1, 0.20, 3),
]

# ── Returns ───────────────────────────────────────────────────────────────────

RETURN_REASONS: list[str] = [
    "size",
    "quality",
    "changed_mind",
    "damaged",
    "wrong_item",
    "late_delivery",
]
RETURN_REASON_WEIGHTS: list[float] = [0.35, 0.20, 0.25, 0.10, 0.05, 0.05]

# Return rate (fraction of units sold) by category
RETURN_RATES: dict[str, float] = {
    "Tops": 0.12,
    "Bottoms": 0.18,
    "Dresses": 0.20,
    "Outerwear": 0.10,
    "Footwear": 0.22,
    "Accessories": 0.06,
}

# ── Web events ────────────────────────────────────────────────────────────────

DEVICE_TYPES: list[str] = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS: list[float] = [0.58, 0.35, 0.07]

# Funnel stage drop-off probabilities (cumulative: share of sessions reaching each stage)
FUNNEL_REACH: dict[str, float] = {
    "page_view": 1.00,
    "product_view": 0.65,
    "add_to_cart": 0.28,
    "checkout_start": 0.12,
    "purchase": 0.05,
    "abandon_cart": 0.00,  # derived: add_to_cart but no purchase
}
