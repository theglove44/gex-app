import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KPICardProps {
    title: string;
    value: string | number;
    subValue?: string;
    trend?: "up" | "down" | "neutral";
    className?: string;
}

export function KPICard({ title, value, subValue, trend, className }: KPICardProps) {
    return (
        <Card className={cn("border-sidebar-border bg-card shadow-sm", className)}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    {title}
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold font-mono tracking-tight text-foreground">
                    {value}
                </div>
                {subValue && (
                    <p className="text-xs text-muted-foreground mt-1">
                        {subValue}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
