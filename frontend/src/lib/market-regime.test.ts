/**
 * Unit tests for market regime functions
 *
 * Tests cover all regime types (positive/negative/neutral) with edge cases,
 * boundary conditions, and styling/color correctness.
 */

import { describe, test, expect } from "vitest";
import {
    MarketRegime,
    GEX_THRESHOLD,
    getRegimeLabel,
    getRegimeDescription,
    getRegimeBorderColor,
    getRegimeBackgroundColor,
    isPositiveGammaRegime,
    isNegativeGammaRegime,
    isNeutralRegime,
} from "./market-regime";

// ============================================================================
// TEST SUITE: Regime Label Classification
// ============================================================================

describe("getRegimeLabel", () => {
    test("returns POSITIVE for values above threshold", () => {
        expect(getRegimeLabel(GEX_THRESHOLD + 1)).toBe(MarketRegime.POSITIVE);
        expect(getRegimeLabel(2_000_000_000)).toBe(MarketRegime.POSITIVE);
        expect(getRegimeLabel(10_000_000_000)).toBe(MarketRegime.POSITIVE);
    });

    test("returns POSITIVE for threshold exact value", () => {
        expect(getRegimeLabel(GEX_THRESHOLD)).toBe(MarketRegime.POSITIVE);
    });

    test("returns NEGATIVE for values below negative threshold", () => {
        expect(getRegimeLabel(-GEX_THRESHOLD - 1)).toBe(MarketRegime.NEGATIVE);
        expect(getRegimeLabel(-2_000_000_000)).toBe(MarketRegime.NEGATIVE);
        expect(getRegimeLabel(-10_000_000_000)).toBe(MarketRegime.NEGATIVE);
    });

    test("returns NEGATIVE for negative threshold exact value", () => {
        expect(getRegimeLabel(-GEX_THRESHOLD)).toBe(MarketRegime.NEGATIVE);
    });

    test("returns NEUTRAL for values between thresholds", () => {
        expect(getRegimeLabel(0)).toBe(MarketRegime.NEUTRAL);
        expect(getRegimeLabel(500_000_000)).toBe(MarketRegime.NEUTRAL);
        expect(getRegimeLabel(-500_000_000)).toBe(MarketRegime.NEUTRAL);
        expect(getRegimeLabel(GEX_THRESHOLD - 1)).toBe(MarketRegime.NEUTRAL);
        expect(getRegimeLabel(-GEX_THRESHOLD + 1)).toBe(MarketRegime.NEUTRAL);
    });

    test("handles extreme values correctly", () => {
        expect(getRegimeLabel(100_000_000_000)).toBe(MarketRegime.POSITIVE);
        expect(getRegimeLabel(-100_000_000_000)).toBe(MarketRegime.NEGATIVE);
    });
});

// ============================================================================
// TEST SUITE: Regime Descriptions
// ============================================================================

describe("getRegimeDescription", () => {
    test("returns positive gamma description for positive regime", () => {
        const description = getRegimeDescription(2_000_000_000);
        expect(description).toContain("Low volatility");
        expect(description).toContain("Dealers long gamma");
        expect(description).toContain("price supportive");
    });

    test("returns negative gamma description for negative regime", () => {
        const description = getRegimeDescription(-2_000_000_000);
        expect(description).toContain("High volatility");
        expect(description).toContain("Dealers short gamma");
        expect(description).toContain("price vulnerable");
    });

    test("returns neutral description for neutral regime", () => {
        const description = getRegimeDescription(0);
        expect(description).toContain("Mixed signals");
        expect(description).toContain("Monitor");
    });

    test("always returns non-empty string", () => {
        const regimes = [
            2_000_000_000,
            -2_000_000_000,
            0,
            GEX_THRESHOLD,
            -GEX_THRESHOLD,
        ];

        regimes.forEach((gex) => {
            const description = getRegimeDescription(gex);
            expect(description.length).toBeGreaterThan(0);
            expect(description).toBeTruthy();
        });
    });
});

// ============================================================================
// TEST SUITE: Styling - Border Colors
// ============================================================================

describe("getRegimeBorderColor", () => {
    test("returns emerald border for positive gamma", () => {
        expect(getRegimeBorderColor(GEX_THRESHOLD + 1)).toBe("border-l-4 border-l-emerald-500");
        expect(getRegimeBorderColor(2_000_000_000)).toBe("border-l-4 border-l-emerald-500");
    });

    test("returns rose border for negative gamma", () => {
        expect(getRegimeBorderColor(-GEX_THRESHOLD - 1)).toBe("border-l-4 border-l-rose-500");
        expect(getRegimeBorderColor(-2_000_000_000)).toBe("border-l-4 border-l-rose-500");
    });

    test("returns slate border for neutral", () => {
        expect(getRegimeBorderColor(0)).toBe("border-l-4 border-l-slate-500");
        expect(getRegimeBorderColor(500_000_000)).toBe("border-l-4 border-l-slate-500");
    });

    test("returns valid Tailwind class format", () => {
        const testGexValues = [
            2_000_000_000,
            -2_000_000_000,
            0,
        ];

        testGexValues.forEach((gex) => {
            const borderColor = getRegimeBorderColor(gex);
            expect(borderColor).toMatch(/^border-l-4 border-l-\w+-\d+$/);
        });
    });
});

// ============================================================================
// TEST SUITE: Styling - Background Colors
// ============================================================================

describe("getRegimeBackgroundColor", () => {
    test("returns emerald background for positive gamma", () => {
        expect(getRegimeBackgroundColor(GEX_THRESHOLD + 1)).toBe("bg-emerald-950/20");
        expect(getRegimeBackgroundColor(2_000_000_000)).toBe("bg-emerald-950/20");
    });

    test("returns rose background for negative gamma", () => {
        expect(getRegimeBackgroundColor(-GEX_THRESHOLD - 1)).toBe("bg-rose-950/20");
        expect(getRegimeBackgroundColor(-2_000_000_000)).toBe("bg-rose-950/20");
    });

    test("returns slate background for neutral", () => {
        expect(getRegimeBackgroundColor(0)).toBe("bg-slate-950/20");
        expect(getRegimeBackgroundColor(500_000_000)).toBe("bg-slate-950/20");
    });

    test("returns valid Tailwind class format", () => {
        const testGexValues = [
            2_000_000_000,
            -2_000_000_000,
            0,
        ];

        testGexValues.forEach((gex) => {
            const bgColor = getRegimeBackgroundColor(gex);
            expect(bgColor).toMatch(/^bg-\w+-\d+\/\d+$/);
        });
    });
});

// ============================================================================
// TEST SUITE: Convenience Predicates
// ============================================================================

describe("isPositiveGammaRegime", () => {
    test("returns true for positive gamma regime", () => {
        expect(isPositiveGammaRegime(GEX_THRESHOLD + 1)).toBe(true);
        expect(isPositiveGammaRegime(2_000_000_000)).toBe(true);
    });

    test("returns true for threshold exact value", () => {
        expect(isPositiveGammaRegime(GEX_THRESHOLD)).toBe(true);
    });

    test("returns false for neutral regime", () => {
        expect(isPositiveGammaRegime(0)).toBe(false);
        expect(isPositiveGammaRegime(500_000_000)).toBe(false);
        expect(isPositiveGammaRegime(GEX_THRESHOLD - 1)).toBe(false);
    });

    test("returns false for negative gamma regime", () => {
        expect(isPositiveGammaRegime(-GEX_THRESHOLD - 1)).toBe(false);
        expect(isPositiveGammaRegime(-2_000_000_000)).toBe(false);
    });
});

describe("isNegativeGammaRegime", () => {
    test("returns true for negative gamma regime", () => {
        expect(isNegativeGammaRegime(-GEX_THRESHOLD - 1)).toBe(true);
        expect(isNegativeGammaRegime(-2_000_000_000)).toBe(true);
    });

    test("returns true for negative threshold exact value", () => {
        expect(isNegativeGammaRegime(-GEX_THRESHOLD)).toBe(true);
    });

    test("returns false for positive gamma regime", () => {
        expect(isNegativeGammaRegime(GEX_THRESHOLD + 1)).toBe(false);
        expect(isNegativeGammaRegime(2_000_000_000)).toBe(false);
    });

    test("returns false for neutral regime", () => {
        expect(isNegativeGammaRegime(0)).toBe(false);
        expect(isNegativeGammaRegime(-500_000_000)).toBe(false);
        expect(isNegativeGammaRegime(-GEX_THRESHOLD + 1)).toBe(false);
    });
});

describe("isNeutralRegime", () => {
    test("returns true for neutral regime values", () => {
        expect(isNeutralRegime(0)).toBe(true);
        expect(isNeutralRegime(500_000_000)).toBe(true);
        expect(isNeutralRegime(-500_000_000)).toBe(true);
    });

    test("returns true at neutral boundaries", () => {
        expect(isNeutralRegime(GEX_THRESHOLD - 1)).toBe(true);
        expect(isNeutralRegime(-GEX_THRESHOLD + 1)).toBe(true);
    });

    test("returns false for positive gamma regime", () => {
        expect(isNeutralRegime(GEX_THRESHOLD)).toBe(false);
        expect(isNeutralRegime(GEX_THRESHOLD + 1)).toBe(false);
    });

    test("returns false for negative gamma regime", () => {
        expect(isNeutralRegime(-GEX_THRESHOLD)).toBe(false);
        expect(isNeutralRegime(-GEX_THRESHOLD - 1)).toBe(false);
    });
});

// ============================================================================
// TEST SUITE: Cross-Function Consistency
// ============================================================================

describe("Cross-function consistency", () => {
    test("all regimes have descriptions", () => {
        const testCases = [
            { gex: 2_000_000_000, regime: MarketRegime.POSITIVE },
            { gex: -2_000_000_000, regime: MarketRegime.NEGATIVE },
            { gex: 0, regime: MarketRegime.NEUTRAL },
        ];

        testCases.forEach(({ gex, regime }) => {
            expect(getRegimeLabel(gex)).toBe(regime);
            const description = getRegimeDescription(gex);
            expect(description.length).toBeGreaterThan(0);
        });
    });

    test("predicates match getRegimeLabel", () => {
        const testGexValues = [
            2_000_000_000,
            -2_000_000_000,
            0,
            GEX_THRESHOLD,
            -GEX_THRESHOLD,
        ];

        testGexValues.forEach((gex) => {
            const regime = getRegimeLabel(gex);
            const isPositive = isPositiveGammaRegime(gex);
            const isNegative = isNegativeGammaRegime(gex);
            const isNeutral = isNeutralRegime(gex);

            // Exactly one predicate should be true
            const predicateSum = [isPositive, isNegative, isNeutral].filter(Boolean).length;
            expect(predicateSum).toBe(1);

            // Predicates must match regime label
            if (regime === MarketRegime.POSITIVE) expect(isPositive).toBe(true);
            if (regime === MarketRegime.NEGATIVE) expect(isNegative).toBe(true);
            if (regime === MarketRegime.NEUTRAL) expect(isNeutral).toBe(true);
        });
    });

    test("border and background colors exist for all regimes", () => {
        const testCases = [
            2_000_000_000,
            -2_000_000_000,
            0,
        ];

        testCases.forEach((gex) => {
            const borderColor = getRegimeBorderColor(gex);
            const bgColor = getRegimeBackgroundColor(gex);

            expect(borderColor).toBeTruthy();
            expect(bgColor).toBeTruthy();
            expect(borderColor.length).toBeGreaterThan(0);
            expect(bgColor.length).toBeGreaterThan(0);
        });
    });
});

// ============================================================================
// TEST SUITE: Constants
// ============================================================================

describe("GEX_THRESHOLD constant", () => {
    test("is set to 1 billion", () => {
        expect(GEX_THRESHOLD).toBe(1_000_000_000);
    });

    test("is used consistently in regime classification", () => {
        // Just above threshold should be positive
        expect(getRegimeLabel(GEX_THRESHOLD + 1)).toBe(MarketRegime.POSITIVE);

        // Just below threshold should be neutral
        expect(getRegimeLabel(GEX_THRESHOLD - 1)).toBe(MarketRegime.NEUTRAL);

        // Negative threshold should be negative
        expect(getRegimeLabel(-GEX_THRESHOLD - 1)).toBe(MarketRegime.NEGATIVE);

        // Between thresholds should be neutral
        expect(getRegimeLabel(0)).toBe(MarketRegime.NEUTRAL);
    });
});

// ============================================================================
// TEST SUITE: Edge Cases and Boundary Conditions
// ============================================================================

describe("Edge cases and boundary conditions", () => {
    test("handles zero correctly", () => {
        expect(getRegimeLabel(0)).toBe(MarketRegime.NEUTRAL);
        expect(isNeutralRegime(0)).toBe(true);
    });

    test("handles threshold boundaries precisely", () => {
        // Positive boundary
        expect(getRegimeLabel(GEX_THRESHOLD - 1)).toBe(MarketRegime.NEUTRAL);
        expect(getRegimeLabel(GEX_THRESHOLD)).toBe(MarketRegime.POSITIVE);
        expect(getRegimeLabel(GEX_THRESHOLD + 1)).toBe(MarketRegime.POSITIVE);

        // Negative boundary
        expect(getRegimeLabel(-GEX_THRESHOLD + 1)).toBe(MarketRegime.NEUTRAL);
        expect(getRegimeLabel(-GEX_THRESHOLD)).toBe(MarketRegime.NEGATIVE);
        expect(getRegimeLabel(-GEX_THRESHOLD - 1)).toBe(MarketRegime.NEGATIVE);
    });

    test("handles very large values", () => {
        const largePositive = 1_000_000_000_000; // 1 trillion
        const largeNegative = -1_000_000_000_000;

        expect(getRegimeLabel(largePositive)).toBe(MarketRegime.POSITIVE);
        expect(getRegimeLabel(largeNegative)).toBe(MarketRegime.NEGATIVE);
    });

    test("handles very small values", () => {
        const smallPositive = 1;
        const smallNegative = -1;

        expect(getRegimeLabel(smallPositive)).toBe(MarketRegime.NEUTRAL);
        expect(getRegimeLabel(smallNegative)).toBe(MarketRegime.NEUTRAL);
    });
});
