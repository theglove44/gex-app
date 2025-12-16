/**
 * Market Regime Utility Functions
 *
 * Provides functions to determine market regime (positive/negative/neutral gamma)
 * and generate appropriate descriptions and styling for KPI display.
 *
 * Market regime is critical context for traders:
 * - Positive gamma: Dealers are long gamma → price supportive, low volatility expected
 * - Negative gamma: Dealers are short gamma → price vulnerable, high volatility expected
 * - Neutral gamma: Mixed signals, unclear direction
 */

// Threshold for significant positive gamma ($1 billion)
export const GEX_THRESHOLD = 1_000_000_000;

/**
 * Represents the market regime based on gamma exposure
 */
export enum MarketRegime {
    POSITIVE = "POSITIVE_GAMMA",
    NEGATIVE = "NEGATIVE_GAMMA",
    NEUTRAL = "NEUTRAL"
}

/**
 * Get market regime label based on total GEX
 *
 * @param totalGex - Total net GEX in dollars
 * @returns MarketRegime enum value
 */
export function getRegimeLabel(totalGex: number): MarketRegime {
    if (totalGex >= GEX_THRESHOLD) return MarketRegime.POSITIVE;
    if (totalGex <= -GEX_THRESHOLD) return MarketRegime.NEGATIVE;
    return MarketRegime.NEUTRAL;
}

/**
 * Get human-readable regime description
 *
 * Provides beginner-friendly explanation of what the regime means for trading
 *
 * @param totalGex - Total net GEX in dollars
 * @returns Description string
 */
export function getRegimeDescription(totalGex: number): string {
    const regime = getRegimeLabel(totalGex);

    switch (regime) {
        case MarketRegime.POSITIVE:
            return "Low volatility expected. Dealers long gamma = price supportive.";
        case MarketRegime.NEGATIVE:
            return "High volatility environment. Dealers short gamma = price vulnerable.";
        case MarketRegime.NEUTRAL:
            return "Mixed signals. Monitor for regime shift.";
    }
}

/**
 * Get border color className for KPI display
 *
 * Colors communicate regime at a glance:
 * - Green (emerald): Positive gamma, supportive
 * - Red (rose): Negative gamma, vulnerable
 * - Gray (muted): Neutral, uncertain
 *
 * @param totalGex - Total net GEX in dollars
 * @returns Tailwind className for border color
 */
export function getRegimeBorderColor(totalGex: number): string {
    const regime = getRegimeLabel(totalGex);

    switch (regime) {
        case MarketRegime.POSITIVE:
            return "border-l-4 border-l-emerald-500";
        case MarketRegime.NEGATIVE:
            return "border-l-4 border-l-rose-500";
        case MarketRegime.NEUTRAL:
            return "border-l-4 border-l-slate-500";
    }
}

/**
 * Get background color className for market regime visualization
 *
 * Subtle background colors enhance regime perception
 *
 * @param totalGex - Total net GEX in dollars
 * @returns Tailwind className for background color
 */
export function getRegimeBackgroundColor(totalGex: number): string {
    const regime = getRegimeLabel(totalGex);

    switch (regime) {
        case MarketRegime.POSITIVE:
            return "bg-emerald-950/20";
        case MarketRegime.NEGATIVE:
            return "bg-rose-950/20";
        case MarketRegime.NEUTRAL:
            return "bg-slate-950/20";
    }
}

/**
 * Check if market is in positive gamma regime
 *
 * Convenience function for conditional rendering or logic
 *
 * @param totalGex - Total net GEX in dollars
 * @returns true if positive gamma regime
 */
export function isPositiveGammaRegime(totalGex: number): boolean {
    return totalGex >= GEX_THRESHOLD;
}

/**
 * Check if market is in negative gamma regime
 *
 * Convenience function for conditional rendering or logic
 *
 * @param totalGex - Total net GEX in dollars
 * @returns true if negative gamma regime
 */
export function isNegativeGammaRegime(totalGex: number): boolean {
    return totalGex <= -GEX_THRESHOLD;
}

/**
 * Check if market is in neutral gamma regime
 *
 * Convenience function for conditional rendering or logic
 *
 * @param totalGex - Total net GEX in dollars
 * @returns true if neutral regime
 */
export function isNeutralRegime(totalGex: number): boolean {
    return !isPositiveGammaRegime(totalGex) && !isNegativeGammaRegime(totalGex);
}
