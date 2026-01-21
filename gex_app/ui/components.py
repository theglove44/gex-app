"""
UI components module for GEX Tool.
Reusable Streamlit and Plotly components for rendering charts, tables, and metrics.
"""

import pandas as pd
import plotly.graph_objects as go

from gex_app import config
from gex_app.core.gex_core import GEXResult


def apply_base_theme() -> None:
    """Inject the base dark theme CSS for consistent styling across pages."""
    from gex_app.ui.theme import apply_theme

    apply_theme()


def get_dark_layout() -> dict:
    """Return common dark theme layout settings for Plotly charts."""
    from gex_app.ui.theme import get_plotly_dark_layout

    return get_plotly_dark_layout()


def add_common_vertical_markers(fig: go.Figure, result: GEXResult) -> go.Figure:
    """Add spot/zero gamma/call wall/put wall markers to a figure."""

    # Spot price line - bright cyan with glow effect
    fig.add_vline(
        x=result.spot_price,
        line_dash="dash",
        line_color=config.COLORS["spot_line"],
        line_width=2,
        annotation_text=f"SPOT ${result.spot_price:.2f}",
        annotation_position="top",
        annotation_font_size=11,
        annotation_font_color=config.COLORS["spot_line"],
        annotation_bgcolor="rgba(0,212,255,0.15)",
        annotation_bordercolor=config.COLORS["spot_line"],
        annotation_borderwidth=1,
        annotation_borderpad=4,
    )

    # Zero gamma level (if calculated) - bright yellow
    if result.zero_gamma_level:
        fig.add_vline(
            x=result.zero_gamma_level,
            line_dash="dot",
            line_color=config.COLORS["zero_gamma"],
            line_width=2,
            annotation_text=f"ZERO γ ${result.zero_gamma_level:.0f}",
            annotation_position="bottom",
            annotation_font_size=10,
            annotation_font_color=config.COLORS["zero_gamma"],
            annotation_bgcolor="rgba(255,214,10,0.15)",
            annotation_bordercolor=config.COLORS["zero_gamma"],
            annotation_borderwidth=1,
            annotation_borderpad=4,
        )

    # Call wall marker - bright green
    if result.call_wall:
        fig.add_vline(
            x=result.call_wall,
            line_dash="solid",
            line_color=config.COLORS["call_gex"],
            line_width=2,
            opacity=0.7,
        )
        fig.add_annotation(
            x=result.call_wall,
            y=1,
            yref="paper",
            text=f"CALL WALL ${result.call_wall:.0f}",
            showarrow=False,
            font={"color": config.COLORS["call_gex"], "size": 9},
            bgcolor="rgba(0,255,136,0.15)",
            bordercolor=config.COLORS["call_gex"],
            borderwidth=1,
            borderpad=3,
        )

    # Put wall marker - bright red/pink
    if result.put_wall:
        fig.add_vline(
            x=result.put_wall,
            line_dash="solid",
            line_color=config.COLORS["put_gex"],
            line_width=2,
            opacity=0.7,
        )
        fig.add_annotation(
            x=result.put_wall,
            y=1,
            yref="paper",
            text=f"PUT WALL ${result.put_wall:.0f}",
            showarrow=False,
            font={"color": config.COLORS["put_gex"], "size": 9},
            bgcolor="rgba(255,51,102,0.15)",
            bordercolor=config.COLORS["put_gex"],
            borderwidth=1,
            borderpad=3,
        )

    return fig


def interpolate_gex_at_spot(strike_gex: pd.DataFrame, spot: float) -> float | None:
    """Estimate net gamma at the current spot using linear interpolation between strikes."""

    if strike_gex.empty:
        return None

    ordered = strike_gex.sort_values("Strike")
    strikes = ordered["Strike"].values
    gex_values = ordered["Net GEX ($M)"].values

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


def create_gex_chart(result: GEXResult) -> go.Figure:
    """Create an interactive Plotly bar chart for GEX profile with dark theme."""
    df = result.strike_gex

    # Separate positive and negative values for different styling
    pos_mask = df["Net GEX ($M)"] >= 0
    neg_mask = df["Net GEX ($M)"] < 0

    fig = go.Figure()

    # Positive GEX bars (calls) - gradient green
    if pos_mask.any():
        fig.add_trace(
            go.Bar(
                x=df.loc[pos_mask, "Strike"],
                y=df.loc[pos_mask, "Net GEX ($M)"],
                customdata=df.loc[pos_mask, ["Total OI", "Total Volume"]].values,
                marker={
                    "color": df.loc[pos_mask, "Net GEX ($M)"],
                    "colorscale": [
                        [0, "rgba(0,180,100,0.7)"],
                        [1, config.COLORS["call_gex"]],
                    ],
                    "line": {"color": config.COLORS["call_gex"], "width": 1},
                },
                name="Call GEX",
                hovertemplate=(
                    '<b style="color:#00ff88">▲ CALL GAMMA</b><br>'
                    "Strike: <b>$%{x:.0f}</b><br>"
                    "GEX: <b>$%{y:+.1f}M</b><br>"
                    "OI: <b>%{customdata[0]:,}</b><br>"
                    "Vol: <b>%{customdata[1]:,}</b>"
                    "<extra></extra>"
                ),
            )
        )

    # Negative GEX bars (puts) - gradient red
    if neg_mask.any():
        fig.add_trace(
            go.Bar(
                x=df.loc[neg_mask, "Strike"],
                y=df.loc[neg_mask, "Net GEX ($M)"],
                customdata=df.loc[neg_mask, ["Total OI", "Total Volume"]].values,
                marker={
                    "color": df.loc[neg_mask, "Net GEX ($M)"].abs(),
                    "colorscale": [
                        [0, "rgba(180,50,80,0.7)"],
                        [1, config.COLORS["put_gex"]],
                    ],
                    "line": {"color": config.COLORS["put_gex"], "width": 1},
                },
                name="Put GEX",
                hovertemplate=(
                    '<b style="color:#ff3366">▼ PUT GAMMA</b><br>'
                    "Strike: <b>$%{x:.0f}</b><br>"
                    "GEX: <b>$%{y:+.1f}M</b><br>"
                    "OI: <b>%{customdata[0]:,}</b><br>"
                    "Vol: <b>%{customdata[1]:,}</b>"
                    "<extra></extra>"
                ),
            )
        )

    fig = add_common_vertical_markers(fig, result)

    # Apply dark theme layout
    dark_layout = get_dark_layout()

    # Merge specific axis overrides into the layout dict directly
    if "xaxis" not in dark_layout:
        dark_layout["xaxis"] = {}
    dark_layout["xaxis"].update(
        {"tickformat": "$,.0f", "showgrid": True, "gridwidth": 1}
    )

    if "yaxis" not in dark_layout:
        dark_layout["yaxis"] = {}
    dark_layout["yaxis"].update(
        {
            "tickformat": "$,.0f",
            "ticksuffix": "M",
            "showgrid": True,
            "gridwidth": 1,
            "zeroline": True,
        }
    )

    fig.update_layout(
        **dark_layout,
        title={
            "text": (
                f'<span style="font-size:24px;font-weight:700">{result.symbol}</span>'
                f'<span style="font-size:16px;color:{config.COLORS["text_secondary"]}"> '
                f"Gamma Exposure Profile</span>"
                f'<br><span style="font-size:12px;color:{config.COLORS["text_muted"]}">'
                f"0-{result.max_dte} DTE • {len(df)} Strikes</span>"
            ),
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16},
        },
        xaxis_title="Strike Price",
        yaxis_title="Net GEX ($M)",
        height=520,
        hovermode="x unified",
        showlegend=False,
        bargap=0.3,
    )

    return fig


def create_breakdown_chart(result: GEXResult) -> go.Figure:
    """Create stacked call/put bars with dark theme styling."""

    calls = (
        result.df[result.df["Type"] == "Call"].groupby("Strike")["Net GEX ($M)"].sum()
    )
    puts = result.df[result.df["Type"] == "Put"].groupby("Strike")["Net GEX ($M)"].sum()

    all_strikes = sorted(set(calls.index).union(set(puts.index)))
    call_values = [calls.get(s, 0) for s in all_strikes]
    put_values = [puts.get(s, 0) for s in all_strikes]

    fig = go.Figure()

    # Call GEX bars - bright cyan/green
    fig.add_trace(
        go.Bar(
            x=all_strikes,
            y=call_values,
            name="Call GEX",
            marker={
                "color": config.COLORS["call_gex"],
                "line": {"color": "rgba(0,255,136,0.8)", "width": 1},
            },
            opacity=0.85,
            hovertemplate=(
                '<b style="color:#00ff88">▲ CALL</b><br>'
                "Strike: <b>$%{x:.0f}</b><br>"
                "GEX: <b>$%{y:+.1f}M</b>"
                "<extra></extra>"
            ),
        )
    )

    # Put GEX bars - bright magenta/red
    fig.add_trace(
        go.Bar(
            x=all_strikes,
            y=put_values,
            name="Put GEX",
            marker={
                "color": config.COLORS["put_gex"],
                "line": {"color": "rgba(255,51,102,0.8)", "width": 1},
            },
            opacity=0.85,
            hovertemplate=(
                '<b style="color:#ff3366">▼ PUT</b><br>'
                "Strike: <b>$%{x:.0f}</b><br>"
                "GEX: <b>$%{y:+.1f}M</b>"
                "<extra></extra>"
            ),
        )
    )

    fig = add_common_vertical_markers(fig, result)

    # Apply dark theme layout
    dark_layout = get_dark_layout()

    # Merge specific axis overrides into the layout dict directly
    if "xaxis" not in dark_layout:
        dark_layout["xaxis"] = {}
    dark_layout["xaxis"].update(
        {"tickformat": "$,.0f", "showgrid": True, "gridwidth": 1}
    )

    if "yaxis" not in dark_layout:
        dark_layout["yaxis"] = {}
    dark_layout["yaxis"].update(
        {
            "tickformat": "$,.0f",
            "ticksuffix": "M",
            "showgrid": True,
            "gridwidth": 1,
            "zeroline": True,
        }
    )

    fig.update_layout(
        **dark_layout,
        barmode="relative",
        title={
            "text": (
                f'<span style="font-size:24px;font-weight:700">{result.symbol}</span>'
                f'<span style="font-size:16px;color:{config.COLORS["text_secondary"]}"> '
                f"Call vs Put Breakdown</span>"
            ),
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16},
        },
        xaxis_title="Strike Price",
        yaxis_title="GEX Contribution ($M)",
        height=520,
        hovermode="x unified",
        bargap=0.15,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": config.COLORS["text_primary"], "size": 12},
        },
    )

    return fig


def render_gex_table(result: GEXResult) -> str:
    """Render the detailed GEX table with Cheddarflow-style visuals."""
    # Group by Strike to get aggregates
    df = result.df.copy()

    # Pre-calculate Call/Put specific columns to make summing easier
    df["Call GEX"] = df.apply(
        lambda x: x["Net GEX ($M)"] if x["Type"] == "Call" else 0, axis=1
    )
    df["Put GEX"] = df.apply(
        lambda x: x["Net GEX ($M)"] if x["Type"] == "Put" else 0, axis=1
    )
    df["Call OI"] = df.apply(lambda x: x["OI"] if x["Type"] == "Call" else 0, axis=1)
    df["Put OI"] = df.apply(lambda x: x["OI"] if x["Type"] == "Put" else 0, axis=1)

    agg = (
        df.groupby("Strike")
        .agg(
            {
                "Net GEX ($M)": "sum",
                "Call GEX": "sum",
                "Put GEX": "sum",
                "Call OI": "sum",
                "Put OI": "sum",
                "OI": "sum",
            }
        )
        .rename(columns={"Net GEX ($M)": "Net GEX", "OI": "Total OI"})
    )

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
    agg = agg.sort_index(ascending=False)  # Highest strike first

    # Max values for bar scaling
    max_net = max(agg["Net GEX"].abs().max(), 1)

    html = '<div class="gex-table-container"><table class="gex-table">'
    html += """
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
    """

    spot_inserted = False

    # helper for formatting
    def fmt_curr(x):
        return f"{x:,.1f}M"

    def fmt_int(x):
        return f"{x:,}"

    for strike, row in agg.iterrows():
        # Insert spot row if we just passed the spot price
        if not spot_inserted and strike < spot_price:
            html += f"""
            <tr class="spot-row">
                <td class="gex-cell-strike">
                    {spot_price:.2f}
                    <span class="spot-label">Spot Price</span>
                </td>
                <td colspan="7"></td>
            </tr>
            """
            spot_inserted = True

        net = row["Net GEX"]
        call = row["Call GEX"]
        put = row["Put GEX"]
        c_oi = int(row["Call OI"])
        p_oi = int(row["Put OI"])
        t_oi = int(row["Total OI"])

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
        viz_html = f"""
        <div class="viz-split-container">
            <div class="viz-left">{left_bar}</div>
            <div class="viz-axis"></div>
            <div class="viz-right">{right_bar}</div>
        </div>
        """

        # Wall labels
        strike_label = f"{strike:.2f}"
        if result.call_wall and strike == result.call_wall:
            strike_label += ' <span class="wall-label call-wall-label">CW</span>'
        if result.put_wall and strike == result.put_wall:
            strike_label += ' <span class="wall-label put-wall-label">PW</span>'

        net_class = "metric-value " + ("positive" if net >= 0 else "negative")

        html += f"""
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
        """

    html += "</tbody></table></div>"
    return html


def render_gex_heatmap(result: GEXResult) -> str:
    """Render a custom HTML heatmap matching the Cheddarflow style."""
    df = result.df.copy()

    if df.empty:
        return ""

    # Pivot data: index=Strike, columns=Expiration, values=Net GEX
    pivot = df.pivot_table(
        values="Net GEX ($M)",
        index="Strike",
        columns="Expiration",
        aggfunc="sum",
        fill_value=0,
    )

    # Sort expirations (columns) and strikes (rows desc)
    pivot = pivot.sort_index(ascending=False)

    # Filter strikes around spot to keep it focused
    spot_price = result.spot_price
    strikes = sorted(pivot.index)

    # Find closest strike index
    closest_idx = 0
    if strikes:
        closest_idx = min(
            range(len(strikes)), key=lambda i: abs(strikes[i] - spot_price)
        )

    # Range of strikes to show (approx +/- 15 from spot)
    start_idx = max(0, closest_idx - 15)
    end_idx = min(len(strikes), closest_idx + 16)

    relevant_strikes = strikes[start_idx:end_idx]
    # Filter pivot and sort descending for display (high strikes at top)
    pivot = pivot.loc[relevant_strikes].sort_index(ascending=False)

    # Date formatting for headers "DEC 08"
    # Columns are datetime.date objects
    headers = [d.strftime("%b %d").upper() for d in pivot.columns]

    # HTML Construction
    html = '<div class="heatmap-container"><table class="heatmap-table">'

    # Header Row
    html += '<thead><tr class="heatmap-header"><th></th>'  # Empty corner cell
    for h in headers:
        html += f"<th>{h}</th>"
    html += "</tr></thead><tbody>"

    # Determine max value for opacity scaling
    # We use a localized max for the visible range to ensure good contrast
    max_val = pivot.abs().max().max() if not pivot.empty else 1

    if max_val == 0:
        max_val = 1

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
            alpha = min(abs_val / max_val * 0.9 + 0.1, 1.0)  # Scale 0.1 to 1.0

            bg_color = "transparent"
            text_class = "cell-zero"
            val_str = ""

            if abs_val > 0.001:  # Threshold to show
                if val > 0:
                    # Green: 0, 255, 136
                    bg_color = f"rgba(0, 255, 136, {alpha:.2f})"
                    text_class = "cell-pos"
                else:
                    # Red: 255, 51, 102
                    bg_color = f"rgba(255, 51, 102, {alpha:.2f})"
                    text_class = "cell-neg"

                # Format Value
                val_str = f"{val:.1f}M" if abs_val >= 1 else f"{val * 1000:.0f}K"

            style = f"background-color: {bg_color};"
            html += (
                f'<td class="heatmap-cell {text_class}" style="{style}">{val_str}</td>'
            )

        html += "</tr>"

    html += "</tbody></table></div>"
    return html


def render_metric_card(
    label: str, value: str, card_type: str = "neutral", subtitle: str = ""
) -> str:
    """Render a custom glassmorphism metric card as HTML."""
    value_class = {
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral",
    }.get(card_type, "neutral")

    subtitle_html = (
        f'<p style="color:{config.COLORS["text_muted"]};font-size:0.7rem;margin:0.25rem 0 0 0;">{subtitle}</p>'
        if subtitle
        else ""
    )

    return f"""
    <div class="metric-card {card_type}">
        <p class="metric-label">{label}</p>
        <p class="metric-value {value_class}">{value}</p>
        {subtitle_html}
    </div>
    """
