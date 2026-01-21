"use client";

import { useMemo } from "react";
import {
    ComposedChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ReferenceArea,
    ResponsiveContainer,
    Cell,
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

interface ChartData extends StrikeGEXData {
    CumulativeGEX: number;
}

interface GEXChartProps {
    data: StrikeGEXData[];
    spotPrice: number;
    callWall?: number;
    putWall?: number;
    zeroGamma?: number; // This is the Gamma Flip
    visibleStrikes?: number;
    weightedMode?: boolean;
}

interface MinMaxStrikes {
    minStrike: number;
    maxStrike: number;
}

interface TooltipPayload {
    payload: ChartData;
}

interface CustomTooltipProps extends TooltipProps<number, string> {
    payload?: TooltipPayload[];
}

// ============================================================================
// CONSTANTS
// ============================================================================

// Chart display and visibility
const DEFAULT_VISIBLE_STRIKES = 12;

// Zone padding
const ZONE_BUFFER = 500; // Large buffer to ensure zones cover the whole view

// Zone fill opacities
const POSITIVE_GAMMA_OPACITY = 0.05; // Green zone
const NEGATIVE_GAMMA_OPACITY = 0.05; // Red zone

// Reference line styling
const REFERENCE_LINE_DASH_WALL = "5 5";
const REFERENCE_LINE_DASH_FLIP = "0"; // Solid
const REFERENCE_LINE_DASH_SPOT = "0"; // Solid

const REFERENCE_LINE_WIDTH = 2;
const SPOT_LINE_WIDTH = 2;

// Font sizes
const AXIS_FONT_SIZE = 12;
const LABEL_FONT_SIZE = 12;

// Chart bar styling
const BAR_SIZE = 6;
const BAR_RADIUS = 0;

// Color palette
const COLOR_PALETTE = {
    // Bars
    positiveBar: "#1d4ed8", // Blue (Tailwind blue-700)
    negativeBar: "#f97316", // Orange (Tailwind orange-500)

    // Line
    cumulativeLine: "#38bdf8", // Light Blue (Tailwind sky-400)

    // Background Zones
    positiveZone: "#dcfce7", // Light Green (Tailwind green-100)
    negativeZone: "#fee2e2", // Light Red (Tailwind red-100)

    // Reference Lines
    spot: "#22c55e", // Green (Tailwind green-500)
    gammaFlip: "#ef4444", // Red (Tailwind red-500)
    callWall: "#94a3b8", // Slate-400
    putWall: "#94a3b8", // Slate-400
};

export function GEXChart({
    data,
    spotPrice,
    callWall,
    putWall,
    zeroGamma, // Gamma Flip
    visibleStrikes = DEFAULT_VISIBLE_STRIKES,
    weightedMode = false
}: GEXChartProps) {
    // Range for visibility
    const RANGE = visibleStrikes;

    // Ensure data is sorted and calculate Cumulative GEX
    const chartData: ChartData[] = useMemo(() => {
        const sorted = [...data].sort((a, b) => a.Strike - b.Strike);
        let cumulative = 0;
        return sorted.map(d => {
            const val = weightedMode ? d.VolWeightedGEX : d["Net GEX ($M)"];
            cumulative += val;
            return {
                ...d,
                CumulativeGEX: cumulative
            };
        });
    }, [data, weightedMode]);

    // Find closest index to spot
    const closestIndex = useMemo(() => {
        let index = 0;
        let minDiff = Number.MAX_VALUE;
        for (let i = 0; i < chartData.length; i++) {
            const diff = Math.abs(chartData[i].Strike - spotPrice);
            if (diff < minDiff) {
                minDiff = diff;
                index = i;
            }
        }
        return index;
    }, [chartData, spotPrice]);

    // Filter view data
    const startIndex = Math.max(0, closestIndex - RANGE);
    const endIndex = Math.min(chartData.length, closestIndex + RANGE + 1);

    const viewData = useMemo(
        () => chartData.slice(startIndex, endIndex),
        [chartData, startIndex, endIndex]
    );

    // Min/Max for background zones
    const { minStrike, maxStrike } = useMemo(() => {
        if (viewData.length === 0) return { minStrike: 0, maxStrike: 0 };
        return {
            minStrike: Math.min(...viewData.map((d) => d.Strike)),
            maxStrike: Math.max(...viewData.map((d) => d.Strike))
        };
    }, [viewData]);

    const dataKey = weightedMode ? "VolWeightedGEX" : "Net GEX ($M)";

    // Calculate max absolute values for symmetric domains to align zero lines
    const { maxAbsGex, maxAbsCumGex } = useMemo(() => {
        if (viewData.length === 0) return { maxAbsGex: 1, maxAbsCumGex: 1 };

        const maxGex = Math.max(...viewData.map((d) => Math.abs(d[dataKey as keyof StrikeGEXData] as number)), 0.1); // Avoid 0
        const maxCum = Math.max(...viewData.map((d) => Math.abs(d.CumulativeGEX)), 0.1);

        // Add 10% buffer to max values for nice padding
        return {
            maxAbsGex: maxGex * 1.1,
            maxAbsCumGex: maxCum * 1.1
        };
    }, [viewData, dataKey]);

    const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
        if (active && payload && payload.length) {
            const d = (payload[0] as TooltipPayload).payload;
            const netGex = d["Net GEX ($M)"];

            return (
                <div className="bg-popover/95 backdrop-blur-md border border-border p-3 rounded-lg shadow-xl text-sm animate-in fade-in-0 zoom-in-95">
                    <p className="font-bold mb-2 text-base border-b border-border pb-1">Strike: {d.Strike}</p>
                    <div className="space-y-1">
                        <p className="flex justify-between gap-4">
                            <span className="text-muted-foreground">Net GEX:</span>
                            <span className={netGex > 0 ? "text-blue-500 font-mono font-bold" : "text-orange-500 font-mono font-bold"}>
                                ${netGex.toFixed(2)}M
                            </span>
                        </p>
                        <p className="flex justify-between gap-4">
                            <span className="text-muted-foreground">Cumulative:</span>
                            <span className="text-sky-500 font-mono font-bold">
                                ${d.CumulativeGEX.toFixed(2)}M
                            </span>
                        </p>
                        <div className="h-px bg-border my-2" />
                        <p className="flex justify-between gap-4">
                            <span className="text-muted-foreground">Call GEX:</span>
                            <span className="text-blue-500 font-mono">${d["Call GEX ($M)"].toFixed(2)}M</span>
                        </p>
                        <p className="flex justify-between gap-4">
                            <span className="text-muted-foreground">Put GEX:</span>
                            <span className="text-orange-500 font-mono">${d["Put GEX ($M)"].toFixed(2)}M</span>
                        </p>
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <Card className="col-span-3 border-none shadow-none bg-transparent">
            {/* Header kept simple or removed as per image which has title inside chart area usually, 
                but we'll keep the CardHeader for structure */}
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex flex-col space-y-1">
                    <CardTitle className="text-2xl font-bold text-center w-full">$SPX - Gamma Exposure by Strike</CardTitle>
                    <div className="flex items-center justify-center gap-6 text-sm">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-blue-600"></div>
                            <span>Gamma Exposure by Strike</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-0.5 bg-sky-400"></div>
                            <span>Aggregate Gamma Exposure</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-0.5 border-t border-slate-400 border-dashed"></div>
                            <span>Put Wall</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-6 h-0.5 border-t border-slate-400 border-dashed"></div>
                            <span>Call Wall</span>
                        </div>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="h-[500px] w-full p-0">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart
                        data={viewData}
                        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />

                        {/* Background Zones */}
                        {/* Negative Gamma Zone (Below Gamma Flip) */}
                        {zeroGamma && (
                            <ReferenceArea
                                x1={minStrike - ZONE_BUFFER}
                                x2={zeroGamma}
                                yAxisId="left"
                                y1={-999999} // Cover full height
                                y2={999999}
                                fill={COLOR_PALETTE.negativeZone}
                                fillOpacity={NEGATIVE_GAMMA_OPACITY}
                            />
                        )}

                        {/* Positive Gamma Zone (Above Gamma Flip) */}
                        {zeroGamma && (
                            <ReferenceArea
                                x1={zeroGamma}
                                x2={maxStrike + ZONE_BUFFER}
                                yAxisId="left"
                                y1={-999999}
                                y2={999999}
                                fill={COLOR_PALETTE.positiveZone}
                                fillOpacity={POSITIVE_GAMMA_OPACITY}
                            />
                        )}

                        <XAxis
                            dataKey="Strike"
                            type="number"
                            domain={['dataMin', 'dataMax']}
                            tickCount={viewData.length}
                            interval={0} // Show all if possible, or let recharts decide
                            angle={0}
                            dy={10}
                            axisLine={false}
                            tickLine={false}
                            fontSize={AXIS_FONT_SIZE}
                        />
                        <YAxis
                            yAxisId="left"
                            orientation="left"
                            domain={[-maxAbsGex, maxAbsGex]}
                            tickFormatter={(val) => `${(val / 1000).toFixed(1)}B`} // Convert M to B roughly for display if large
                            axisLine={false}
                            tickLine={false}
                            fontSize={AXIS_FONT_SIZE}
                        />
                        <YAxis
                            yAxisId="right"
                            orientation="right"
                            domain={[-maxAbsCumGex, maxAbsCumGex]}
                            tickFormatter={(val) => `${(val / 1000).toFixed(1)}B`}
                            axisLine={false}
                            tickLine={false}
                            fontSize={AXIS_FONT_SIZE}
                        />

                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />

                        {/* Walls */}
                        {putWall && (
                            <ReferenceLine
                                x={putWall}
                                yAxisId="left"
                                stroke={COLOR_PALETTE.putWall}
                                strokeDasharray={REFERENCE_LINE_DASH_WALL}
                            />
                        )}
                        {callWall && (
                            <ReferenceLine
                                x={callWall}
                                yAxisId="left"
                                stroke={COLOR_PALETTE.callWall}
                                strokeDasharray={REFERENCE_LINE_DASH_WALL}
                            />
                        )}

                        {/* Last Price (Spot) */}
                        <ReferenceLine
                            x={spotPrice}
                            yAxisId="left"
                            stroke={COLOR_PALETTE.spot}
                            strokeDasharray={REFERENCE_LINE_DASH_SPOT}
                            strokeWidth={SPOT_LINE_WIDTH}
                            label={{
                                value: `Last Price: ${spotPrice.toLocaleString()}`,
                                position: 'insideTopLeft',
                                fill: COLOR_PALETTE.spot,
                                fontSize: LABEL_FONT_SIZE,
                                fontWeight: 'bold'
                            }}
                        />

                        {/* Gamma Flip */}
                        {zeroGamma && (
                            <ReferenceLine
                                x={zeroGamma}
                                yAxisId="left"
                                stroke={COLOR_PALETTE.gammaFlip}
                                strokeDasharray={REFERENCE_LINE_DASH_FLIP}
                                strokeWidth={SPOT_LINE_WIDTH}
                                label={{
                                    value: `Gamma Flip: ${zeroGamma.toLocaleString()}`,
                                    position: 'insideTopRight',
                                    fill: COLOR_PALETTE.gammaFlip,
                                    fontSize: LABEL_FONT_SIZE,
                                    fontWeight: 'bold'
                                }}
                            />
                        )}

                        {/* Cumulative Gamma Line */}
                        <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="CumulativeGEX"
                            stroke={COLOR_PALETTE.cumulativeLine}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6 }}
                        />

                        {/* Net GEX Bars */}
                        <Bar
                            dataKey={dataKey}
                            yAxisId="left"
                            barSize={BAR_SIZE}
                        >
                            {viewData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={entry[dataKey as keyof StrikeGEXData] > 0 ? COLOR_PALETTE.positiveBar : COLOR_PALETTE.negativeBar}
                                />
                            ))}
                        </Bar>

                    </ComposedChart>
                </ResponsiveContainer>

                {/* Legend / Info Footer */}
                <div className="mt-4 px-4 py-2 border-t border-border/50 text-xs text-muted-foreground space-y-2">
                    <div className="flex items-start gap-2">
                        <div className="w-4 h-4 mt-0.5 rounded border border-green-500 bg-green-500/10 shrink-0"></div>
                        <p><span className="font-bold text-foreground">Positive Gamma:</span> When price is above the gamma flip point, dealers are considered net long gamma...</p>
                    </div>
                    <div className="flex items-start gap-2">
                        <div className="w-4 h-4 mt-0.5 rounded border border-red-500 bg-red-500/10 shrink-0"></div>
                        <p><span className="font-bold text-foreground">Negative Gamma:</span> When price is below the gamma flip point, dealers are considered net short gamma...</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
