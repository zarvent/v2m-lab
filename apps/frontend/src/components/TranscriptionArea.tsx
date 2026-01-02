import React, { useState, useEffect } from "react";
import {
  CopyIcon,
  SparklesIcon,
  PauseIcon,
  PlayIcon,
  TrashIcon,
  LoaderIcon,
} from "../assets/Icons";
import type { Status } from "../types";

interface TranscriptionAreaProps {
  transcription: string;
  status: Status;
  lastCopied: boolean;
  onTranscriptionChange: (text: string) => void;
  onCopy: () => void;
  onRefine: () => void;
  onTogglePause: () => void;
}

/**
 * Panel principal de visualización y edición de la transcripción.
 * Contiene el área de texto y la barra de acciones (copiar, refinar, pausar, limpiar).
 */
export const TranscriptionArea = React.memo(
  ({
    transcription,
    status,
    lastCopied,
    onTranscriptionChange,
    onCopy,
    onRefine,
    onTogglePause,
  }: TranscriptionAreaProps) => {
    // Calcular conteo de caracteres
    const charCount = transcription.length;
    const isProcessing = status === "processing";
    const [confirmClear, setConfirmClear] = useState(false);

    // Resetear confirmación después de 3 segundos
    useEffect(() => {
      if (confirmClear) {
        const timer = setTimeout(() => setConfirmClear(false), 3000);
        return () => clearTimeout(timer);
      }
    }, [confirmClear]);

    const handleClearClick = () => {
      if (confirmClear) {
        onTranscriptionChange("");
        setConfirmClear(false);
      } else {
        setConfirmClear(true);
      }
    };

    return (
      <div className="transcription-panel">
        {/* Barra de herramientas superior */}
        <div className="action-bar" role="toolbar" aria-label="Editor controls">
          <button
            className="btn-secondary"
            onClick={onCopy}
            disabled={!transcription}
            aria-label="Copiar texto al portapapeles"
          >
            <CopyIcon /> {lastCopied ? "Copiado" : "Copiar"}
          </button>
          <button
            className="btn-secondary"
            onClick={onRefine}
            // Deshabilitar si no hay texto o si el sistema no está inactivo (permitiendo 'processing' para mostrar estado pero no click)
            // Corrección: Debe estar deshabilitado SIEMPRE que no sea 'idle'.
            disabled={!transcription || status !== "idle"}
            title="Refinar gramática y estilo con IA"
            aria-label={
              isProcessing
                ? "Refinando texto..."
                : "Refinar con Inteligencia Artificial"
            }
          >
            {isProcessing ? (
              <div className="spin-anim btn-loader">
                <LoaderIcon />
              </div>
            ) : (
              <SparklesIcon />
            )}
            {isProcessing ? "Mejorando..." : "Mejorar con IA"}
          </button>
          <button
            className="btn-secondary"
            onClick={handleClearClick}
            disabled={!transcription || status === "paused"}
            title={
              confirmClear
                ? "Click otra vez para confirmar"
                : "Borrar todo el texto"
            }
            aria-label={confirmClear ? "Confirmar borrado" : "Borrar contenido"}
            style={
              confirmClear
                ? { borderColor: "var(--error)", color: "var(--error)" }
                : undefined
            }
          >
            <TrashIcon /> {confirmClear ? "¿Seguro?" : "Limpiar"}
          </button>
          <button
            className="btn-secondary"
            onClick={onTogglePause}
            disabled={status === "disconnected"}
            aria-pressed={status === "paused"}
            aria-label={
              status === "paused" ? "Reanudar sistema" : "Pausar sistema"
            }
          >
            {status === "paused" ? <PlayIcon /> : <PauseIcon />}
            {status === "paused" ? "Reanudar" : "Pausar Sistema"}
          </button>
        </div>

        {/* Área de texto editable */}
        <div className="editor-container">
          <textarea
            className="editor"
            value={transcription}
            onChange={(e) => onTranscriptionChange(e.target.value)}
            placeholder={
              status === "paused"
                ? "Sistema pausado..."
                : "Empieza a hablar para transcribir..."
            }
            spellCheck={false}
            disabled={status === "paused"}
            aria-label="Texto transcrito"
          />

          {/* Contador de caracteres (Micro-UX) */}
          <div className="char-count" aria-live="polite">
            {charCount > 0 &&
              `${charCount} ${charCount === 1 ? "carácter" : "caracteres"}`}
          </div>
        </div>
      </div>
    );
  }
);
