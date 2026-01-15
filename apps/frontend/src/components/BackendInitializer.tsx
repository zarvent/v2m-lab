import React, { useEffect, useRef } from 'react';
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import type { DaemonState } from "../types/ipc";
import { useBackendStore } from '../stores/backendStore';
import { useTelemetryStore } from '../stores/telemetryStore';
import { STATUS_POLL_INTERVAL_MS } from "../constants";

export const BackendInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const handleStateUpdate = useBackendStore((state) => state.handleStateUpdate);
  const loadHistory = useBackendStore((state) => state.loadHistory);
  const setIsConnected = useBackendStore((state) => state.setIsConnected);
  const setStatus = useBackendStore((state) => state.setStatus);
  const updateTelemetry = useTelemetryStore((state) => state.updateTelemetry);
  
  const lastEventTimeRef = useRef<number>(Date.now());

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    let unlisten: (() => void) | null = null;

    const handleUpdate = (data: DaemonState) => {
      lastEventTimeRef.current = Date.now();
      handleStateUpdate(data);
      if (data.telemetry) {
        updateTelemetry(data.telemetry);
      }
    };

    const pollStatus = async () => {
      try {
        const data = await invoke<DaemonState>("get_status");
        handleUpdate(data);
      } catch (e) {
        console.warn("[BackendInitializer] Poll failed:", e);
        setIsConnected(false);
        setStatus("disconnected");
      }
    };

    // Initial Poll
    pollStatus();

    // Listen to events
    listen<DaemonState>("v2m://state-update", (event) => handleUpdate(event.payload))
      .then((fn) => { unlisten = fn; });

    // Fallback Polling
    const fallbackInterval = setInterval(() => {
      if (Date.now() - lastEventTimeRef.current > STATUS_POLL_INTERVAL_MS * 4) {
        pollStatus();
      }
    }, STATUS_POLL_INTERVAL_MS);

    return () => {
      unlisten?.();
      clearInterval(fallbackInterval);
    };
  }, [handleStateUpdate, updateTelemetry, setIsConnected, setStatus]);

  return <>{children}</>;
};
