import React, { useRef, useState, useEffect } from "react";
import { cn } from "../../utils/classnames";
import "../../styles/components/studio-header.css";
import {
  CopyIcon,
  CheckIcon,
  ExportIcon,
  SaveIcon,
  EditIcon,
  FileTextIcon,
  FileCodeIcon,
  FileJsonIcon,
} from "../../assets/Icons";

export interface StudioHeaderProps {
  noteTitle: string;
  isEditingTitle: boolean;
  hasContent: boolean;
  isBusy: boolean;
  currentLanguage: "es" | "en";
  copyState: "idle" | "copied" | "error";
  onTitleChange: (title: string) => void;
  onTitleSubmit: () => void;
  onEditTitle: () => void;
  onCopy: () => void;
  onTranslate: (lang: "es" | "en") => void;
  onExport: (format: "txt" | "md" | "json") => void;
  onSaveToLibrary: () => void;
}

const EXPORT_FORMATS = {
  txt: {
    label: "Texto Plano",
    Icon: FileTextIcon,
    description: "Archivo de texto simple",
  },
  md: {
    label: "Markdown",
    Icon: FileCodeIcon,
    description: "Documento formateado",
  },
  json: {
    label: "JSON",
    Icon: FileJsonIcon,
    description: "Datos estructurados",
  },
};

export const StudioHeader: React.FC<StudioHeaderProps> = React.memo(
  ({
    noteTitle,
    isEditingTitle,
    hasContent,
    isBusy,
    currentLanguage,
    copyState,
    onTitleChange,
    onTitleSubmit,
    onEditTitle,
    onCopy,
    onTranslate,
    onExport,
    onSaveToLibrary,
  }) => {
    const titleInputRef = useRef<HTMLInputElement>(null);
    const [showExportMenu, setShowExportMenu] = useState(false);
    const exportMenuRef = useRef<HTMLDivElement>(null);

    // Focus input when editing starts
    useEffect(() => {
      if (isEditingTitle && titleInputRef.current) {
        titleInputRef.current.focus();
        titleInputRef.current.select();
      }
    }, [isEditingTitle]);

    // Close export menu on outside click
    useEffect(() => {
      if (!showExportMenu) return;
      const handleClickOutside = (e: MouseEvent) => {
        if (
          exportMenuRef.current &&
          !exportMenuRef.current.contains(e.target as Node)
        ) {
          setShowExportMenu(false);
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }, [showExportMenu]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter") onTitleSubmit();
    };

    return (
      <header className="studio-header">
        <div
          className="studio-title-section"
          style={{ minWidth: 0, flex: 1, marginRight: "var(--space-md)" }}
        >
          {isEditingTitle ? (
            <input
              ref={titleInputRef}
              type="text"
              className="studio-title-input"
              value={noteTitle}
              onChange={(e) => onTitleChange(e.target.value)}
              onBlur={onTitleSubmit}
              onKeyDown={handleKeyDown}
              placeholder="Nombra tu idea..."
              aria-label="Título de nota"
              maxLength={100}
              style={{ width: "100%" }}
            />
          ) : (
            <button
              className="studio-title-display"
              onClick={onEditTitle}
              aria-label="Clic para editar título"
              style={{
                maxWidth: "100%",
                display: "flex",
                alignItems: "center",
              }}
            >
              <h1
                className="studio-title-text"
                style={{
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {noteTitle}
              </h1>
              <span className="studio-title-edit-icon" style={{ flexShrink: 0 }}>
                <EditIcon />
              </span>
            </button>
          )}
          <span className="studio-title-hint">
            <span className="hint-dot" />
            Borrador
          </span>
        </div>

        {/* --- HUB DE ACCIONES --- */}
        <div className="studio-header-actions">
          {/* Botón Copiar */}
          <button
            className={cn("studio-btn studio-btn-copy", copyState)}
            onClick={onCopy}
            disabled={!hasContent || isBusy}
            aria-label={
              copyState === "copied" ? "¡Copiado!" : "Copiar al portapapeles"
            }
          >
            {copyState === "copied" ? <CheckIcon /> : <CopyIcon />}
            <span>{copyState === "copied" ? "¡Copiado!" : "Copiar"}</span>
          </button>
          {/* Switch de Traducción Magnético */}
          <div
            className="semantic-toggle-group"
            role="group"
            aria-label="Idioma de Traducción"
          >
            <button
              className={cn(
                "semantic-toggle-option",
                currentLanguage === "en" && "active"
              )}
              onClick={() => onTranslate("en")}
              disabled={isBusy}
              title="Traducir a Inglés"
            >
              <span className="toggle-label">EN</span>
            </button>
            <button
              className={cn(
                "semantic-toggle-option",
                currentLanguage === "es" && "active"
              )}
              onClick={() => onTranslate("es")}
              disabled={isBusy}
              title="Traducir a Español"
            >
              <span className="toggle-label">ES</span>
            </button>
            {/* Indicador Activo (Solo visual) */}
            <div
              className={cn("toggle-indicator", currentLanguage)}
              aria-hidden="true"
            />
          </div>

          <div className="studio-action-divider" />

          {/* Acción Primaria: Exportar */}
          <div className="studio-export-wrapper" ref={exportMenuRef}>
            <button
              className="studio-btn-primary-ghost"
              onClick={() => onExport("txt")}
              disabled={!hasContent || isBusy}
              title="Exportar a Archivo de Texto"
            >
              <ExportIcon />
              <span>Exportar</span>
            </button>

            {/* Gatillo Dropdown */}
            <button
              className="studio-btn-icon-ghost"
              onClick={() => setShowExportMenu(!showExportMenu)}
              disabled={!hasContent || isBusy}
              aria-label="Más opciones de exportación"
              aria-expanded={showExportMenu}
            >
              <span className="chevron-down">▼</span>
            </button>

            {showExportMenu && (
              <div className="spatial-dropdown-menu" role="menu">
                <div className="dropdown-menu-header">Elegir Formato</div>
                {(
                  Object.entries(EXPORT_FORMATS) as [
                    "txt" | "md" | "json",
                    typeof EXPORT_FORMATS["txt"]
                  ][]
                ).map(([format, { label, Icon, description }]) => (
                  <button
                    key={format}
                    className="spatial-dropdown-item"
                    onClick={() => {
                      onExport(format);
                      setShowExportMenu(false);
                    }}
                    role="menuitem"
                  >
                    <span className="item-icon-wrapper">
                      <Icon />
                    </span>
                    <div className="item-content">
                      <span className="item-label">{label}</span>
                      <span className="item-desc">{description}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Guardar en Librería (Secundario) */}
          <button
            className="studio-btn-icon-ghost"
            onClick={onSaveToLibrary}
            disabled={!hasContent || isBusy}
            title="Guardar en Librería"
          >
            <SaveIcon />
          </button>
        </div>
      </header>
    );
  }
);

StudioHeader.displayName = "StudioHeader";
