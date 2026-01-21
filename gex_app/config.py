"""
Configuration module for GEX Tool.
Centralized configuration for colors, UI defaults, and parameter ranges.
"""

# === DARK THEME COLOR PALETTE ===
COLORS = {
    # Background colors
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_card": "#21262d",
    "bg_elevated": "#30363d",
    # Text colors
    "text_primary": "#f0f6fc",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    # Accent colors (vibrant neon)
    "cyan": "#00d4ff",
    "magenta": "#ff006e",
    "lime": "#39ff14",
    "orange": "#ff9500",
    "purple": "#bf5af2",
    "yellow": "#ffd60a",
    # GEX specific
    "call_gex": "#00ff88",  # Bright green for calls
    "put_gex": "#ff3366",  # Bright red/pink for puts
    "spot_line": "#00d4ff",  # Cyan for spot price
    "zero_gamma": "#ffd60a",  # Yellow for zero gamma
    # Gradients (for CSS)
    "gradient_green": "linear-gradient(180deg, #00ff88 0%, #00cc6a 100%)",
    "gradient_red": "linear-gradient(180deg, #ff3366 0%, #cc2952 100%)",
    "gradient_card": "linear-gradient(135deg, rgba(0,212,255,0.1) 0%, rgba(191,90,242,0.1) 100%)",
}

# === UI DEFAULTS AND PARAMETER RANGES ===

# Symbol options
DEFAULT_SYMBOLS = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "AAPL",
    "TSLA",
    "NVDA",
    "AMD",
    "AMZN",
    "MSFT",
]
DEFAULT_SYMBOL = "SPY"

# DTE (Days to Expiration) slider range
DTE_MIN = 1
DTE_MAX = 60
DTE_DEFAULT = 30

# Strike range (as % from spot) slider range
STRIKE_RANGE_MIN = 5
STRIKE_RANGE_MAX = 50
STRIKE_RANGE_DEFAULT = 20

# Major GEX threshold (for filtering significant gamma walls)
MAJOR_THRESHOLD_MIN = 10
MAJOR_THRESHOLD_MAX = 500
MAJOR_THRESHOLD_DEFAULT = 50

# Data collection time (seconds)
DATA_WAIT_MIN = 2
DATA_WAIT_MAX = 10
DATA_WAIT_DEFAULT = 5

# Auto-update interval
AUTO_UPDATE_INTERVAL = 60  # seconds

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "GEX Tool - Gamma Exposure Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# App version
APP_VERSION = "1.2.0"
