import { useEffect, useState, useRef } from 'react';
import { toast } from 'sonner';

interface UseGEXAlertsProps {
    spotPrice: number;
    callWall?: number;
    putWall?: number;
    zeroGamma?: number | null; // e.g., 4450
    symbol: string;
}

const ALERT_COOLDOWN_MS = 300000; // 5 minutes cooldown per level

export function useGEXAlerts({
    symbol,
    spotPrice,
    callWall,
    putWall,
    zeroGamma
}: UseGEXAlertsProps) {
    const [alertsEnabled, setAlertsEnabled] = useState(false);
    const [soundEnabled, setSoundEnabled] = useState(false);

    const prevSpotRef = useRef<number>(spotPrice);
    const lastTriggeredRef = useRef<Record<string, number>>({}); // Track last alert timestamp per level to detect crossings
    // Store previous price to detect crossings
    const prevPriceRef = useRef<number | null>(null);

    const playSound = () => {
        if (!soundEnabled) return;
        try {
            const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 880; // A5
            gain.gain.value = 0.05; // Low volume
            osc.start();
            setTimeout(() => osc.stop(), 200);
        } catch (e) {
            console.error("Audio play failed", e);
        }
    };

    useEffect(() => {
        if (!alertsEnabled) {
            prevSpotRef.current = spotPrice; // Always update prevSpotRef even if alerts are disabled
            return;
        }

        const prevSpot = prevSpotRef.current;

        const checkCross = (level: number | undefined | null, name: string) => {
            if (level === undefined || level === null) return;

            const now = Date.now();
            const lastTrigger = lastTriggeredRef.current[name] || 0;
            if (now - lastTrigger < ALERT_COOLDOWN_MS) return; // Skip if in cooldown

            // Bullish Cross (Breakout/Reclaim)
            if (prevSpot < level && spotPrice >= level) {
                const msg = `🚀 ${symbol} crossed ABOVE ${name} (${level})`;
                toast.success(msg);
                playSound();
                lastTriggeredRef.current[name] = now;
            }
            // Bearish Cross (Breakdown/Loss)
            else if (prevSpot > level && spotPrice <= level) {
                const msg = `🔻 ${symbol} crossed BELOW ${name} (${level})`;
                toast.error(msg);
                playSound();
                lastTriggeredRef.current[name] = now;
            }
        };

        checkCross(zeroGamma, "Zero Gamma");
        checkCross(callWall, "Call Wall");
        checkCross(putWall, "Put Wall");

        prevSpotRef.current = spotPrice;
    }, [spotPrice, zeroGamma, callWall, putWall, alertsEnabled, symbol, playSound]);

    return {
        alertsEnabled,
        setAlertsEnabled,
        soundEnabled,
        setSoundEnabled
    };
}
