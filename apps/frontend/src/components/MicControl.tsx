import React from "react";
import { MicIcon, StopIcon, LoaderIcon } from "../assets/Icons";
import type { Status } from "../types";

interface MicControlProps {
  status: Status;
  onToggleRecord: () => void;
}

/**
 * Botón flotante principal para control de grabación.
 * Cambia de apariencia (rojo/normal) y de icono (mic/stop) según el estado.
 */
export const MicControl = React.memo(
  ({ status, onToggleRecord }: MicControlProps) => {
    const isRecording = status === "recording";
    const isProcessing = status === "transcribing" || status === "processing";

    // Deshabilitar botón si el sistema está ocupado o desconectado
    const isDisabled =
      isProcessing || status === "disconnected" || status === "paused";

    const getTooltip = () => {
      if (status === "disconnected")
        return "Sistema desconectado - Verifique el daemon";
      if (status === "transcribing") return "Transcribiendo audio...";
      if (status === "processing") return "Procesando texto...";
      if (status === "paused") return "Sistema pausado - Reanudar para grabar";
      if (isRecording) return "Click para detener (Ctrl+Espacio)";
      return "Click para grabar (Ctrl+Espacio)";
    };

    return (
      <div className="mic-float">
        <button
          className={`mic-btn ${isRecording ? "recording" : ""} ${
            isProcessing ? "processing" : ""
          }`}
          onClick={onToggleRecord}
          disabled={isDisabled}
          aria-label={
            isProcessing
              ? "Procesando..."
              : isRecording
              ? "Detener grabación"
              : "Iniciar grabación"
          }
          title={getTooltip()}
        >
          {isProcessing ? (
            <div className="spin-anim">
              <LoaderIcon />
            </div>
          ) : isRecording ? (
            <StopIcon />
          ) : (
            <MicIcon />
          )}
        </button>
      </div>
    );
  }
);
