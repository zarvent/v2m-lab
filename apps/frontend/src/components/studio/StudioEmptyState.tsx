import React from "react";
import { MicIcon } from "../../assets/Icons";
import "../../styles/components/buttons.css";

export interface StudioEmptyStateProps {
  isIdle: boolean;
  recordShortcut: string;
  onStartRecording: (mode?: "replace" | "append") => void;
}

export const StudioEmptyState: React.FC<StudioEmptyStateProps> = React.memo(
  ({ isIdle, recordShortcut, onStartRecording }) => (
    <div className="flex-1 flex flex-col items-center justify-center text-center text-secondary animate-[fade-in-up_0.5s_ease-out]"> {/* .studio-empty-state */}
      <div className="text-[3rem] text-strong mb-lg animate-[float_6s_ease-in-out_infinite]"> {/* .empty-state-icon */}
        <MicIcon />
      </div>
      <h2 className="text-xl text-primary mb-sm">Captura tus ideas</h2> {/* .empty-state-title */}
      <p className="mb-lg opacity-80"> {/* .empty-state-description */}
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
      <div className="flex items-center gap-[8px] text-sm text-muted"> {/* .studio-empty-shortcut */}
        <span className="shortcut-label">Presiona</span>
        <kbd className="bg-surface border border-subtle rounded px-[6px] py-[2px] font-mono text-primary shadow-[0_1px_0_var(--border-subtle)]"> {/* kbd */}
          {recordShortcut}
        </kbd>
        <span className="shortcut-label">para capturar</span>
      </div>
    </div>
  )
);
StudioEmptyState.displayName = "StudioEmptyState";
