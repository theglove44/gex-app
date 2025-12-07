"""
GEX Tool - Gamma Exposure Web Dashboard
A Streamlit-based interactive dashboard for analyzing gamma exposure profiles.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from gex_core import run_gex_calculation, get_credentials

# Page configuration
st.set_page_config(
    page_title="GEX Tool - Gamma Exposure Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .positive-gex {
        color: #00c853;
        font-weight: bold;
    }
    .negative-gex {
        color: #ff5252;
        font-weight: bold;
    }
    .stMetric > div {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


def _add_common_vertical_markers(fig: go.Figure, result):
    """Add spot/zero gamma/call wall/put wall markers to a figure."""

    # Spot price line
    fig.add_vline(
        x=result.spot_price,
        line_dash="dash",
        line_color="#2196f3",
        line_width=2,
        annotation_text=f"Spot: ${result.spot_price:.2f}",
        annotation_position="top",
        annotation_font_size=12,
        annotation_font_color="#2196f3"
    )

    # Zero gamma level (if calculated)
    if result.zero_gamma_level:
        fig.add_vline(
            x=result.zero_gamma_level,
            line_dash="dot",
            line_color="#ff9800",
            line_width=2,
            annotation_text=f"Zero Gamma: ${result.zero_gamma_level:.0f}",
            annotation_position="bottom",
            annotation_font_size=11,
            annotation_font_color="#ff9800"
        )

    # Call wall marker
    if result.call_wall:
        fig.add_vline(
            x=result.call_wall,
            line_dash="dashdot",
            line_color="#00c853",
            line_width=1,
            opacity=0.5
        )

    # Put wall marker
    if result.put_wall:
        fig.add_vline(
            x=result.put_wall,
            line_dash="dashdot",
            line_color="#ff5252",
            line_width=1,
            opacity=0.5
        )

    return fig


def interpolate_gex_at_spot(strike_gex: pd.DataFrame, spot: float) -> float | None:
    """Estimate net gamma at the current spot using linear interpolation between strikes."""

    if strike_gex.empty:
        return None

    ordered = strike_gex.sort_values('Strike')
    strikes = ordered['Strike'].values
    gex_values = ordered['Net GEX ($M)'].values

    # Exact strike match
    for strike, gex_value in zip(strikes, gex_values):
        if strike == spot:
            return float(gex_value)

    # Spot below/above bounds, clamp to nearest edge
    if spot <= strikes[0]:
        return float(gex_values[0])
    if spot >= strikes[-1]:
        return float(gex_values[-1])

    # Linear interpolation between surrounding strikes
    for i in range(len(strikes) - 1):
        left_strike, right_strike = strikes[i], strikes[i + 1]
        if left_strike <= spot <= right_strike:
            left_gex, right_gex = gex_values[i], gex_values[i + 1]
            slope = (right_gex - left_gex) / (right_strike - left_strike)
            return float(left_gex + slope * (spot - left_strike))

    return None


def create_gex_chart(result) -> go.Figure:
    """Create an interactive Plotly bar chart for GEX profile."""
    df = result.strike_gex

    # Color coding: green for positive (call walls), red for negative (put walls)
    colors = ['#00c853' if x >= 0 else '#ff5252' for x in df['Net GEX ($M)']]

    fig = go.Figure()

    # Main GEX bars
    fig.add_trace(go.Bar(
        x=df['Strike'],
        y=df['Net GEX ($M)'],
        marker_color=colors,
        name='Net GEX',
        hovertemplate='<b>Strike: $%{x:.0f}</b><br>GEX: $%{y:.1f}M<extra></extra>',
        opacity=0.8
    ))

    fig = _add_common_vertical_markers(fig, result)

    # Layout
    fig.update_layout(
        title=dict(
            text=f"<b>{result.symbol}</b> Gamma Exposure Profile (0-{result.max_dte} DTE)",
            font=dict(size=20),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Strike Price",
        yaxis_title="Net GEX ($M)",
        template="plotly_white",
        height=500,
        hovermode='x unified',
        showlegend=False,
        xaxis=dict(
            tickformat="$,.0f",
            gridcolor='#e0e0e0',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            tickformat="$,.0fM",
            gridcolor='#e0e0e0',
            tickfont=dict(size=11),
            zeroline=True,
            zerolinecolor='#333',
            zerolinewidth=1
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        plot_bgcolor='rgba(250,250,250,0.8)'
    )

    return fig


def create_breakdown_chart(result) -> go.Figure:
    """Create stacked call/put bars similar to the Cheddar Flow layout."""

    calls = (
        result.df[result.df['Type'] == 'Call']
        .groupby('Strike')['Net GEX ($M)']
        .sum()
    )
    puts = (
        result.df[result.df['Type'] == 'Put']
        .groupby('Strike')['Net GEX ($M)']
        .sum()
    )

    all_strikes = sorted(set(calls.index).union(set(puts.index)))
    call_values = [calls.get(s, 0) for s in all_strikes]
    put_values = [puts.get(s, 0) for s in all_strikes]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=all_strikes,
        y=call_values,
        name='Call GEX',
        marker_color='#1f77b4',
        opacity=0.9,
        hovertemplate='<b>Strike: $%{x:.0f}</b><br>Call GEX: $%{y:.1f}M<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        x=all_strikes,
        y=put_values,
        name='Put GEX',
        marker_color='#ff7f0e',
        opacity=0.9,
        hovertemplate='<b>Strike: $%{x:.0f}</b><br>Put GEX: $%{y:.1f}M<extra></extra>'
    ))

    fig = _add_common_vertical_markers(fig, result)

    fig.update_layout(
        barmode='relative',
        title=dict(
            text=f"<b>{result.symbol}</b> Call vs Put Gamma Exposure", 
            font=dict(size=20),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Strike Price",
        yaxis_title="GEX Contribution ($M)",
        template="plotly_white",
        height=500,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(
            tickformat="$,.0f",
            gridcolor='#e0e0e0',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            tickformat="$,.0fM",
            gridcolor='#e0e0e0',
            tickfont=dict(size=11),
            zeroline=True,
            zerolinecolor='#333',
            zerolinewidth=1
        ),
        margin=dict(l=60, r=40, t=80, b=60),
        plot_bgcolor='rgba(250,250,250,0.8)'
    )

    return fig


def validate_symbol(symbol: str) -> tuple[bool, str]:
    """
    Validate custom symbol input.

    Returns:
        (is_valid, error_message)
    """
    if not symbol:
        return False, "Symbol cannot be empty"

    # Remove whitespace
    symbol = symbol.strip().upper()

    # Check length (reasonable bounds)
    if len(symbol) < 1 or len(symbol) > 10:
        return False, "Symbol must be 1-10 characters"

    # Check alphanumeric only
    if not symbol.replace('.', '').replace('-', '').isalnum():
        return False, "Symbol must contain only letters, numbers, dots, and dashes"

    return True, ""


def create_heatmap_by_expiration(result) -> go.Figure:
    """Create a heatmap showing GEX by strike and expiration."""
    df = result.df

    if df.empty:
        return None

    # Pivot table: strikes as rows, expirations as columns
    pivot = df.pivot_table(
        values='Net GEX ($M)',
        index='Strike',
        columns='Expiration',
        aggfunc='sum',
        fill_value=0
    )

    # Sort by strike
    pivot = pivot.sort_index(ascending=False)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[str(d) for d in pivot.columns],
        y=[f"${s:.0f}" for s in pivot.index],
        colorscale=[
            [0, '#ff5252'],      # Red for negative
            [0.5, '#ffffff'],    # White for zero
            [1, '#00c853']       # Green for positive
        ],
        zmid=0,
        hovertemplate='Strike: %{y}<br>Exp: %{x}<br>GEX: $%{z:.1f}M<extra></extra>',
        colorbar=dict(title='GEX ($M)')
    ))

    fig.update_layout(
        title=dict(
            text="GEX Heatmap by Strike & Expiration",
            font=dict(size=16),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Expiration Date",
        yaxis_title="Strike Price",
        height=400,
        template="plotly_white"
    )

    return fig


def main():
    # Header
    st.markdown('<p class="main-header">📊 GEX Tool</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gamma Exposure Analysis Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Check credentials
    client_secret, refresh_token = get_credentials()
    if not client_secret or not refresh_token:
        st.error("⚠️ **Missing Credentials**")
        st.markdown("""
        Please configure your Tastytrade API credentials as environment variables:
        - `TT_CLIENT_SECRET`
        - `TT_REFRESH_TOKEN`

        For more information, see the [Tastytrade API documentation](https://tastytrade-api-js.readthedocs.io/).
        """)
        st.stop()

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Settings")

        # Symbol selection
        symbol = st.selectbox(
            "Symbol",
            options=["SPY", "QQQ", "IWM", "DIA", "AAPL", "TSLA", "NVDA", "AMD", "AMZN", "MSFT"],
            index=0,
            help="Select the underlying symbol to analyze"
        )

        # Custom symbol input
        custom_symbol = st.text_input(
            "Or enter custom symbol",
            placeholder="e.g., META",
            help="Enter any optionable symbol"
        )
        if custom_symbol:
            is_valid, error_msg = validate_symbol(custom_symbol)
            if not is_valid:
                st.error(f"Invalid symbol: {error_msg}")
                st.stop()
            symbol = custom_symbol.strip().upper()

        st.markdown("---")

        # DTE slider
        max_dte = st.slider(
            "Max Days to Expiration",
            min_value=1,
            max_value=60,
            value=30,
            step=1,
            help="Include options expiring within this many days"
        )

        # Strike range
        strike_range = st.slider(
            "Strike Range (% from spot)",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Filter strikes within this percentage of spot price"
        )

        st.markdown("---")

        # Advanced settings
        with st.expander("Advanced Settings"):
            major_threshold = st.number_input(
                "Major Level Threshold ($M)",
                min_value=10,
                max_value=500,
                value=50,
                step=10,
                help="Minimum GEX for 'major' gamma walls"
            )

            data_wait = st.slider(
                "Data Collection Time (s)",
                min_value=2,
                max_value=10,
                value=5,
                help="Seconds to wait for streaming data"
            )

        st.markdown("---")

        # Calculate button
        calculate_btn = st.button(
            "🔄 Calculate GEX",
            type="primary",
            use_container_width=True
        )

    # Main content area
    if calculate_btn:
        # Progress indicator
        progress_container = st.empty()
        status_text = st.empty()

        def update_progress(msg):
            status_text.text(f"⏳ {msg}")

        with st.spinner(f"Calculating GEX for {symbol}..."):
            result = run_gex_calculation(
                symbol=symbol,
                max_dte=max_dte,
                strike_range_pct=strike_range / 100,
                progress_callback=update_progress
            )

        status_text.empty()

        if result.error:
            st.error(f"❌ Error: {result.error}")
            st.stop()

        # Store result in session state
        st.session_state['gex_result'] = result
        st.session_state['last_update'] = datetime.now()

    # Display results if available
    if 'gex_result' in st.session_state:
        result = st.session_state['gex_result']
        last_update = st.session_state.get('last_update', datetime.now())

        # Timestamp
        st.caption(f"Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")

        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                label="Spot Price",
                value=f"${result.spot_price:.2f}"
            )

        with col2:
            gex_delta = "+" if result.total_gex >= 0 else ""
            st.metric(
                label="Total Net GEX",
                value=f"${result.total_gex:,.0f}M",
                delta=f"{gex_delta}{result.total_gex:,.0f}M" if result.total_gex != 0 else None,
                delta_color="normal"
            )

        with col3:
            st.metric(
                label="Zero Gamma",
                value=f"${result.zero_gamma_level:.0f}" if result.zero_gamma_level else "N/A",
                help="Price level where dealer gamma exposure flips"
            )

        with col4:
            st.metric(
                label="Call Wall",
                value=f"${result.call_wall:.0f}" if result.call_wall else "N/A",
                help="Strike with highest positive GEX (resistance)"
            )

        with col5:
            st.metric(
                label="Put Wall",
                value=f"${result.put_wall:.0f}" if result.put_wall else "N/A",
                help="Strike with most negative GEX (support)"
            )

        st.markdown("---")

        # Snapshot similar to Cheddar Flow cards
        total_call_gex = result.df[result.df['Type'] == 'Call']['Net GEX ($M)'].sum()
        total_put_gex = result.df[result.df['Type'] == 'Put']['Net GEX ($M)'].sum()
        net_at_spot = interpolate_gex_at_spot(result.strike_gex, result.spot_price)

        snap_col1, snap_col2, snap_col3 = st.columns(3)
        snap_col1.metric(
            label="Call Gamma Exposure",
            value=f"${total_call_gex:,.0f}M",
            help="Sum of positive gamma from call open interest"
        )
        snap_col2.metric(
            label="Put Gamma Exposure",
            value=f"${total_put_gex:,.0f}M",
            help="Sum of negative gamma from puts (normally negative)"
        )
        snap_col3.metric(
            label="Net at Spot",
            value=f"${net_at_spot:,.0f}M" if net_at_spot is not None else "N/A",
            help=(
                "Interpolated net gamma at the current spot price across nearby strikes. "
                "Total Net GEX (above) remains the sum across the full strike range."
            )
        )

        st.caption("These snapshots mirror the Cheddar Flow view by showing call/put contributions before drilling into the profile charts.")

        # Main chart
        st.subheader("📈 GEX Profile")
        chart_mode = st.radio(
            "Chart view",
            options=["Net Gamma Exposure", "Call vs Put Breakdown"],
            horizontal=True,
            help="Switch to the call/put breakdown to mirror the Cheddar Flow style screenshot."
        )

        if chart_mode == "Net Gamma Exposure":
            fig = create_gex_chart(result)
        else:
            fig = create_breakdown_chart(result)

        st.plotly_chart(fig, use_container_width=True)

        # Two columns for additional info
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🎯 Major Gamma Levels")
            if not result.major_levels.empty:
                # Style the dataframe
                styled_df = result.major_levels.copy()
                styled_df['Strike'] = styled_df['Strike'].apply(lambda x: f"${x:.0f}")
                styled_df['Type'] = styled_df['Net GEX ($M)'].apply(
                    lambda x: "🟢 Call Wall" if x > 0 else "🔴 Put Wall"
                )
                styled_df['Net GEX ($M)'] = styled_df['Net GEX ($M)'].apply(
                    lambda x: f"${x:+,.0f}M"
                )
                styled_df = styled_df[['Strike', 'Type', 'Net GEX ($M)']]
                styled_df = styled_df.sort_values('Strike', key=lambda x: x.str.replace('$', '').astype(float), ascending=False)

                st.dataframe(
                    styled_df,
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No major gamma levels found above threshold.")

        with col_right:
            st.subheader("📊 GEX by Expiration")
            heatmap_fig = create_heatmap_by_expiration(result)
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True)

        # Expandable raw data section
        with st.expander("📋 View Raw Data"):
            st.dataframe(
                result.df.sort_values(['Expiration', 'Strike']),
                hide_index=True,
                use_container_width=True
            )

            # Download button
            csv = result.df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"gex_{result.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        # Interpretation guide
        with st.expander("📖 How to Interpret GEX"):
            st.markdown("""
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
            """)

    else:
        # Initial state - show instructions
        st.info("👈 Configure settings and click **Calculate GEX** to get started!")

        # Show example layout
        st.markdown("""
        ### What you'll see:

        1. **Key Metrics** - Spot price, total GEX, zero gamma level, major walls
        2. **Interactive Chart** - Bar chart of GEX by strike with hover details
        3. **Major Levels Table** - Significant gamma walls for quick reference
        4. **Heatmap** - GEX distribution by strike and expiration
        5. **Raw Data** - Full dataset with CSV download option
        """)


if __name__ == "__main__":
    main()
