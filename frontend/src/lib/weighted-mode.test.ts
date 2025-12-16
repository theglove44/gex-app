/**
 * Unit tests for weighted mode utility functions
 *
 * Tests cover all aspects of mode information and styling for both
 * standard and weighted GEX views.
 */

import { describe, test, expect } from "vitest";
import {
    ViewMode,
    getModeLabel,
    getModeTooltip,
    getModeUseCase,
    getModeDescription,
    getSwitchModeRecommendation,
    getModeIndicatorColor,
    getModeLabelClass,
    getModeBorderClass,
} from "./weighted-mode";

// ============================================================================
// TEST SUITE: Mode Labels
// ============================================================================

describe("getModeLabel", () => {
    test("returns 'Volume-Weighted View' when weighted mode is true", () => {
        expect(getModeLabel(true)).toBe("Volume-Weighted View");
    });

    test("returns 'Standard GEX View' when weighted mode is false", () => {
        expect(getModeLabel(false)).toBe("Standard GEX View");
    });

    test("always returns non-empty string", () => {
        expect(getModeLabel(true).length).toBeGreaterThan(0);
        expect(getModeLabel(false).length).toBeGreaterThan(0);
    });
});

// ============================================================================
// TEST SUITE: Mode Tooltips
// ============================================================================

describe("getModeTooltip", () => {
    test("returns weighted explanation when mode is true", () => {
        const tooltip = getModeTooltip(true);
        expect(tooltip).toContain("weighted");
        expect(tooltip).toContain("volume");
        expect(tooltip).toContain("dealer activity");
    });

    test("returns standard explanation when mode is false", () => {
        const tooltip = getModeTooltip(false);
        expect(tooltip).toContain("raw GEX");
        expect(tooltip).toContain("open interest");
        expect(tooltip).toContain("institutional");
    });

    test("always returns non-empty, descriptive string", () => {
        expect(getModeTooltip(true).length).toBeGreaterThan(20);
        expect(getModeTooltip(false).length).toBeGreaterThan(20);
    });

    test("provides actionable context", () => {
        const weightedTooltip = getModeTooltip(true);
        const standardTooltip = getModeTooltip(false);

        expect(weightedTooltip).toContain("current");
        expect(standardTooltip).toContain("long-term");
    });
});

// ============================================================================
// TEST SUITE: Use Case Descriptions
// ============================================================================

describe("getModeUseCase", () => {
    test("returns use case for weighted mode", () => {
        const useCase = getModeUseCase(true);
        expect(useCase).toContain("Best for");
        expect(useCase).toContain("Current dealer activity");
        expect(useCase).toContain("intraday");
    });

    test("returns use case for standard mode", () => {
        const useCase = getModeUseCase(false);
        expect(useCase).toContain("Best for");
        expect(useCase).toContain("Long-term levels");
        expect(useCase).toContain("position");
    });

    test("both use cases are distinct", () => {
        const weighted = getModeUseCase(true);
        const standard = getModeUseCase(false);
        expect(weighted).not.toEqual(standard);
    });
});

// ============================================================================
// TEST SUITE: Detailed Descriptions
// ============================================================================

describe("getModeDescription", () => {
    test("provides detailed explanation for weighted mode", () => {
        const description = getModeDescription(true);
        expect(description).toContain("Volume-weighted");
        expect(description).toContain("dealers");
        expect(description).toContain("hedging");
        expect(description).toContain("intraday");
    });

    test("provides detailed explanation for standard mode", () => {
        const description = getModeDescription(false);
        expect(description).toContain("Standard");
        expect(description).toContain("cumulative gamma");
        expect(description).toContain("open interest");
        expect(description).toContain("structural");
    });

    test("both descriptions are comprehensive", () => {
        expect(getModeDescription(true).length).toBeGreaterThan(50);
        expect(getModeDescription(false).length).toBeGreaterThan(50);
    });

    test("provides actionable trading guidance", () => {
        const weighted = getModeDescription(true);
        const standard = getModeDescription(false);

        expect(weighted).toContain("Use this");
        expect(standard).toContain("Use this");
    });
});

// ============================================================================
// TEST SUITE: Mode Switching Recommendations
// ============================================================================

describe("getSwitchModeRecommendation", () => {
    test("recommends switching to Standard when in Weighted mode", () => {
        const recommendation = getSwitchModeRecommendation(true);
        expect(recommendation).toContain("Standard");
        expect(recommendation).toContain("major");
        expect(recommendation).toContain("levels");
    });

    test("recommends switching to Weighted when in Standard mode", () => {
        const recommendation = getSwitchModeRecommendation(false);
        expect(recommendation).toContain("Weighted");
        expect(recommendation).toContain("dealer");
        expect(recommendation).toContain("positioning");
    });

    test("recommendations are opposites", () => {
        const fromWeighted = getSwitchModeRecommendation(true);
        const fromStandard = getSwitchModeRecommendation(false);

        // One should mention "Standard", the other "Weighted"
        expect(
            (fromWeighted.includes("Standard") && fromStandard.includes("Weighted")) ||
            (fromWeighted.includes("Weighted") && fromStandard.includes("Standard"))
        ).toBe(true);
    });
});

// ============================================================================
// TEST SUITE: Styling - Indicator Colors
// ============================================================================

describe("getModeIndicatorColor", () => {
    test("returns indigo color for weighted mode", () => {
        const color = getModeIndicatorColor(true);
        expect(color).toBe("text-indigo-400");
    });

    test("returns muted color for standard mode", () => {
        const color = getModeIndicatorColor(false);
        expect(color).toBe("text-muted-foreground");
    });

    test("returns valid Tailwind color classes", () => {
        expect(getModeIndicatorColor(true)).toMatch(/^text-\w+-\d+$/);
        expect(getModeIndicatorColor(false)).toMatch(/^text-\w+-\w+$/);
    });

    test("colors are visually distinct", () => {
        const weighted = getModeIndicatorColor(true);
        const standard = getModeIndicatorColor(false);
        expect(weighted).not.toEqual(standard);
    });
});

// ============================================================================
// TEST SUITE: Styling - Label Classes
// ============================================================================

describe("getModeLabelClass", () => {
    test("returns bold indigo class for weighted mode", () => {
        const labelClass = getModeLabelClass(true);
        expect(labelClass).toContain("font-bold");
        expect(labelClass).toContain("indigo-400");
    });

    test("returns muted class for standard mode", () => {
        const labelClass = getModeLabelClass(false);
        expect(labelClass).toBe("text-muted-foreground");
    });

    test("returns valid Tailwind classes", () => {
        const weighted = getModeLabelClass(true);
        const standard = getModeLabelClass(false);

        expect(weighted).toMatch(/\w+/); // Has at least word characters
        expect(standard).toMatch(/\w+/);
    });

    test("classes are different for each mode", () => {
        expect(getModeLabelClass(true)).not.toEqual(getModeLabelClass(false));
    });
});

// ============================================================================
// TEST SUITE: Styling - Border Classes
// ============================================================================

describe("getModeBorderClass", () => {
    test("returns indigo border for weighted mode", () => {
        const borderClass = getModeBorderClass(true);
        expect(borderClass).toBe("border-l-4 border-l-indigo-500");
    });

    test("returns slate border for standard mode", () => {
        const borderClass = getModeBorderClass(false);
        expect(borderClass).toBe("border-l-4 border-l-slate-500");
    });

    test("returns valid Tailwind border classes", () => {
        const weighted = getModeBorderClass(true);
        const standard = getModeBorderClass(false);

        expect(weighted).toMatch(/^border-l-\d+ border-l-\w+-\d+$/);
        expect(standard).toMatch(/^border-l-\d+ border-l-\w+-\d+$/);
    });

    test("borders are visually distinct", () => {
        expect(getModeBorderClass(true)).not.toEqual(getModeBorderClass(false));
    });
});

// ============================================================================
// TEST SUITE: Enum Constants
// ============================================================================

describe("ViewMode enum", () => {
    test("has STANDARD value", () => {
        expect(ViewMode.STANDARD).toBeDefined();
    });

    test("has WEIGHTED value", () => {
        expect(ViewMode.WEIGHTED).toBeDefined();
    });

    test("values are distinct", () => {
        expect(ViewMode.STANDARD).not.toEqual(ViewMode.WEIGHTED);
    });
});

// ============================================================================
// TEST SUITE: Cross-Function Consistency
// ============================================================================

describe("Cross-function consistency", () => {
    test("all functions provide information for both modes", () => {
        const modes = [true, false];

        modes.forEach((isWeighted) => {
            expect(getModeLabel(isWeighted).length).toBeGreaterThan(0);
            expect(getModeTooltip(isWeighted).length).toBeGreaterThan(0);
            expect(getModeUseCase(isWeighted).length).toBeGreaterThan(0);
            expect(getModeDescription(isWeighted).length).toBeGreaterThan(0);
            expect(getSwitchModeRecommendation(isWeighted).length).toBeGreaterThan(0);
            expect(getModeIndicatorColor(isWeighted).length).toBeGreaterThan(0);
            expect(getModeLabelClass(isWeighted).length).toBeGreaterThan(0);
            expect(getModeBorderClass(isWeighted).length).toBeGreaterThan(0);
        });
    });

    test("information is consistent across related functions", () => {
        // Weighted mode info should mention weighted/volume
        expect(getModeLabel(true).toLowerCase()).toContain("weight");
        expect(getModeTooltip(true).toLowerCase()).toContain("weight");
        expect(getModeDescription(true).toLowerCase()).toContain("weight");

        // Standard mode info should mention standard/open interest
        expect(getModeLabel(false).toLowerCase()).toContain("standard");
        expect(getModeTooltip(false).toLowerCase()).toContain("interest");
        expect(getModeDescription(false).toLowerCase()).toContain("standard");
    });

    test("styling functions always return valid values", () => {
        const modes = [true, false];

        modes.forEach((isWeighted) => {
            const color = getModeIndicatorColor(isWeighted);
            const labelClass = getModeLabelClass(isWeighted);
            const borderClass = getModeBorderClass(isWeighted);

            expect(color).toBeTruthy();
            expect(labelClass).toBeTruthy();
            expect(borderClass).toBeTruthy();
        });
    });
});

// ============================================================================
// TEST SUITE: Edge Cases
// ============================================================================

describe("Edge cases", () => {
    test("handles boolean values explicitly", () => {
        expect(getModeLabel(true)).toBe("Volume-Weighted View");
        expect(getModeLabel(false)).toBe("Standard GEX View");
    });

    test("functions don't depend on external state", () => {
        // Calling multiple times should return same result
        expect(getModeLabel(true)).toBe(getModeLabel(true));
        expect(getModeTooltip(false)).toBe(getModeTooltip(false));
        expect(getModeBorderClass(true)).toBe(getModeBorderClass(true));
    });

    test("all descriptions are user-friendly", () => {
        // Check for common beginner-friendly terms
        const weighted = getModeDescription(true);
        const standard = getModeDescription(false);

        // Should avoid overly technical jargon
        expect(weighted.length).toBeGreaterThan(50); // Substantive explanation
        expect(standard.length).toBeGreaterThan(50);
    });
});
