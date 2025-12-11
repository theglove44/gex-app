import { Badge } from "@/components/ui/badge";

export function Header() {
    return (
        <header className="flex h-16 items-center border-b px-6 bg-background">
            <div className="flex items-center gap-4 ml-auto">
                <Badge variant="outline" className="text-emerald-500 border-emerald-900 bg-emerald-950/30">
                    ● Market Open
                </Badge>
                <span className="text-sm text-muted-foreground">
                    {new Date().toLocaleDateString()}
                </span>
            </div>
        </header>
    );
}
