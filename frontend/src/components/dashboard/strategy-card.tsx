import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus, Anchor, Zap } from "lucide-react";

interface StrategySignal {
    signal: string;
    bias: string;
    message: string;
    validity: string;
    color: string;
}

interface StrategyCardProps {
    strategy: StrategySignal;
}

export function StrategyCard({ strategy }: StrategyCardProps) {
    if (!strategy) return null;

    const getIcon = () => {
        switch (strategy.signal) {
            case "MEAN_REVERSION": return <Minus className="h-5 w-5" />;
            case "ACCELERATION": return <Zap className="h-5 w-5" />;
            case "MAGNET_PIN": return <Anchor className="h-5 w-5" />;
            default: return <TrendingUp className="h-5 w-5" />;
        }
    };

    const getBiasIcon = () => {
        if (strategy.bias.includes("BULLISH")) return <TrendingUp className="h-3 w-3 mr-1" />;
        if (strategy.bias.includes("BEARISH")) return <TrendingDown className="h-3 w-3 mr-1" />;
        return <Minus className="h-3 w-3 mr-1" />;
    };

    // Color mapping specific to tailwind-merge safelist or standard palette
    // 'emerald', 'rose', 'amber' mapped to border/text classes
    const colorClasses: Record<string, string> = {
        emerald: "border-emerald-500/50 bg-emerald-950/20 text-emerald-100",
        rose: "border-rose-500/50 bg-rose-950/20 text-rose-100",
        amber: "border-amber-500/50 bg-amber-950/20 text-amber-100",
        blue: "border-blue-500/50 bg-blue-950/20 text-blue-100",
    };

    const activeClass = colorClasses[strategy.color] || colorClasses.blue;

    return (
        <Card className={`border-l-4 ${activeClass} transition-all duration-500 animate-in slide-in-from-top-2`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    {getIcon()}
                    Active Strategy: {strategy.signal.replace(/_/g, " ")}
                </CardTitle>
                <Badge variant="outline" className="bg-background/50">
                    {getBiasIcon()}
                    {strategy.bias}
                </Badge>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold tracking-tight mb-1">
                    {strategy.validity} Validity
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                    {strategy.message}
                </p>
            </CardContent>
        </Card>
    );
}
