import streamlit as st

from gex_app.ui.components import apply_base_theme


apply_base_theme()


st.title("Settings")

st.info(
    "This page will let you configure defaults (e.g. default symbol, "
    "default DTE window, default price range, theme options)."
)
