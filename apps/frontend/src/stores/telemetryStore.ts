import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { TelemetryData } from "../types/ipc";
import { SPARKLINE_HISTORY_LENGTH } from "../constants";

interface TelemetryState {
  telemetry: TelemetryData | null;
  cpuHistory: number[];
  ramHistory: number[];

  updateTelemetry: (data: TelemetryData) => void;
}

function isTelemetryEqual(a: TelemetryData | null, b: TelemetryData | null): boolean {
  if (a === b) return true;
  if (!a || !b) return false;
  const EPSILON_PERCENT = 1.0;
  const EPSILON_RAM_GB = 0.15;
  const EPSILON_VRAM_MB = 75;
  if (Math.abs(a.cpu.percent - b.cpu.percent) > EPSILON_PERCENT) return false;
  if (Math.abs(a.ram.percent - b.ram.percent) > EPSILON_PERCENT) return false;
  if (Math.abs(a.ram.used_gb - b.ram.used_gb) > EPSILON_RAM_GB) return false;
  if (!!a.gpu !== !!b.gpu) return false;
  if (a.gpu && b.gpu && (
      Math.abs(a.gpu.vram_used_mb - b.gpu.vram_used_mb) > EPSILON_VRAM_MB ||
      Math.abs(a.gpu.temp_c - b.gpu.temp_c) > 1
  )) return false;
  return true;
}

export const useTelemetryStore = create<TelemetryState>()(
  devtools(
    (set, get) => ({
      telemetry: null,
      cpuHistory: [],
      ramHistory: [],

      updateTelemetry: (data: TelemetryData) => {
        const { telemetry } = get();
        if (!isTelemetryEqual(telemetry, data)) {
          set((state) => ({
            telemetry: data,
            cpuHistory: [...state.cpuHistory, data.cpu.percent].slice(-SPARKLINE_HISTORY_LENGTH),
            ramHistory: [...state.ramHistory, data.ram.percent].slice(-SPARKLINE_HISTORY_LENGTH),
          }));
        }
      },
    }),
    { name: 'TelemetryStore' }
  )
);
