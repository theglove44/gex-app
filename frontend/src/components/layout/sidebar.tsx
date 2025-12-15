"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Radio, Settings, HelpCircle, FileText } from "lucide-react";
import { useConfig } from "@/lib/config-context";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";


interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> { }

export function Sidebar({ className }: SidebarProps) {
    const {
        symbol, setSymbol,
        max_dte, setMaxDte,
        major_threshold, setMajorThreshold,
        api_url, setApiUrl
    } = useConfig();

    return (
        <div className={cn("pb-12 w-80 border-r border-sidebar-border bg-sidebar h-screen sticky top-0 flex flex-col", className)}>
            <div className="space-y-4 py-4 flex-1 overflow-y-auto">
                <div className="px-3 py-2">
                    <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight text-sidebar-foreground">
                        GEX Tool
                    </h2>
                    <div className="space-y-1">
                        <Button variant="ghost" className="w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground" asChild>
                            <Link href="/">
                                <LayoutDashboard className="mr-2 h-4 w-4" />
                                Dashboard
                            </Link>
                        </Button>
                        <Button variant="ghost" className="w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground" asChild>
                            <Link href="/scanner">
                                <Radio className="mr-2 h-4 w-4" />
                                Scanner
                            </Link>
                        </Button>
                    </div>
                </div>

                <div className="px-3 py-2">
                    <div className="px-4 mb-2 flex items-center gap-2">
                        <Settings className="h-4 w-4 text-muted-foreground" />
                        <h2 className="text-sm font-semibold uppercase tracking-widest text-sidebar-foreground/70">
                            Active Config
                        </h2>
                    </div>

                    <div className="space-y-4 px-4">
                        <div className="space-y-2">
                            <span className="text-xs font-medium text-muted-foreground">Symbol</span>
                            <Input
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                                className="h-8 font-mono bg-sidebar-accent/50 border-sidebar-border"
                            />
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <span className="text-xs font-medium text-muted-foreground">Max DTE</span>
                                <span className="text-xs font-mono text-emerald-500">{max_dte} days</span>
                            </div>
                            <Slider
                                value={[max_dte]}
                                max={30}
                                step={1}
                                onValueChange={(v) => setMaxDte(v[0])}
                                className="py-1"
                            />
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between">
                                <span className="text-xs font-medium text-muted-foreground">Major Level ($M)</span>
                                <span className="text-xs font-mono text-emerald-500">${major_threshold}M</span>
                            </div>
                            <Slider
                                value={[major_threshold]}
                                min={10}
                                max={500}
                                step={10}
                                onValueChange={(v) => setMajorThreshold(v[0])}
                                className="py-1"
                            />
                        </div>

                        <div className="space-y-2 pt-4 border-t border-sidebar-border">
                            <span className="text-xs font-medium text-muted-foreground">API Connection</span>
                            <Input
                                value={api_url}
                                onChange={(e) => setApiUrl(e.target.value)}
                                className="h-8 font-mono text-[10px] bg-sidebar-accent/50 border-sidebar-border"
                                placeholder="http://localhost:8000"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
