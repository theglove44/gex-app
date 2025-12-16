import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { HelpCircle, TrendingUp, TrendingDown } from "lucide-react";

interface MajorLevel {
    Strike: number;
    Type: string;
    "Net GEX ($M)": number;
}

interface MajorLevelsTableProps {
    data: MajorLevel[];
    spotPrice?: number;
    callWall?: number;
    putWall?: number;
}

/**
 * Calculate distance from spot price
 * Returns both absolute distance ($) and percentage
 */
function calculateDistance(strike: number, spotPrice: number): { dollar: number; percent: number } {
    const dollar = strike - spotPrice;
    const percent = (dollar / spotPrice) * 100;
    return { dollar, percent };
}

/**
 * Get significance stars based on GEX magnitude
 * More extreme GEX = more stars (★★★)
 *
 * @param gexAmount - The GEX value for this specific strike
 * @param maxAbsGex - Pre-calculated max absolute GEX (avoid O(n²) complexity)
 */
function getSignificanceStars(gexAmount: number, maxAbsGex: number): string {
    const intensity = Math.abs(gexAmount) / maxAbsGex;

    if (intensity >= 0.8) return "★★★";
    if (intensity >= 0.5) return "★★";
    return "★";
}

/**
 * Get context label for a strike level
 *
 * Context labels reflect actual market dynamics:
 * - Call walls: Primary resistance (dealer hedging creates selling pressure)
 * - Put walls: Primary support (dealer hedging creates buying pressure)
 * - Call strikes above spot: Secondary resistance
 * - Put strikes below spot: Secondary support
 * - Put strikes above spot: Can be resistance in bearish markets (bearish put selling)
 * - Call strikes below spot: Typically not meaningful (ignored)
 *
 * @param strike - Strike price
 * @param spotPrice - Current spot price
 * @param callWall - Primary resistance level
 * @param putWall - Primary support level
 * @param type - "Call" or "Put"
 */
function getContextLabel(
    strike: number,
    spotPrice: number | undefined,
    callWall: number | undefined,
    putWall: number | undefined,
    type: string
): string {
    if (!spotPrice) return "";

    // Primary walls take precedence
    if (type === "Call" && callWall && strike === callWall) {
        return "Primary Resistance";
    }

    if (type === "Put" && putWall && strike === putWall) {
        return "Primary Support";
    }

    // Call strikes above spot: Secondary resistance
    if (type === "Call" && strike > spotPrice) {
        return "Resistance";
    }

    // Put strikes below spot: Secondary support
    if (type === "Put" && strike < spotPrice) {
        return "Support";
    }

    // Put strikes above spot: Can be resistance in bearish markets
    // (dealers hedging short puts creates selling pressure above spot)
    if (type === "Put" && strike > spotPrice) {
        return "Resistance";
    }

    // Call strikes at or below spot: Not meaningful resistance
    // (typically expired or not relevant for bullish positioning)

    return "";
}

export function MajorLevelsTable({ data, spotPrice, callWall, putWall }: MajorLevelsTableProps) {
    // Get all GEX values for significance calculation
    const allGexValues = data.map(level => level["Net GEX ($M)"]);

    // Calculate max GEX for significance comparison
    const maxAbsGex = Math.max(...allGexValues.map(Math.abs), 1);

    return (
        <TooltipProvider>
            <div className="w-full">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[100px]">Strike</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead className="text-right">Distance</TableHead>
                            <TableHead className="text-right">Net GEX</TableHead>
                            <TableHead className="text-center">Significance</TableHead>
                            <TableHead className="text-left">Context</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                                    No major levels found
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.map((level, i) => {
                                const distance = spotPrice ? calculateDistance(level.Strike, spotPrice) : null;
                                const significance = getSignificanceStars(level["Net GEX ($M)"], maxAbsGex);
                                const contextLabel = getContextLabel(level.Strike, spotPrice, callWall, putWall, level.Type);
                                const isWall = (level.Type === "Call" && level.Strike === callWall) ||
                                    (level.Type === "Put" && level.Strike === putWall);

                                return (
                                    <TableRow
                                        key={i}
                                        className={isWall ? "bg-gradient-to-r from-amber-950/30 to-transparent border-l-2 border-l-amber-500" : ""}
                                    >
                                        {/* Strike Price */}
                                        <TableCell className={`font-mono font-medium ${isWall ? "font-bold text-amber-400" : ""}`}>
                                            ${level.Strike}
                                        </TableCell>

                                        {/* Type Badge */}
                                        <TableCell>
                                            <Badge
                                                variant="outline"
                                                className={level.Type === 'Call'
                                                    ? "text-emerald-500 border-emerald-900 bg-emerald-950/20"
                                                    : "text-rose-500 border-rose-900 bg-rose-950/20"}
                                            >
                                                {level.Type.toUpperCase()}
                                            </Badge>
                                        </TableCell>

                                        {/* Distance from Spot */}
                                        <TableCell className="text-right">
                                            {distance ? (
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <span className={`font-mono text-sm ${
                                                            distance.dollar > 0
                                                                ? "text-emerald-400"
                                                                : "text-rose-400"
                                                        }`}>
                                                            {distance.dollar > 0 ? '+' : ''}{distance.dollar.toFixed(2)} ({distance.percent > 0 ? '+' : ''}{distance.percent.toFixed(1)}%)
                                                        </span>
                                                    </TooltipTrigger>
                                                    <TooltipContent>
                                                        <div className="text-xs space-y-1">
                                                            <p>Distance from spot: ${distance.dollar.toFixed(2)}</p>
                                                            <p>Percentage: {distance.percent.toFixed(2)}%</p>
                                                        </div>
                                                    </TooltipContent>
                                                </Tooltip>
                                            ) : (
                                                <span className="text-muted-foreground">—</span>
                                            )}
                                        </TableCell>

                                        {/* Net GEX */}
                                        <TableCell className={`text-right font-mono ${
                                            level['Net GEX ($M)'] > 0
                                                ? "text-emerald-500"
                                                : "text-rose-500"
                                        }`}>
                                            {level['Net GEX ($M)'] > 0 ? '+' : ''}{level["Net GEX ($M)"]}M
                                        </TableCell>

                                        {/* Significance Stars */}
                                        <TableCell className="text-center">
                                            <Tooltip>
                                                <TooltipTrigger asChild>
                                                    <span className="text-amber-400 cursor-help text-sm">
                                                        {significance}
                                                    </span>
                                                </TooltipTrigger>
                                                <TooltipContent>
                                                    <p className="text-xs">
                                                        {significance === "★★★" && "Very significant level"}
                                                        {significance === "★★" && "Moderately significant level"}
                                                        {significance === "★" && "Lower significance level"}
                                                    </p>
                                                </TooltipContent>
                                            </Tooltip>
                                        </TableCell>

                                        {/* Context Label */}
                                        <TableCell className="text-left">
                                            {contextLabel && (
                                                <div className="flex items-center gap-1">
                                                    {contextLabel === "Primary Resistance" && (
                                                        <>
                                                            <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                                                            <span className="text-xs font-medium text-emerald-400">{contextLabel}</span>
                                                        </>
                                                    )}
                                                    {contextLabel === "Primary Support" && (
                                                        <>
                                                            <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
                                                            <span className="text-xs font-medium text-rose-400">{contextLabel}</span>
                                                        </>
                                                    )}
                                                    {contextLabel === "Resistance" && (
                                                        <span className="text-xs text-emerald-400/70">{contextLabel}</span>
                                                    )}
                                                    {contextLabel === "Support" && (
                                                        <span className="text-xs text-rose-400/70">{contextLabel}</span>
                                                    )}
                                                </div>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                );
                            })
                        )}
                    </TableBody>
                </Table>
            </div>
        </TooltipProvider>
    );
}
