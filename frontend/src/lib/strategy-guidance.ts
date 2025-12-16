/**
 * Strategy Guidance Utility
 *
 * Provides actionable trading recommendations, risk assessments, and time horizons
 * for different GEX-based strategy signals. These functions help beginners
 * understand not just what a signal means, but what to DO with it.
 */

// ============================================================================
// TYPES
// ============================================================================

export enum StrategySignalType {
    MEAN_REVERSION = "MEAN_REVERSION",
    ACCELERATION = "ACCELERATION",
    MAGNET_PIN = "MAGNET_PIN",
}

export interface StrategyGuidance {
    approach: string;
    risk: string;
    timeHorizon: string;
}

// ============================================================================
// TRADING APPROACH GUIDANCE
// ============================================================================

/**
 * Get trading approach guidance based on signal type.
 *
 * Provides specific trading tactics and strategies for each signal type,
 * helping traders know exactly what actions to take.
 *
 * @param signal - The strategy signal type (MEAN_REVERSION, ACCELERATION, MAGNET_PIN)
 * @returns String describing the recommended trading approach
 */
export function getTradingApproach(signal: string): string {
    switch (signal) {
        case StrategySignalType.MEAN_REVERSION:
            return "Fade breakouts. Sell OTM options. Target range midpoint.";
        case StrategySignalType.ACCELERATION:
            return "Trade breakouts. Buy straddles/strangles. Wide stops.";
        case StrategySignalType.MAGNET_PIN:
            return "Expect consolidation near wall. Sell theta, avoid directional.";
        default:
            return "Monitor for clear directional signal.";
    }
}

// ============================================================================
// RISK GUIDANCE
// ============================================================================

/**
 * Get risk level guidance based on signal type.
 *
 * Provides assessment of volatility and position sizing recommendations
 * to help traders manage risk appropriately for each signal.
 *
 * @param signal - The strategy signal type
 * @returns String describing the risk level and considerations
 */
export function getRiskGuidance(signal: string): string {
    switch (signal) {
        case StrategySignalType.MEAN_REVERSION:
            return "Low - Confined range expected. Watch overnight gaps.";
        case StrategySignalType.ACCELERATION:
            return "High - Volatile. Use smaller position sizes.";
        case StrategySignalType.MAGNET_PIN:
            return "Medium - Risk of late-day volatility if wall breaks.";
        default:
            return "Assess volatility relative to your risk tolerance.";
    }
}

// ============================================================================
// TIME HORIZON GUIDANCE
// ============================================================================

/**
 * Get time horizon guidance based on signal type.
 *
 * Indicates how long a signal is expected to remain valid,
 * helping traders set appropriate holding periods and take-profit targets.
 *
 * @param signal - The strategy signal type
 * @returns String describing the expected duration of the signal
 */
export function getTimeHorizon(signal: string): string {
    switch (signal) {
        case StrategySignalType.MEAN_REVERSION:
            return "Intraday to 1-3 days (within DTE window)";
        case StrategySignalType.ACCELERATION:
            return "Same day - momentum exhaustion can be rapid";
        case StrategySignalType.MAGNET_PIN:
            return "Into market close (typically after 2 PM)";
        default:
            return "Monitor throughout trading session.";
    }
}

// ============================================================================
// COMBINED GUIDANCE
// ============================================================================

/**
 * Get all guidance for a signal type in one call.
 *
 * Convenience function that returns approach, risk, and time horizon
 * guidance together for a given signal type.
 *
 * @param signal - The strategy signal type
 * @returns Object containing approach, risk, and timeHorizon strings
 */
export function getAllGuidance(signal: string): StrategyGuidance {
    return {
        approach: getTradingApproach(signal),
        risk: getRiskGuidance(signal),
        timeHorizon: getTimeHorizon(signal),
    };
}
