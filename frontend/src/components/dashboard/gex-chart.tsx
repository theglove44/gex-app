"use client";

import { useMemo } from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ReferenceArea,
    ResponsiveContainer,
    Cell,
    Label,
    TooltipProps,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// ============================================================================
// TYPES & INTERFACES
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

interface GEXChartProps {
    data: StrikeGEXData[];
    spotPrice: number;
    callWall?: number;
    putWall?: number;
    zeroGamma?: number;
    visibleStrikes?: number;
    weightedMode?: boolean;
}

interface MinMaxStrikes {
    minStrike: number;
    maxStrike: number;
}

interface TooltipPayload {
    payload: StrikeGEXData;
}

interface CustomTooltipProps extends TooltipProps<number, string> {
    payload?: TooltipPayload[];
}

// ============================================================================
// CONSTANTS
// ============================================================================

// Chart display and visibility
const DEFAULT_VISIBLE_STRIKES = 12;
const MIN_VISIBLE_STRIKES = 5;
const MAX_VISIBLE_STRIKES = 50;

// Opacity ranges for significance-based visualization
const MIN_BAR_OPACITY = 0.4;
const MAX_BAR_OPACITY = 0.9;

// Zone padding and transitions
const ZONE_BUFFER = 1; // Strike buffer for breakout zones
const ZERO_GAMMA_RANGE = 0.02; // ±2% around zero gamma level

// Zone fill opacities
const EXPECTED_RANGE_OPACITY = 0.05; // Green zone (call/put wall range)
const BREAKOUT_ZONE_OPACITY = 0.05; // Red zones (outside walls)
const ZERO_GAMMA_ZONE_OPACITY = 0.08; // Amber zone (gamma transition)

// Reference line styling
const REFERENCE_LINE_DASH_CALL_WALL = "5 5";
const REFERENCE_LINE_DASH_PUT_WALL = "5 5";
const REFERENCE_LINE_DASH_ZERO_GAMMA = "2 2";
const REFERENCE_LINE_DASH_SPOT = "0";

const REFERENCE_LINE_WIDTH = 2;
const SPOT_LINE_WIDTH = 3;

// Font sizes
const AXIS_FONT_SIZE = 12;
const LABEL_FONT_SIZE = 11;
const SPOT_LABEL_FONT_SIZE = 12;

// Label positioning
const SPOT_LABEL_DY = -10;

// Chart bar styling
const BAR_SIZE = 16;
const BAR_RADIUS = 4;

// Color palette (theme-aware)
const COLOR_PALETTE = {
    // Positive/Bullish colors
    positive: {
        gex: "hsl(161, 72%, 40%)", // #10B981 converted - Emerald-500
        rgb: "rgb(16, 185, 129)",
    },
    // Negative/Bearish colors
    negative: {
        gex: "hsl(348, 86%, 61%)", // #F43F5E converted - Rose-500
        rgb: "rgb(244, 63, 94)",
    },
    // Reference colors (using CSS variables - will inherit from theme)
    zone: {
        expectedRange: "rgb(16, 185, 129)", // Green (emerald)
        breakout: "rgb(239, 68, 68)", // Red (red-500)
        zeroGamma: "rgb(251, 191, 36)", // Amber (amber-400)
    },
    reference: {
        spot: "#FFD700", // Gold
        callWall: "var(--chart-1)", // Cyan/Blue
        putWall: "var(--chart-2)", // Rose
        zeroGamma: "var(--chart-4)", // Amber
    },
};

// Data key selection for standard vs weighted mode
const DATA_KEYS = {
    standard: "Net GEX ($M)",
    weighted: "VolWeightedGEX",
} as const;

export function GEXChart({
    data,
    spotPrice,
    callWall,
    putWall,
    zeroGamma,
    visibleStrikes = DEFAULT_VISIBLE_STRIKES,
    weightedMode = false
}: GEXChartProps) {
    // Filter data to show only +/- visibleStrikes around the spot price to eliminate scrolling
    // and keep the view compact and focused.
    const RANGE = visibleStrikes;

    // Ensure data is sorted by strike
    const sortedData = useMemo(() => {
        return [...data].sort((a, b) => a.Strike - b.Strike);
    }, [data]);

    // Find the index of the strike closest to the spot price
    const closestIndex = useMemo(() => {
        let index = 0;
        let minDiff = Number.MAX_VALUE;

        for (let i = 0; i < sortedData.length; i++) {
            const diff = Math.abs(sortedData[i].Strike - spotPrice);
            if (diff < minDiff) {
                minDiff = diff;
                index = i;
            }
        }
        return index;
    }, [sortedData, spotPrice]);

    // Calculate slice indices
    const startIndex = Math.max(0, closestIndex - RANGE);
    const endIndex = Math.min(sortedData.length, closestIndex + RANGE + 1);

    const viewData = useMemo(
        () => sortedData.slice(startIndex, endIndex),
        [sortedData, startIndex, endIndex]
    );

    // Select data key based on mode
    const dataKey = weightedMode ? DATA_KEYS.weighted : DATA_KEYS.standard;

    // Memoize min/max strike calculations to avoid re-computation on every render
    const { minStrike, maxStrike }: MinMaxStrikes = useMemo(() => {
        if (viewData.length === 0) return { minStrike: 0, maxStrike: 0 };
        return {
            minStrike: Math.min(...viewData.map((d) => d.Strike)),
            maxStrike: Math.max(...viewData.map((d) => d.Strike))
        };
    }, [viewData]);

    // Calculate max absolute GEX for significance-based opacity
    const maxAbsGex = useMemo(() => {
        return Math.max(...viewData.map((d) => Math.abs(d[dataKey as keyof StrikeGEXData])), 1);
    }, [viewData, dataKey]);

    // Validate wall configuration (edge case: inverted walls)
    const isValidWallConfig = useMemo(() => {
        if (!callWall || !putWall) return true; // Single wall is always valid
        return putWall < callWall; // Put wall should be below call wall
    }, [callWall, putWall]);

    // Helper function to calculate bar opacity based on significance
    const getBarOpacity = (value: number): number => {
        const intensity = Math.abs(value) / maxAbsGex;
        return MIN_BAR_OPACITY + intensity * (MAX_BAR_OPACITY - MIN_BAR_OPACITY);
    };

    // Custom tooltip component with proper typing
    const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
        if (active && payload && payload.length) {
            const d = (payload[0] as TooltipPayload).payload;
            const netGex = d["Net GEX ($M)"];
            const weightedGex = d.VolWeightedGEX;

            return (
                <div className="bg-popover/90 backdrop-blur-md border border-border/50 p-4 rounded-xl shadow-2xl text-popover-foreground text-sm ring-1 ring-white/10">
                    <p className="font-bold mb-3 text-lg border-b border-border/50 pb-2">Strike: ${d.Strike}</p>
                    <div className="space-y-2">
                        {/* Weighted GEX (Primary if mode enabled) */}
                        {weightedMode && (
                            <p className="flex justify-between gap-6 items-center">
                                <span className="text-indigo-400 font-medium font-bold">Vol-Wtd GEX:</span>
                                <span className={weightedGex > 0 ? "text-[#10B981] font-mono font-bold" : "text-[#F43F5E] font-mono font-bold"}>
                                    {weightedGex?.toFixed(2) ?? "0.00"}
                                </span>
                            </p>
                        )}

                        <p className="flex justify-between gap-6 items-center">
                            <span className="text-muted-foreground font-medium">Net GEX:</span>
                            <span className={netGex > 0 ? "text-[#10B981] font-mono font-bold glow-green" : "text-[#F43F5E] font-mono font-bold glow-red"}>
                                ${netGex.toFixed(2)}M
                            </span>
                        </p>
                        <p className="flex justify-between gap-6 items-center">
                            <span className="text-muted-foreground font-medium">Call GEX:</span>
                            <span className="text-[#10B981] font-mono">${d["Call GEX ($M)"]?.toFixed(2) ?? "—"}M</span>
                        </p>
                        <p className="flex justify-between gap-6 items-center">
                            <span className="text-muted-foreground font-medium">Put GEX:</span>
                            <span className="text-[#F43F5E] font-mono">${d["Put GEX ($M)"]?.toFixed(2) ?? "—"}M</span>
                        </p>
                        <p className="flex justify-between gap-6 items-center border-t border-border/50 pt-2 mt-2">
                            <span className="text-muted-foreground font-medium">Total Volume:</span>
                            <span className="font-mono text-foreground/80">{d["Total Volume"]?.toLocaleString() ?? "—"}</span>
                        </p>
                        <p className="flex justify-between gap-6 items-center">
                            <span className="text-muted-foreground font-medium">Total OI:</span>
                            <span className="font-mono text-foreground/80">{d["Total OI"]?.toLocaleString() ?? "—"}</span>
                        </p>
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <Card className="col-span-3 border-sidebar-border bg-card flex flex-col h-[600px]">
            <CardHeader className="flex-none py-4">
                <CardTitle>Gamma Exposure Profile ({weightedMode ? "Volume-Weighted View" : "Neon View"})</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 relative p-0 pb-2">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        layout="vertical"
                        data={viewData}
                        margin={{ top: 20, right: 30, left: 40, bottom: 20 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} opacity={0.1} />
                        <XAxis
                            type="number"
                            stroke="var(--muted-foreground)"
                            fontSize={AXIS_FONT_SIZE}
                            tickFormatter={(val) => weightedMode ? val.toFixed(1) : `$${val}M`}
                            orientation="top"
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            dataKey="Strike"
                            type="number"
                            domain={['dataMin', 'dataMax']}
                            stroke="var(--muted-foreground)"
                            fontSize={AXIS_FONT_SIZE}
                            width={50}
                            interval={0}
                            tickCount={viewData.length}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--muted)', opacity: 0.1 }} />

                        {/* Expected Range Zone - Green (Between Put Wall and Call Wall) */}
                        {isValidWallConfig && putWall && callWall && (
                            <ReferenceArea
                                y1={putWall}
                                y2={callWall}
                                fill={COLOR_PALETTE.zone.expectedRange}
                                fillOpacity={EXPECTED_RANGE_OPACITY}
                                stroke="none"
                            />
                        )}

                        {/* Breakout Zone Above Call Wall - Red */}
                        {callWall && (
                            <ReferenceArea
                                y1={callWall}
                                y2={maxStrike + ZONE_BUFFER}
                                fill={COLOR_PALETTE.zone.breakout}
                                fillOpacity={BREAKOUT_ZONE_OPACITY}
                                stroke="none"
                            />
                        )}

                        {/* Breakout Zone Below Put Wall - Red */}
                        {putWall && (
                            <ReferenceArea
                                y1={minStrike - ZONE_BUFFER}
                                y2={putWall}
                                fill={COLOR_PALETTE.zone.breakout}
                                fillOpacity={BREAKOUT_ZONE_OPACITY}
                                stroke="none"
                            />
                        )}

                        {/* Zero Gamma Transition Zone - Amber */}
                        {zeroGamma && (
                            <ReferenceArea
                                y1={zeroGamma * (1 - ZERO_GAMMA_RANGE)}
                                y2={zeroGamma * (1 + ZERO_GAMMA_RANGE)}
                                fill={COLOR_PALETTE.zone.zeroGamma}
                                fillOpacity={ZERO_GAMMA_ZONE_OPACITY}
                                stroke={COLOR_PALETTE.zone.zeroGamma}
                                strokeDasharray="3 3"
                                strokeOpacity={0.3}
                            />
                        )}

                        {/* Spot Price Line - Gold & Glowing */}
                        <ReferenceLine
                            y={spotPrice}
                            stroke={COLOR_PALETTE.reference.spot}
                            strokeWidth={SPOT_LINE_WIDTH}
                            strokeDasharray={REFERENCE_LINE_DASH_SPOT}
                            className="glow-gold"
                            label={{
                                value: `Spot: $${spotPrice.toFixed(2)}`,
                                position: 'insideTopRight',
                                fill: COLOR_PALETTE.reference.spot,
                                fontSize: SPOT_LABEL_FONT_SIZE,
                                fontWeight: 'bold',
                                dy: SPOT_LABEL_DY
                            }}
                            ifOverflow="extendDomain"
                        />

                        {/* Call Wall with Distance */}
                        {callWall && (
                            <ReferenceLine
                                y={callWall}
                                stroke={COLOR_PALETTE.reference.callWall}
                                strokeDasharray={REFERENCE_LINE_DASH_CALL_WALL}
                                strokeWidth={REFERENCE_LINE_WIDTH}
                                label={{
                                    value: `Call Wall: $${callWall.toFixed(0)} (+${((callWall - spotPrice) / spotPrice * 100).toFixed(1)}%)`,
                                    position: 'right',
                                    fill: COLOR_PALETTE.reference.callWall,
                                    fontSize: LABEL_FONT_SIZE,
                                    fontWeight: 'bold'
                                }}
                            />
                        )}

                        {/* Put Wall with Distance */}
                        {putWall && (
                            <ReferenceLine
                                y={putWall}
                                stroke={COLOR_PALETTE.reference.putWall}
                                strokeDasharray={REFERENCE_LINE_DASH_PUT_WALL}
                                strokeWidth={REFERENCE_LINE_WIDTH}
                                label={{
                                    value: `Put Wall: $${putWall.toFixed(0)} (${((putWall - spotPrice) / spotPrice * 100).toFixed(1)}%)`,
                                    position: 'right',
                                    fill: COLOR_PALETTE.reference.putWall,
                                    fontSize: LABEL_FONT_SIZE,
                                    fontWeight: 'bold'
                                }}
                            />
                        )}

                        {/* Zero Gamma Flip Point */}
                        {zeroGamma && (
                            <ReferenceLine
                                y={zeroGamma}
                                stroke={COLOR_PALETTE.reference.zeroGamma}
                                strokeDasharray={REFERENCE_LINE_DASH_ZERO_GAMMA}
                                strokeWidth={REFERENCE_LINE_WIDTH}
                                label={{
                                    value: `Zero Gamma: $${zeroGamma.toFixed(0)}`,
                                    position: 'right',
                                    fill: COLOR_PALETTE.reference.zeroGamma,
                                    fontSize: LABEL_FONT_SIZE,
                                    fontWeight: 'bold'
                                }}
                            />
                        )}

                        <Bar
                            dataKey={dataKey}
                            name={weightedMode ? "Vol-Wtd GEX" : "Net GEX"}
                            barSize={BAR_SIZE}
                            radius={[BAR_RADIUS, BAR_RADIUS, BAR_RADIUS, BAR_RADIUS]}
                        >
                            {viewData.map((entry: StrikeGEXData, index: number) => {
                                const gexValue = entry[dataKey as keyof StrikeGEXData] as number;
                                const isPositive = gexValue > 0;
                                return (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={isPositive ? COLOR_PALETTE.positive.rgb : COLOR_PALETTE.negative.rgb}
                                        className={isPositive ? "glow-green" : "glow-red"}
                                        fillOpacity={getBarOpacity(gexValue)}
                                    />
                                );
                            })}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
