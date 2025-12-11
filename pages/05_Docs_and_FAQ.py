import streamlit as st

from gex_app.ui.components import apply_base_theme


apply_base_theme()


st.title("Docs & FAQ")

st.markdown(
    """
    Here you'll find:
    - An explanation of GEX and how this tool computes it.
    - How to interpret zero gamma, walls, and net GEX.
    - Typical workflows for intraday vs swing trading.
    """
)
