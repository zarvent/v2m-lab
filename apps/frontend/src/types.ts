/**
 * DEFINICIONES DE TIPOS (TYPESCRIPT)
 * Centraliza interfaces para mantener consistencia y limpieza (SEIKETSU).
 *
 * @module Types
 */

// Import and re-export IPC types
import type {
  TelemetryData as TelemetryDataType,
  CpuInfo,
  RamInfo,
  GpuInfo,
  DaemonState,
  IpcError,
} from "./types/ipc";

export type TelemetryData = TelemetryDataType;
export type { CpuInfo, RamInfo, GpuInfo, DaemonState, IpcError };

/**
 * Estados posibles del sistema (Máquina de estados finita simplificada).
 * - idle: Esperando acción
 * - recording: Grabando audio activamente
 * - transcribing: Procesando audio a texto (Whisper)
 * - processing: Refinando texto (LLM)
 * - paused: Daemon pausado manualmente
 * - error: Estado de error recuperable
 * - disconnected: Sin conexión con el daemon backend
 * - restarting: Reiniciando el servicio
 * - shutting_down: Apagando el servicio
 */
export type Status =
  | "idle"
  | "recording"
  | "transcribing"
  | "processing"
  | "paused"
  | "error"
  | "disconnected"
  | "restarting"
  | "shutting_down";

/**
 * Item individual del historial de transcripciones.
 * Persistido en localStorage.
 */
export interface HistoryItem {
  /** UUID único */
  id: string;
  /** Timestamp UNIX (ms) de creación */
  timestamp: number;
  /** Contenido del texto */
  text: string;
  /** Origen del texto: grabación directa o refinamiento IA */
  source: "recording" | "refinement";
}

/**
 * Estado global del backend expuesto a la UI mediante useBackend.
 */
export interface BackendState {
  /** Estado actual del flujo */
  status: Status;
  /** Texto actual en el área de transcripción */
  transcription: string;
  /** Datos de rendimiento en tiempo real */
  telemetry: TelemetryData | null;
  /** Historial de uso de CPU para gráficas */
  cpuHistory: number[];
  /** Historial de uso de RAM para gráficas */
  ramHistory: number[];
  /** Mensaje de error actual (si existe) */
  errorMessage: string;
  /** Flag de conexión socket activa */
  isConnected: boolean;
  /** Timestamp del último heartbeat recibido */
  lastPingTime: number | null;
  /** Historial local de transcripciones */
  history: HistoryItem[];
}

/**
 * Acciones disponibles para la UI para interactuar con el backend.
 * Patrón Command/Action.
 */
export interface BackendActions {
  /** Inicia la grabación de micrófono */
  startRecording: (mode?: "replace" | "append") => Promise<void>;
  /** Detiene grabación y dispara transcripción */
  stopRecording: () => Promise<void>;
  /** Envía el texto actual al LLM para refinamiento */
  processText: () => Promise<void>;
  /** Alterna entre pausar/reanudar el daemon */
  togglePause: () => Promise<void>;
  /** Actualiza manualmente el texto en UI */
  setTranscription: (text: string) => void;
  /** Limpia el mensaje de error actual */
  clearError: () => void;
  /** Fuerza un re-intento de conexión */
  retryConnection: () => Promise<void>;
  /** Solicita reinicio completo del proceso daemon */
  restartDaemon: () => Promise<void>;
  /** Apaga completamente el daemon */
  shutdownDaemon: () => Promise<void>;
}

/** Configuración específica para el modelo Whisper */
export interface WhisperConfig {
  /** Nombre del modelo (ej: tiny, base, small, medium, large-v3-turbo) */
  model?: string;
  /** Idioma forzado (opcional) */
  language?: string;
  /** Dispositivo de cómputo: "cuda" o "cpu" */
  device?: string;
  /** Precisión de cómputo (int8, float16, int8_float16) */
  compute_type?: string;
  /** Activar filtro VAD (Voice Activity Detection) */
  vad_filter?: boolean;
  /** Tamaño del beam search */
  beam_size?: number;
  /** Parámetros finos de VAD */
  vad_parameters?: {
    min_silence_duration_ms?: number;
    speech_pad_ms?: number;
  };
}

/** Configuración para Gemini (Google Cloud) */
export interface GeminiConfig {
  api_key?: string;
  model?: string;
}

/** Configuración para LLM Local (llama.cpp) */
export interface LocalLLMConfig {
  /** Ruta relativa a models/ del archivo .gguf */
  model_path?: string;
  /** Máximo de tokens a generar */
  max_tokens?: number;
}

/** Configuración general de LLM */
export interface LLMConfig {
  /** Backend seleccionado */
  backend?: "local" | "gemini";
  gemini?: GeminiConfig;
  local?: LocalLLMConfig;
}

/**
 * Configuración completa del sistema mapeada desde config.toml.
 */
export interface AppConfig {
  whisper?: WhisperConfig;
  llm?: LLMConfig;
  paths?: {
    output_dir?: string;
  };
  notifications?: {
    auto_dismiss?: boolean;
    expire_time_ms?: number;
  };
}
