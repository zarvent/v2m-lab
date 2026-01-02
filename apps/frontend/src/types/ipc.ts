/**
 * IPC Types - Shared type definitions for Tauri-Python communication
 * Mirrors Rust DaemonState and IpcError for type safety across the stack
 */

/** CPU telemetry */
export interface CpuInfo {
  percent: number;
}

/** RAM telemetry */
export interface RamInfo {
  used_gb: number;
  total_gb: number;
  percent: number;
}

/** GPU telemetry (optional - only if NVIDIA/AMD detected) */
export interface GpuInfo {
  name: string;
  vram_used_mb: number;
  vram_total_mb: number;
  temp_c: number;
}

/** System telemetry data */
export interface TelemetryData {
  cpu: CpuInfo;
  ram: RamInfo;
  gpu?: GpuInfo;
}

/** Daemon state payload - pushed from Rust via events */
export interface DaemonState {
  state: string;
  transcription?: string;
  refined_text?: string;
  message?: string;
  telemetry?: TelemetryData;
}

/** Structured IPC error */
export interface IpcError {
  code: string;
  message: string;
}

/** Event payload wrapper */
export interface StateUpdateEvent {
  payload: DaemonState;
}

/** IPC error codes for typed handling */
export const IpcErrorCode = {
  IPC_ERROR: "IPC_ERROR",
  DAEMON_ERROR: "DAEMON_ERROR",
  PAYLOAD_TOO_LARGE: "PAYLOAD_TOO_LARGE",
  RESTART_FAILED: "RESTART_FAILED",
  SHUTDOWN_FAILED: "SHUTDOWN_FAILED",
} as const;

export type IpcErrorCodeType = (typeof IpcErrorCode)[keyof typeof IpcErrorCode];
