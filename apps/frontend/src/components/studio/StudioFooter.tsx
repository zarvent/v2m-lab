import React from "react";
import { MicIcon, PlusIcon } from "../../assets/Icons";
import "../../styles/components/buttons.css";

export interface StudioFooterProps {
  wordCount: number;
  charCount: number;
  lineCount: number;
  isRecording: boolean;
  isBusy: boolean;
  isIdle: boolean;
  isError: boolean;
  hasContent: boolean;
  recordShortcut: string;
  onStartRecording: (mode: "replace" | "append") => void;
  onStopRecording: () => void;
  onNewNote: () => void;
}

export const StudioFooter: React.FC<StudioFooterProps> = React.memo(
  ({
    wordCount,
    charCount,
    lineCount,
    isRecording,
    isBusy,
    isIdle,
    isError,
    hasContent,
    recordShortcut,
    onStartRecording,
    onStopRecording,
    onNewNote,
  }) => {
    return (
      <footer className="studio-footer">
        {/* Izquierda: Estadísticas */}
        <div className="studio-stats">
          <span className="studio-stat">
            <strong>{wordCount.toLocaleString()}</strong>
            <span className="stat-label">palabras</span>
          </span>
          <span className="studio-stat-divider" />
          <span className="studio-stat">
            <strong>{charCount.toLocaleString()}</strong>
            <span className="stat-label">caracteres</span>
          </span>
          <span className="studio-stat-divider" />
          <span className="studio-stat">
            <strong>{lineCount}</strong>
            <span className="stat-label">líneas</span>
          </span>
        </div>

        {/* Centro: Pista de atajo de teclado */}
        <div className="studio-shortcut-hint">
          <kbd>{recordShortcut}</kbd>
          <span>para {isRecording ? "parar" : "empezar"}</span>
        </div>

        {/* Derecha: Acción Primaria */}
        <div className="studio-primary-action">
          {(isIdle || isError) && (
            <>
              {/* Botón secundario para NUEVA nota cuando ya hay contenido */}
              {hasContent && (
                <button
                  className="studio-btn studio-btn-secondary-action"
                  onClick={onNewNote}
                  aria-label="Nueva nota y grabar"
                  title="Crear nueva nota y empezar a grabar"
                >
                  <PlusIcon />
                  <span>Nueva</span>
                </button>
              )}

              {/* Botón PRINCIPAL: Grabar o Continuar (Append) */}
              <button
                className="studio-record-btn"
                onClick={() =>
                  onStartRecording(hasContent ? "append" : "replace")
                }
                aria-label={
                  hasContent
                    ? "Continuar actual (Append)"
                    : "Iniciar grabación"
                }
                title={
                  hasContent
                    ? "Continuar grabando en esta nota"
                    : "Iniciar grabación"
                }
              >
                <span className="record-btn-pulse" />
                <span className="record-btn-icon">
                  <MicIcon />
                </span>
                <span className="record-btn-text">
                  {hasContent ? "Continuar" : "Grabar"}
                </span>
              </button>
            </>
          )}

          {isRecording && (
            <button
              className="studio-stop-btn"
              onClick={onStopRecording}
              aria-label="Detener grabación"
            >
              <span className="stop-btn-icon" />
              <span className="stop-btn-text">Parar</span>
            </button>
          )}

          {isBusy && (
            <button
              className="studio-busy-btn"
              disabled
              aria-label="Procesando"
            >
              <span className="processing-spinner" />
              <span>Procesando</span>
            </button>
          )}
        </div>
      </footer>
    );
  }
);

StudioFooter.displayName = "StudioFooter";
