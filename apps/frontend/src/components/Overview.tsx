import React, { useCallback, useState, useEffect } from "react";
import { LoaderIcon, PlayIcon } from "../assets/Icons";
import { useTelemetryStore } from "../stores/telemetryStore";
import { useBackendStore } from "../stores/backendStore";
import "../styles/components/overview.css";

/**
 * Overview - Panel de control del Demonio.
 *
 * Provee controles para gestionar el proceso de fondo (Daemon):
 * - Iniciar/Reanudar/Pausar
 * - Reiniciar
 * - Apagar
 *
 * También visualiza telemetría del sistema (CPU, RAM, GPU) en tiempo real.
 */
export const Overview: React.FC = React.memo(() => {
    const { telemetry, cpuHistory, ramHistory } = useTelemetryStore();
    const status = useBackendStore((state) => state.status);
    const isConnected = useBackendStore((state) => state.isConnected);
    const lastPingTime = useBackendStore((state) => state.lastPingTime);
    const onRestart = useBackendStore((state) => state.restartDaemon);
    const onShutdown = useBackendStore((state) => state.shutdownDaemon);
    const onResume = useBackendStore((state) => state.togglePause);

    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [pendingAction, setPendingAction] = useState<
      "restart" | "shutdown" | null
    >(null);

    const isOperating = status === "restarting" || status === "shutting_down";
    const isDisconnected = status === "disconnected";
    const isPaused = status === "paused";
    const isRunning =
      status === "idle" ||
      status === "recording" ||
      status === "transcribing" ||
      status === "processing";

    // Formatear última hora de ping
    const lastPingFormatted = lastPingTime
      ? new Date(lastPingTime).toLocaleTimeString()
      : "Nunca";

    const handleResumeClick = useCallback(async () => {
      await onResume();
    }, [onResume]);

    const handleRestartClick = useCallback(() => {
      setPendingAction("restart");
      setShowConfirmModal(true);
    }, []);

    const handleShutdownClick = useCallback(() => {
      setPendingAction("shutdown");
      setShowConfirmModal(true);
    }, []);

    const handleConfirm = useCallback(async () => {
      setShowConfirmModal(false);
      if (pendingAction === "restart") {
        await onRestart();
      } else if (pendingAction === "shutdown") {
        await onShutdown();
      }
      setPendingAction(null);
    }, [pendingAction, onRestart, onShutdown]);

    const handleCancel = useCallback(() => {
      setShowConfirmModal(false);
      setPendingAction(null);
    }, []);

    // Cerrar modal con Escape
    useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape" && showConfirmModal) {
          handleCancel();
        }
      };
      if (showConfirmModal) {
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
      }
    }, [showConfirmModal, handleCancel]);

    return (
      <div className="overview-container">
        {/* Tarjeta de Estado de Conexión */}
        <div className="overview-card">
          <h2 className="overview-card-title">Estado del Demonio</h2>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Conexión</span>
              <span
                className={`status-badge ${
                  isConnected ? "connected" : "disconnected"
                }`}
              >
                <span className="status-dot" />
                {isConnected ? "Conectado" : "Desconectado"}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Estado</span>
              <span className={`status-badge state-${status}`}>{status}</span>
            </div>
            <div className="status-item">
              <span className="status-label">Último Ping</span>
              <span className="status-value mono">{lastPingFormatted}</span>
            </div>
          </div>
        </div>

        {/* Tarjeta de Controles del Demonio */}
        <div className="overview-card">
          <h2 className="overview-card-title">Controles</h2>
          <div className="daemon-controls-grid">
            {/* Botón Iniciar/Reanudar/Pausar */}
            <button
              onClick={handleResumeClick}
              disabled={isOperating}
              className={`btn-daemon btn-start ${
                isConnected && !isPaused ? "btn-pause" : ""
              }`}
              title={
                isPaused
                  ? "Reanudar demonio"
                  : isRunning
                  ? "Pausar demonio"
                  : "Iniciar demonio"
              }
              aria-label={
                isPaused
                  ? "Reanudar demonio"
                  : isRunning
                  ? "Pausar demonio"
                  : "Iniciar demonio"
              }
            >
              {isConnected && !isPaused ? (
                // Icono de Pausa
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </svg>
              ) : (
                <PlayIcon />
              )}
              <span>
                {isPaused ? "Reanudar" : isRunning ? "Pausar" : "Iniciar"}
              </span>
            </button>

            {/* Botón Reiniciar */}
            <button
              onClick={handleRestartClick}
              disabled={isOperating || isDisconnected}
              className={`btn-daemon btn-restart ${
                status === "restarting" ? "btn-loading" : ""
              }`}
              title="Reiniciar demonio"
              aria-label="Reiniciar demonio"
              aria-busy={status === "restarting"}
            >
              {status === "restarting" ? (
                <>
                  <span className="spin-anim">
                    <LoaderIcon />
                  </span>
                  <span>Reiniciando...</span>
                </>
              ) : (
                <>
                  <RestartIcon />
                  <span>Reiniciar</span>
                </>
              )}
            </button>

            {/* Botón Apagar */}
            <button
              onClick={handleShutdownClick}
              disabled={isOperating || isDisconnected}
              className={`btn-daemon btn-shutdown ${
                status === "shutting_down" ? "btn-loading" : ""
              }`}
              title="Apagar demonio"
              aria-label="Apagar demonio"
              aria-busy={status === "shutting_down"}
            >
              {status === "shutting_down" ? (
                <>
                  <span className="spin-anim">
                    <LoaderIcon />
                  </span>
                  <span>Apagando...</span>
                </>
              ) : (
                <>
                  <PowerIcon />
                  <span>Apagar</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Tarjeta de Telemetría del Sistema */}
        {telemetry && (
          <div className="overview-card">
            <h2 className="overview-card-title">Recursos del Sistema</h2>
            <div className="telemetry-grid">
              {/* CPU */}
              <div className="telemetry-item">
                <div className="telemetry-header">
                  <span className="telemetry-label">CPU</span>
                  <span className="telemetry-value mono">
                    {telemetry.cpu.percent.toFixed(1)}%
                  </span>
                </div>
                <div className="telemetry-bar">
                  <div
                    className="telemetry-fill cpu"
                    style={{ width: `${telemetry.cpu.percent}%` }}
                  />
                </div>
                {cpuHistory.length > 0 && (
                  <Sparkline data={cpuHistory} color="var(--color-cpu)" />
                )}
              </div>

              {/* RAM */}
              <div className="telemetry-item">
                <div className="telemetry-header">
                  <span className="telemetry-label">RAM</span>
                  <span className="telemetry-value mono">
                    {telemetry.ram.used_gb.toFixed(1)} GB (
                    {telemetry.ram.percent.toFixed(1)}%)
                  </span>
                </div>
                <div className="telemetry-bar">
                  <div
                    className="telemetry-fill ram"
                    style={{ width: `${telemetry.ram.percent}%` }}
                  />
                </div>
                {ramHistory.length > 0 && (
                  <Sparkline data={ramHistory} color="var(--color-ram)" />
                )}
              </div>

              {/* GPU (si disponible) */}
              {telemetry.gpu && (
                <div className="telemetry-item">
                  <div className="telemetry-header">
                    <span className="telemetry-label">
                      GPU ({telemetry.gpu.name || "GPU"})
                    </span>
                    <span className="telemetry-value mono">
                      {telemetry.gpu.vram_used_mb.toFixed(0)} /{" "}
                      {telemetry.gpu.vram_total_mb.toFixed(0)} MB |{" "}
                      {telemetry.gpu.temp_c}°C
                    </span>
                  </div>
                  <div className="telemetry-bar">
                    <div
                      className="telemetry-fill gpu"
                      style={{
                        width: `${Math.min(
                          telemetry.gpu.vram_total_mb > 0
                            ? (telemetry.gpu.vram_used_mb /
                                telemetry.gpu.vram_total_mb) *
                                100
                            : 0,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Modal de Confirmación */}
        {showConfirmModal && (
          <div
            className="modal-overlay"
            onClick={(e) => e.target === e.currentTarget && handleCancel()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirm-title"
          >
            <div className="confirm-modal">
              <div className="confirm-modal-icon">
                {pendingAction === "shutdown" ? <PowerIcon /> : <RestartIcon />}
              </div>
              <h3 id="confirm-title" className="confirm-modal-title">
                {pendingAction === "shutdown"
                  ? "¿Apagar demonio?"
                  : "¿Reiniciar demonio?"}
              </h3>
              <p className="confirm-modal-description">
                {pendingAction === "shutdown"
                  ? "El servicio se detendrá completamente. Deberás iniciarlo manualmente para volver a usarlo."
                  : "El servicio se reiniciará. Esto puede tomar unos segundos."}
              </p>
              <div className="confirm-modal-actions">
                <button
                  onClick={handleCancel}
                  className="btn-secondary"
                  autoFocus
                >
                  Cancelar
                </button>
                <button
                  onClick={handleConfirm}
                  className={
                    pendingAction === "shutdown" ? "btn-danger" : "btn-warning"
                  }
                >
                  {pendingAction === "shutdown" ? "Apagar" : "Reiniciar"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  });


Overview.displayName = "Overview";

// --- SPARKLINE COMPONENT ---

interface SparklineProps {
  data: number[];
  color: string;
  height?: number;
}

const Sparkline: React.FC<SparklineProps> = React.memo(
  ({ data, color, height = 24 }) => {
    if (data.length < 2) return null;

    const width = 100;
    const max = Math.max(...data, 100);
    const min = Math.min(...data, 0);
    const range = max - min || 1;

    const points = data
      .map((val, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((val - min) / range) * height;
        return `${x},${y}`;
      })
      .join(" ");

    return (
      <svg
        className="sparkline"
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        aria-hidden="true"
      >
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          points={points}
        />
      </svg>
    );
  }
);

Sparkline.displayName = "Sparkline";

// --- INLINE ICONS ---

const RestartIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
    <path d="M3 3v5h5" />
    <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
    <path d="M16 16h5v5" />
  </svg>
);

const PowerIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M18.36 6.64a9 9 0 1 1-12.73 0" />
    <line x1="12" y1="2" x2="12" y2="12" />
  </svg>
);
