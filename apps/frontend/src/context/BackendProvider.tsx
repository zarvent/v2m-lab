import React, { createContext, useContext, useState, useEffect, useCallback, useRef, useMemo } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import type { UnlistenFn } from "@tauri-apps/api/event";
import type { Status, HistoryItem } from "../types";
import type { DaemonState, TelemetryData, IpcError } from "../types/ipc";
import {
  STATUS_POLL_INTERVAL_MS,
  PING_UPDATE_INTERVAL_MS,
  HISTORY_STORAGE_KEY,
  MAX_HISTORY_ITEMS,
  SPARKLINE_HISTORY_LENGTH,
} from "../constants";

// --- TYPES ---

interface BackendContextValue {
  status: Status;
  transcription: string;
  errorMessage: string;
  isConnected: boolean;
  lastPingTime: number | null;
  history: HistoryItem[];
  actions: {
    startRecording: (mode?: "replace" | "append") => Promise<void>;
    stopRecording: () => Promise<void>;
    processText: () => Promise<void>;
    translateText: (targetLang: "es" | "en") => Promise<void>;
    setTranscription: (text: string) => void;
    togglePause: () => Promise<void>;
    clearError: () => void;
    retryConnection: () => Promise<void>;
    restartDaemon: () => Promise<void>;
    shutdownDaemon: () => Promise<void>;
  };
}

interface TelemetryContextValue {
  telemetry: TelemetryData | null;
  cpuHistory: number[];
  ramHistory: number[];
}

// --- CONTEXTS ---

const BackendContext = createContext<BackendContextValue | null>(null);
const TelemetryContext = createContext<TelemetryContextValue | null>(null);

// --- HELPERS ---

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

function mapDaemonState(state: string): Status {
  switch (state) {
    case "recording": return "recording";
    case "paused": return "paused";
    case "restarting": return "restarting";
    case "disconnected": return "disconnected";
    case "idle":
    case "running": return "idle";
    default: return "idle";
  }
}

function extractError(e: unknown): string {
  if (typeof e === "object" && e !== null && "message" in e) {
    return (e as IpcError).message;
  }
  return String(e);
}

// --- PROVIDER ---

export const BackendProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // State: Backend
  const [status, setStatus] = useState<Status>("disconnected");
  const [transcription, setTranscription] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [lastPingTime, setLastPingTime] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // State: Telemetry
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [cpuHistory, setCpuHistory] = useState<number[]>([]);
  const [ramHistory, setRamHistory] = useState<number[]>([]);

  // Refs
  const statusRef = useRef<Status>(status);
  const prevTelemetryRef = useRef<TelemetryData | null>(null);
  const lastPingTimeRef = useRef<number>(0);
  const lastEventTimeRef = useRef<number>(Date.now());
  const recordingModeRef = useRef<"replace" | "append">("replace");
  const transcriptionBeforeAppendRef = useRef<string>("");

  useEffect(() => { statusRef.current = status; }, [status]);

  // Load History
  useEffect(() => {
    try {
      const saved = localStorage.getItem(HISTORY_STORAGE_KEY);
      if (saved) setHistory(JSON.parse(saved));
    } catch (e) {
      console.error("Fallo al cargar historial:", e);
    }
  }, []);

  const addToHistory = useCallback((text: string, source: "recording" | "refinement") => {
    if (!text.trim()) return;
    const newItem: HistoryItem = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      text,
      source,
    };
    setHistory((prev) => {
      const updated = [newItem, ...prev].slice(0, MAX_HISTORY_ITEMS);
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Handler for state updates
  const handleStateUpdate = useCallback((data: DaemonState) => {
    lastEventTimeRef.current = Date.now();
    setIsConnected(true);

    const now = Date.now();
    if (now - lastPingTimeRef.current > PING_UPDATE_INTERVAL_MS) {
      setLastPingTime(now);
      lastPingTimeRef.current = now;
    }

    // Telemetry Update
    if (data.telemetry && !isTelemetryEqual(prevTelemetryRef.current, data.telemetry)) {
      prevTelemetryRef.current = data.telemetry;
      setTelemetry(data.telemetry);
      setCpuHistory((h) => [...h, data.telemetry!.cpu.percent].slice(-SPARKLINE_HISTORY_LENGTH));
      setRamHistory((h) => [...h, data.telemetry!.ram.percent].slice(-SPARKLINE_HISTORY_LENGTH));
    }

    // Transcription Update
    if (data.transcription !== undefined) setTranscription(data.transcription);
    if (data.refined_text !== undefined) setTranscription(data.refined_text);

    // Status Update
    const newStatus = mapDaemonState(data.state);
    setStatus((prev) => {
      if ((prev === "transcribing" || prev === "processing") && newStatus === "idle") {
        return prev;
      }
      return newStatus;
    });
  }, []);

  const pollStatus = useCallback(async () => {
    try {
      const data = await invoke<DaemonState>("get_status");
      handleStateUpdate(data);
      if (statusRef.current === "disconnected") setErrorMessage("");
    } catch (e) {
      console.warn("[BackendProvider] Poll failed:", e);
      setIsConnected(false);
      setStatus("disconnected");
    }
  }, [handleStateUpdate]);

  // Listener Setup
  useEffect(() => {
    let unlisten: UnlistenFn | null = null;
    pollStatus();
    listen<DaemonState>("v2m://state-update", (event) => handleStateUpdate(event.payload))
      .then((fn) => { unlisten = fn; });

    const fallbackInterval = setInterval(() => {
      if (Date.now() - lastEventTimeRef.current > STATUS_POLL_INTERVAL_MS * 4) {
        pollStatus();
      }
    }, STATUS_POLL_INTERVAL_MS);

    return () => {
      unlisten?.();
      clearInterval(fallbackInterval);
    };
  }, [pollStatus, handleStateUpdate]);

  // Actions
  const actions = useMemo(() => ({
    startRecording: async (mode: "replace" | "append" = "replace") => {
      if (statusRef.current === "paused") return;
      try {
        recordingModeRef.current = mode;
        if (mode === "append") transcriptionBeforeAppendRef.current = transcription;
        const data = await invoke<DaemonState>("start_recording");
        handleStateUpdate(data);
      } catch (e) {
        setErrorMessage(extractError(e));
        setStatus("error");
      }
    },
    stopRecording: async () => {
      setStatus("transcribing");
      try {
        const data = await invoke<DaemonState>("stop_recording");
        if (data.transcription) {
          setTranscription(data.transcription);
          addToHistory(data.transcription, "recording");
          setStatus("idle");
        } else {
          setErrorMessage("No se detectó voz");
          setStatus("error");
        }
      } catch (e) {
        setErrorMessage(extractError(e));
        setStatus("error");
      }
    },
    processText: async () => {
      if (!transcription) return;
      setStatus("processing");
      try {
        const data = await invoke<DaemonState>("process_text", { text: transcription });
        if (data.refined_text) {
          setTranscription(data.refined_text);
          addToHistory(data.refined_text, "refinement");
          setStatus("idle");
        } else {
          setErrorMessage("Error de LLM");
          setStatus("error");
        }
      } catch (e) {
        setErrorMessage(extractError(e));
        setStatus("error");
      }
    },
    translateText: async (targetLang: "es" | "en") => {
      if (!transcription) return;
      setStatus("processing");
      try {
        const data = await invoke<DaemonState>("translate_text", { text: transcription, targetLang });
        if (data.refined_text) {
          setTranscription(data.refined_text);
          addToHistory(data.refined_text, "refinement");
          setStatus("idle");
        } else {
          setErrorMessage("Falló traducción");
          setStatus("error");
        }
      } catch (e) {
        setErrorMessage(extractError(e));
        setStatus("error");
      }
    },
    togglePause: async () => {
      try {
        if (statusRef.current === "paused") {
          await invoke<DaemonState>("resume_daemon");
          setStatus("idle");
        } else {
          await invoke<DaemonState>("pause_daemon");
          setStatus("paused");
        }
      } catch (e) {
        setErrorMessage(extractError(e));
      }
    },
    setTranscription,
    clearError: () => setErrorMessage(""),
    retryConnection: async () => { await pollStatus(); },
    restartDaemon: async () => {
      setStatus("restarting");
      try { await invoke<DaemonState>("restart_daemon"); }
      catch (e) { setErrorMessage(extractError(e)); setStatus("error"); }
    },
    shutdownDaemon: async () => {
      setStatus("shutting_down");
      try {
        await invoke<DaemonState>("shutdown_daemon");
        setStatus("disconnected");
        setIsConnected(false);
      } catch (e) {
        setErrorMessage(extractError(e));
        setStatus("error");
      }
    },
  }), [transcription, addToHistory, pollStatus, handleStateUpdate]);

  const backendValue = useMemo(() => ({
    status, transcription, errorMessage, isConnected, lastPingTime, history, actions
  }), [status, transcription, errorMessage, isConnected, lastPingTime, history, actions]);

  const telemetryValue = useMemo(() => ({
    telemetry, cpuHistory, ramHistory
  }), [telemetry, cpuHistory, ramHistory]);

  return (
    <BackendContext.Provider value={backendValue}>
      <TelemetryContext.Provider value={telemetryValue}>
        {children}
      </TelemetryContext.Provider>
    </BackendContext.Provider>
  );
};

// --- HOOKS ---

export const useBackendState = () => {
  const context = useContext(BackendContext);
  if (!context) throw new Error("useBackendState must be used within BackendProvider");
  return context;
};

export const useTelemetry = () => {
  const context = useContext(TelemetryContext);
  if (!context) throw new Error("useTelemetry must be used within BackendProvider");
  return context;
};
