import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import type { Status } from "../types";

export interface TimerState {
  seconds: number;
  formatted: string;
  isRunning: boolean;
  reset: () => void;
}

// Tabla de búsqueda pre-calculada: evita padStart() y toString() en tiempo de ejecución
const PAD = Object.freeze(
  Array.from({ length: 60 }, (_, i) => (i < 10 ? `0${i}` : `${i}`))
) as readonly string[];

/**
 * Hook optimizado para el seguimiento de la duración de la sesión.
 * - Único useEffect para todas las transiciones de estado.
 * - División bitwise para formateo (más rápido que Math.floor).
 * - Tabla de búsqueda elimina operaciones de cadena costosas.
 */
export function useTimer(status: Status): TimerState {
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevStatusRef = useRef<Status>(status);

  const isRunning = status === "recording";

  // Efecto consolidado para toda la lógica del temporizador
  useEffect(() => {
    const prevStatus = prevStatusRef.current;
    prevStatusRef.current = status;

    // Reiniciar al iniciar una nueva grabación (idle → recording)
    if (status === "recording" && prevStatus === "idle") {
      setSeconds(0);
    }

    // Iniciar intervalo si se está grabando
    if (status === "recording" && !intervalRef.current) {
      intervalRef.current = setInterval(() => {
        setSeconds((s) => s + 1);
      }, 1000);
    }

    // Detener intervalo cuando no se graba
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

  // Salida formateada memoizada con división bitwise
  const formatted = useMemo(() => {
    const m = (seconds / 60) | 0; // Bitwise floor
    const s = seconds % 60;
    return `${PAD[m] ?? m}:${PAD[s]}`;
  }, [seconds]);

  return { seconds, formatted, isRunning, reset };
}
