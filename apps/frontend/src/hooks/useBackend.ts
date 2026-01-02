import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import type { UnlistenFn } from "@tauri-apps/api/event";
import type {
  BackendState,
  BackendActions,
  Status,
  HistoryItem,
} from "../types";
import type { DaemonState, TelemetryData, IpcError } from "../types/ipc";
import {
  STATUS_POLL_INTERVAL_MS,
  PING_UPDATE_INTERVAL_MS,
  HISTORY_STORAGE_KEY,
  MAX_HISTORY_ITEMS,
  SPARKLINE_HISTORY_LENGTH,
} from "../constants";

// --- OPTIMIZED HELPERS ---

/**
 * O(1) Fuzzy telemetry comparison.
 * Ignores negligible changes (epsilon) to prevent excessive re-renders.
 */
function isTelemetryEqual(
  a: TelemetryData | null,
  b: TelemetryData | null
): boolean {
  if (a === b) return true;
  if (!a || !b) return false;

  const EPSILON_PERCENT = 0.5; // 0.5% change threshold
  const EPSILON_RAM_GB = 0.1; // 100MB change threshold
  const EPSILON_VRAM_MB = 50; // 50MB change threshold

  // CPU
  if (Math.abs(a.cpu.percent - b.cpu.percent) > EPSILON_PERCENT) return false;

  // RAM
  if (Math.abs(a.ram.percent - b.ram.percent) > EPSILON_PERCENT) return false;
  if (Math.abs(a.ram.used_gb - b.ram.used_gb) > EPSILON_RAM_GB) return false;

  // GPU
  if (!!a.gpu !== !!b.gpu) return false;
  if (
    a.gpu &&
    b.gpu &&
    (Math.abs(a.gpu.vram_used_mb - b.gpu.vram_used_mb) > EPSILON_VRAM_MB ||
      Math.abs(a.gpu.temp_c - b.gpu.temp_c) > 1)
  )
    return false;

  return true;
}

/** Map daemon state string to Status type */
function mapDaemonState(state: string): Status {
  switch (state) {
    case "recording":
      return "recording";
    case "paused":
      return "paused";
    case "restarting":
      return "restarting";
    case "disconnected":
      return "disconnected";
    case "idle":
    case "running":
      return "idle";
    default:
      // Log unexpected states for debugging
      console.warn(`[useBackend] Unexpected daemon state: ${state}`);
      return "idle";
  }
}

/** Extract error message from IpcError or string */
function extractError(e: unknown): string {
  if (typeof e === "object" && e !== null && "message" in e) {
    return (e as IpcError).message;
  }
  return String(e);
}

/**
 * OPTIMIZED BACKEND HOOK - Event-driven with typed IPC
 *
 * Architecture:
 * - Initial GET_STATUS on mount for hydration
 * - Tauri event listener for push updates (v2m://state-update)
 * - Fallback polling only when events not received (disconnection recovery)
 * - Typed invoke() calls - no JSON.parse overhead
 */
export function useBackend(): [BackendState, BackendActions] {
  // --- STATE ---
  const [status, setStatus] = useState<Status>("disconnected");
  const [transcription, setTranscription] = useState("");
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [cpuHistory, setCpuHistory] = useState<number[]>([]);
  const [ramHistory, setRamHistory] = useState<number[]>([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [lastPingTime, setLastPingTime] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // --- REFS (avoid stale closures) ---
  const statusRef = useRef<Status>(status);
  const prevTelemetryRef = useRef<TelemetryData | null>(null);
  const lastPingTimeRef = useRef<number>(0);
  const lastEventTimeRef = useRef<number>(Date.now());
  const recordingModeRef = useRef<"replace" | "append">("replace");
  const transcriptionBeforeAppendRef = useRef<string>("");

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  // --- HISTORY PERSISTENCE ---
  useEffect(() => {
    try {
      const saved = localStorage.getItem(HISTORY_STORAGE_KEY);
      if (saved) setHistory(JSON.parse(saved));
    } catch (e) {
      console.error("Failed to load history from localStorage:", e);
    }
  }, []);

  const addToHistory = useCallback(
    (text: string, source: "recording" | "refinement") => {
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
    },
    []
  );

  // --- STATE UPDATE HANDLER (shared by poll and events) ---
  const handleStateUpdate = useCallback((data: DaemonState) => {
    lastEventTimeRef.current = Date.now();
    setIsConnected(true);

    // Throttle ping time updates (5s)
    const now = Date.now();
    if (now - lastPingTimeRef.current > PING_UPDATE_INTERVAL_MS) {
      setLastPingTime(now);
      lastPingTimeRef.current = now;
    }

    // Update telemetry with diff check
    if (
      data.telemetry &&
      !isTelemetryEqual(prevTelemetryRef.current, data.telemetry)
    ) {
      prevTelemetryRef.current = data.telemetry;
      setTelemetry(data.telemetry);
      setCpuHistory((h) =>
        [...h, data.telemetry!.cpu.percent].slice(-SPARKLINE_HISTORY_LENGTH)
      );
      setRamHistory((h) =>
        [...h, data.telemetry!.ram.percent].slice(-SPARKLINE_HISTORY_LENGTH)
      );
    }

    // Update transcription if present
    if (data.transcription !== undefined) {
      setTranscription(data.transcription);
    }
    if (data.refined_text !== undefined) {
      setTranscription(data.refined_text);
    }

    // Map state - preserve transitional states
    const newStatus = mapDaemonState(data.state);
    setStatus((prev) => {
      if (
        (prev === "transcribing" || prev === "processing") &&
        newStatus === "idle"
      ) {
        return prev; // Don't interrupt transitional state
      }
      return newStatus;
    });
  }, []);

  // --- POLL FUNCTION (for initial load and fallback) ---
  const pollStatus = useCallback(async () => {
    try {
      const data = await invoke<DaemonState>("get_status");
      handleStateUpdate(data);
      if (statusRef.current === "disconnected") setErrorMessage("");
    } catch {
      setIsConnected(false);
      setStatus("disconnected");
    }
  }, [handleStateUpdate]);

  // --- EVENT LISTENER (primary update mechanism) ---
  useEffect(() => {
    let unlisten: UnlistenFn | null = null;

    // Initial fetch
    pollStatus();

    // Subscribe to push events
    listen<DaemonState>("v2m://state-update", (event) => {
      handleStateUpdate(event.payload);
    }).then((fn) => {
      unlisten = fn;
    });

    // Fallback polling - only if no events received in 2 seconds
    const fallbackInterval = setInterval(() => {
      const timeSinceLastEvent = Date.now() - lastEventTimeRef.current;
      if (timeSinceLastEvent > STATUS_POLL_INTERVAL_MS * 4) {
        pollStatus();
      }
    }, STATUS_POLL_INTERVAL_MS);

    return () => {
      unlisten?.();
      clearInterval(fallbackInterval);
    };
  }, [pollStatus, handleStateUpdate]);

  // --- ACTIONS (typed invoke, no JSON.parse) ---

  const startRecording = useCallback(
    async (mode: "replace" | "append" = "replace") => {
      if (statusRef.current === "paused") return;
      try {
        // Store mode and current transcription for append
        recordingModeRef.current = mode;
        if (mode === "append") {
          transcriptionBeforeAppendRef.current = transcription;
        }
        const data = await invoke<DaemonState>("start_recording");
        handleStateUpdate(data);
      } catch (e) {
        setErrorMessage(extractError(e));
        setStatus("error");
      }
    },
    [handleStateUpdate, transcription]
  );

  const stopRecording = useCallback(async () => {
    setStatus("transcribing"); // Optimistic UI
    try {
      const data = await invoke<DaemonState>("stop_recording");
      if (data.transcription) {
        // Handle append mode: combine previous + new transcription
        if (
          recordingModeRef.current === "append" &&
          transcriptionBeforeAppendRef.current
        ) {
          const combined = `${transcriptionBeforeAppendRef.current}\n\n${data.transcription}`;
          setTranscription(combined);
          addToHistory(combined, "recording");
        } else {
          setTranscription(data.transcription);
          addToHistory(data.transcription, "recording");
        }
        // Reset mode
        recordingModeRef.current = "replace";
        transcriptionBeforeAppendRef.current = "";
        setStatus("idle");
      } else {
        setErrorMessage("No speech detected in audio");
        setStatus("error");
      }
    } catch (e) {
      setErrorMessage(extractError(e));
      setStatus("error");
    }
  }, [addToHistory]);

  const processText = useCallback(async () => {
    if (!transcription) return;
    setStatus("processing"); // Optimistic UI
    try {
      const data = await invoke<DaemonState>("process_text", {
        text: transcription,
      });
      if (data.refined_text) {
        setTranscription(data.refined_text);
        addToHistory(data.refined_text, "refinement");
        setStatus("idle");
      } else {
        setErrorMessage("Unexpected LLM response");
        setStatus("error");
      }
    } catch (e) {
      setErrorMessage(extractError(e));
      setStatus("error");
    }
  }, [transcription, addToHistory]);

  const togglePause = useCallback(async () => {
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
  }, []);

  const clearError = useCallback(() => setErrorMessage(""), []);

  const retryConnection = useCallback(async () => {
    await pollStatus();
  }, [pollStatus]);

  const restartDaemon = useCallback(async () => {
    setStatus("restarting");
    try {
      await invoke<DaemonState>("restart_daemon");
      // Event listener will detect when daemon is back online
    } catch (e) {
      setErrorMessage(extractError(e));
      setStatus("error");
    }
  }, []);

  const shutdownDaemon = useCallback(async () => {
    setStatus("shutting_down");
    try {
      await invoke<DaemonState>("shutdown_daemon");
      setStatus("disconnected");
      setIsConnected(false);
    } catch (e) {
      setErrorMessage(extractError(e));
      setStatus("error");
    }
  }, []);
  // --- MEMOIZED RETURN VALUES ---

  const state: BackendState = useMemo(
    () => ({
      status,
      transcription,
      telemetry,
      cpuHistory,
      ramHistory,
      errorMessage,
      isConnected,
      lastPingTime,
      history,
    }),
    [
      status,
      transcription,
      telemetry,
      cpuHistory,
      ramHistory,
      errorMessage,
      isConnected,
      lastPingTime,
      history,
    ]
  );

  const actions: BackendActions = useMemo(
    () => ({
      startRecording,
      stopRecording,
      processText,
      togglePause,
      setTranscription,
      clearError,
      retryConnection,
      restartDaemon,
      shutdownDaemon,
    }),
    [
      startRecording,
      stopRecording,
      processText,
      togglePause,
      clearError,
      retryConnection,
      restartDaemon,
      shutdownDaemon,
    ]
  );

  return [state, actions];
}
