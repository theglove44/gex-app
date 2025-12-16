/**
 * Unit tests for strategy guidance functions
 *
 * Tests cover all three guidance types (approach, risk, time horizon)
 * for all supported signal types, plus edge cases and defaults.
 */

import { describe, test, expect, vi } from "vitest";
import {
    getTradingApproach,
    getRiskGuidance,
    getTimeHorizon,
    getAllGuidance,
    isValidSignal,
    normalizeSignal,
    StrategySignalType,
    type StrategyGuidance,
} from "./strategy-guidance";

// ============================================================================
// TEST SUITE: Type Validation & Normalization (CRITICAL FOR TYPE SAFETY)
// ============================================================================

describe("isValidSignal", () => {
    test("returns true for valid enum values", () => {
        expect(isValidSignal(StrategySignalType.MEAN_REVERSION)).toBe(true);
        expect(isValidSignal(StrategySignalType.ACCELERATION)).toBe(true);
        expect(isValidSignal(StrategySignalType.MAGNET_PIN)).toBe(true);
    });

    test("returns true for valid string values", () => {
        expect(isValidSignal("MEAN_REVERSION")).toBe(true);
        expect(isValidSignal("ACCELERATION")).toBe(true);
        expect(isValidSignal("MAGNET_PIN")).toBe(true);
    });

    test("returns false for invalid string values", () => {
        expect(isValidSignal("mean_reversion")).toBe(false);
        expect(isValidSignal("UNKNOWN")).toBe(false);
        expect(isValidSignal("")).toBe(false);
    });

    test("returns false for null, undefined, and non-string types", () => {
        expect(isValidSignal(null)).toBe(false);
        expect(isValidSignal(undefined)).toBe(false);
        expect(isValidSignal(123)).toBe(false);
        expect(isValidSignal({})).toBe(false);
        expect(isValidSignal([])).toBe(false);
    });
});

describe("normalizeSignal", () => {
    test("returns signal unchanged if already valid", () => {
        expect(normalizeSignal(StrategySignalType.MEAN_REVERSION)).toBe(StrategySignalType.MEAN_REVERSION);
        expect(normalizeSignal("ACCELERATION")).toBe("ACCELERATION");
    });

    test("converts lowercase to uppercase (backend compatibility)", () => {
        // This handles cases where backend might send lowercase by mistake
        expect(normalizeSignal("mean_reversion")).toBe(StrategySignalType.MEAN_REVERSION);
        expect(normalizeSignal("acceleration")).toBe(StrategySignalType.ACCELERATION);
        expect(normalizeSignal("magnet_pin")).toBe(StrategySignalType.MAGNET_PIN);
    });

    test("returns null for null/undefined", () => {
        expect(normalizeSignal(null)).toBe(null);
        expect(normalizeSignal(undefined)).toBe(null);
    });

    test("returns null for invalid signals and logs warning", () => {
        // Spy on console.warn to verify warning is logged
        const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});

        expect(normalizeSignal("INVALID_SIGNAL")).toBe(null);
        expect(warnSpy).toHaveBeenCalledWith(
            expect.stringContaining("Unexpected signal format")
        );

        warnSpy.mockRestore();
    });

    test("handles non-string types by converting to string", () => {
        // Number that matches no signal
        expect(normalizeSignal(123)).toBe(null);
    });
});

// ============================================================================
// TEST SUITE: getTradingApproach
// ============================================================================

describe("getTradingApproach", () => {
    test("returns mean reversion approach", () => {
        const result = getTradingApproach(StrategySignalType.MEAN_REVERSION);
        expect(result).toBe("Fade breakouts. Sell OTM options. Target range midpoint.");
        expect(result).toContain("Fade breakouts");
        expect(result).toContain("OTM options");
    });

    test("returns acceleration approach", () => {
        const result = getTradingApproach(StrategySignalType.ACCELERATION);
        expect(result).toBe("Trade breakouts. Buy straddles/strangles. Wide stops.");
        expect(result).toContain("Trade breakouts");
        expect(result).toContain("straddles");
    });

    test("returns magnet pin approach", () => {
        const result = getTradingApproach(StrategySignalType.MAGNET_PIN);
        expect(result).toBe("Expect consolidation near wall. Sell theta, avoid directional.");
        expect(result).toContain("consolidation");
        expect(result).toContain("theta");
    });

    test("throws error for unknown signal", () => {
        expect(() => getTradingApproach("UNKNOWN_SIGNAL")).toThrow(
            /Invalid signal type/
        );
    });

    test("throws error for empty string", () => {
        expect(() => getTradingApproach("")).toThrow(
            /Invalid signal type/
        );
    });

    test("normalizes lowercase signal to uppercase (case-insensitive for backend compatibility)", () => {
        const result = getTradingApproach("mean_reversion"); // lowercase
        expect(result).toBe("Fade breakouts. Sell OTM options. Target range midpoint.");
    });

    test("always returns a non-empty string for valid signals", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
        ];

        signals.forEach((signal) => {
            const result = getTradingApproach(signal);
            expect(result).toBeTruthy();
            expect(result.length).toBeGreaterThan(0);
        });
    });
});

// ============================================================================
// TEST SUITE: getRiskGuidance
// ============================================================================

describe("getRiskGuidance", () => {
    test("returns mean reversion risk guidance (low)", () => {
        const result = getRiskGuidance(StrategySignalType.MEAN_REVERSION);
        expect(result).toBe("Low - Confined range expected. Watch overnight gaps.");
        expect(result).toContain("Low");
        expect(result).toContain("overnight gaps");
    });

    test("returns acceleration risk guidance (high)", () => {
        const result = getRiskGuidance(StrategySignalType.ACCELERATION);
        expect(result).toBe("High - Volatile. Use smaller position sizes.");
        expect(result).toContain("High");
        expect(result).toContain("smaller position");
    });

    test("returns magnet pin risk guidance (medium)", () => {
        const result = getRiskGuidance(StrategySignalType.MAGNET_PIN);
        expect(result).toBe("Medium - Risk of late-day volatility if wall breaks.");
        expect(result).toContain("Medium");
        expect(result).toContain("late-day volatility");
    });

    test("throws error for unknown signal", () => {
        expect(() => getRiskGuidance("UNKNOWN_SIGNAL")).toThrow(
            /Invalid signal type/
        );
    });

    test("identifies relative risk levels correctly", () => {
        const mrRisk = getRiskGuidance(StrategySignalType.MEAN_REVERSION);
        const accRisk = getRiskGuidance(StrategySignalType.ACCELERATION);
        const mpRisk = getRiskGuidance(StrategySignalType.MAGNET_PIN);

        expect(mrRisk).toContain("Low");
        expect(accRisk).toContain("High");
        expect(mpRisk).toContain("Medium");
    });

    test("provides actionable position sizing guidance", () => {
        const accelerationRisk = getRiskGuidance(StrategySignalType.ACCELERATION);
        expect(accelerationRisk).toContain("smaller position");
    });

    test("always returns a non-empty string for valid signals", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
        ];

        signals.forEach((signal) => {
            const result = getRiskGuidance(signal);
            expect(result).toBeTruthy();
            expect(result.length).toBeGreaterThan(0);
        });
    });
});

// ============================================================================
// TEST SUITE: getTimeHorizon
// ============================================================================

describe("getTimeHorizon", () => {
    test("returns mean reversion time horizon (multi-day)", () => {
        const result = getTimeHorizon(StrategySignalType.MEAN_REVERSION);
        expect(result).toBe("Intraday to 1-3 days (within DTE window)");
        expect(result).toContain("1-3 days");
    });

    test("returns acceleration time horizon (same-day)", () => {
        const result = getTimeHorizon(StrategySignalType.ACCELERATION);
        expect(result).toBe("Same day - momentum exhaustion can be rapid");
        expect(result).toContain("Same day");
        expect(result).toContain("rapid");
    });

    test("returns magnet pin time horizon (end-of-day)", () => {
        const result = getTimeHorizon(StrategySignalType.MAGNET_PIN);
        expect(result).toBe("Into market close (typically after 2 PM)");
        expect(result).toContain("market close");
        expect(result).toContain("2 PM");
    });

    test("throws error for unknown signal", () => {
        expect(() => getTimeHorizon("UNKNOWN_SIGNAL")).toThrow(
            /Invalid signal type/
        );
    });

    test("provides specific time references where applicable", () => {
        const magnetPin = getTimeHorizon(StrategySignalType.MAGNET_PIN);
        expect(magnetPin).toContain("2 PM");
    });

    test("indicates relative durations correctly", () => {
        const mr = getTimeHorizon(StrategySignalType.MEAN_REVERSION);
        const acc = getTimeHorizon(StrategySignalType.ACCELERATION);
        const mp = getTimeHorizon(StrategySignalType.MAGNET_PIN);

        // MEAN_REVERSION: longer (1-3 days)
        expect(mr).toContain("1-3 days");

        // ACCELERATION: shortest (same day)
        expect(acc).toContain("Same day");

        // MAGNET_PIN: medium (until close)
        expect(mp).toContain("market close");
    });

    test("always returns a non-empty string for valid signals", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
        ];

        signals.forEach((signal) => {
            const result = getTimeHorizon(signal);
            expect(result).toBeTruthy();
            expect(result.length).toBeGreaterThan(0);
        });
    });
});

// ============================================================================
// TEST SUITE: getAllGuidance
// ============================================================================

describe("getAllGuidance", () => {
    test("returns complete guidance object for mean reversion", () => {
        const result = getAllGuidance(StrategySignalType.MEAN_REVERSION);

        expect(result).toHaveProperty("approach");
        expect(result).toHaveProperty("risk");
        expect(result).toHaveProperty("timeHorizon");

        expect(result.approach).toContain("Fade breakouts");
        expect(result.risk).toContain("Low");
        expect(result.timeHorizon).toContain("1-3 days");
    });

    test("returns complete guidance object for acceleration", () => {
        const result = getAllGuidance(StrategySignalType.ACCELERATION);

        expect(result).toHaveProperty("approach");
        expect(result).toHaveProperty("risk");
        expect(result).toHaveProperty("timeHorizon");

        expect(result.approach).toContain("Trade breakouts");
        expect(result.risk).toContain("High");
        expect(result.timeHorizon).toContain("Same day");
    });

    test("returns complete guidance object for magnet pin", () => {
        const result = getAllGuidance(StrategySignalType.MAGNET_PIN);

        expect(result).toHaveProperty("approach");
        expect(result).toHaveProperty("risk");
        expect(result).toHaveProperty("timeHorizon");

        expect(result.approach).toContain("consolidation");
        expect(result.risk).toContain("Medium");
        expect(result.timeHorizon).toContain("market close");
    });

    test("returns valid StrategyGuidance interface object", () => {
        const result = getAllGuidance(StrategySignalType.MEAN_REVERSION);

        // Verify type structure
        expect(typeof result.approach).toBe("string");
        expect(typeof result.risk).toBe("string");
        expect(typeof result.timeHorizon).toBe("string");

        // Verify no empty strings
        expect(result.approach.length).toBeGreaterThan(0);
        expect(result.risk.length).toBeGreaterThan(0);
        expect(result.timeHorizon.length).toBeGreaterThan(0);
    });

    test("matches individual function outputs", () => {
        const signal = StrategySignalType.MEAN_REVERSION;
        const combined = getAllGuidance(signal);

        expect(combined.approach).toBe(getTradingApproach(signal));
        expect(combined.risk).toBe(getRiskGuidance(signal));
        expect(combined.timeHorizon).toBe(getTimeHorizon(signal));
    });

    test("throws error for unknown signals", () => {
        expect(() => getAllGuidance("UNKNOWN")).toThrow(
            /Invalid signal type/
        );
    });
});

// ============================================================================
// TEST SUITE: Cross-Function Consistency
// ============================================================================

describe("Cross-function consistency", () => {
    test("all signals have guidance for all three types (no defaults)", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
        ];

        signals.forEach((signal) => {
            const approach = getTradingApproach(signal);
            const risk = getRiskGuidance(signal);
            const horizon = getTimeHorizon(signal);

            // All should return specific values (not generic defaults)
            expect(approach.length).toBeGreaterThan(0);
            expect(risk.length).toBeGreaterThan(0);
            expect(horizon.length).toBeGreaterThan(0);
        });
    });

    test("enum signals are consistent across all functions", () => {
        // Verify that all StrategySignalType enum values work consistently
        const enumValues = Object.values(StrategySignalType);

        enumValues.forEach((signal) => {
            // Each should produce guidance
            expect(getTradingApproach(signal)).toBeTruthy();
            expect(getRiskGuidance(signal)).toBeTruthy();
            expect(getTimeHorizon(signal)).toBeTruthy();
        });
    });

    test("valid signals are handled correctly", () => {
        const validInputs = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
        ];

        validInputs.forEach((input) => {
            // All valid inputs should work without throwing
            expect(() => getTradingApproach(input)).not.toThrow();
            expect(() => getRiskGuidance(input)).not.toThrow();
            expect(() => getTimeHorizon(input)).not.toThrow();

            // All should return strings
            expect(typeof getTradingApproach(input)).toBe("string");
            expect(typeof getRiskGuidance(input)).toBe("string");
            expect(typeof getTimeHorizon(input)).toBe("string");
        });
    });

    test("invalid signals throw descriptive errors", () => {
        const invalidInputs = [
            "UNKNOWN",
            "",
            "null",
            "undefined",
        ];

        invalidInputs.forEach((input) => {
            // Invalid inputs should throw errors with helpful messages
            expect(() => getTradingApproach(input)).toThrow(/Invalid signal type/);
            expect(() => getRiskGuidance(input)).toThrow(/Invalid signal type/);
            expect(() => getTimeHorizon(input)).toThrow(/Invalid signal type/);
        });
    });
});

// ============================================================================
// TEST SUITE: Content Validation
// ============================================================================

describe("Content quality and completeness", () => {
    test("approach guidance includes actionable verbs", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
        ];

        const actionVerbs = ["Fade", "Trade", "Sell", "Buy", "Expect", "Monitor"];

        signals.forEach((signal) => {
            const approach = getTradingApproach(signal);
            const hasAction = actionVerbs.some((verb) => approach.includes(verb));
            expect(hasAction).toBe(true);
        });
    });

    test("risk guidance specifies risk level (Low/Medium/High)", () => {
        const mr = getRiskGuidance(StrategySignalType.MEAN_REVERSION);
        const acc = getRiskGuidance(StrategySignalType.ACCELERATION);
        const mp = getRiskGuidance(StrategySignalType.MAGNET_PIN);

        expect(mr).toMatch(/^Low/);
        expect(acc).toMatch(/^High/);
        expect(mp).toMatch(/^Medium/);
    });

    test("time horizon guidance includes duration reference", () => {
        const horizons = [
            getTimeHorizon(StrategySignalType.MEAN_REVERSION),
            getTimeHorizon(StrategySignalType.ACCELERATION),
            getTimeHorizon(StrategySignalType.MAGNET_PIN),
        ];

        const durationKeywords = ["day", "hour", "close", "rapid", "intraday"];

        horizons.forEach((horizon) => {
            const hasDuration = durationKeywords.some((keyword) =>
                horizon.toLowerCase().includes(keyword)
            );
            expect(hasDuration).toBe(true);
        });
    });
});
