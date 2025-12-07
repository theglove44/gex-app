import matplotlib.pyplot as plt
from gex_core import run_gex_calculation

def visualize_and_print_results(result):
    """Print results and generate visualization chart."""
    if result.error:
        print(f"Error: {result.error}")
        return

    print(f"\n=== GEX Profile ({result.symbol}, 0-{result.max_dte} DTE) ===")
    print(f"Spot Price: ${result.spot_price:.2f}")
    print(f"Total Net GEX: ${result.total_gex:,.2f}M")

    if result.zero_gamma_level:
        print(f"Zero Gamma Level: ${result.zero_gamma_level:.0f}")

    if result.call_wall:
        print(f"Call Wall: ${result.call_wall:.0f}")

    if result.put_wall:
        print(f"Put Wall: ${result.put_wall:.0f}")

    # Display major levels
    if not result.major_levels.empty:
        print("\nMajor Gamma Levels (>$50M):")
        print(result.major_levels.to_string(index=False))
    else:
        print("\nNo major gamma walls (>$50M) found.")

    # Generate chart
    print("\nGenerating GEX Profile Chart...")
    try:
        strike_gex = result.strike_gex
        plt.figure(figsize=(12, 6))

        # Color coding: Green for Call Walls (positive), Red for Put Walls (negative)
        colors = ['green' if x >= 0 else 'red' for x in strike_gex['Net GEX ($M)']]

        plt.bar(strike_gex['Strike'], strike_gex['Net GEX ($M)'], color=colors, width=2.0, alpha=0.7)

        # Spot Price Line
        plt.axvline(x=result.spot_price, color='blue', linestyle='--', label=f'Spot: {result.spot_price:.2f}')

        plt.title(f'{result.symbol} Net GEX Profile (0-{result.max_dte} DTE)', fontsize=14)
        plt.xlabel('Strike Price')
        plt.ylabel('Net GEX ($M)')
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Annotate Major Levels
        for _, row in result.major_levels.iterrows():
            plt.text(row['Strike'], row['Net GEX ($M)'],
                     f"{int(row['Net GEX ($M)'])}",
                     ha='center', va='bottom' if row['Net GEX ($M)'] > 0 else 'top',
                     fontsize=8, rotation=90)

        # Save
        plt.savefig('gex_profile.png')
        print("Chart saved to 'gex_profile.png'")
        plt.close()

    except Exception as e:
        print(f"Failed to generate chart: {e}")


if __name__ == "__main__":
    # Run GEX calculation using the core module
    result = run_gex_calculation(symbol='SPY', max_dte=30)

    # Print results and generate visualization
    visualize_and_print_results(result)