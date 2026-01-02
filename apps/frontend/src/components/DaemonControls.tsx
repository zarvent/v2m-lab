import React, { useState, useCallback } from "react";
import type { Status } from "../types";
import { LoaderIcon } from "../assets/Icons";

interface DaemonControlsProps {
  status: Status;
  onRestart: () => Promise<void>;
  onShutdown: () => Promise<void>;
}

/**
 * Controles para gestionar el daemon backend.
 * Proporciona botones para reiniciar y apagar con confirmación y feedback visual.
 */
export const DaemonControls: React.FC<DaemonControlsProps> = ({
  status,
  onRestart,
  onShutdown,
}) => {
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<
    "restart" | "shutdown" | null
  >(null);

  const isOperating = status === "restarting" || status === "shutting_down";
  const isDisconnected = status === "disconnected";

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
  React.useEffect(() => {
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
    <>
      <div className="daemon-controls">
        {/* Botón Reiniciar */}
        <button
          onClick={handleRestartClick}
          disabled={isOperating || isDisconnected}
          className={`btn-daemon btn-restart ${
            status === "restarting" ? "btn-loading" : ""
          }`}
          title="Reiniciar el daemon"
          aria-label="Reiniciar daemon"
          aria-busy={status === "restarting"}
        >
          {status === "restarting" ? (
            <>
              <span className="spin-anim">
                <LoaderIcon />
              </span>
              Reiniciando...
            </>
          ) : (
            <>
              <RestartIcon />
              Reiniciar
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
          title="Apagar el daemon"
          aria-label="Apagar daemon"
          aria-busy={status === "shutting_down"}
        >
          {status === "shutting_down" ? (
            <>
              <span className="spin-anim">
                <LoaderIcon />
              </span>
              Apagando...
            </>
          ) : (
            <>
              <PowerIcon />
              Apagar
            </>
          )}
        </button>
      </div>

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
                ? "¿Apagar el daemon?"
                : "¿Reiniciar el daemon?"}
            </h3>
            <p className="confirm-modal-description">
              {pendingAction === "shutdown"
                ? "El servicio se detendrá completamente. Necesitarás iniciarlo manualmente para volver a usarlo."
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
    </>
  );
};

DaemonControls.displayName = "DaemonControls";

// --- ICONOS INLINE ---

const RestartIcon = () => (
  <svg
    width="16"
    height="16"
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
    width="16"
    height="16"
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
