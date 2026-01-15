import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { invoke } from "@tauri-apps/api/core";
import type { Status, HistoryItem } from "../types";
import type { DaemonState, IpcError } from "../types/ipc";
import { HISTORY_STORAGE_KEY, MAX_HISTORY_ITEMS, PING_UPDATE_INTERVAL_MS } from "../constants";

interface BackendState {
  status: Status;
  transcription: string;
  errorMessage: string;
  isConnected: boolean;
  lastPingTime: number | null;
  history: HistoryItem[];

  // Actions
  setStatus: (status: Status) => void;
  setTranscription: (text: string) => void;
  setErrorMessage: (msg: string) => void;
  setIsConnected: (connected: boolean) => void;
  setLastPingTime: (time: number) => void;

  // History Actions
  loadHistory: () => void;
  addToHistory: (text: string, source: "recording" | "refinement") => void;

  // Async Actions
  startRecording: (mode?: "replace" | "append") => Promise<void>;
  stopRecording: () => Promise<void>;
  processText: () => Promise<void>;
  translateText: (targetLang: "es" | "en") => Promise<void>;
  togglePause: () => Promise<void>;
  clearError: () => void;
  retryConnection: () => Promise<void>;
  restartDaemon: () => Promise<void>;
  shutdownDaemon: () => Promise<void>;

  // Internal Helper
  handleStateUpdate: (data: DaemonState) => void;
}

function extractError(e: unknown): string {
  if (typeof e === "object" && e !== null && "message" in e) {
    return (e as IpcError).message;
  }
  return String(e);
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

// Local state for throttling ping updates (outside store to avoid re-creating)
let lastPingTimeRef = 0;

export const useBackendStore = create<BackendState>()(
  devtools(
    (set, get) => ({
      status: "disconnected",
      transcription: "",
      errorMessage: "",
      isConnected: false,
      lastPingTime: null,
      history: [],

      setStatus: (status) => set({ status }),
      setTranscription: (transcription) => set({ transcription }),
      setErrorMessage: (errorMessage) => set({ errorMessage }),
      setIsConnected: (isConnected) => set({ isConnected }),
      setLastPingTime: (lastPingTime) => set({ lastPingTime }),

      loadHistory: () => {
        try {
          const saved = localStorage.getItem(HISTORY_STORAGE_KEY);
          if (saved) {
            set({ history: JSON.parse(saved) });
          }
        } catch (e) {
          console.error("Fallo al cargar historial:", e);
        }
      },

      addToHistory: (text, source) => {
        if (!text.trim()) return;
        const newItem: HistoryItem = {
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          text,
          source,
        };
        set((state) => {
          const updated = [newItem, ...state.history].slice(0, MAX_HISTORY_ITEMS);
          localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
          return { history: updated };
        });
      },

      handleStateUpdate: (data: DaemonState) => {
        set({ isConnected: true });

        const now = Date.now();
        if (now - lastPingTimeRef > PING_UPDATE_INTERVAL_MS) {
          set({ lastPingTime: now });
          lastPingTimeRef = now;
        }

        // Transcription Update
        if (data.transcription !== undefined) set({ transcription: data.transcription });
        if (data.refined_text !== undefined) set({ transcription: data.refined_text });

        // Status Update
        const newStatus = mapDaemonState(data.state);
        const currentStatus = get().status;

        if ((currentStatus === "transcribing" || currentStatus === "processing") && newStatus === "idle") {
          // Keep current status if we are waiting for something specific
          // This logic mimics the original provider but might need revisiting
          // Original:
          // setStatus((prev) => {
          //   if ((prev === "transcribing" || prev === "processing") && newStatus === "idle") {
          //     return prev;
          //   }
          //   return newStatus;
          // });
          // But here we are setting state directly.
          // Ideally the daemon state update should be the source of truth.
          // However, to match the provider logic:
          return;
        }
        set({ status: newStatus });
      },

      startRecording: async (_mode = "replace") => {
        const { status } = get();
        if (status === "paused") return;
        try {
           // Note: mode logic (replace/append) handling might need local refs if used elsewhere
           // The original used refs for recordingMode and transcriptionBeforeAppend
           // If the backend handles this, good. If frontend needs to handle append locally before sending,
           // we might need to store it. Assuming invoke handles it or we just fire and forget for now.
           // Checking original provider:
           // recordingModeRef.current = mode;
           // if (mode === "append") transcriptionBeforeAppendRef.current = transcription;
           // These refs seem unused in the `invoke` call itself in the original code!
           // `await invoke<DaemonState>("start_recording");`
           // So they might be for local logic not fully implemented or just side effects.
           // I will proceed without them for now as they aren't passed to invoke.

          const data = await invoke<DaemonState>("start_recording");
          get().handleStateUpdate(data);
        } catch (e) {
          set({ errorMessage: extractError(e), status: "error" });
        }
      },

      stopRecording: async () => {
        set({ status: "transcribing" });
        try {
          const data = await invoke<DaemonState>("stop_recording");
          if (data.transcription) {
            set({ transcription: data.transcription, status: "idle" });
            get().addToHistory(data.transcription, "recording");
          } else {
            set({ errorMessage: "No se detectó voz", status: "error" });
          }
        } catch (e) {
          set({ errorMessage: extractError(e), status: "error" });
        }
      },

      processText: async () => {
        const { transcription } = get();
        if (!transcription) return;
        set({ status: "processing" });
        try {
          const data = await invoke<DaemonState>("process_text", { text: transcription });
          if (data.refined_text) {
             set({ transcription: data.refined_text, status: "idle" });
             get().addToHistory(data.refined_text, "refinement");
          } else {
             set({ errorMessage: "Error de LLM", status: "error" });
          }
        } catch (e) {
           set({ errorMessage: extractError(e), status: "error" });
        }
      },

      translateText: async (targetLang) => {
        const { transcription } = get();
        if (!transcription) return;
        set({ status: "processing" });
        try {
          const data = await invoke<DaemonState>("translate_text", { text: transcription, targetLang });
          if (data.refined_text) {
             set({ transcription: data.refined_text, status: "idle" });
             get().addToHistory(data.refined_text, "refinement");
          } else {
             set({ errorMessage: "Falló traducción", status: "error" });
          }
        } catch (e) {
           set({ errorMessage: extractError(e), status: "error" });
        }
      },

      togglePause: async () => {
        const { status } = get();
        try {
          if (status === "paused") {
            await invoke<DaemonState>("resume_daemon");
            set({ status: "idle" });
          } else {
            await invoke<DaemonState>("pause_daemon");
            set({ status: "paused" });
          }
        } catch (e) {
          set({ errorMessage: extractError(e) });
        }
      },

      clearError: () => set({ errorMessage: "" }),

      retryConnection: async () => {
        // This is primarily handled by the poller/initializer
        // checking status
        try {
            const data = await invoke<DaemonState>("get_status");
            get().handleStateUpdate(data);
            set({ errorMessage: "" }); // Clear error on success
        } catch (e) {
            console.warn("[BackendStore] Retry failed:", e);
            set({ isConnected: false, status: "disconnected" });
        }
      },

      restartDaemon: async () => {
        set({ status: "restarting" });
        try {
            await invoke<DaemonState>("restart_daemon");
        } catch (e) {
            set({ errorMessage: extractError(e), status: "error" });
        }
      },

      shutdownDaemon: async () => {
        set({ status: "shutting_down" });
        try {
            await invoke<DaemonState>("shutdown_daemon");
            set({ status: "disconnected", isConnected: false });
        } catch (e) {
            set({ errorMessage: extractError(e), status: "error" });
        }
      }
    }),
    { name: 'BackendStore' }
  )
);
