"use client";

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ResponsiveContainer,
    Cell,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface GEXChartProps {
    data: any[];
    spotPrice: number;
    callWall?: number;
    putWall?: number;
    zeroGamma?: number;
    visibleStrikes?: number;
}

export function GEXChart({ data, spotPrice, callWall, putWall, zeroGamma, visibleStrikes = 12 }: GEXChartProps) {
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

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            const d = payload[0].payload;
            return (
                <div className="bg-popover/90 backdrop-blur-md border border-border/50 p-4 rounded-xl shadow-2xl text-popover-foreground text-sm ring-1 ring-white/10">
                    <p className="font-bold mb-3 text-lg border-b border-border/50 pb-2">Strike: ${d.Strike}</p>
                    <div className="space-y-2">
                        <p className="flex justify-between gap-6 items-center">
                            <span className="text-muted-foreground font-medium">Net GEX:</span>
                            <span className={d["Net GEX ($M)"] > 0 ? "text-[#10B981] font-mono font-bold glow-green" : "text-[#F43F5E] font-mono font-bold glow-red"}>
                                ${d["Net GEX ($M)"].toFixed(2)}M
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
                <CardTitle>Gamma Exposure Profile (Neon View)</CardTitle>
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
                            tickFormatter={(val) => `$${val}M`}
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

                        {/* Spot Price Line - Gold & Glowing */}
                        <ReferenceLine
                            y={spotPrice}
                            stroke="#FFD700"
                            strokeWidth={3}
                            strokeDasharray="0"
                            className="glow-gold"
                            label={{ position: 'insideTopRight', value: 'Spot', fill: '#FFD700', fontSize: 13, fontWeight: 'bold' }}
                            ifOverflow="extendDomain"
                        />

                        {/* Other Lines */}
                        {callWall && (
                            <ReferenceLine y={callWall} stroke="var(--chart-1)" strokeDasharray="5 5" label={{ position: 'right', value: 'Call Wall', fill: 'var(--chart-1)', fontSize: 10 }} />
                        )}
                        {putWall && (
                            <ReferenceLine y={putWall} stroke="var(--chart-2)" strokeDasharray="5 5" label={{ position: 'right', value: 'Put Wall', fill: 'var(--chart-2)', fontSize: 10 }} />
                        )}
                        {zeroGamma && (
                            <ReferenceLine y={zeroGamma} stroke="var(--chart-4)" strokeDasharray="2 2" label={{ position: 'right', value: 'Zero Gamma', fill: 'var(--chart-4)', fontSize: 10 }} />
                        )}

                        <Bar dataKey="Net GEX ($M)" name="Net GEX" barSize={16} radius={[4, 4, 4, 4]}>
                            {viewData.map((entry: any, index: number) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={entry["Net GEX ($M)"] > 0 ? "#10B981" : "#F43F5E"}
                                    className={entry["Net GEX ($M)"] > 0 ? "glow-green" : "glow-red"}
                                    fillOpacity={0.9}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}
