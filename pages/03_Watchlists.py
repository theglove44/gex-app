import streamlit as st

from gex_app.ui.components import apply_base_theme

apply_base_theme()


st.title("Watchlists")

st.info(
    "This page will manage named watchlists (e.g. 'Index ETFs', 'Tech Names') "
    "and let you pick them as scan universes for the GEX dashboard."
)
