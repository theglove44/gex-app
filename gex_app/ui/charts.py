import plotly.graph_objects as go
from plotly.subplots import make_subplots

from gex_app.core.gex_core import GEXResult


def render_gex_chart(result: GEXResult) -> go.Figure:
    """
    Render a Plotly chart for GEX profile matching the provided screenshot style.
    - Bar chart for Net GEX per strike
    - Line chart for Cumulative GEX
    - Vertical lines for Spot Price and Gamma Flip
    """
    df = result.strike_gex.copy()

    if df.empty:
        return go.Figure()

    # Calculate Cumulative GEX (Aggregate)
    df = df.sort_values("Strike")
    df["Cumulative GEX"] = df["Net GEX ($M)"].cumsum()

    # Convert to Billions for display
    df["Net GEX ($B)"] = df["Net GEX ($M)"] / 1000.0
    df["Cumulative GEX ($B)"] = df["Cumulative GEX"] / 1000.0

    # Prepare custom data for hover
    # Columns: [Agg GEX ($B), Call OI, Put OI, Call Volume, Put Volume]
    custom_data = df[
        ["Cumulative GEX ($B)", "Call OI", "Put OI", "Call Volume", "Put Volume"]
    ].values

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Colors
    # Positive GEX: Blue, Negative GEX: Orange/Gold
    colors = ["#0000FF" if val >= 0 else "#FFA500" for val in df["Net GEX ($B)"]]

    # 1. Bar Chart: Gamma Exposure by Strike
    fig.add_trace(
        go.Bar(
            x=df["Strike"],
            y=df["Net GEX ($B)"],
            name="Gamma Exposure by Strike",
            marker_color=colors,
            marker_line_width=0,
            opacity=1.0,
            customdata=custom_data,
            hovertemplate=(
                "<b>Strike: %{x}</b><br>"
                "Net Gamma Exposure: %{y:.3f}B<br>"
                "Aggregate Gamma Exposure: %{customdata[0]:.1f}B<br>"
                "<br>"
                "Call Open Interest: %{customdata[1]:,}<br>"
                "Put Open Interest: %{customdata[2]:,}<br>"
                "<br>"
                "Call Volume: %{customdata[3]:,}<br>"
                "Put Volume: %{customdata[4]:,}<br>"
                "<extra></extra>"
            ),
        ),
        secondary_y=False,
    )

    # 2. Line Chart: Aggregate Gamma Exposure
    fig.add_trace(
        go.Scatter(
            x=df["Strike"],
            y=df["Cumulative GEX ($B)"],
            name="Aggregate Gamma Exposure",
            mode="lines",
            line={"color": "#56B4E9", "width": 2},  # Light Sky Blue
            hovertemplate="Strike: %{x}<br>Agg GEX: %{y:.2f}B<extra></extra>",
        ),
        secondary_y=True,
    )

    # 3. Vertical Lines & Annotations
    spot = result.spot_price

    # Last Price Line (Green)
    fig.add_vline(x=spot, line_width=1.5, line_dash="solid", line_color="#00AA00")
    # Annotation for Last Price
    fig.add_annotation(
        x=spot,
        y=1.02,
        yref="paper",
        text=f"Last Price: {spot:,.2f}",
        showarrow=False,
        font={"color": "#00AA00", "size": 12},
        xanchor="left",
        yshift=10,  # Shift up slightly
    )

    # Gamma Flip Line (Red)
    if result.zero_gamma_level:
        flip = result.zero_gamma_level
        fig.add_vline(x=flip, line_width=1.5, line_dash="solid", line_color="#FF0000")
        fig.add_annotation(
            x=flip,
            y=1.02,
            yref="paper",
            text=f"Gamma Flip: {flip:,.2f}",
            showarrow=False,
            font={"color": "#FF0000", "size": 12},
            xanchor="right",
            yshift=10,  # Shift up slightly
        )

    # Layout Configuration
    fig.update_layout(
        title={
            "text": f"<b>${result.symbol} - Gamma Exposure by Strike</b>",
            "y": 0.95,  # Moved up
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 24, "color": "black"},
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.08,  # Moved up above title area
            "xanchor": "center",
            "x": 0.5,
            "bgcolor": "rgba(255,255,255,0.0)",
        },
        template="plotly_white",
        bargap=0.5,  # Increased from 0.2 to 0.5 per user request
        height=750,
        margin={"l": 60, "r": 60, "t": 140, "b": 60},
        hovermode="x unified",
        plot_bgcolor="rgba(245, 255, 245, 0.4)",
        paper_bgcolor="white",
    )

    # Y-Axes Configuration
    fig.update_yaxes(
        title_text="",
        secondary_y=False,
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.2)",
        ticksuffix="B",
        tickfont={"color": "black"},
    )

    fig.update_yaxes(
        title_text="",
        secondary_y=True,
        showgrid=False,
        ticksuffix="B",
        tickfont={"color": "black"},
    )

    # X-Axis
    fig.update_xaxes(
        title_text="Strike Price",
        title_font={"size": 14},
        showgrid=False,
        tickfont={"color": "black"},
    )

    return fig
