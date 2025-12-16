/**
 * Unit tests for strategy guidance functions
 *
 * Tests cover all three guidance types (approach, risk, time horizon)
 * for all supported signal types, plus edge cases and defaults.
 */

import {
    getTradingApproach,
    getRiskGuidance,
    getTimeHorizon,
    getAllGuidance,
    StrategySignalType,
    type StrategyGuidance,
} from "./strategy-guidance";

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

    test("returns default approach for unknown signal", () => {
        const result = getTradingApproach("UNKNOWN_SIGNAL");
        expect(result).toBe("Monitor for clear directional signal.");
    });

    test("returns default approach for empty string", () => {
        const result = getTradingApproach("");
        expect(result).toBe("Monitor for clear directional signal.");
    });

    test("is case-sensitive for signal matching", () => {
        const result = getTradingApproach("mean_reversion"); // lowercase
        expect(result).not.toBe("Fade breakouts. Sell OTM options. Target range midpoint.");
        expect(result).toBe("Monitor for clear directional signal.");
    });

    test("always returns a non-empty string", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
            "UNKNOWN",
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

    test("returns default risk guidance for unknown signal", () => {
        const result = getRiskGuidance("UNKNOWN_SIGNAL");
        expect(result).toBe("Assess volatility relative to your risk tolerance.");
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

    test("always returns a non-empty string", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
            "UNKNOWN",
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

    test("returns default time horizon for unknown signal", () => {
        const result = getTimeHorizon("UNKNOWN_SIGNAL");
        expect(result).toBe("Monitor throughout trading session.");
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

    test("always returns a non-empty string", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
            "UNKNOWN",
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

    test("works with unknown signals", () => {
        const result = getAllGuidance("UNKNOWN");

        expect(result).toHaveProperty("approach");
        expect(result).toHaveProperty("risk");
        expect(result).toHaveProperty("timeHorizon");

        // Should return default values
        expect(result.approach).toBe("Monitor for clear directional signal.");
        expect(result.risk).toBe("Assess volatility relative to your risk tolerance.");
        expect(result.timeHorizon).toBe("Monitor throughout trading session.");
    });
});

// ============================================================================
// TEST SUITE: Cross-Function Consistency
// ============================================================================

describe("Cross-function consistency", () => {
    test("all signals have guidance for all three types", () => {
        const signals = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
        ];

        signals.forEach((signal) => {
            const approach = getTradingApproach(signal);
            const risk = getRiskGuidance(signal);
            const horizon = getTimeHorizon(signal);

            // All should return non-default values
            expect(approach).not.toBe("Monitor for clear directional signal.");
            expect(risk).not.toBe("Assess volatility relative to your risk tolerance.");
            expect(horizon).not.toBe("Monitor throughout trading session.");
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

    test("guidance functions handle all reasonable inputs", () => {
        const testInputs = [
            StrategySignalType.MEAN_REVERSION,
            StrategySignalType.ACCELERATION,
            StrategySignalType.MAGNET_PIN,
            "UNKNOWN",
            "",
            null,
            undefined,
        ];

        testInputs.forEach((input) => {
            // All inputs should be handled gracefully
            expect(() => getTradingApproach(input as string)).not.toThrow();
            expect(() => getRiskGuidance(input as string)).not.toThrow();
            expect(() => getTimeHorizon(input as string)).not.toThrow();

            // All should return strings (not null/undefined)
            expect(typeof getTradingApproach(input as string)).toBe("string");
            expect(typeof getRiskGuidance(input as string)).toBe("string");
            expect(typeof getTimeHorizon(input as string)).toBe("string");
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
