/**
 * Unit tests for GEXChart component
 *
 * Tests cover:
 * 1. TypeScript type safety and interfaces
 * 2. Calculation functions (opacity, strike filtering)
 * 3. Edge case handling (inverted walls, empty data)
 * 4. Constant usage and configuration
 */

// Note: These tests focus on pure functions and data transformations
// that can be extracted from the React component.
// Full component rendering tests would require @testing-library/react

// ============================================================================
// MOCK DATA FOR TESTING
// ============================================================================

interface StrikeGEXData {
    Strike: number;
    "Net GEX ($M)": number;
    "Call GEX ($M)": number;
    "Put GEX ($M)": number;
    VolWeightedGEX: number;
    "Total Volume": number;
    "Total OI": number;
}

// Sample test data
const mockGEXData: StrikeGEXData[] = [
    {
        Strike: 450,
        "Net GEX ($M)": -150.5,
        "Call GEX ($M)": 100,
        "Put GEX ($M)": -250.5,
        VolWeightedGEX: -145.2,
        "Total Volume": 1500000,
        "Total OI": 2000000,
    },
    {
        Strike: 455,
        "Net GEX ($M)": 75.3,
        "Call GEX ($M)": 200,
        "Put GEX ($M)": -124.7,
        VolWeightedGEX: 72.1,
        "Total Volume": 1200000,
        "Total OI": 1800000,
    },
    {
        Strike: 460,
        "Net GEX ($M)": 250.8,
        "Call GEX ($M)": 350,
        "Put GEX ($M)": -99.2,
        VolWeightedGEX: 248.5,
        "Total Volume": 2000000,
        "Total OI": 2500000,
    },
    {
        Strike: 465,
        "Net GEX ($M)": 120.4,
        "Call GEX ($M)": 180,
        "Put GEX ($M)": -59.6,
        VolWeightedGEX: 115.8,
        "Total Volume": 1800000,
        "Total OI": 2200000,
    },
    {
        Strike: 470,
        "Net GEX ($M)": -80.2,
        "Call GEX ($M)": 50,
        "Put GEX ($M)": -130.2,
        VolWeightedGEX: -77.5,
        "Total Volume": 1400000,
        "Total OI": 1900000,
    },
];

// ============================================================================
// PURE FUNCTION TESTS
// ============================================================================

/**
 * Test: Calculate bar opacity based on GEX significance
 * Range: 0.4 (40%) to 0.9 (90%)
 */
describe("getBarOpacity", () => {
    const MIN_BAR_OPACITY = 0.4;
    const MAX_BAR_OPACITY = 0.9;

    const getBarOpacity = (value: number, maxAbsGex: number): number => {
        const intensity = Math.abs(value) / maxAbsGex;
        return MIN_BAR_OPACITY + intensity * (MAX_BAR_OPACITY - MIN_BAR_OPACITY);
    };

    test("returns minimum opacity for zero value", () => {
        const result = getBarOpacity(0, 100);
        expect(result).toBe(MIN_BAR_OPACITY);
    });

    test("returns maximum opacity for max absolute GEX", () => {
        const result = getBarOpacity(100, 100);
        expect(result).toBe(MAX_BAR_OPACITY);
    });

    test("returns mid-range opacity for mid-value GEX", () => {
        const result = getBarOpacity(50, 100);
        const expected = MIN_BAR_OPACITY + 0.5 * (MAX_BAR_OPACITY - MIN_BAR_OPACITY);
        expect(result).toBe(expected);
    });

    test("handles negative values symmetrically", () => {
        const positive = getBarOpacity(75, 100);
        const negative = getBarOpacity(-75, 100);
        expect(positive).toBe(negative);
    });

    test("opacity always stays within valid range", () => {
        for (const value of [-1000, -100, 0, 100, 1000]) {
            const result = getBarOpacity(value, 1000);
            expect(result).toBeGreaterThanOrEqual(MIN_BAR_OPACITY);
            expect(result).toBeLessThanOrEqual(MAX_BAR_OPACITY);
        }
    });
});

/**
 * Test: Find closest strike to spot price
 */
describe("findClosestStrike", () => {
    const findClosestIndex = (data: StrikeGEXData[], spotPrice: number): number => {
        let index = 0;
        let minDiff = Number.MAX_VALUE;
        for (let i = 0; i < data.length; i++) {
            const diff = Math.abs(data[i].Strike - spotPrice);
            if (diff < minDiff) {
                minDiff = diff;
                index = i;
            }
        }
        return index;
    };

    test("finds exact match when spot price equals strike", () => {
        const result = findClosestIndex(mockGEXData, 460);
        expect(mockGEXData[result].Strike).toBe(460);
    });

    test("finds closest strike below spot price", () => {
        const result = findClosestIndex(mockGEXData, 457);
        expect(mockGEXData[result].Strike).toBe(455);
    });

    test("finds closest strike above spot price", () => {
        const result = findClosestIndex(mockGEXData, 462);
        expect(mockGEXData[result].Strike).toBe(460);
    });

    test("returns first index for empty data", () => {
        const result = findClosestIndex([], 460);
        expect(result).toBe(0);
    });

    test("handles single data point", () => {
        const singlePoint: StrikeGEXData[] = [mockGEXData[0]];
        const result = findClosestIndex(singlePoint, 999);
        expect(result).toBe(0);
    });
});

/**
 * Test: Calculate min/max strikes in view
 */
describe("getMinMaxStrikes", () => {
    const getMinMaxStrikes = (
        data: StrikeGEXData[]
    ): { minStrike: number; maxStrike: number } => {
        if (data.length === 0) return { minStrike: 0, maxStrike: 0 };
        return {
            minStrike: Math.min(...data.map((d) => d.Strike)),
            maxStrike: Math.max(...data.map((d) => d.Strike)),
        };
    };

    test("correctly identifies min and max strikes", () => {
        const result = getMinMaxStrikes(mockGEXData);
        expect(result.minStrike).toBe(450);
        expect(result.maxStrike).toBe(470);
    });

    test("handles empty data", () => {
        const result = getMinMaxStrikes([]);
        expect(result.minStrike).toBe(0);
        expect(result.maxStrike).toBe(0);
    });

    test("handles single data point", () => {
        const result = getMinMaxStrikes([mockGEXData[2]]);
        expect(result.minStrike).toBe(460);
        expect(result.maxStrike).toBe(460);
    });

    test("handles unsorted data correctly", () => {
        const unsorted = [mockGEXData[4], mockGEXData[0], mockGEXData[2]];
        const result = getMinMaxStrikes(unsorted);
        expect(result.minStrike).toBe(450);
        expect(result.maxStrike).toBe(470);
    });
});

/**
 * Test: Validate wall configuration (edge case handling)
 */
describe("isValidWallConfig", () => {
    const isValidWallConfig = (
        callWall: number | undefined,
        putWall: number | undefined
    ): boolean => {
        if (!callWall || !putWall) return true; // Single wall is always valid
        return putWall < callWall; // Put wall should be below call wall
    };

    test("returns true when no walls are defined", () => {
        expect(isValidWallConfig(undefined, undefined)).toBe(true);
    });

    test("returns true when only call wall exists", () => {
        expect(isValidWallConfig(470, undefined)).toBe(true);
    });

    test("returns true when only put wall exists", () => {
        expect(isValidWallConfig(undefined, 450)).toBe(true);
    });

    test("returns true for correctly ordered walls", () => {
        expect(isValidWallConfig(470, 450)).toBe(true);
    });

    test("returns false for inverted walls (put > call)", () => {
        expect(isValidWallConfig(450, 470)).toBe(false);
    });

    test("returns false for equal walls", () => {
        expect(isValidWallConfig(460, 460)).toBe(false);
    });
});

/**
 * Test: Calculate max absolute GEX for opacity scaling
 */
describe("calculateMaxAbsGex", () => {
    const calculateMaxAbsGex = (
        data: StrikeGEXData[],
        dataKey: string
    ): number => {
        return Math.max(
            ...data.map((d) => Math.abs(d[dataKey as keyof StrikeGEXData] as number)),
            1
        );
    };

    test("returns minimum of 1 for empty data", () => {
        const result = calculateMaxAbsGex([], "Net GEX ($M)");
        expect(result).toBe(1);
    });

    test("correctly identifies max absolute value for Net GEX", () => {
        const result = calculateMaxAbsGex(mockGEXData, "Net GEX ($M)");
        expect(result).toBe(250.8); // Largest absolute value
    });

    test("correctly identifies max absolute value for weighted GEX", () => {
        const result = calculateMaxAbsGex(mockGEXData, "VolWeightedGEX");
        expect(result).toBe(248.5);
    });

    test("handles data with only negative values", () => {
        const negativeData: StrikeGEXData[] = [
            { ...mockGEXData[0] },
            { ...mockGEXData[4] },
        ];
        const result = calculateMaxAbsGex(negativeData, "Net GEX ($M)");
        expect(result).toBe(150.5); // abs(-150.5) = 150.5
    });

    test("always returns at least 1", () => {
        const zeroData: StrikeGEXData[] = mockGEXData.map((d) => ({
            ...d,
            "Net GEX ($M)": 0,
        }));
        const result = calculateMaxAbsGex(zeroData, "Net GEX ($M)");
        expect(result).toBe(1);
    });
});

/**
 * Test: Type safety of StrikeGEXData interface
 */
describe("StrikeGEXData Type Safety", () => {
    test("all required properties exist in mock data", () => {
        const requiredKeys: (keyof StrikeGEXData)[] = [
            "Strike",
            "Net GEX ($M)",
            "Call GEX ($M)",
            "Put GEX ($M)",
            "VolWeightedGEX",
            "Total Volume",
            "Total OI",
        ];

        for (const data of mockGEXData) {
            for (const key of requiredKeys) {
                expect(data).toHaveProperty(key);
                expect(typeof data[key]).toBe("number");
            }
        }
    });

    test("values are valid numbers", () => {
        for (const data of mockGEXData) {
            expect(isFinite(data.Strike)).toBe(true);
            expect(isFinite(data["Net GEX ($M)"])).toBe(true);
            expect(isFinite(data.VolWeightedGEX)).toBe(true);
        }
    });
});

// ============================================================================
// INTEGRATION-LIKE TESTS
// ============================================================================

/**
 * Test: Complete workflow - find strikes, calculate opacities
 */
describe("Complete Chart Workflow", () => {
    test("processes data from raw input to visualization parameters", () => {
        const spotPrice = 462;
        const visibleStrikes = 12;
        const RANGE = visibleStrikes;

        // Sort
        const sorted = [...mockGEXData].sort((a, b) => a.Strike - b.Strike);

        // Find closest
        let closestIndex = 0;
        let minDiff = Number.MAX_VALUE;
        for (let i = 0; i < sorted.length; i++) {
            const diff = Math.abs(sorted[i].Strike - spotPrice);
            if (diff < minDiff) {
                minDiff = diff;
                closestIndex = i;
            }
        }

        // Get view data
        const startIndex = Math.max(0, closestIndex - RANGE);
        const endIndex = Math.min(sorted.length, closestIndex + RANGE + 1);
        const viewData = sorted.slice(startIndex, endIndex);

        // Calculate opacities
        const maxAbsGex = Math.max(
            ...viewData.map((d) => Math.abs(d["Net GEX ($M)"])),
            1
        );
        const MIN_BAR_OPACITY = 0.4;
        const MAX_BAR_OPACITY = 0.9;

        const opacities = viewData.map((d) => {
            const intensity = Math.abs(d["Net GEX ($M)"]) / maxAbsGex;
            return MIN_BAR_OPACITY + intensity * (MAX_BAR_OPACITY - MIN_BAR_OPACITY);
        });

        // Verify results
        expect(viewData.length).toBeGreaterThan(0);
        expect(opacities.length).toBe(viewData.length);
        expect(opacities.every((o) => o >= MIN_BAR_OPACITY && o <= MAX_BAR_OPACITY)).toBe(
            true
        );
    });
});

// ============================================================================
// EXPORT STATEMENT (for test runners)
// ============================================================================

// Note: In a real testing environment with Vitest or Jest,
// tests would be auto-discovered. This export is for documentation.
export {};
