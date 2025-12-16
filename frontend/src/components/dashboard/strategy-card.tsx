import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrendingUp, TrendingDown, Minus, Anchor, Zap, Target, AlertTriangle, Clock, HelpCircle } from "lucide-react";
import {
    getTradingApproach,
    getRiskGuidance,
    getTimeHorizon,
} from "@/lib/strategy-guidance";

interface StrategySignal {
    signal: string;
    bias: string;
    message: string;
    validity: string;
    color: string;
}

interface StrategyCardProps {
    strategy: StrategySignal;
    onHelpClick?: () => void;
}

export function StrategyCard({ strategy, onHelpClick }: StrategyCardProps) {
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

    const tradingApproach = getTradingApproach(strategy.signal);
    const riskGuidance = getRiskGuidance(strategy.signal);
    const timeHorizon = getTimeHorizon(strategy.signal);

    return (
        <Card className={`border-l-4 ${activeClass} transition-all duration-500 animate-in slide-in-from-top-2`}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    {getIcon()}
                    Active Strategy: {strategy.signal.replace(/_/g, " ")}
                </CardTitle>
                <Badge variant="outline" className="bg-background/50">
                    {getBiasIcon()}
                    {strategy.bias}
                </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Signal Message */}
                <div>
                    <div className="text-2xl font-bold tracking-tight mb-1">
                        {strategy.validity} Validity
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                        {strategy.message}
                    </p>
                </div>

                {/* Trading Guidance Section */}
                <div className="border-t border-border/50 pt-3 space-y-3">
                    <div className="text-xs font-semibold text-foreground/70 uppercase tracking-wider">
                        Trading Guidance
                    </div>

                    {/* Trading Approach */}
                    <div className="flex gap-3">
                        <Target className="h-4 w-4 mt-0.5 text-emerald-400 flex-shrink-0" />
                        <div>
                            <div className="text-xs font-medium text-foreground/80">Trading Approach</div>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                {tradingApproach}
                            </p>
                        </div>
                    </div>

                    {/* Risk Level */}
                    <div className="flex gap-3">
                        <AlertTriangle className="h-4 w-4 mt-0.5 text-rose-400 flex-shrink-0" />
                        <div>
                            <div className="text-xs font-medium text-foreground/80">Risk Level</div>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                {riskGuidance}
                            </p>
                        </div>
                    </div>

                    {/* Time Horizon */}
                    <div className="flex gap-3">
                        <Clock className="h-4 w-4 mt-0.5 text-amber-400 flex-shrink-0" />
                        <div>
                            <div className="text-xs font-medium text-foreground/80">Time Horizon</div>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                {timeHorizon}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="border-t border-border/50 pt-3 flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-8 flex-1"
                        onClick={onHelpClick}
                    >
                        <HelpCircle className="h-3 w-3 mr-1" />
                        Learn More
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        className="text-xs h-8 flex-1"
                        disabled
                        title="Highlights relevant price levels on chart (Future Enhancement)"
                    >
                        <Target className="h-3 w-3 mr-1" />
                        Key Levels
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
