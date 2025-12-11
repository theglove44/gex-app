
"use client";

import { useEffect, useState, useCallback } from "react";
import { KPICard } from "./kpi-card";
import { GEXChart } from "./gex-chart";
import { MajorLevelsTable } from "./major-levels-table";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { useConfig } from "@/lib/config-context";

export function DashboardView() {
    const { symbol, max_dte, strike_range_pct, major_threshold, data_wait } = useConfig();

    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async (signal: AbortSignal) => {
        if (!symbol) return;

        setLoading(true);
        setError(null);
        try {
            // Explicitly point to localhost to match typical Setup
            // Or if you want relative path via proxy, but here use absolute for simplicity
            // Ensure backend listens on 0.0.0.0 if accessing via LAN IP
            const res = await fetch("http://127.0.0.1:8000/api/v1/gex/calculate", {
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
        } catch (err: any) {
            if (err.name === 'AbortError') {
                console.log('Fetch aborted');
                return;
            }
            console.error("Dashboard Fetch Error:", err);
            setError(err.message || "Unknown error occurred");
        } finally {
            if (!signal.aborted) {
                setLoading(false);
            }
        }
    }, [symbol, max_dte, strike_range_pct, major_threshold, data_wait]);

    useEffect(() => {
        const controller = new AbortController();
        fetchData(controller.signal);

        return () => {
            controller.abort();
        };
    }, [fetchData]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold tracking-tight">Dashboard ({symbol} {max_dte}DTE)</h1>
                <Button onClick={() => {
                    const controller = new AbortController();
                    fetchData(controller.signal);
                }} disabled={loading}>
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Refresh Data
                </Button>
            </div>

            {error && (
                <div className="p-4 border border-rose-900/50 bg-rose-950/20 text-rose-500 rounded-md">
                    <p className="font-bold">Error loading data:</p>
                    <p className="font-mono text-sm">{error}</p>
                    <p className="text-xs mt-2 text-muted-foreground">Make sure the backend is running on http://127.0.0.1:8000</p>
                </div>
            )}

            {data && (
                <>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <KPICard title="Spot Price" value={`$${data.spot_price.toFixed(2)} `} />
                        <KPICard
                            title="Total Net GEX"
                            value={`$${(data.total_gex / 1000).toFixed(2)} B`}
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
                        <GEXChart
                            data={data.strike_gex}
                            spotPrice={data.spot_price}
                            callWall={data.call_wall}
                            putWall={data.put_wall}
                            zeroGamma={data.zero_gamma_level}
                        />
                    </div>
                </>
            )}
        </div>
    );
}

