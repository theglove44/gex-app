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

interface MajorLevel {
    Strike: number;
    Type: string;
    "Net GEX ($M)": number;
}

interface MajorLevelsTableProps {
    data: MajorLevel[];
}

export function MajorLevelsTable({ data }: MajorLevelsTableProps) {
    return (
        <Card className="col-span-2 border-sidebar-border bg-card">
            <CardHeader>
                <CardTitle>Major Gamma Levels</CardTitle>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[100px]">Strike</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead className="text-right">Net GEX</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {data.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={3} className="text-center text-muted-foreground py-8">
                                    No major levels found
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.map((level, i) => (
                                <TableRow key={i}>
                                    <TableCell className="font-mono font-medium">${level.Strike}</TableCell>
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
                                    <TableCell className={level['Net GEX ($M)'] > 0 ? "text-right font-mono text-emerald-500" : "text-right font-mono text-rose-500"}>
                                        ${level["Net GEX ($M)"]}M
                                    </TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    );
}
