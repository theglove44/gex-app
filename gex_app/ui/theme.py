"""
Theme configuration and styling for GEX Tool.
"""

from pathlib import Path

import streamlit as st

THEME_COLORS = {
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_card": "#21262d",
    "bg_elevated": "#30363d",
    "text_primary": "#f0f6fc",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    "cyan": "#00d4ff",
    "magenta": "#ff006e",
    "lime": "#39ff14",
    "orange": "#ff9500",
    "purple": "#bf5af2",
    "yellow": "#ffd60a",
    "call_gex": "#00ff88",
    "put_gex": "#ff3366",
    "spot_line": "#00d4ff",
    "zero_gamma": "#ffd60a",
}


def apply_theme() -> None:
    """Inject the base dark theme CSS."""
    css_path = Path(__file__).resolve().parents[2] / "assets" / "dark_theme.css"
    if not css_path.exists():
        st.warning("Dark theme CSS file not found.")
        return
    st.markdown(
        f"<style>{{{Path(css_path).read_text()}}}</style>", unsafe_allow_html=True
    )


def get_plotly_dark_layout() -> dict:
    """Return common dark theme layout settings for Plotly charts."""
    c = THEME_COLORS
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(13,17,23,0.8)",
        "font": {"family": "system-ui", "color": c["text_primary"]},
        "xaxis": {"gridcolor": "rgba(48,54,61,0.5)", "zerolinecolor": c["bg_elevated"]},
        "yaxis": {
            "gridcolor": "rgba(48,54,61,0.5)",
            "zerolinecolor": c["text_muted"],
            "zerolinewidth": 2,
        },
        "margin": {"l": 60, "r": 40, "t": 80, "b": 60},
    }
