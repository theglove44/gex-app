/**
 * Strategy Guidance Utility
 *
 * Provides actionable trading recommendations, risk assessments, and time horizons
 * for different GEX-based strategy signals. These functions help beginners
 * understand not just what a signal means, but what to DO with it.
 *
 * CRITICAL: Type safety is enforced via discriminated union types to prevent
 * silent failures if backend signal format changes or sends unexpected values.
 */

// ============================================================================
// TYPES
// ============================================================================

export enum StrategySignalType {
    MEAN_REVERSION = "MEAN_REVERSION",
    ACCELERATION = "ACCELERATION",
    MAGNET_PIN = "MAGNET_PIN",
}

/**
 * Valid signal types - Used as a discriminated union for type safety.
 * This ensures functions can only be called with known signal values.
 */
export type ValidSignal = StrategySignalType | keyof typeof StrategySignalType;

export interface StrategyGuidance {
    approach: string;
    risk: string;
    timeHorizon: string;
}

// ============================================================================
// TYPE GUARDS & VALIDATION
// ============================================================================

/**
 * Type guard to validate if a value is a valid signal type.
 * Returns true only if the value is one of the known signal types.
 *
 * @param signal - Value to validate
 * @returns true if signal is valid, false otherwise
 */
export function isValidSignal(signal: unknown): signal is StrategySignalType {
    return Object.values(StrategySignalType).includes(signal as StrategySignalType);
}

/**
 * Normalizes and validates signal input from backend.
 * Handles cases where backend might send unexpected formats.
 *
 * @param signal - Signal value from backend (potentially unsafe)
 * @returns Validated StrategySignalType or null if invalid
 * @throws Error with helpful message if signal format is unexpected
 */
export function normalizeSignal(signal: unknown): StrategySignalType | null {
    // Handle null/undefined
    if (signal === null || signal === undefined) {
        return null;
    }

    // Convert to string if it's not already
    const signalStr = typeof signal === "string" ? signal : String(signal);

    // Check exact match first
    if (isValidSignal(signalStr)) {
        return signalStr;
    }

    // Try uppercase normalization (in case backend sends lowercase)
    const upperSignal = signalStr.toUpperCase();
    if (isValidSignal(upperSignal as StrategySignalType)) {
        return upperSignal as StrategySignalType;
    }

    // Log unexpected signal format for debugging
    console.warn(
        `[Strategy Guidance] Unexpected signal format: "${signalStr}". ` +
        `Expected one of: ${Object.values(StrategySignalType).join(", ")}`
    );

    return null;
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
 * @throws Error if signal is not a valid strategy type
 */
export function getTradingApproach(signal: StrategySignalType | string): string {
    // Normalize and validate the signal
    const normalized = typeof signal === "string" && !isValidSignal(signal)
        ? normalizeSignal(signal)
        : signal as StrategySignalType;

    if (!normalized || !isValidSignal(normalized)) {
        throw new Error(
            `Invalid signal type: "${signal}". Must be one of: ${Object.values(StrategySignalType).join(", ")}`
        );
    }

    switch (normalized) {
        case StrategySignalType.MEAN_REVERSION:
            return "Fade breakouts. Sell OTM options. Target range midpoint.";
        case StrategySignalType.ACCELERATION:
            return "Trade breakouts. Buy straddles/strangles. Wide stops.";
        case StrategySignalType.MAGNET_PIN:
            return "Expect consolidation near wall. Sell theta, avoid directional.";
        // This should never happen due to exhaustiveness checking, but TypeScript requires it
        default:
            // Exhaustiveness check - if you see this error, add the new signal type
            const _exhaustiveCheck: never = normalized;
            return _exhaustiveCheck;
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
 * @throws Error if signal is not a valid strategy type
 */
export function getRiskGuidance(signal: StrategySignalType | string): string {
    // Normalize and validate the signal
    const normalized = typeof signal === "string" && !isValidSignal(signal)
        ? normalizeSignal(signal)
        : signal as StrategySignalType;

    if (!normalized || !isValidSignal(normalized)) {
        throw new Error(
            `Invalid signal type: "${signal}". Must be one of: ${Object.values(StrategySignalType).join(", ")}`
        );
    }

    switch (normalized) {
        case StrategySignalType.MEAN_REVERSION:
            return "Low - Confined range expected. Watch overnight gaps.";
        case StrategySignalType.ACCELERATION:
            return "High - Volatile. Use smaller position sizes.";
        case StrategySignalType.MAGNET_PIN:
            return "Medium - Risk of late-day volatility if wall breaks.";
        // This should never happen due to exhaustiveness checking, but TypeScript requires it
        default:
            // Exhaustiveness check - if you see this error, add the new signal type
            const _exhaustiveCheck: never = normalized;
            return _exhaustiveCheck;
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
 * @throws Error if signal is not a valid strategy type
 */
export function getTimeHorizon(signal: StrategySignalType | string): string {
    // Normalize and validate the signal
    const normalized = typeof signal === "string" && !isValidSignal(signal)
        ? normalizeSignal(signal)
        : signal as StrategySignalType;

    if (!normalized || !isValidSignal(normalized)) {
        throw new Error(
            `Invalid signal type: "${signal}". Must be one of: ${Object.values(StrategySignalType).join(", ")}`
        );
    }

    switch (normalized) {
        case StrategySignalType.MEAN_REVERSION:
            return "Intraday to 1-3 days (within DTE window)";
        case StrategySignalType.ACCELERATION:
            return "Same day - momentum exhaustion can be rapid";
        case StrategySignalType.MAGNET_PIN:
            return "Into market close (typically after 2 PM)";
        // This should never happen due to exhaustiveness checking, but TypeScript requires it
        default:
            // Exhaustiveness check - if you see this error, add the new signal type
            const _exhaustiveCheck: never = normalized;
            return _exhaustiveCheck;
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
 * @throws Error if signal is not a valid strategy type
 */
export function getAllGuidance(signal: StrategySignalType | string): StrategyGuidance {
    return {
        approach: getTradingApproach(signal),
        risk: getRiskGuidance(signal),
        timeHorizon: getTimeHorizon(signal),
    };
}
