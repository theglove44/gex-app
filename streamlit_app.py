import streamlit as st

from gex_app.ui.components import apply_base_theme

st.set_page_config(
    page_title="GEX Tool",
    page_icon="📊",
    layout="wide",
)

apply_base_theme()

st.title("GEX Tool")
st.write("Welcome to the GEX Tool.")

st.info("👈 Use the sidebar to navigate, or click below to open the Dashboard.")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.page_link(
        "pages/01_GEX_Dashboard.py",
        label="Open GEX Dashboard",
        icon="📊",
        use_container_width=True,
    )
with col2:
    st.page_link(
        "pages/02_Universe_Scanner.py",
        label="Open Universe Scanner",
        icon="🔭",
        use_container_width=True,
    )
