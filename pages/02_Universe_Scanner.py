import streamlit as st
import pandas as pd

from gex_app.ui.components import apply_base_theme
from gex_app.core.gex_core import (
    run_gex_calculation,
    get_credentials,
    create_session,
    GEXResult,
)
from gex_app import config
from gex_app.layouts import Layout, load_layouts, upsert_layout, delete_layout
from typing import Dict, Any

apply_base_theme()

st.title("Universe GEX Scanner")
st.caption("Scan GEX context across multiple symbols at once.")

# Layout controls row (reuse from dashboard)
st.markdown("---")
st.markdown("### Layouts")

layouts = load_layouts()
layout_names = [layout.name for layout in layouts]
selected_layout_name = None

col1, col2, col3 = st.columns([3, 2, 2])

with col1:
    selected_layout_name = st.selectbox(
        "Saved layouts",
        options=["(None)"] + layout_names,
        index=0,
        key="universe_layout_select",
        help="Select a saved layout to load"
    )

with col2:
    new_layout_name = st.text_input(
        "New layout name",
        value="",
        placeholder="e.g. SPX 0DTE scalp",
        key="universe_new_layout_name_input",
        help="Enter a name for saving current settings"
    )

with col3:
    col3a, col3b = st.columns([1, 1])
    with col3a:
        save_clicked = st.button("Save/Update layout", key="universe_save_layout_btn_main", use_container_width=True)
    with col3b:
        delete_clicked = st.button("Delete selected", key="universe_delete_layout_btn_main", type="secondary", use_container_width=True, disabled=(selected_layout_name == "(None)"))

# Handle layout operations
selected_layout_obj = None
if selected_layout_name not in (None, "(None)"):
    for layout in layouts:
        if layout.name == selected_layout_name:
            selected_layout_obj = layout
            break

if selected_layout_obj is not None:
    # Update session state if layout is selected
    if "universe_symbols" not in st.session_state:
        st.session_state.universe_symbols = ["SPX", "QQQ", "IWM"]
    if "universe_max_dte" not in st.session_state:
        st.session_state.universe_max_dte = config.DTE_DEFAULT
    if "universe_strike_range_pct" not in st.session_state:
        st.session_state.universe_strike_range_pct = config.STRIKE_RANGE_DEFAULT
    if "universe_major_threshold" not in st.session_state:
        st.session_state.universe_major_threshold = config.MAJOR_THRESHOLD_DEFAULT
    
    st.session_state.universe_symbols = [selected_layout_obj.symbol] if selected_layout_obj.symbol else ["SPX", "QQQ", "IWM"]
    st.session_state.universe_max_dte = selected_layout_obj.max_dte
    st.session_state.universe_strike_range_pct = selected_layout_obj.strike_range_pct
    st.session_state.universe_major_threshold = selected_layout_obj.major_threshold
    st.rerun()

if save_clicked:
    name = new_layout_name.strip() or selected_layout_name
    if not name or name == "(None)":
        st.warning("Please enter a layout name or select an existing one to overwrite.")
    else:
        symbols = st.session_state.get("universe_symbols", ["SPX", "QQQ", "IWM"])
        symbol = symbols[0] if symbols else "SPY"
        layout = Layout(
            name=name,
            symbol=symbol,
            max_dte=st.session_state.get("universe_max_dte", config.DTE_DEFAULT),
            strike_range_pct=st.session_state.get("universe_strike_range_pct", config.STRIKE_RANGE_DEFAULT),
            major_threshold=st.session_state.get("universe_major_threshold", config.MAJOR_THRESHOLD_DEFAULT),
            data_wait=st.session_state.get("universe_data_wait", config.DATA_WAIT_DEFAULT),
            auto_update=st.session_state.get("universe_auto_update", False),
        )
        upsert_layout(layout)
        st.success(f"Layout '{name}' saved.")
        st.rerun()

if delete_clicked and selected_layout_name not in (None, "(None)"):
    delete_layout(selected_layout_name)
    st.success(f"Layout '{selected_layout_name}' deleted.")
    st.rerun()

st.markdown("---")

# Symbols input section
st.markdown("### Symbols")

def parse_symbols(raw: str) -> list[str]:
    """Parse raw input string into a list of clean symbols."""
    if not raw.strip():
        return []
    # split by both newline and comma
    parts = []
    for line in raw.splitlines():
        parts.extend(line.split(","))
    # normalise, strip, uppercase, drop empties & duplicates
    seen = set()
    symbols: list[str] = []
    for p in parts:
        sym = p.strip().upper()
        if not sym:
            continue
        if sym not in seen:
            seen.add(sym)
            symbols.append(sym)
    return symbols

# Initialize session state for symbols
if "universe_symbols" not in st.session_state:
    st.session_state.universe_symbols = ["SPX", "QQQ", "IWM"]
    st.session_state.universe_symbols_text = "SPX\nQQQ\nIWM"

symbols_text = st.text_area(
    "Enter symbols (one per line, or comma-separated):",
    value=st.session_state.get("universe_symbols_text", "SPX\nQQQ\nIWM"),
    height=100,
    key="universe_symbols_text"
)

symbols = parse_symbols(symbols_text)

# Update session state when symbols change
if symbols != st.session_state.get("universe_symbols", []):
    st.session_state.universe_symbols = symbols

# Display parsed symbols
if symbols:
    st.info(f"📊 **{len(symbols)} symbols ready to scan: {', '.join(symbols)}")
else:
    st.warning("⚠️ No valid symbols entered")

# Scan configuration section
st.markdown("### Scan configuration")

col1, col2 = st.columns(2)

with col1:
    # Initialize session state for scan parameters
    if "universe_max_dte" not in st.session_state:
        st.session_state.universe_max_dte = config.DTE_DEFAULT
    if "universe_data_wait" not in st.session_state:
        st.session_state.universe_data_wait = config.DATA_WAIT_DEFAULT
    
    max_dte = st.slider(
        "Max Days to Expiration",
        min_value=config.DTE_MIN,
        max_value=config.DTE_MAX,
        value=st.session_state.universe_max_dte,
        step=1,
        help="Include options expiring within this many days",
        key="universe_max_dte_slider"
    )
    
    data_wait = st.slider(
        "Data Collection Time (s)",
        min_value=config.DATA_WAIT_MIN,
        max_value=config.DATA_WAIT_MAX,
        value=st.session_state.universe_data_wait,
        step=1,
        help="Seconds to wait for streaming data",
        key="universe_data_wait_slider"
    )

with col2:
    if "universe_strike_range_pct" not in st.session_state:
        st.session_state.universe_strike_range_pct = config.STRIKE_RANGE_DEFAULT
    if "universe_major_threshold" not in st.session_state:
        st.session_state.universe_major_threshold = config.MAJOR_THRESHOLD_DEFAULT
    
    strike_range_pct = st.slider(
        "Price range (% from spot)",
        min_value=config.STRIKE_RANGE_MIN,
        max_value=config.STRIKE_RANGE_MAX,
        value=st.session_state.universe_strike_range_pct,
        step=5,
        help="Filter strikes within this percentage of spot price",
        key="universe_strike_range_slider"
    )
    
    major_threshold = st.number_input(
        "Major Level Threshold ($M)",
        min_value=config.MAJOR_THRESHOLD_MIN,
        max_value=config.MAJOR_THRESHOLD_MAX,
        value=st.session_state.universe_major_threshold,
        step=10,
        help="Minimum GEX for 'major' gamma walls",
        key="universe_major_threshold_input"
    )

# Update session state when parameters change
st.session_state.universe_max_dte = max_dte
st.session_state.universe_strike_range_pct = strike_range_pct
st.session_state.universe_major_threshold = major_threshold
st.session_state.universe_data_wait = data_wait

run_button = st.button("🚀 Run universe scan", type="primary", disabled=not symbols, use_container_width=True)


def build_universe_row(symbol: str, gex_result: GEXResult) -> Dict[str, Any]:
    """
    Convert a GEXResult into a flat dict row for the universe table.
    Using real GEXResult attributes: spot_price, total_gex, zero_gamma_level, etc.
    """
    spot = gex_result.spot_price
    zero_gamma = gex_result.zero_gamma_level
    total_net_gex = gex_result.total_gex
    call_wall = gex_result.call_wall
    put_wall = gex_result.put_wall

    # Distance from spot to zero gamma in %
    zero_gamma_dist_pct = None
    if spot is not None and zero_gamma is not None and spot != 0:
        zero_gamma_dist_pct = (zero_gamma / spot - 1.0) * 100.0

    # Call / put GEX totals from the calculated dataframe
    call_gex = None
    put_gex = None
    if hasattr(gex_result, "df") and not gex_result.df.empty:
        call_gex = gex_result.df[gex_result.df["Type"] == "Call"]["Net GEX ($M)"].sum()
        put_gex = gex_result.df[gex_result.df["Type"] == "Put"]["Net GEX ($M)"].sum()

    # Find strongest wall using strike_gex (largest absolute Net GEX)
    strongest_wall_strike = None
    strongest_wall_gex = None
    strongest_wall_type = None

    if hasattr(gex_result, "strike_gex") and not gex_result.strike_gex.empty:
        strongest_row = gex_result.strike_gex.loc[gex_result.strike_gex["Net GEX ($M)"].abs().idxmax()]
        strongest_wall_strike = strongest_row["Strike"]
        strongest_wall_gex = strongest_row["Net GEX ($M)"]
        strongest_wall_type = "Call" if strongest_wall_gex > 0 else "Put"

    # Regime indicator based on net GEX sign
    regime = None
    if isinstance(total_net_gex, (int, float)):
        if total_net_gex > 0:
            regime = "call-dominated"
        elif total_net_gex < 0:
            regime = "put-dominated"
        else:
            regime = "neutral"

    status = "✅ Success" if not gex_result.error else f"❌ {gex_result.error[:30]}..."

    return {
        "symbol": symbol,
        "spot": spot,
        "zero_gamma": zero_gamma,
        "zero_gamma_dist_pct": zero_gamma_dist_pct,
        "net_gex": total_net_gex,
        "call_gex": call_gex,
        "put_gex": put_gex,
        "strongest_wall_strike": strongest_wall_strike,
        "strongest_wall_gex": strongest_wall_gex,
        "strongest_wall_type": strongest_wall_type,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "regime": regime,
        "status": status,
        "error": gex_result.error,
    }


# Fallback build_universe_row for backwards compatibility with display formatting
def build_universe_row_display(symbol: str, gex_result: GEXResult) -> dict:
    """Build a summary row for the universe scan results (formatted for display)."""
    if gex_result.error:
        return {
            "Symbol": symbol,
            "Spot Price": "—",
            "Total Net GEX": "—",
            "Call GEX": "—", 
            "Put GEX": "—",
            "Zero Gamma": "—",
            "Call Wall": "—",
            "Put Wall": "—",
            "Status": f"❌ {gex_result.error[:50]}..."
        }
    
    # Calculate call/put GEX totals
    total_call_gex = gex_result.df[gex_result.df["Type"] == "Call"]["Net GEX ($M)"].sum()
    total_put_gex = gex_result.df[gex_result.df["Type"] == "Put"]["Net GEX ($M)"].sum()
    
    # Get strongest wall info
    wall_info = build_universe_row(symbol, gex_result)
    
    return {
        "Symbol": gex_result.symbol,
        "Spot Price": f"${gex_result.spot_price:.2f}",
        "Total Net GEX": f"${gex_result.total_gex:+,.0f}M",
        "Call GEX": f"${total_call_gex:+,.0f}M",
        "Put GEX": f"${total_put_gex:+,.0f}M",
        "Zero Gamma": f"${gex_result.zero_gamma_level:.0f}" if gex_result.zero_gamma_level else "—",
        "Zero Gamma % from Spot": f"{wall_info['zero_gamma_dist_pct']:+.1f}%" if wall_info['zero_gamma_dist_pct'] is not None else "—",
        "Call Wall": f"${gex_result.call_wall:.0f}" if gex_result.call_wall else "—",
        "Put Wall": f"${gex_result.put_wall:.0f}" if gex_result.put_wall else "—",
        "Strongest Wall": f"{wall_info['strongest_wall_type']} ${wall_info['strongest_wall_strike']:.0f}" if wall_info['strongest_wall_type'] else "—",
        "Regime": wall_info['regime'],
        "Status": "✅ Success"
    }


if run_button:
    if not symbols:
        st.warning("Please enter at least one symbol.")
    else:
        client_secret, refresh_token = get_credentials()
        if not client_secret or not refresh_token:
            st.error("Missing Tastytrade credentials. Please configure them first.")
        else:
            with st.spinner(f"Running GEX scan for {len(symbols)} symbols..."):
                session = create_session()
                results = []

                for sym in symbols:
                    try:
                        gex_result = run_gex_calculation(
                            symbol=sym,
                            max_dte=max_dte,
                            strike_range_pct=strike_range_pct,
                            major_level_threshold=major_threshold,
                            data_wait_seconds=data_wait,
                            progress_callback=None,
                            session=session,
                        )
                        summary = build_universe_row_display(sym, gex_result)
                        results.append(summary)
                    except Exception as e:
                        st.error(f"{sym} failed: {type(e).__name__}: {e}")
                        results.append(
                            {
                                "Symbol": sym,
                                "Spot Price": "—",
                                "Total Net GEX": "—",
                                "Call GEX": "—",
                                "Put GEX": "—",
                                "Zero Gamma": "—",
                                "Zero Gamma % from Spot": "—",
                                "Call Wall": "—",
                                "Put Wall": "—",
                                "Strongest Wall": "—",
                                "Regime": "—",
                                "Status": f"Error: {type(e).__name__}",
                            }
                        )

            if not results:
                st.info("No results produced by the scan.")
            else:
                # Build display dataframe with enhanced formatting
                display_results = []
                for result in results:
                    if isinstance(result, dict) and ("symbol" in result or "Symbol" in result):
                        # This is a successful result with display formatting
                        display_results.append(result)
                    else:
                        # Create error row for consistency
                        error_row = {
                            "Symbol": result.get("symbol", "Unknown"),
                            "Spot Price": "—",
                            "Total Net GEX": "—",
                            "Call GEX": "—", 
                            "Put GEX": "—",
                            "Zero Gamma": "—",
                            "Zero Gamma % from Spot": "—",
                            "Call Wall": "—",
                            "Put Wall": "—",
                            "Strongest Wall": "—",
                            "Regime": "—",
                            "Status": result.get("status", "❌ Error")
                        }
                        display_results.append(error_row)
                
                df = pd.DataFrame(display_results)
                
                # Pre-sort results - by default, sort by absolute zero gamma distance (closest to zero first)
                if "Zero Gamma % from Spot" in df.columns:
                    def format_zero_gamma_dist(val):
                        """Extract numeric value from formatted Zero Gamma % from Spot column."""
                        if isinstance(val, str) and val != "—":
                            # Remove % symbol and clean
                            val_clean = val.replace("%", "").replace("+", "")
                            try:
                                return float(val_clean)
                            except ValueError:
                                return 0.0
                        return 0.0
                    
                    # Sort by absolute distance from zero gamma (closest to zero first)
                    df = df.sort_values(
                        by="Zero Gamma % from Spot", 
                        key=lambda s: s.apply(format_zero_gamma_dist).abs(),
                        ascending=True
                    )
                    
                    # Format zero gamma distance to 2 decimal places for display
                    df["Zero Gamma % from Spot"] = df["Zero Gamma % from Spot"].apply(
                        lambda x: f"{float(str(x).replace('%', '').replace('+', '').replace('—', '0')):.2f}%" if isinstance(x, str) and x != "—" else x
                    )
                
                # Alternative sorting options could be added here as user controls
                # For example: by abs(net_gex) descending, or by symbol
                
                st.markdown("### 📊 Scan Results")
                
                # Summary metrics
                successful_scans = [r for r in display_results if r.get("Status", "").startswith("✅")]
                total_results = len(display_results)
                st.markdown(f"**Successfully scanned:** {len(successful_scans)}/{total_results} symbols")
                
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Export functionality
                st.markdown("### 📤 Export Data")
                csv = df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download Results CSV",
                    data=csv,
                    file_name=f"gex_universe_scan_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

# Info section
st.markdown("---")
with st.expander("📖 About Universe Scanner"):
    st.markdown("""
    **What is Universe Scanning?**
    
    The Universe GEX Scanner allows you to analyze gamma exposure across multiple symbols simultaneously, providing a comprehensive market-wide view of dealer positioning.
    
    **Key Features:**
    
    - **Multi-Symbol Analysis**: Scan multiple ETFs, indices, or custom symbols in one run
    - **Comparative Insights**: Spot relative strength/weakness across the universe
    - **Market Structure**: Identify where gamma walls cluster across different instruments
    - **Efficient Workflow**: No need to run individual calculations for each symbol
    - **Layout Persistence**: Save and reload your scan configurations
    
    **Use Cases:**
    
    - Market breadth analysis across major ETFs
    - Relative strength comparison between SPY vs QQQ
    - Index options context (SPX/NDX) vs ETF alternatives (SPY/QQQ)
    - Custom basket analysis for specific sectors or themes
    
    **Data Quality Notes:**
    
    - Scan time increases with symbol count and wait time settings
    - Some symbols may have limited option chain depth
    - Real-time data accuracy depends on market hours and API availability
    """)
