"""
GEX Dashboard - Main page for viewing Gamma Exposure profiles.

This page renders the full GEX dashboard experience, including controls,
progress indicators, KPI cards, tables, and heatmaps.
"""

import time
from datetime import datetime

import streamlit as st

from gex_app.core.gex_core import create_session, get_credentials, run_gex_calculation
from gex_app import config
from gex_app.ui.components import (
    apply_base_theme,
    interpolate_gex_at_spot,
    render_gex_heatmap,
    render_gex_table,
    render_metric_card,
)
from gex_app.layouts import Layout, load_layouts, upsert_layout, delete_layout


st.set_page_config(**config.PAGE_CONFIG)
apply_base_theme()


def _init_state():
    """Initialize session state with default values from config."""
    if "symbol" not in st.session_state:
        st.session_state["symbol"] = config.DEFAULT_SYMBOLS[0]
    if "max_dte" not in st.session_state:
        st.session_state["max_dte"] = config.DTE_DEFAULT
    if "strike_range_pct" not in st.session_state:
        st.session_state["strike_range_pct"] = config.STRIKE_RANGE_DEFAULT
    if "major_threshold" not in st.session_state:
        st.session_state["major_threshold"] = config.MAJOR_THRESHOLD_DEFAULT
    if "data_wait" not in st.session_state:
        st.session_state["data_wait"] = config.DATA_WAIT_DEFAULT
    if "auto_update" not in st.session_state:
        st.session_state["auto_update"] = False


def validate_symbol(symbol: str) -> tuple[bool, str]:
    """
    Validate custom symbol input.

    Returns:
        (is_valid, error_message)
    """

    if not symbol:
        return False, "Symbol cannot be empty"

    cleaned = symbol.strip().upper()

    if len(cleaned) < 1 or len(cleaned) > 10:
        return False, "Symbol must be 1-10 characters"

    if not cleaned.replace(".", "").replace("-", "").isalnum():
        return False, "Symbol must contain only letters, numbers, dots, and dashes"

    return True, ""


@st.fragment
def render_gex_section_manual(symbol, max_dte, strike_range_pct, major_threshold, data_wait, auto_update):
    """
    Manual rendering fragment (no auto-update).
    """

    _render_gex_content(symbol, max_dte, strike_range_pct, major_threshold, data_wait, auto_update)


@st.fragment(run_every=60)
def render_gex_section_auto(symbol, max_dte, strike_range_pct, major_threshold, data_wait, auto_update):
    """
    Auto-updating fragment (runs every 60s).
    """

    _render_gex_content(symbol, max_dte, strike_range_pct, major_threshold, data_wait, auto_update)


def _render_gex_content(symbol, max_dte, strike_range_pct, major_threshold, data_wait, auto_update):
    """
    Core GEX calculation and rendering logic.
    """

    if "tt_session" not in st.session_state or st.session_state.tt_session is None:
        with st.spinner("Initializing Tastytrade session..."):
            try:
                st.session_state.tt_session = create_session()
            except Exception as e:
                st.error(f"Failed to initialize Tastytrade session: {e}")
                st.stop()

    if auto_update:
        st.markdown(
            f"""
            <div style="font-size:0.8rem;color:{config.COLORS['text_muted']};margin-bottom:1rem;">
                ⚡ Auto-updating every 60s
            </div>
        """,
            unsafe_allow_html=True,
        )

    if "last_run_params" not in st.session_state:
        st.session_state.last_run_params = {}

    current_params = {
        "symbol": symbol,
        "max_dte": max_dte,
        "strike_range_pct": strike_range_pct,
        "major_threshold": major_threshold,
        "data_wait": data_wait,
        "auto_update": auto_update,
    }

    params_changed = st.session_state.last_run_params != current_params

    calculate_btn = st.button("Calculate GEX", type="primary", use_container_width=True)

    should_run = calculate_btn or params_changed or auto_update

    if should_run:
        st.session_state.last_run_params = current_params

        status_container = st.empty()
        progress_bar = st.progress(0)

        def update_progress(msg):
            status_container.info(f"🔄 {msg}")

        try:
            session = st.session_state.get("tt_session")

            if not session:
                update_progress("Re-initializing Tastytrade session...")
                session = create_session()
                st.session_state.tt_session = session

            update_progress(f"Calculating GEX for {symbol}...")
            result = run_gex_calculation(
                symbol=symbol,
                max_dte=max_dte,
                strike_range_pct=strike_range_pct,
                major_level_threshold=major_threshold,
                data_wait_seconds=data_wait,
                progress_callback=update_progress,
                session=session,
            )

            if result.error and "unauthorized" in result.error.lower():
                update_progress("Session expired. Re-authenticating...")

                if "tt_session" in st.session_state:
                    del st.session_state.tt_session

                session = create_session()
                st.session_state.tt_session = session

                if session:
                    update_progress(f"Retrying GEX calculation for {symbol}...")
                    result = run_gex_calculation(
                        symbol=symbol,
                        max_dte=max_dte,
                        strike_range_pct=strike_range_pct,
                        major_level_threshold=major_threshold,
                        data_wait_seconds=data_wait,
                        progress_callback=update_progress,
                        session=session,
                    )

            progress_bar.progress(100)
            status_container.empty()
            time.sleep(0.5)
            progress_bar.empty()

            if result.error:
                st.error(f"❌ {result.error}")

                err_lower = result.error.lower()
                if "authentication" in err_lower or "credentials" in err_lower or "unauthorized" in err_lower:
                    if "tt_session" in st.session_state:
                        del st.session_state.tt_session
            else:
                st.session_state["gex_result"] = result
                st.session_state["last_update"] = datetime.now()

        except Exception as e:
            st.error(f"An unexpected error occurred during calculation: {str(e)}")

            if "tt_session" in st.session_state:
                del st.session_state.tt_session

    if "gex_result" in st.session_state:
        result = st.session_state["gex_result"]
        last_update = st.session_state.get("last_update", datetime.now())

        st.markdown(
            f'''
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;gap:1rem;">
                <span style="
                    background:linear-gradient(135deg,{config.COLORS['cyan']},{config.COLORS['purple']});
                    padding:0.5rem 1.25rem;
                    border-radius:8px;
                    font-size:1.5rem;
                    font-weight:700;
                    color:{config.COLORS['bg_primary']};
                ">{result.symbol}</span>
                <span style="color:{config.COLORS['text_muted']};font-size:0.9rem;">
                    {last_update.strftime('%Y-%m-%d %H:%M:%S')}
                </span>
            </div>
        </div>
        ''',
            unsafe_allow_html=True,
        )

        total_call_gex = result.df[result.df["Type"] == "Call"]["Net GEX ($M)"].sum()
        total_put_gex = result.df[result.df["Type"] == "Put"]["Net GEX ($M)"].sum()
        net_at_spot = interpolate_gex_at_spot(result.strike_gex, result.spot_price)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(
                render_metric_card("Spot Price", f"${result.spot_price:.2f}", "neutral"),
                unsafe_allow_html=True,
            )

        with col2:
            gex_type = "positive" if result.total_gex >= 0 else "negative"
            st.markdown(
                render_metric_card("Total Net GEX", f"${result.total_gex:+,.0f}M", gex_type),
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                render_metric_card(
                    "Zero Gamma",
                    f"${result.zero_gamma_level:.0f}" if result.zero_gamma_level else "—",
                    "neutral",
                    "Flip level",
                ),
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                render_metric_card(
                    "Call Wall",
                    f"${result.call_wall:.0f}" if result.call_wall else "—",
                    "positive",
                    "Resistance",
                ),
                unsafe_allow_html=True,
            )

        with col5:
            st.markdown(
                render_metric_card(
                    "Put Wall",
                    f"${result.put_wall:.0f}" if result.put_wall else "—",
                    "negative",
                    "Support",
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        snap_col1, snap_col2, snap_col3 = st.columns(3)

        with snap_col1:
            st.markdown(
                render_metric_card("Call Gamma", f"${total_call_gex:+,.0f}M", "positive"),
                unsafe_allow_html=True,
            )

        with snap_col2:
            st.markdown(
                render_metric_card("Put Gamma", f"${total_put_gex:+,.0f}M", "negative"),
                unsafe_allow_html=True,
            )

        with snap_col3:
            net_type = "positive" if (net_at_spot or 0) >= 0 else "negative"
            st.markdown(
                render_metric_card(
                    "Net at Spot",
                    f"${net_at_spot:+,.0f}M" if net_at_spot is not None else "—",
                    net_type,
                    "Interpolated",
                ),
                unsafe_allow_html=True,
            )

        st.markdown(
            f'''
        <p class="section-header">Gamma Exposure Profile</p>
        ''',
            unsafe_allow_html=True,
        )

        gex_table_html = render_gex_table(result)
        st.html(gex_table_html)

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown(
                f'''
            <p class="section-header">Major Gamma Levels</p>
            ''',
                unsafe_allow_html=True,
            )

            if not result.major_levels.empty:
                styled_df = result.major_levels.copy()
                styled_df["Strike"] = styled_df["Strike"].apply(lambda x: f"${x:.0f}")
                styled_df["Type"] = styled_df["Net GEX ($M)"].apply(lambda x: "CALL" if x > 0 else "PUT")
                styled_df["Net GEX ($M)"] = styled_df["Net GEX ($M)"].apply(lambda x: f"${x:+,.0f}M")
                styled_df = styled_df[["Strike", "Type", "Net GEX ($M)"]]
                styled_df = styled_df.sort_values(
                    "Strike",
                    key=lambda x: x.str.replace("$", "").astype(float),
                    ascending=False,
                )

                st.dataframe(styled_df, hide_index=True, use_container_width=True)
            else:
                st.markdown(
                    f'''
                <div style="
                    background:{config.COLORS['bg_card']};
                    border:1px solid {config.COLORS['bg_elevated']};
                    border-radius:12px;
                    padding:2rem;
                    text-align:center;
                    color:{config.COLORS['text_muted']};
                ">
                    No major gamma levels found above threshold
                </div>
                ''',
                    unsafe_allow_html=True,
                )

        with col_right:
            st.markdown(
                f'''
            <p class="section-header">Net GEX Heatmap</p>
            ''',
                unsafe_allow_html=True,
            )

            heatmap_html = render_gex_heatmap(result)
            st.html(heatmap_html)

        with st.expander("📋 View Raw Data"):
            st.dataframe(
                result.df.sort_values(["Expiration", "Strike"]),
                hide_index=True,
                use_container_width=True,
            )

            csv = result.df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"gex_{result.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

        with st.expander("📖 How to Interpret GEX"):
            st.markdown(
                """
            ### Understanding Gamma Exposure

            **What is GEX?**
            - Gamma Exposure measures how much market makers need to hedge their options positions
            - It indicates potential support/resistance levels based on dealer positioning

            **Key Levels:**
            - 🟢 **Call Walls (Positive GEX)**: Act as resistance - dealers sell into rallies
            - 🔴 **Put Walls (Negative GEX)**: Act as support - dealers buy into dips
            - 🟡 **Zero Gamma**: Where dealer hedging flips from supportive to resistive

            **Trading Implications:**
            - Price tends to gravitate toward high GEX strikes (gamma pinning)
            - Moves through major gamma walls can accelerate (gamma squeeze)
            - Near zero gamma, expect higher volatility and less dealer support

            **Formula:**
            ```
            GEX = (Open Interest × Gamma × 100 × Spot² × 0.01) / 1,000,000
            ```
            - Calls contribute positive GEX
            - Puts contribute negative GEX
            """
            )

    else:
        st.html(
            f'''
        <div style="
            background: {config.COLORS['gradient_card']};
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 3rem;
            text-align: center;
            margin: 2rem 0;
        ">
            <h2 style="
                color: {config.COLORS['text_primary']};
                font-size: 1.8rem;
                margin-bottom: 1rem;
            ">Welcome to GEX Tool</h2>
            <p style="
                color: {config.COLORS['text_secondary']};
                font-size: 1.1rem;
                max-width: 500px;
                margin: 0 auto 2rem auto;
                line-height: 1.6;
            ">
                Analyze gamma exposure profiles to identify key support/resistance levels
                and understand dealer positioning in the options market.
            </p>

            <div style="
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 1rem;
                margin-top: 2rem;
                text-align: left;
            ">
                <div style="
                    background: rgba(0,255,136,0.1);
                    border-left: 3px solid {config.COLORS['call_gex']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{config.COLORS['call_gex']};font-weight:600;margin:0 0 0.25rem 0;">Call Walls</p>
                    <p style="color:{config.COLORS['text_muted']};font-size:0.85rem;margin:0;">Resistance levels</p>
                </div>
                <div style="
                    background: rgba(255,51,102,0.1);
                    border-left: 3px solid {config.COLORS['put_gex']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{config.COLORS['put_gex']};font-weight:600;margin:0 0 0.25rem 0;">Put Walls</p>
                    <p style="color:{config.COLORS['text_muted']};font-size:0.85rem;margin:0;">Support levels</p>
                </div>
                <div style="
                    background: rgba(255,214,10,0.1);
                    border-left: 3px solid {config.COLORS['zero_gamma']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{config.COLORS['zero_gamma']};font-weight:600;margin:0 0 0.25rem 0;">Zero Gamma</p>
                    <p style="color:{config.COLORS['text_muted']};font-size:0.85rem;margin:0;">Volatility flip point</p>
                </div>
                <div style="
                    background: rgba(0,212,255,0.1);
                    border-left: 3px solid {config.COLORS['cyan']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{config.COLORS['cyan']};font-weight:600;margin:0 0 0.25rem 0;">Heatmaps</p>
                    <p style="color:{config.COLORS['text_muted']};font-size:0.85rem;margin:0;">By strike & expiry</p>
                </div>
            </div>
        </div>

        <p style="text-align:center;color:{config.COLORS['text_muted']};margin-top:1rem;">
            Configure settings in the sidebar and click <b>Calculate GEX</b> to begin
        </p>
        ''',
        )


def render_gex_dashboard():
    # Initialize session state defaults first
    _init_state()
    
    st.markdown(
        '''
    <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
        <p class="main-header">GEX Tool</p>
        <p class="sub-header">Real-Time Gamma Exposure Analysis</p>
    </div>
    ''',
        unsafe_allow_html=True,
    )
    
    # Layout controls row
    st.markdown("---")
    st.markdown("<h3 style='color: #fff; font-size: 1.1rem; margin-bottom: 1rem;'>Layouts</h3>", unsafe_allow_html=True)
    
    layouts = load_layouts()
    layout_names = [layout.name for layout in layouts]
    selected_layout_name = None

    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        selected_layout_name = st.selectbox(
            "Saved layouts",
            options=["(None)"] + layout_names,
            index=0,
            key="layout_select",
            help="Select a saved layout to load"
        )

    with col2:
        new_layout_name = st.text_input(
            "New layout name",
            value="",
            placeholder="e.g. SPX 0DTE scalp",
            key="new_layout_name_input",
            help="Enter a name for saving current settings"
        )

    with col3:
        col3a, col3b = st.columns([1, 1])
        with col3a:
            save_clicked = st.button("Save/Update layout", key="save_layout_btn_main", use_container_width=True)
        with col3b:
            delete_clicked = st.button("Delete selected", key="delete_layout_btn_main", type="secondary", use_container_width=True, disabled=(selected_layout_name == "(None)"))
    
    # Handle layout operations
    selected_layout_obj = None
    if selected_layout_name not in (None, "(None)"):
        for layout in layouts:
            if layout.name == selected_layout_name:
                selected_layout_obj = layout
                break

    if selected_layout_obj is not None:
        # Update session state if it doesn't already match the layout
        st.session_state["symbol"] = selected_layout_obj.symbol
        st.session_state["max_dte"] = selected_layout_obj.max_dte
        st.session_state["strike_range_pct"] = selected_layout_obj.strike_range_pct
        st.session_state["major_threshold"] = selected_layout_obj.major_threshold
        st.session_state["data_wait"] = selected_layout_obj.data_wait
        st.session_state["auto_update"] = selected_layout_obj.auto_update
        st.rerun()
    
    if save_clicked:
        name = new_layout_name.strip() or selected_layout_name
        if not name or name == "(None)":
            st.warning("Please enter a layout name or select an existing one to overwrite.")
        else:
            layout = Layout(
                name=name,
                symbol=st.session_state["symbol"],
                max_dte=st.session_state["max_dte"],
                strike_range_pct=st.session_state["strike_range_pct"],
                major_threshold=st.session_state["major_threshold"],
                data_wait=st.session_state["data_wait"],
                auto_update=st.session_state["auto_update"],
            )
            upsert_layout(layout)
            st.success(f"Layout '{name}' saved.")
            st.rerun()
    
    if delete_clicked and selected_layout_name not in (None, "(None)"):
        delete_layout(selected_layout_name)
        st.success(f"Layout '{selected_layout_name}' deleted.")
        st.rerun()

    st.markdown("---")

    client_secret, refresh_token = get_credentials()
    if not client_secret or not refresh_token:
        st.error("⚠️ **Missing Credentials**")
        st.markdown(
            """
        Please configure your Tastytrade API credentials as environment variables:
        - `TT_CLIENT_SECRET`
        - `TT_REFRESH_TOKEN`

        For more information, see the [Tastytrade API documentation](https://tastytrade-api-js.readthedocs.io/).
        """
        )
        st.stop()

    with st.sidebar:
        st.markdown(
            f'''
        <div style="text-align:center;padding:0.5rem 0 1rem 0;">
            <span style="font-size:1.5rem;font-weight:700;color:{config.COLORS['text_primary']};">
                Settings
            </span>
        </div>
        ''',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<p style="color:{config.COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">SYMBOL</p>',
            unsafe_allow_html=True,
        )
        symbol = st.selectbox(
            "Symbol",
            options=config.DEFAULT_SYMBOLS,
            index=config.DEFAULT_SYMBOLS.index(st.session_state.symbol) if st.session_state.symbol in config.DEFAULT_SYMBOLS else 0,
            help="Select the underlying symbol to analyze",
            label_visibility="collapsed",
            key="symbol_dropdown",
        )

        custom_symbol = st.text_input(
            "Or enter custom symbol",
            placeholder="Enter custom symbol...",
            help="Enter any optionable symbol",
            label_visibility="collapsed",
            key="custom_symbol_input",
        )
        if custom_symbol:
            is_valid, error_msg = validate_symbol(custom_symbol)
            if not is_valid:
                st.error(f"Invalid symbol: {error_msg}")
                st.stop()
            # Update session state if custom symbol is valid
            st.session_state.symbol = custom_symbol.strip().upper()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            f'<p style="color:{config.COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">MAX DAYS TO EXPIRATION</p>',
            unsafe_allow_html=True,
        )
        st.slider(
            "Max Days to Expiration",
            min_value=config.DTE_MIN,
            max_value=config.DTE_MAX,
            value=st.session_state.max_dte,
            step=1,
            help="Include options expiring within this many days",
            label_visibility="collapsed",
            key="max_dte_slider",
        )

        st.markdown(
            f'<p style="color:{config.COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">STRIKE RANGE (% FROM SPOT)</p>',
            unsafe_allow_html=True,
        )
        st.slider(
            "Strike Range (% from spot)",
            min_value=config.STRIKE_RANGE_MIN,
            max_value=config.STRIKE_RANGE_MAX,
            value=st.session_state.strike_range_pct,
            step=5,
            help="Filter strikes within this percentage of spot price",
            label_visibility="collapsed",
            key="strike_range_slider",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("Advanced Settings"):
            st.number_input(
                "Major Level Threshold ($M)",
                min_value=config.MAJOR_THRESHOLD_MIN,
                max_value=config.MAJOR_THRESHOLD_MAX,
                value=st.session_state.major_threshold,
                step=10,
                help="Minimum GEX for 'major' gamma walls",
                key="major_threshold_input",
            )

            st.slider(
                "Data Collection Time (s)",
                min_value=config.DATA_WAIT_MIN,
                max_value=config.DATA_WAIT_MAX,
                value=st.session_state.data_wait,
                help="Seconds to wait for streaming data",
                key="data_wait_slider",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            f'<p style="color:{config.COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">AUTO UPDATE</p>',
            unsafe_allow_html=True,
        )
        st.checkbox(
            "Auto-update (every 60s)",
            value=st.session_state.auto_update,
            help="Automatically refresh data every minute",
            key="auto_update_checkbox",
        )

        st.markdown("---")
        st.markdown(
            f"""
        <div style="font-size:0.8rem;color:{config.COLORS['text_muted']};text-align:center;">
            v{config.APP_VERSION} • Powered by Tastytrade
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Get current values from session state for use in calculations
    symbol = st.session_state.symbol
    max_dte = st.session_state.max_dte
    strike_range_pct = st.session_state.strike_range_pct / 100  # Convert to decimal
    major_threshold = st.session_state.major_threshold
    data_wait = st.session_state.data_wait
    auto_update = st.session_state.auto_update

    if auto_update:
        render_gex_section_auto(symbol, max_dte, strike_range_pct, major_threshold, data_wait, auto_update)
    else:
        render_gex_section_manual(symbol, max_dte, strike_range_pct, major_threshold, data_wait, auto_update)


render_gex_dashboard()
