import React, { useState } from "react";
import { SaveIcon, CheckIcon } from "../../assets/Icons";
import "../../styles/components/modals.css";
import "../../styles/components/buttons.css";

export interface SaveDialogProps {
  initialTitle: string;
  content: string;
  wordCount: number;
  currentLanguage: "es" | "en";
  onConfirm: (title: string, text: string, lang: "es" | "en") => void;
  onCancel: () => void;
}

export const SaveDialog: React.FC<SaveDialogProps> = React.memo(
  ({
    initialTitle,
    content,
    wordCount,
    currentLanguage,
    onConfirm,
    onCancel,
  }) => {
    const [title, setTitle] = useState(initialTitle);
    const [success, setSuccess] = useState(false);

    const handleConfirm = () => {
      // Show success state locally first
      setSuccess(true);

      // Delay closing to show the animation
      setTimeout(() => {
        onConfirm(title || initialTitle, content, currentLanguage);
      }, 1000);
    };

    return (
      <div
        className="studio-modal-overlay"
        onClick={(e) => e.target === e.currentTarget && onCancel()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="save-dialog-title"
      >
        <div className={`studio-modal ${success ? "success" : ""}`}>
          {success ? (
            <div className="save-success-state">
              <span className="success-icon">
                <CheckIcon />
              </span>
              <span>¡Guardado!</span>
            </div>
          ) : (
            <>
              <header className="studio-modal-header">
                <h2 id="save-dialog-title" className="studio-modal-title">
                  Guardar en Librería
                </h2>
              </header>

              <div className="studio-modal-body">
                <div className="form-field">
                  <label htmlFor="snippet-title-input">Título</label>
                  <input
                    id="snippet-title-input"
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Ingresa un título..."
                    autoFocus
                    maxLength={100}
                  />
                </div>

                <div className="snippet-preview-box">
                  <p className="snippet-preview-text">
                    {content.slice(0, 200)}
                    {content.length > 200 ? "..." : ""}
                  </p>
                  <div className="snippet-preview-meta">
                    <span>{wordCount} palabras</span>
                    <span>•</span>
                    <span>{content.length} caracteres</span>
                  </div>
                </div>
              </div>

              <footer className="studio-modal-actions">
                <button onClick={onCancel} className="studio-btn-cancel">
                  Cancelar
                </button>
                <button
                  onClick={handleConfirm}
                  className="studio-btn-confirm"
                >
                  <SaveIcon />
                  <span>Guardar Fragmento</span>
                </button>
              </footer>
            </>
          )}
        </div>
      </div>
    );
  }
);

SaveDialog.displayName = "SaveDialog";
