"use client";

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
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface GEXChartProps {
    data: any[];
    spotPrice: number;
    callWall?: number;
    putWall?: number;
    zeroGamma?: number;
    visibleStrikes?: number;
    weightedMode?: boolean;
}

export function GEXChart({ data, spotPrice, callWall, putWall, zeroGamma, visibleStrikes = 12, weightedMode = false }: GEXChartProps) {
    // Filter data to show only +/- visibleStrikes around the spot price to eliminate scrolling
    // and keep the view compact and focused.
    const RANGE = visibleStrikes; // Number of strikes above and below spot to show

    // Ensure data is sorted by strike
    const sortedData = [...data].sort((a, b) => a.Strike - b.Strike);

    // Find the index of the strike closest to the spot price
    let closestIndex = 0;
    let minDiff = Number.MAX_VALUE;

    for (let i = 0; i < sortedData.length; i++) {
        const diff = Math.abs(sortedData[i].Strike - spotPrice);
        if (diff < minDiff) {
            minDiff = diff;
            closestIndex = i;
        }
    }

    // specific slice indices
    const startIndex = Math.max(0, closestIndex - RANGE);
    const endIndex = Math.min(sortedData.length, closestIndex + RANGE + 1);

    const viewData = sortedData.slice(startIndex, endIndex);

    const dataKey = weightedMode ? "VolWeightedGEX" : "Net GEX ($M)";

    // Calculate max absolute GEX for significance-based opacity
    const maxAbsGex = Math.max(...viewData.map((d: any) => Math.abs(d[dataKey])), 1);

    // Helper function to calculate bar opacity based on significance
    const getBarOpacity = (value: number) => {
        const intensity = Math.abs(value) / maxAbsGex;
        return 0.4 + intensity * 0.5; // Range from 40% to 90%
    };

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            const d = payload[0].payload;
            const netGex = d["Net GEX ($M)"];
            const weightedGex = d["VolWeightedGEX"];

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
                            fontSize={12}
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
                            fontSize={12}
                            width={50}
                            interval={0}
                            tickCount={viewData.length}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--muted)', opacity: 0.1 }} />

                        {/* Expected Range Zone - Green (Between Put Wall and Call Wall) */}
                        {putWall && callWall && putWall < callWall && (
                            <ReferenceArea
                                y1={putWall}
                                y2={callWall}
                                fill="rgb(16, 185, 129)"
                                fillOpacity={0.05}
                                stroke="none"
                            />
                        )}

                        {/* Breakout Zone Above Call Wall - Red */}
                        {callWall && (
                            <ReferenceArea
                                y1={callWall}
                                y2={Math.max(...viewData.map((d: any) => d.Strike)) + 1}
                                fill="rgb(239, 68, 68)"
                                fillOpacity={0.05}
                                stroke="none"
                            />
                        )}

                        {/* Breakout Zone Below Put Wall - Red */}
                        {putWall && (
                            <ReferenceArea
                                y1={Math.min(...viewData.map((d: any) => d.Strike)) - 1}
                                y2={putWall}
                                fill="rgb(239, 68, 68)"
                                fillOpacity={0.05}
                                stroke="none"
                            />
                        )}

                        {/* Zero Gamma Transition Zone - Amber */}
                        {zeroGamma && (
                            <ReferenceArea
                                y1={zeroGamma * 0.98}
                                y2={zeroGamma * 1.02}
                                fill="rgb(251, 191, 36)"
                                fillOpacity={0.08}
                                stroke="rgb(251, 191, 36)"
                                strokeDasharray="3 3"
                                strokeOpacity={0.3}
                            />
                        )}

                        {/* Spot Price Line - Gold & Glowing */}
                        <ReferenceLine
                            y={spotPrice}
                            stroke="#FFD700"
                            strokeWidth={3}
                            strokeDasharray="0"
                            className="glow-gold"
                            label={{
                                value: `Spot: $${spotPrice.toFixed(2)}`,
                                position: 'insideTopRight',
                                fill: '#FFD700',
                                fontSize: 12,
                                fontWeight: 'bold',
                                dy: -10
                            }}
                            ifOverflow="extendDomain"
                        />

                        {/* Call Wall with Distance */}
                        {callWall && (
                            <ReferenceLine
                                y={callWall}
                                stroke="var(--chart-1)"
                                strokeDasharray="5 5"
                                strokeWidth={2}
                                label={{
                                    value: `Call Wall: $${callWall.toFixed(0)} (+${((callWall - spotPrice) / spotPrice * 100).toFixed(1)}%)`,
                                    position: 'right',
                                    fill: 'var(--chart-1)',
                                    fontSize: 11,
                                    fontWeight: 'bold'
                                }}
                            />
                        )}

                        {/* Put Wall with Distance */}
                        {putWall && (
                            <ReferenceLine
                                y={putWall}
                                stroke="var(--chart-2)"
                                strokeDasharray="5 5"
                                strokeWidth={2}
                                label={{
                                    value: `Put Wall: $${putWall.toFixed(0)} (${((putWall - spotPrice) / spotPrice * 100).toFixed(1)}%)`,
                                    position: 'right',
                                    fill: 'var(--chart-2)',
                                    fontSize: 11,
                                    fontWeight: 'bold'
                                }}
                            />
                        )}

                        {/* Zero Gamma Flip Point */}
                        {zeroGamma && (
                            <ReferenceLine
                                y={zeroGamma}
                                stroke="var(--chart-4)"
                                strokeDasharray="2 2"
                                strokeWidth={2}
                                label={{
                                    value: `Zero Gamma: $${zeroGamma.toFixed(0)}`,
                                    position: 'right',
                                    fill: 'var(--chart-4)',
                                    fontSize: 11,
                                    fontWeight: 'bold'
                                }}
                            />
                        )}

                        <Bar dataKey={dataKey} name={weightedMode ? "Vol-Wtd GEX" : "Net GEX"} barSize={16} radius={[4, 4, 4, 4]}>
                            {viewData.map((entry: any, index: number) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={entry[dataKey] > 0 ? "#10B981" : "#F43F5E"}
                                    className={entry[dataKey] > 0 ? "glow-green" : "glow-red"}
                                    fillOpacity={getBarOpacity(entry[dataKey])}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
