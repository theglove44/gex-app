import { ScannerView } from "@/components/scanner/scanner-view";

export default function ScannerPage() {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold tracking-tight">Universe Scanner</h1>
            </div>
            <ScannerView />
        </div>
    );
}
