"use client";

import { useEffect, useState, useCallback } from "react";
import { KPICard } from "./kpi-card";
import { GEXChart } from "./gex-chart";
import { MajorLevelsTable } from "./major-levels-table";
import { Button } from "@/components/ui/button";
import { Loader2, Zap } from "lucide-react";
import { useConfig } from "@/lib/config-context";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

export function DashboardView() {
    const {
        symbol,
        max_dte,
        strike_range_pct,
        major_threshold,
        data_wait,
        api_url,
        auto_update,
        setAutoUpdate
    } = useConfig();

    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [visibleStrikes, setVisibleStrikes] = useState(12);
    const [weightedMode, setWeightedMode] = useState(false); // New state for Weighted Mode
    const [isInitialized, setIsInitialized] = useState(false);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    // Persist visibleStrikes
    useEffect(() => {
        try {
            const stored = localStorage.getItem("gex_visible_strikes");
            if (stored) {
                const parsed = parseInt(stored);
                // Validation: must be number between 5 and 50
                if (!isNaN(parsed) && parsed >= 5 && parsed <= 50) {
                    setVisibleStrikes(parsed);
                }
            }
        } catch (error) {
            console.error("Failed to load visibleStrikes:", error);
        } finally {
            setIsInitialized(true);
        }
    }, []);

    useEffect(() => {
        if (!isInitialized) return;
        try {
            localStorage.setItem("gex_visible_strikes", visibleStrikes.toString());
        } catch (error) {
            console.error("Failed to save visibleStrikes:", error);
        }
    }, [visibleStrikes, isInitialized]);

    const fetchData = useCallback(async (signal?: AbortSignal) => {
        if (!symbol) return;

        // If auto-updating, don't show full loading spinner to avoid flicker
        // unless it's the very first load
        if (!data) setLoading(true);
        setError(null);

        try {
            const res = await fetch(`${api_url}/api/v1/gex/calculate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    symbol,
                    max_dte,
                    strike_range_pct,
                    major_threshold,
                    data_wait
                }),
                signal
            });

            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Failed to fetch: ${res.status} ${text}`);
            }

            const json = await res.json();
            if (json.error) throw new Error(json.error);

            setData(json);
            setLastUpdated(new Date());
        } catch (err: any) {
            if (err.name === 'AbortError') return;
            console.error("Dashboard Fetch Error:", err);
            setError(err.message || "Unknown error occurred");
        } finally {
            setLoading(false);
        }
    }, [symbol, max_dte, strike_range_pct, major_threshold, data_wait, api_url, data]);

    // Initial fetch and config change
    useEffect(() => {
        const controller = new AbortController();
        fetchData(controller.signal);

        return () => {
            controller.abort();
        };
    }, [symbol, max_dte, strike_range_pct, major_threshold, data_wait, api_url]);

    // Auto-Refresh Polling Effect
    useEffect(() => {
        if (!auto_update) return;

        const intervalId = setInterval(() => {
            fetchData();
        }, 15000); // 15 seconds

        return () => clearInterval(intervalId);
    }, [auto_update, fetchData]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <h1 className="text-2xl font-bold tracking-tight">Dashboard ({symbol} {max_dte}DTE)</h1>
                    {/* Heartbeat & Status */}
                    {lastUpdated && (
                        <div className="flex items-center gap-2 text-xs text-muted-foreground animate-in fade-in duration-500">
                            <div className={`h-2 w-2 rounded-full ${auto_update ? "bg-emerald-500 animate-pulse" : "bg-gray-400"}`} />
                            {auto_update ? "Live" : `Updated ${lastUpdated.toLocaleTimeString()}`}
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    {/* Weighted Mode Toggle */}
                    <div className="flex items-center space-x-2 border-r pr-4 mr-2">
                        <Switch
                            id="weighted-mode"
                            checked={weightedMode}
                            onCheckedChange={setWeightedMode}
                        />
                        <Label htmlFor="weighted-mode" className="flex items-center gap-1 cursor-pointer">
                            <span className={weightedMode ? "text-indigo-400 font-bold" : "text-muted-foreground"}>Weighted</span>
                        </Label>
                    </div>

                    <div className="flex items-center space-x-2 border-r pr-4 mr-2">
                        <Switch
                            id="auto-update"
                            checked={auto_update}
                            onCheckedChange={setAutoUpdate}
                        />
                        <Label htmlFor="auto-update" className="flex items-center gap-1 cursor-pointer">
                            <Zap className={`h-3 w-3 ${auto_update ? "text-amber-400 fill-amber-400" : "text-gray-400"}`} />
                            Live Mode
                        </Label>
                    </div>

                    <Button onClick={() => fetchData()} disabled={loading}>
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Refresh Result
                    </Button>
                </div>
            </div>

            {error && (
                <div className="p-4 border border-rose-900/50 bg-rose-950/20 text-rose-500 rounded-md">
                    <p className="font-bold">Error loading data:</p>
                    <p className="font-mono text-sm">{error}</p>
                    <p className="text-xs mt-2 text-muted-foreground">Make sure the backend is running on {api_url}</p>
                </div>
            )}

            {data && (
                <>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <KPICard title="Spot Price" value={`$${data.spot_price.toFixed(2)} `} />
                        <KPICard
                            title={weightedMode ? "Total Weighted GEX (Rel)" : "Total Net GEX"}
                            value={weightedMode ? "—" : `$${(data.total_gex / 1000).toFixed(2)} B`}
                            subValue={weightedMode ? "Metric is relative" : undefined}
                            className={data.total_gex > 0 ? "border-l-4 border-l-emerald-500" : "border-l-4 border-l-rose-500"}
                        />
                        <KPICard
                            title="Call Wall"
                            value={data.call_wall ? `$${data.call_wall} ` : "—"}
                            subValue="Major Resistance"
                            className="border-l-4 border-l-emerald-500"
                        />
                        <KPICard
                            title="Put Wall"
                            value={data.put_wall ? `$${data.put_wall} ` : "—"}
                            subValue="Major Support"
                            className="border-l-4 border-l-rose-500"
                        />
                    </div>

                    <div className="grid gap-4 md:grid-cols-1">
                        <div className="flex justify-end items-center gap-4 mb-2">
                            <span className="text-sm font-medium text-muted-foreground">Zoom Level: +/- {visibleStrikes} Strikes</span>
                            <Slider
                                value={[visibleStrikes]}
                                min={5}
                                max={50}
                                step={1}
                                onValueChange={(v) => setVisibleStrikes(v[0])}
                                className="w-[200px]"
                            />
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setVisibleStrikes(12)}
                                className="h-8 text-xs"
                            >
                                Reset
                            </Button>
                        </div>
                        <GEXChart
                            data={data.strike_gex}
                            spotPrice={data.spot_price}
                            callWall={data.call_wall}
                            putWall={data.put_wall}
                            zeroGamma={data.zero_gamma_level}
                            visibleStrikes={visibleStrikes}
                            weightedMode={weightedMode}
                        />
                    </div>
                </>
            )}
        </div>
    );
}
