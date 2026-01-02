import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import type { Status } from "../types";

export interface TimerState {
  seconds: number;
  formatted: string;
  isRunning: boolean;
  reset: () => void;
}

// Pre-computed lookup table: avoids padStart() and toString() at runtime
const PAD = Object.freeze(
  Array.from({ length: 60 }, (_, i) => (i < 10 ? `0${i}` : `${i}`))
) as readonly string[];

/**
 * Optimized hook for session duration tracking.
 * - Single useEffect for all state transitions
 * - Bitwise division for formatting (faster than Math.floor)
 * - Lookup table eliminates string operations
 */
export function useTimer(status: Status): TimerState {
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevStatusRef = useRef<Status>(status);

  const isRunning = status === "recording";

  // Single consolidated effect for all timer logic
  useEffect(() => {
    const prevStatus = prevStatusRef.current;
    prevStatusRef.current = status;

    // Reset on fresh recording start (idle → recording)
    if (status === "recording" && prevStatus === "idle") {
      setSeconds(0);
    }

    // Start interval if recording
    if (status === "recording" && !intervalRef.current) {
      intervalRef.current = setInterval(() => {
        setSeconds((s) => s + 1);
      }, 1000);
    }

    // Stop interval when not recording
    if (status !== "recording" && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [status]);

  const reset = useCallback(() => setSeconds(0), []);

  // Memoized formatted output with bitwise division
  const formatted = useMemo(() => {
    const m = (seconds / 60) | 0; // Bitwise floor
    const s = seconds % 60;
    return `${PAD[m] ?? m}:${PAD[s]}`;
  }, [seconds]);

  return { seconds, formatted, isRunning, reset };
}
