import streamlit as st

from gex_app.ui.components import apply_base_theme


st.set_page_config(
    page_title="GEX Tool",
    page_icon="📊",
    layout="wide",
)

apply_base_theme()

st.title("GEX Tool")
st.write(
    "Welcome to the GEX Tool. Use the sidebar to open the **GEX Dashboard** "
    "and other pages."
)
