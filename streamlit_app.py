"""
GEX Tool - Gamma Exposure Web Dashboard
A Streamlit-based interactive dashboard for analyzing gamma exposure profiles.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from gex_core import run_gex_calculation, get_credentials, create_session
import time

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

# Load CSS from external file with version tracking
# CSS last tested with Streamlit 1.40.0 (Dec 2025)
try:
    with open('assets/dark_theme.css', 'r') as f:
        css_content = f.read()

    # Inject CSS variables for dynamic color values
    st.markdown(f"""
    <style>
        :root {{
            --bg-primary: {COLORS['bg_primary']};
            --bg-secondary: {COLORS['bg_secondary']};
            --bg-card: {COLORS['bg_card']};
            --bg-elevated: {COLORS['bg_elevated']};
            --text-primary: {COLORS['text_primary']};
            --text-secondary: {COLORS['text_secondary']};
            --text-muted: {COLORS['text_muted']};
            --cyan: {COLORS['cyan']};
            --magenta: {COLORS['magenta']};
            --lime: {COLORS['lime']};
            --orange: {COLORS['orange']};
            --purple: {COLORS['purple']};
            --yellow: {COLORS['yellow']};
            --call-gex: {COLORS['call_gex']};
            --put-gex: {COLORS['put_gex']};
            --spot-line: {COLORS['spot_line']};
            --zero-gamma: {COLORS['zero_gamma']};
            --gradient-card: {COLORS['gradient_card']};
        }}

        {css_content}
    </style>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ Dark theme CSS file not found. Using default Streamlit theme.")


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
    
    # Merge specific axis overrides into the layout dict directly
    if 'xaxis' not in dark_layout: dark_layout['xaxis'] = {}
    dark_layout['xaxis'].update(dict(
        tickformat="$,.0f",
        showgrid=True,
        gridwidth=1
    ))
    
    if 'yaxis' not in dark_layout: dark_layout['yaxis'] = {}
    dark_layout['yaxis'].update(dict(
        tickformat="$,.0f",
        ticksuffix="M",
        showgrid=True,
        gridwidth=1,
        zeroline=True
    ))

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
        bargap=0.15
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
    
    # Merge specific axis overrides into the layout dict directly
    if 'xaxis' not in dark_layout: dark_layout['xaxis'] = {}
    dark_layout['xaxis'].update(dict(
        tickformat="$,.0f",
        showgrid=True,
        gridwidth=1
    ))
    
    if 'yaxis' not in dark_layout: dark_layout['yaxis'] = {}
    dark_layout['yaxis'].update(dict(
        tickformat="$,.0f",
        ticksuffix="M",
        showgrid=True,
        gridwidth=1,
        zeroline=True
    ))

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
        )
    )

    return fig



def render_gex_table(result) -> str:
    """Render the detailed GEX table with Cheddarflow-style visuals."""
    # Group by Strike to get aggregates
    df = result.df.copy()
    
    # Pre-calculate Call/Put specific columns to make summing easier
    df['Call GEX'] = df.apply(lambda x: x['Net GEX ($M)'] if x['Type'] == 'Call' else 0, axis=1)
    df['Put GEX'] = df.apply(lambda x: x['Net GEX ($M)'] if x['Type'] == 'Put' else 0, axis=1)
    df['Call OI'] = df.apply(lambda x: x['OI'] if x['Type'] == 'Call' else 0, axis=1)
    df['Put OI'] = df.apply(lambda x: x['OI'] if x['Type'] == 'Put' else 0, axis=1)
    
    agg = df.groupby('Strike').agg({
        'Net GEX ($M)': 'sum',
        'Call GEX': 'sum',
        'Put GEX': 'sum',
        'Call OI': 'sum',
        'Put OI': 'sum',
        'OI': 'sum'
    }).rename(columns={'Net GEX ($M)': 'Net GEX', 'OI': 'Total OI'})
    
    # Filter for strikes around spot (custom visual range)
    # We want roughly +/- 15 strikes from spot to keep it focused like the screenshot
    spot_price = result.spot_price
    strikes = sorted(agg.index.unique())
    
    # Find index closest to spot
    closest_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price))
    
    # Slice range
    start_idx = max(0, closest_idx - 12)
    end_idx = min(len(strikes), closest_idx + 13)
    
    relevant_strikes = strikes[start_idx:end_idx]
    agg = agg.loc[relevant_strikes]
    agg = agg.sort_index(ascending=False) # Highest strike first
    
    # Max values for bar scaling
    max_net = max(agg['Net GEX'].abs().max(), 1)
    
    html = '<div class="gex-table-container"><table class="gex-table">'
    html += '''
    <thead>
        <tr class="gex-header">
            <th class="th-strike">Strike</th>
            <th class="th-viz"></th> <!-- Visual Bar Column -->
            <th class="th-net">Net GEX</th>
            <th class="th-call">Call GEX</th>
            <th class="th-put">Put GEX</th>
            <th class="th-oi">Call OI</th>
            <th class="th-oi">Put OI</th>
            <th class="th-oi">Total OI</th>
        </tr>
    </thead>
    <tbody>
    '''
    
    spot_inserted = False
    
    # helper for formatting
    def fmt_curr(x): return f"{x:,.1f}M"
    def fmt_int(x): return f"{x:,}"
    
    for strike, row in agg.iterrows():
        # Insert spot row if we just passed the spot price
        if not spot_inserted and strike < spot_price:
            html += f'''
            <tr class="spot-row">
                <td class="gex-cell-strike">
                    {spot_price:.2f}
                    <span class="spot-label">Spot Price</span>
                </td>
                <td colspan="7"></td>
            </tr>
            '''
            spot_inserted = True
            
        net = row['Net GEX']
        call = row['Call GEX']
        put = row['Put GEX']
        c_oi = int(row['Call OI'])
        p_oi = int(row['Put OI'])
        t_oi = int(row['Total OI'])
        
        # Bar chart generation (Split Axis)
        pct = min(abs(net) / max_net * 100, 100)
        width_style = f"width: {pct}%;"
        
        # Determine which side of the axis the bar goes
        # Negative (Red) -> Left side, aligned right
        # Positive (Green) -> Right side, aligned left
        
        left_bar = ""
        right_bar = ""
        
        if net < 0:
            left_bar = f'<div class="gex-bar bar-neg" style="{width_style}"></div>'
        else:
            right_bar = f'<div class="gex-bar bar-pos" style="{width_style}"></div>'
        
        # The Viz cell
        viz_html = f'''
        <div class="viz-split-container">
            <div class="viz-left">{left_bar}</div>
            <div class="viz-axis"></div>
            <div class="viz-right">{right_bar}</div>
        </div>
        '''

        # Wall labels
        strike_label = f"{strike:.2f}"
        if result.call_wall and strike == result.call_wall:
            strike_label += ' <span class="wall-label call-wall-label">CW</span>'
        if result.put_wall and strike == result.put_wall:
            strike_label += ' <span class="wall-label put-wall-label">PW</span>'
            
        net_class = "metric-value " + ("positive" if net >= 0 else "negative")

        html += f'''
        <tr class="gex-row">
            <td class="gex-cell gex-cell-strike">{strike_label}</td>
            <td class="gex-cell gex-cell-viz">{viz_html}</td>
            <td class="gex-cell {net_class}">{fmt_curr(net)}</td>
            <td class="gex-cell text-muted">{fmt_curr(call)}</td>
            <td class="gex-cell text-muted">{fmt_curr(put)}</td>
            <td class="gex-cell text-muted">{fmt_int(c_oi)}</td>
            <td class="gex-cell text-muted">{fmt_int(p_oi)}</td>
            <td class="gex-cell text-muted">{fmt_int(t_oi)}</td>
        </tr>
        '''
        
    html += '</tbody></table></div>'
    return html


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


def render_gex_heatmap(result) -> str:
    """Render a custom HTML heatmap matching the Cheddarflow style."""
    df = result.df.copy()

    if df.empty:
        return ""

    # Pivot data: index=Strike, columns=Expiration, values=Net GEX
    pivot = df.pivot_table(
        values='Net GEX ($M)',
        index='Strike',
        columns='Expiration',
        aggfunc='sum',
        fill_value=0
    )

    # Sort expirations (columns) and strikes (rows desc)
    pivot = pivot.sort_index(ascending=False)

    # Filter strikes around spot to keep it focused
    spot_price = result.spot_price
    strikes = sorted(pivot.index)
    
    # Find closest strike index
    closest_idx = 0
    if strikes:
        closest_idx = min(range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price))

    # Range of strikes to show (approx +/- 15 from spot)
    start_idx = max(0, closest_idx - 15)
    end_idx = min(len(strikes), closest_idx + 16)

    relevant_strikes = strikes[start_idx:end_idx]
    # Filter pivot and sort descending for display (high strikes at top)
    pivot = pivot.loc[relevant_strikes].sort_index(ascending=False)

    # Date formatting for headers "DEC 08"
    # Columns are datetime.date objects
    headers = [d.strftime('%b %d').upper() for d in pivot.columns]

    # HTML Construction
    html = '<div class="heatmap-container"><table class="heatmap-table">'

    # Header Row
    html += '<thead><tr class="heatmap-header"><th></th>'  # Empty corner cell
    for h in headers:
        html += f'<th>{h}</th>'
    html += '</tr></thead><tbody>'

    # Determine max value for opacity scaling
    # We use a localized max for the visible range to ensure good contrast
    if not pivot.empty:
        max_val = pivot.abs().max().max()
    else:
        max_val = 1
        
    if max_val == 0: max_val = 1

    for strike, row in pivot.iterrows():
        # Highlight row if it is the closest strike to spot
        row_class = ""
        # Check if this strike is the absolute closest to spot
        if abs(strike - spot_price) == min([abs(s - spot_price) for s in strikes]):
             row_class = "heatmap-row-spot"

        html += f'<tr class="{row_class}">'
        html += f'<td class="heatmap-strike-cell">{strike:.0f}</td>'

        for date_col in pivot.columns:
            val = row[date_col]
            abs_val = abs(val)

            # Color logic
            # Green (Pos), Red (Neg)
            # Opacity based on magnitude relative to max
            # Min opacity 0.1 so non-zero values are visible
            alpha = min(abs_val / max_val * 0.9 + 0.1, 1.0) # Scale 0.1 to 1.0

            bg_color = "transparent"
            text_class = "cell-zero"
            val_str = ""

            if abs_val > 0.001: # Threshold to show
                if val > 0:
                    # Green: 0, 255, 136
                    bg_color = f"rgba(0, 255, 136, {alpha:.2f})"
                    text_class = "cell-pos"
                else:
                    # Red: 255, 51, 102
                    bg_color = f"rgba(255, 51, 102, {alpha:.2f})"
                    text_class = "cell-neg"

                # Format Value
                if abs_val >= 1:
                    val_str = f"{val:.1f}M"
                else:
                    val_str = f"{val*1000:.0f}K"
            
            style = f'background-color: {bg_color};'
            html += f'<td class="heatmap-cell {text_class}" style="{style}">{val_str}</td>'

        html += '</tr>'

    html += '</tbody></table></div>'
    return html


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


import time
from datetime import datetime
import streamlit as st

# Assuming COLORS, create_session, run_gex_calculation, create_gex_chart, create_breakdown_chart,
# render_gex_table, render_gex_heatmap are defined elsewhere in the file or imported.
# For this edit, I will assume they are available in the scope.

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
    # Create or reuse session
    if 'tt_session' not in st.session_state or st.session_state.tt_session is None:
        with st.spinner("Initializing Tastytrade session..."):
            try:
                # Assuming create_session() is defined elsewhere and handles credentials
                st.session_state.tt_session = create_session()
            except Exception as e:
                st.error(f"Failed to initialize Tastytrade session: {e}")
                st.stop()
            
    # Auto-update logic (just visual indicator, the loop is handled by the fragment decorator)
    if auto_update:
        st.markdown(f"""
            <div style="font-size:0.8rem;color:{COLORS['text_muted']};margin-bottom:1rem;">
                ⚡ Auto-updating every 60s
            </div>
        """, unsafe_allow_html=True)

    # Use a session state variable to track if we should be calculating
    # This helps in triggering the first run or re-runs when inputs change
    if 'last_run_params' not in st.session_state:
        st.session_state.last_run_params = {}
    
    current_params = {
        'symbol': symbol,
        'max_dte': max_dte,
        'strike_range_pct': strike_range_pct,
        'major_threshold': major_threshold,
        'data_wait': data_wait,
        'auto_update': auto_update
    }

    # Check if parameters have changed or if it's the first run
    params_changed = st.session_state.last_run_params != current_params
    
    # Button to trigger manual calculation
    calculate_btn = st.button("Calculate GEX", type="primary", use_container_width=True)
    
    # For auto-update, we always run if the session is stale or parameters changed.
    # Actually, with run_every, the function is called periodically.
    # We should run if:
    # 1. Button clicked
    # 2. Params changed
    # 3. Auto-update is ON (this function is called periodically, so we just run)
    
    should_run = calculate_btn or params_changed or auto_update
    
    # If we are in manual mode (passed auto_update=False), simple invalidation logic applies.
    # If in auto mode, we run every time this function is called (which is every 60s + interactions).

    if should_run:
        st.session_state.last_run_params = current_params # Update last run params
        
        status_container = st.empty()
        progress_bar = st.progress(0)
        
        def update_progress(msg):
            status_container.info(f"🔄 {msg}")
            
        try:
            session = st.session_state.get('tt_session')
            
            # If session is dead/missing, try to recreate
            if not session:
                update_progress("Re-initializing Tastytrade session...")
                session = create_session()
                st.session_state.tt_session = session

            # Initial calculation attempt
            update_progress(f"Calculating GEX for {symbol}...")
            result = run_gex_calculation(
                symbol=symbol, 
                max_dte=max_dte,
                strike_range_pct=strike_range_pct,
                major_level_threshold=major_threshold,
                data_wait_seconds=data_wait,
                progress_callback=update_progress,
                session=session
            )
            
            # Check for Unauthorized error and retry logic
            if result.error and "unauthorized" in result.error.lower():
                update_progress("Session expired. Re-authenticating...")
                # Clear invalid session
                if 'tt_session' in st.session_state:
                    del st.session_state.tt_session
                
                # Create new session
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
                        session=session
                    )
            
            progress_bar.progress(100)
            status_container.empty()
            time.sleep(0.5)
            progress_bar.empty()
            
            if result.error:
                st.error(f"❌ {result.error}")
                # If auth error persists, ensure session is cleared
                err_lower = result.error.lower()
                if "authentication" in err_lower or "credentials" in err_lower or "unauthorized" in err_lower:
                    if 'tt_session' in st.session_state:
                        del st.session_state.tt_session
            else:
                # Store result in session state for display
                st.session_state['gex_result'] = result
                st.session_state['last_update'] = datetime.now()
        
        except Exception as e:
            st.error(f"An unexpected error occurred during calculation: {str(e)}")
            # Clear session on error to be safe
            if 'tt_session' in st.session_state:
                del st.session_state.tt_session
    
    # Display results if available in session state
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

        # Main GEX Table
        st.markdown(f'''
        <p class="section-header">Gamma Exposure Profile</p>
        ''', unsafe_allow_html=True)

        gex_table_html = render_gex_table(result)
        st.html(gex_table_html)


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
            <p class="section-header">Net GEX Heatmap</p>
            ''', unsafe_allow_html=True)

            heatmap_html = render_gex_heatmap(result)
            st.html(heatmap_html)

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
        st.html(f'''
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
        ''')



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
        
        # Auto-update toggle
        st.markdown(f'<p style="color:{COLORS["text_secondary"]};font-size:0.8rem;margin-bottom:0.25rem;">AUTO UPDATE</p>', unsafe_allow_html=True)
        auto_update = st.checkbox(
            "Auto-update (every 60s)", 
            value=False,
            help="Automatically refresh data every minute"
        )

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.8rem;color:{COLORS['text_muted']};text-align:center;">
            v1.2.0 • Powered by Tastytrade
        </div>
        """, unsafe_allow_html=True)

    # Main content area - Render GEX Section via Fragment
    # Main content area - Render GEX Section via Fragment
    # Choose between auto-updating fragment or manual fragment based on toggle
    if auto_update:
        render_gex_section_auto(
            symbol, 
            max_dte, 
            strike_range / 100, 
            major_threshold, 
            data_wait, 
            auto_update
        )
    else:
        render_gex_section_manual(
            symbol, 
            max_dte, 
            strike_range / 100, 
            major_threshold, 
            data_wait, 
            auto_update
        )


if __name__ == "__main__":
    main()
