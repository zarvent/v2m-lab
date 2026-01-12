import React from "react";
import { MicIcon } from "../../assets/Icons";

export interface StudioEmptyStateProps {
  isIdle: boolean;
  recordShortcut: string;
  onStartRecording: (mode?: "replace" | "append") => void;
}

export const StudioEmptyState: React.FC<StudioEmptyStateProps> = React.memo(
  ({ isIdle, recordShortcut, onStartRecording }) => (
    <div className="studio-empty-state">
      <div className="empty-state-icon">
        <MicIcon />
      </div>
      <h2 className="empty-state-title">Captura tus ideas</h2>
      <p className="empty-state-description">
        Solo habla. Tu voz se convierte en texto, al instante.
        <br />
        Local, privado y rápido.
      </p>
      {isIdle && (
        <button
          className="studio-empty-cta"
          onClick={() => onStartRecording("replace")}
          aria-label="Iniciar grabación"
        >
          <MicIcon />
          <span>Iniciar Captura</span>
        </button>
      )}
      <div className="studio-empty-shortcut">
        <span className="shortcut-label">Presiona</span>
        <kbd>{recordShortcut}</kbd>
        <span className="shortcut-label">para capturar</span>
      </div>
    </div>
  )
);
StudioEmptyState.displayName = "StudioEmptyState";
