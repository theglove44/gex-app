import { useEffect, useState, useRef } from 'react';
import { toast } from 'sonner';

interface UseGEXAlertsProps {
    spotPrice: number;
    callWall?: number;
    putWall?: number;
    zeroGamma?: number;
    symbol: string;
}

export function useGEXAlerts({ spotPrice, callWall, putWall, zeroGamma, symbol }: UseGEXAlertsProps) {
    const [alertsEnabled, setAlertsEnabled] = useState(false);
    const [soundEnabled, setSoundEnabled] = useState(false);

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
        if (!alertsEnabled || prevPriceRef.current === null) {
            prevPriceRef.current = spotPrice;
            return;
        }

        const prev = prevPriceRef.current;
        const curr = spotPrice;

        const checkCross = (level: number | undefined, name: string, type: 'bullish' | 'bearish') => {
            if (!level) return;

            // Bullish Cross: Prev < Level <= Curr
            if (prev < level && curr >= level) {
                toast.success(`${symbol} crossed ABOVE ${name} (${level})!`, {
                    description: `Bullish Breakout? Price: $${curr.toFixed(2)}`,
                    duration: 5000,
                });
                playSound();
            }

            // Bearish Cross: Prev > Level >= Curr
            if (prev > level && curr <= level) {
                toast.error(`${symbol} crossed BELOW ${name} (${level})!`, {
                    description: `Bearish Breakdown? Price: $${curr.toFixed(2)}`,
                    duration: 5000,
                });
                playSound();
            }
        };

        checkCross(callWall, "Call Wall", 'bullish'); // Usually bullish if broken, or resistant
        checkCross(putWall, "Put Wall", 'bearish');   // Usually bearish if broken, or support
        checkCross(zeroGamma, "Zero Gamma", curr > (zeroGamma || 0) ? 'bullish' : 'bearish');

        prevPriceRef.current = curr;
    }, [spotPrice, alertsEnabled, soundEnabled, callWall, putWall, zeroGamma, symbol]);

    return {
        alertsEnabled,
        setAlertsEnabled,
        soundEnabled,
        setSoundEnabled
    };
}
