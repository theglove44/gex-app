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

# === DARK THEME COLOR PALETTE ===
COLORS = {
    # Background colors
    'bg_primary': '#0d1117',
    'bg_secondary': '#161b22',
    'bg_card': '#21262d',
    'bg_elevated': '#30363d',

    # Text colors
    'text_primary': '#f0f6fc',
    'text_secondary': '#8b949e',
    'text_muted': '#6e7681',

    # Accent colors (vibrant neon)
    'cyan': '#00d4ff',
    'magenta': '#ff006e',
    'lime': '#39ff14',
    'orange': '#ff9500',
    'purple': '#bf5af2',
    'yellow': '#ffd60a',

    # GEX specific
    'call_gex': '#00ff88',      # Bright green for calls
    'put_gex': '#ff3366',       # Bright red/pink for puts
    'spot_line': '#00d4ff',     # Cyan for spot price
    'zero_gamma': '#ffd60a',    # Yellow for zero gamma

    # Gradients (for CSS)
    'gradient_green': 'linear-gradient(180deg, #00ff88 0%, #00cc6a 100%)',
    'gradient_red': 'linear-gradient(180deg, #ff3366 0%, #cc2952 100%)',
    'gradient_card': 'linear-gradient(135deg, rgba(0,212,255,0.1) 0%, rgba(191,90,242,0.1) 100%)',
}

# Custom CSS for dark theme
st.markdown(f"""
<style>
    /* === DARK THEME BASE === */
    .stApp {{
        background: linear-gradient(180deg, {COLORS['bg_primary']} 0%, #0a0f14 100%);
    }}

    /* Main content area */
    .main .block-container {{
        background: transparent;
        padding-top: 2rem;
    }}

    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: {COLORS['bg_secondary']};
        border-right: 1px solid {COLORS['bg_elevated']};
    }}

    [data-testid="stSidebar"] .stMarkdown {{
        color: {COLORS['text_primary']};
    }}

    /* Headers */
    .main-header {{
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, {COLORS['cyan']} 0%, {COLORS['purple']} 50%, {COLORS['magenta']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0;
        letter-spacing: -0.02em;
    }}

    .sub-header {{
        font-size: 1.1rem;
        color: {COLORS['text_secondary']};
        margin-top: 0.25rem;
        font-weight: 400;
    }}

    /* === GLASSMORPHISM METRIC CARDS === */
    [data-testid="stMetric"] {{
        background: {COLORS['gradient_card']};
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    [data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,212,255,0.2);
    }}

    [data-testid="stMetric"] label {{
        color: {COLORS['text_secondary']} !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {COLORS['text_primary']} !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }}

    [data-testid="stMetric"] [data-testid="stMetricDelta"] {{
        color: {COLORS['call_gex']} !important;
    }}

    /* === CUSTOM METRIC CARDS === */
    .metric-card {{
        background: {COLORS['gradient_card']};
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }}

    .metric-card.call {{
        border-left: 4px solid {COLORS['call_gex']};
    }}

    .metric-card.put {{
        border-left: 4px solid {COLORS['put_gex']};
    }}

    .metric-card.neutral {{
        border-left: 4px solid {COLORS['cyan']};
    }}

    .metric-label {{
        color: {COLORS['text_secondary']};
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }}

    .metric-value.positive {{
        color: {COLORS['call_gex']};
        text-shadow: 0 0 20px rgba(0,255,136,0.5);
    }}

    .metric-value.negative {{
        color: {COLORS['put_gex']};
        text-shadow: 0 0 20px rgba(255,51,102,0.5);
    }}

    .metric-value.neutral {{
        color: {COLORS['cyan']};
        text-shadow: 0 0 20px rgba(0,212,255,0.5);
    }}

    /* === SECTION STYLING === */
    .section-header {{
        color: {COLORS['text_primary']};
        font-size: 1.3rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {COLORS['bg_elevated']};
    }}

    /* === DATAFRAME STYLING === */
    [data-testid="stDataFrame"] {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        border: 1px solid {COLORS['bg_elevated']};
    }}

    /* === BUTTON STYLING === */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['cyan']} 0%, {COLORS['purple']} 100%);
        color: {COLORS['bg_primary']};
        font-weight: 600;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,212,255,0.3);
    }}

    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0,212,255,0.5);
    }}

    /* === EXPANDER STYLING === */
    [data-testid="stExpander"] {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['bg_elevated']};
        border-radius: 12px;
    }}

    [data-testid="stExpander"] summary {{
        color: {COLORS['text_primary']};
    }}

    /* === SLIDER STYLING === */
    .stSlider > div > div {{
        background: {COLORS['bg_elevated']};
    }}

    .stSlider > div > div > div {{
        background: linear-gradient(90deg, {COLORS['cyan']}, {COLORS['purple']});
    }}

    /* === RADIO BUTTONS === */
    .stRadio > div {{
        background: {COLORS['bg_card']};
        border-radius: 12px;
        padding: 0.5rem;
    }}

    /* === INFO/WARNING BOXES === */
    .stAlert {{
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['bg_elevated']};
        border-radius: 12px;
    }}

    /* === DIVIDERS === */
    hr {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, {COLORS['bg_elevated']}, transparent);
        margin: 2rem 0;
    }}

    /* === SELECTBOX === */
    .stSelectbox > div > div {{
        background: {COLORS['bg_card']};
        border-color: {COLORS['bg_elevated']};
    }}

    /* Text inputs */
    .stTextInput > div > div > input {{
        background: {COLORS['bg_card']};
        border-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
    }}

    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* Glow effects for key elements */
    .glow-green {{
        box-shadow: 0 0 20px rgba(0,255,136,0.3);
    }}

    .glow-red {{
        box-shadow: 0 0 20px rgba(255,51,102,0.3);
    }}

    .glow-cyan {{
        box-shadow: 0 0 20px rgba(0,212,255,0.3);
    }}
</style>
""", unsafe_allow_html=True)


def _get_dark_layout() -> dict:
    """Return common dark theme layout settings for Plotly charts."""
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(13,17,23,0.8)',
        font=dict(
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color=COLORS['text_primary']
        ),
        xaxis=dict(
            gridcolor='rgba(48,54,61,0.5)',
            zerolinecolor=COLORS['bg_elevated'],
            tickfont=dict(color=COLORS['text_secondary'], size=11),
            title_font=dict(color=COLORS['text_secondary'], size=12)
        ),
        yaxis=dict(
            gridcolor='rgba(48,54,61,0.5)',
            zerolinecolor=COLORS['text_muted'],
            zerolinewidth=2,
            tickfont=dict(color=COLORS['text_secondary'], size=11),
            title_font=dict(color=COLORS['text_secondary'], size=12)
        ),
        hoverlabel=dict(
            bgcolor=COLORS['bg_card'],
            bordercolor=COLORS['bg_elevated'],
            font=dict(color=COLORS['text_primary'], size=13)
        ),
        margin=dict(l=60, r=40, t=80, b=60)
    )


def _add_common_vertical_markers(fig: go.Figure, result):
    """Add spot/zero gamma/call wall/put wall markers to a figure."""

    # Spot price line - bright cyan with glow effect
    fig.add_vline(
        x=result.spot_price,
        line_dash="dash",
        line_color=COLORS['spot_line'],
        line_width=2,
        annotation_text=f"SPOT ${result.spot_price:.2f}",
        annotation_position="top",
        annotation_font_size=11,
        annotation_font_color=COLORS['spot_line'],
        annotation_bgcolor='rgba(0,212,255,0.15)',
        annotation_bordercolor=COLORS['spot_line'],
        annotation_borderwidth=1,
        annotation_borderpad=4
    )

    # Zero gamma level (if calculated) - bright yellow
    if result.zero_gamma_level:
        fig.add_vline(
            x=result.zero_gamma_level,
            line_dash="dot",
            line_color=COLORS['zero_gamma'],
            line_width=2,
            annotation_text=f"ZERO γ ${result.zero_gamma_level:.0f}",
            annotation_position="bottom",
            annotation_font_size=10,
            annotation_font_color=COLORS['zero_gamma'],
            annotation_bgcolor='rgba(255,214,10,0.15)',
            annotation_bordercolor=COLORS['zero_gamma'],
            annotation_borderwidth=1,
            annotation_borderpad=4
        )

    # Call wall marker - bright green
    if result.call_wall:
        fig.add_vline(
            x=result.call_wall,
            line_dash="solid",
            line_color=COLORS['call_gex'],
            line_width=2,
            opacity=0.7
        )
        fig.add_annotation(
            x=result.call_wall,
            y=1,
            yref='paper',
            text=f"CALL WALL ${result.call_wall:.0f}",
            showarrow=False,
            font=dict(color=COLORS['call_gex'], size=9),
            bgcolor='rgba(0,255,136,0.15)',
            bordercolor=COLORS['call_gex'],
            borderwidth=1,
            borderpad=3
        )

    # Put wall marker - bright red/pink
    if result.put_wall:
        fig.add_vline(
            x=result.put_wall,
            line_dash="solid",
            line_color=COLORS['put_gex'],
            line_width=2,
            opacity=0.7
        )
        fig.add_annotation(
            x=result.put_wall,
            y=1,
            yref='paper',
            text=f"PUT WALL ${result.put_wall:.0f}",
            showarrow=False,
            font=dict(color=COLORS['put_gex'], size=9),
            bgcolor='rgba(255,51,102,0.15)',
            bordercolor=COLORS['put_gex'],
            borderwidth=1,
            borderpad=3
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
    """Create an interactive Plotly bar chart for GEX profile with dark theme."""
    df = result.strike_gex

    # Separate positive and negative values for different styling
    pos_mask = df['Net GEX ($M)'] >= 0
    neg_mask = df['Net GEX ($M)'] < 0

    fig = go.Figure()

    # Positive GEX bars (calls) - gradient green
    if pos_mask.any():
        fig.add_trace(go.Bar(
            x=df.loc[pos_mask, 'Strike'],
            y=df.loc[pos_mask, 'Net GEX ($M)'],
            marker=dict(
                color=df.loc[pos_mask, 'Net GEX ($M)'],
                colorscale=[
                    [0, 'rgba(0,180,100,0.7)'],
                    [1, COLORS['call_gex']]
                ],
                line=dict(color=COLORS['call_gex'], width=1)
            ),
            name='Call GEX',
            hovertemplate=(
                '<b style="color:#00ff88">▲ CALL GAMMA</b><br>'
                'Strike: <b>$%{x:.0f}</b><br>'
                'GEX: <b>$%{y:+.1f}M</b>'
                '<extra></extra>'
            )
        ))

    # Negative GEX bars (puts) - gradient red
    if neg_mask.any():
        fig.add_trace(go.Bar(
            x=df.loc[neg_mask, 'Strike'],
            y=df.loc[neg_mask, 'Net GEX ($M)'],
            marker=dict(
                color=df.loc[neg_mask, 'Net GEX ($M)'].abs(),
                colorscale=[
                    [0, 'rgba(180,50,80,0.7)'],
                    [1, COLORS['put_gex']]
                ],
                line=dict(color=COLORS['put_gex'], width=1)
            ),
            name='Put GEX',
            hovertemplate=(
                '<b style="color:#ff3366">▼ PUT GAMMA</b><br>'
                'Strike: <b>$%{x:.0f}</b><br>'
                'GEX: <b>$%{y:+.1f}M</b>'
                '<extra></extra>'
            )
        ))

    fig = _add_common_vertical_markers(fig, result)

    # Apply dark theme layout
    dark_layout = _get_dark_layout()
    fig.update_layout(
        **dark_layout,
        title=dict(
            text=(
                f'<span style="font-size:24px;font-weight:700">{result.symbol}</span>'
                f'<span style="font-size:16px;color:{COLORS["text_secondary"]}"> '
                f'Gamma Exposure Profile</span>'
                f'<br><span style="font-size:12px;color:{COLORS["text_muted"]}">'
                f'0-{result.max_dte} DTE • {len(df)} Strikes</span>'
            ),
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis_title="Strike Price",
        yaxis_title="Net GEX ($M)",
        height=520,
        hovermode='x unified',
        showlegend=False,
        bargap=0.15,
        xaxis=dict(
            **dark_layout['xaxis'],
            tickformat="$,.0f",
            showgrid=True,
            gridwidth=1
        ),
        yaxis=dict(
            **dark_layout['yaxis'],
            tickformat="$,.0f",
            ticksuffix="M",
            showgrid=True,
            gridwidth=1,
            zeroline=True
        )
    )

    return fig


def create_breakdown_chart(result) -> go.Figure:
    """Create stacked call/put bars with dark theme styling."""

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

    # Call GEX bars - bright cyan/green
    fig.add_trace(go.Bar(
        x=all_strikes,
        y=call_values,
        name='Call GEX',
        marker=dict(
            color=COLORS['call_gex'],
            line=dict(color='rgba(0,255,136,0.8)', width=1)
        ),
        opacity=0.85,
        hovertemplate=(
            '<b style="color:#00ff88">▲ CALL</b><br>'
            'Strike: <b>$%{x:.0f}</b><br>'
            'GEX: <b>$%{y:+.1f}M</b>'
            '<extra></extra>'
        )
    ))

    # Put GEX bars - bright magenta/red
    fig.add_trace(go.Bar(
        x=all_strikes,
        y=put_values,
        name='Put GEX',
        marker=dict(
            color=COLORS['put_gex'],
            line=dict(color='rgba(255,51,102,0.8)', width=1)
        ),
        opacity=0.85,
        hovertemplate=(
            '<b style="color:#ff3366">▼ PUT</b><br>'
            'Strike: <b>$%{x:.0f}</b><br>'
            'GEX: <b>$%{y:+.1f}M</b>'
            '<extra></extra>'
        )
    ))

    fig = _add_common_vertical_markers(fig, result)

    # Apply dark theme layout
    dark_layout = _get_dark_layout()
    fig.update_layout(
        **dark_layout,
        barmode='relative',
        title=dict(
            text=(
                f'<span style="font-size:24px;font-weight:700">{result.symbol}</span>'
                f'<span style="font-size:16px;color:{COLORS["text_secondary"]}"> '
                f'Call vs Put Breakdown</span>'
            ),
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis_title="Strike Price",
        yaxis_title="GEX Contribution ($M)",
        height=520,
        hovermode='x unified',
        bargap=0.15,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color=COLORS['text_primary'], size=12)
        ),
        xaxis=dict(
            **dark_layout['xaxis'],
            tickformat="$,.0f",
            showgrid=True,
            gridwidth=1
        ),
        yaxis=dict(
            **dark_layout['yaxis'],
            tickformat="$,.0f",
            ticksuffix="M",
            showgrid=True,
            gridwidth=1,
            zeroline=True
        )
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
    """Create a heatmap showing GEX by strike and expiration with dark theme."""
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

    # Custom colorscale for dark theme - vibrant neon colors
    colorscale = [
        [0.0, '#ff3366'],       # Bright red/pink for most negative
        [0.25, '#cc2952'],      # Darker red
        [0.45, COLORS['bg_elevated']],  # Dark gray near zero
        [0.5, COLORS['bg_card']],       # Dark at zero
        [0.55, COLORS['bg_elevated']],  # Dark gray near zero
        [0.75, '#00cc6a'],      # Darker green
        [1.0, '#00ff88']        # Bright green for most positive
    ]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[str(d) for d in pivot.columns],
        y=[f"${s:.0f}" for s in pivot.index],
        colorscale=colorscale,
        zmid=0,
        hovertemplate=(
            '<b>Strike: %{y}</b><br>'
            'Expiration: %{x}<br>'
            'GEX: <b>$%{z:+.1f}M</b>'
            '<extra></extra>'
        ),
        colorbar=dict(
            title=dict(
                text='GEX ($M)',
                font=dict(color=COLORS['text_secondary'], size=11)
            ),
            tickfont=dict(color=COLORS['text_secondary'], size=10),
            bgcolor='rgba(0,0,0,0)',
            borderwidth=0,
            tickformat='$,.0f',
            ticksuffix='M'
        )
    ))

    dark_layout = _get_dark_layout()
    fig.update_layout(
        **dark_layout,
        title=dict(
            text=(
                f'<span style="font-size:16px;font-weight:600">'
                f'GEX by Strike & Expiration</span>'
            ),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Expiration Date",
        yaxis_title="Strike Price",
        height=420,
        xaxis=dict(
            **dark_layout['xaxis'],
            tickangle=45,
            side='bottom'
        ),
        yaxis=dict(
            **dark_layout['yaxis']
        )
    )

    return fig


def render_metric_card(label: str, value: str, card_type: str = "neutral", subtitle: str = "") -> str:
    """Render a custom glassmorphism metric card as HTML."""
    value_class = {
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral"
    }.get(card_type, "neutral")

    subtitle_html = f'<p style="color:{COLORS["text_muted"]};font-size:0.7rem;margin:0.25rem 0 0 0;">{subtitle}</p>' if subtitle else ""

    return f"""
    <div class="metric-card {card_type}">
        <p class="metric-label">{label}</p>
        <p class="metric-value {value_class}">{value}</p>
        {subtitle_html}
    </div>
    """


def main():
    # Header with gradient text
    st.markdown('''
    <div style="text-align: center; padding: 1rem 0 0.5rem 0;">
        <p class="main-header">GEX Tool</p>
        <p class="sub-header">Real-Time Gamma Exposure Analysis</p>
    </div>
    ''', unsafe_allow_html=True)
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
        st.markdown(f'''
        <div style="text-align:center;padding:0.5rem 0 1rem 0;">
            <span style="font-size:1.5rem;font-weight:700;color:{COLORS['text_primary']};">
                Settings
            </span>
        </div>
        ''', unsafe_allow_html=True)

        # Symbol selection
        st.markdown(f'<p style="color:{COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">SYMBOL</p>', unsafe_allow_html=True)
        symbol = st.selectbox(
            "Symbol",
            options=["SPY", "QQQ", "IWM", "DIA", "AAPL", "TSLA", "NVDA", "AMD", "AMZN", "MSFT"],
            index=0,
            help="Select the underlying symbol to analyze",
            label_visibility="collapsed"
        )

        # Custom symbol input
        custom_symbol = st.text_input(
            "Or enter custom symbol",
            placeholder="Enter custom symbol...",
            help="Enter any optionable symbol",
            label_visibility="collapsed"
        )
        if custom_symbol:
            is_valid, error_msg = validate_symbol(custom_symbol)
            if not is_valid:
                st.error(f"Invalid symbol: {error_msg}")
                st.stop()
            symbol = custom_symbol.strip().upper()

        st.markdown("<br>", unsafe_allow_html=True)

        # DTE slider
        st.markdown(f'<p style="color:{COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">MAX DAYS TO EXPIRATION</p>', unsafe_allow_html=True)
        max_dte = st.slider(
            "Max Days to Expiration",
            min_value=1,
            max_value=60,
            value=30,
            step=1,
            help="Include options expiring within this many days",
            label_visibility="collapsed"
        )

        # Strike range
        st.markdown(f'<p style="color:{COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">STRIKE RANGE (% FROM SPOT)</p>', unsafe_allow_html=True)
        strike_range = st.slider(
            "Strike Range (% from spot)",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Filter strikes within this percentage of spot price",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

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

        st.markdown("<br>", unsafe_allow_html=True)

        # Calculate button
        calculate_btn = st.button(
            "Calculate GEX",
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

        # Symbol badge and timestamp
        st.markdown(f'''
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;gap:1rem;">
                <span style="
                    background:linear-gradient(135deg,{COLORS['cyan']},{COLORS['purple']});
                    padding:0.5rem 1.25rem;
                    border-radius:8px;
                    font-size:1.5rem;
                    font-weight:700;
                    color:{COLORS['bg_primary']};
                ">{result.symbol}</span>
                <span style="color:{COLORS['text_muted']};font-size:0.9rem;">
                    {last_update.strftime('%Y-%m-%d %H:%M:%S')}
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Calculate values
        total_call_gex = result.df[result.df['Type'] == 'Call']['Net GEX ($M)'].sum()
        total_put_gex = result.df[result.df['Type'] == 'Put']['Net GEX ($M)'].sum()
        net_at_spot = interpolate_gex_at_spot(result.strike_gex, result.spot_price)

        # Primary metrics row with custom cards
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(render_metric_card(
                "Spot Price",
                f"${result.spot_price:.2f}",
                "neutral"
            ), unsafe_allow_html=True)

        with col2:
            gex_type = "positive" if result.total_gex >= 0 else "negative"
            st.markdown(render_metric_card(
                "Total Net GEX",
                f"${result.total_gex:+,.0f}M",
                gex_type
            ), unsafe_allow_html=True)

        with col3:
            st.markdown(render_metric_card(
                "Zero Gamma",
                f"${result.zero_gamma_level:.0f}" if result.zero_gamma_level else "—",
                "neutral",
                "Flip level"
            ), unsafe_allow_html=True)

        with col4:
            st.markdown(render_metric_card(
                "Call Wall",
                f"${result.call_wall:.0f}" if result.call_wall else "—",
                "positive",
                "Resistance"
            ), unsafe_allow_html=True)

        with col5:
            st.markdown(render_metric_card(
                "Put Wall",
                f"${result.put_wall:.0f}" if result.put_wall else "—",
                "negative",
                "Support"
            ), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Secondary metrics - Call/Put breakdown
        snap_col1, snap_col2, snap_col3 = st.columns(3)

        with snap_col1:
            st.markdown(render_metric_card(
                "Call Gamma",
                f"${total_call_gex:+,.0f}M",
                "positive"
            ), unsafe_allow_html=True)

        with snap_col2:
            st.markdown(render_metric_card(
                "Put Gamma",
                f"${total_put_gex:+,.0f}M",
                "negative"
            ), unsafe_allow_html=True)

        with snap_col3:
            net_type = "positive" if (net_at_spot or 0) >= 0 else "negative"
            st.markdown(render_metric_card(
                "Net at Spot",
                f"${net_at_spot:+,.0f}M" if net_at_spot is not None else "—",
                net_type,
                "Interpolated"
            ), unsafe_allow_html=True)

        # Main chart section
        st.markdown(f'''
        <p class="section-header">Gamma Exposure Profile</p>
        ''', unsafe_allow_html=True)

        chart_mode = st.radio(
            "Chart view",
            options=["Net Gamma Exposure", "Call vs Put Breakdown"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if chart_mode == "Net Gamma Exposure":
            fig = create_gex_chart(result)
        else:
            fig = create_breakdown_chart(result)

        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        })

        # Two columns for additional info
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown(f'''
            <p class="section-header">Major Gamma Levels</p>
            ''', unsafe_allow_html=True)

            if not result.major_levels.empty:
                # Style the dataframe
                styled_df = result.major_levels.copy()
                styled_df['Strike'] = styled_df['Strike'].apply(lambda x: f"${x:.0f}")
                styled_df['Type'] = styled_df['Net GEX ($M)'].apply(
                    lambda x: "CALL" if x > 0 else "PUT"
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
                st.markdown(f'''
                <div style="
                    background:{COLORS['bg_card']};
                    border:1px solid {COLORS['bg_elevated']};
                    border-radius:12px;
                    padding:2rem;
                    text-align:center;
                    color:{COLORS['text_muted']};
                ">
                    No major gamma levels found above threshold
                </div>
                ''', unsafe_allow_html=True)

        with col_right:
            st.markdown(f'''
            <p class="section-header">GEX by Expiration</p>
            ''', unsafe_allow_html=True)

            heatmap_fig = create_heatmap_by_expiration(result)
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True, config={
                    'displayModeBar': False
                })

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
        # Initial state - show welcome screen
        st.markdown(f'''
        <div style="
            background: {COLORS['gradient_card']};
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 3rem;
            text-align: center;
            margin: 2rem 0;
        ">
            <h2 style="
                color: {COLORS['text_primary']};
                font-size: 1.8rem;
                margin-bottom: 1rem;
            ">Welcome to GEX Tool</h2>
            <p style="
                color: {COLORS['text_secondary']};
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
                    border-left: 3px solid {COLORS['call_gex']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{COLORS['call_gex']};font-weight:600;margin:0 0 0.25rem 0;">Call Walls</p>
                    <p style="color:{COLORS['text_muted']};font-size:0.85rem;margin:0;">Resistance levels</p>
                </div>
                <div style="
                    background: rgba(255,51,102,0.1);
                    border-left: 3px solid {COLORS['put_gex']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{COLORS['put_gex']};font-weight:600;margin:0 0 0.25rem 0;">Put Walls</p>
                    <p style="color:{COLORS['text_muted']};font-size:0.85rem;margin:0;">Support levels</p>
                </div>
                <div style="
                    background: rgba(255,214,10,0.1);
                    border-left: 3px solid {COLORS['zero_gamma']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{COLORS['zero_gamma']};font-weight:600;margin:0 0 0.25rem 0;">Zero Gamma</p>
                    <p style="color:{COLORS['text_muted']};font-size:0.85rem;margin:0;">Volatility flip point</p>
                </div>
                <div style="
                    background: rgba(0,212,255,0.1);
                    border-left: 3px solid {COLORS['cyan']};
                    padding: 1rem;
                    border-radius: 8px;
                ">
                    <p style="color:{COLORS['cyan']};font-weight:600;margin:0 0 0.25rem 0;">Heatmaps</p>
                    <p style="color:{COLORS['text_muted']};font-size:0.85rem;margin:0;">By strike & expiry</p>
                </div>
            </div>
        </div>

        <p style="text-align:center;color:{COLORS['text_muted']};margin-top:1rem;">
            Configure settings in the sidebar and click <b>Calculate GEX</b> to begin
        </p>
        ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
