"use client";

import { useState } from "react";
import {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    flexRender,
    createColumnHelper,
    SortingState,
} from "@tanstack/react-table";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowUpDown, Info } from "lucide-react";
import { Slider } from "@/components/ui/slider";
import { useConfig } from "@/lib/config-context";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

// Data type matching API GEXResponse
interface ScanResult {
    symbol: string;
    spot_price: number;
    total_gex: number;
    zero_gamma_level: number | null;
    call_wall: number | null;
    put_wall: number | null;
    error: string | null;
}

const columnHelper = createColumnHelper<ScanResult>();

const columns = [
    columnHelper.accessor("symbol", {
        header: "Symbol",
        cell: (info) => <span className="font-bold">{info.getValue()}</span>,
    }),
    columnHelper.accessor("spot_price", {
        header: "Spot",
        cell: (info) => info.getValue() ? `$${info.getValue().toFixed(2)}` : "—",
    }),
    columnHelper.accessor("total_gex", {
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    className="hover:bg-transparent px-0"
                >
                    Net GEX ($M)
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            )
        },
        cell: (info) => {
            const val = info.getValue() || 0;
            // Convert to millions for display if raw is in actual dollars? 
            // API currently returns Millions directly for Net GEX in dataframe but total_gex might be raw?
            // Wait, backend `calculate_gex_profile` returns total_gex as sum of "Net GEX ($M)".
            // So it is already in millions.
            const formatted = val.toFixed(2);
            const isPos = val > 0;
            return (
                <span className={isPos ? "text-emerald-500 font-mono font-bold" : "text-rose-500 font-mono font-bold"}>
                    ${formatted}M
                </span>
            );
        },
    }),
    columnHelper.accessor("zero_gamma_level", {
        header: "Zero Gamma",
        cell: (info) => info.getValue() ? <span className="font-mono text-amber-500">${info.getValue()}</span> : "—",
    }),
    columnHelper.accessor("call_wall", {
        header: "Call Wall",
        cell: (info) => info.getValue() ? <span className="font-mono text-emerald-500 bg-emerald-950/20 px-1 rounded">${info.getValue()}</span> : "—",
    }),
    columnHelper.accessor("put_wall", {
        header: "Put Wall",
        cell: (info) => info.getValue() ? <span className="font-mono text-rose-500 bg-rose-950/20 px-1 rounded">${info.getValue()}</span> : "—",
    }),
    columnHelper.accessor("error", {
        header: "Status",
        cell: (info) => {
            const err = info.getValue();
            if (err) {
                return (
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger>
                                <Badge variant="destructive" className="cursor-help flex items-center gap-1">
                                    Error <Info className="h-3 w-3" />
                                </Badge>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p className="max-w-xs text-xs">{err}</p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                );
            }
            return <Badge variant="outline" className="text-emerald-500 border-emerald-900 bg-emerald-950/30">Success</Badge>;
        },
    }),
];

export function ScannerView() {
    const [symbolsInput, setSymbolsInput] = useState("SPX, QQQ, IWM, SPY, TSLA, NVDA, AMD");
    const [maxDte, setMaxDte] = useState(30);
    const [strikeRange, setStrikeRange] = useState(20);
    const [data, setData] = useState<ScanResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [sorting, setSorting] = useState<SortingState>([]);
    const [error, setError] = useState<string | null>(null);
    const { api_url } = useConfig();

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        onSortingChange: setSorting,
        state: {
            sorting,
        },
    });

    const handleScan = async () => {
        setLoading(true);
        setError(null);
        setData([]);

        const symbols = symbolsInput.split(",").map((s) => s.trim().toUpperCase()).filter((s) => s.length > 0);

        if (symbols.length === 0) {
            setLoading(false);
            return;
        }

        try {
            const res = await fetch(`${api_url}/api/v1/gex/scan`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    symbols: symbols,
                    max_dte: maxDte,
                    strike_range_pct: strikeRange / 100.0, // Convert to decimal
                    major_threshold: 50,
                }),
            });

            if (!res.ok) throw new Error("Failed to scan universe");

            const json = await res.json();
            setData(json);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 p-4 border border-sidebar-border bg-card rounded-lg">
                <h2 className="text-lg font-semibold">Universe Configuration</h2>
                <div className="flex gap-4 items-center">
                    <Input
                        value={symbolsInput}
                        onChange={(e) => setSymbolsInput(e.target.value)}
                        placeholder="Enter symbols separated by comma (e.g. SPX, QQQ)"
                        className="max-w-xl font-mono"
                    />
                    <Button onClick={handleScan} disabled={loading} className="w-40">
                        {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Run Scan"}
                    </Button>
                </div>
                <p className="text-xs text-muted-foreground">Note: Scanning multiple symbols may take several seconds due to API rate limits.</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <label className="text-sm font-medium">Max DTE: {maxDte} days</label>
                        </div>
                        <Slider
                            value={[maxDte]}
                            onValueChange={(val) => setMaxDte(val[0])}
                            max={60}
                            min={0}
                            step={1}
                            className="w-full"
                        />
                        <p className="text-[10px] text-muted-foreground">
                            Include options expiring within this many days. Use 0 for 0DTE only.
                        </p>
                    </div>

                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <label className="text-sm font-medium">Strike Range: ±{strikeRange}%</label>
                        </div>
                        <Slider
                            value={[strikeRange]}
                            onValueChange={(val) => setStrikeRange(val[0])}
                            max={50}
                            min={5}
                            step={5}
                            className="w-full"
                        />
                        <p className="text-[10px] text-muted-foreground">
                            Filter strikes within this % of spot price.
                        </p>
                    </div>
                </div>

                {error && <p className="text-sm text-rose-500 font-semibold">{error}</p>}
            </div>

            <div className="rounded-md border border-sidebar-border bg-card">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => {
                                    return (
                                        <TableHead key={header.id}>
                                            {header.isPlaceholder
                                                ? null
                                                : flexRender(
                                                    header.column.columnDef.header,
                                                    header.getContext()
                                                )}
                                        </TableHead>
                                    );
                                })}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <TableRow
                                    key={row.id}
                                    data-state={row.getIsSelected() && "selected"}
                                >
                                    {row.getVisibleCells().map((cell) => (
                                        <TableCell key={cell.id}>
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={columns.length} className="h-24 text-center">
                                    {loading ? "Scanning..." : "No results. Run a scan to see data."}
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
