import React, {
  useCallback,
  useState,
  useRef,
  useEffect,
  useMemo,
} from "react";
import type { Status } from "../types";
import { COPY_FEEDBACK_DURATION_MS } from "../constants";
import { countWords } from "../utils";
import {
  SaveIcon,
  ExportIcon,
  MicIcon,
  CopyIcon,
  CheckIcon,
  EditIcon,
  FileTextIcon,
  FileCodeIcon,
  FileJsonIcon,
  PlusIcon,
} from "../assets/Icons";
import { TabBar } from "./TabBar";
import { useNoteTabs } from "../hooks/useNoteTabs";

// ============================================
// TYPES
// ============================================

/** Ítem de fragmento almacenado en localStorage */
export interface SnippetItem {
  id: string;
  timestamp: number;
  text: string;
  title: string;
  language?: "es" | "en";
}

/** Opciones de formato de exportación */
type ExportFormat = "txt" | "md" | "json";

/** Estado del botón de copiar */
type CopyState = "idle" | "copied" | "error";

interface StudioProps {
  status: Status;
  transcription: string;
  timerFormatted: string;
  errorMessage: string;
  onStartRecording: (mode?: "replace" | "append") => void;
  onStopRecording: () => void;
  onClearError: () => void;
  /** Callback para guardar fragmento en la librería */
  onSaveSnippet?: (snippet: Omit<SnippetItem, "id" | "timestamp">) => void;
  /** Callback para actualizar transcripción en el estado padre */
  onTranscriptionChange?: (text: string) => void;
  /** Callback para traducir texto vía backend */
  onTranslate?: (targetLang: "es" | "en") => Promise<void>;
}

// ============================================
// CONSTANTS
// ============================================

/** Información de extensión de archivo para formatos de exportación */
const EXPORT_FORMATS: Record<
  ExportFormat,
  { label: string; Icon: React.FC; mimeType: string; description: string }
> = {
  txt: {
    label: "Texto Plano",
    Icon: FileTextIcon,
    mimeType: "text/plain",
    description: "Archivo de texto simple",
  },
  md: {
    label: "Markdown",
    Icon: FileCodeIcon,
    mimeType: "text/markdown",
    description: "Documento formateado",
  },
  json: {
    label: "JSON",
    Icon: FileJsonIcon,
    mimeType: "application/json",
    description: "Datos estructurados",
  },
};

/** Atajo de teclado para alternar grabación */
const RECORD_SHORTCUT = navigator.platform.includes("Mac")
  ? "⌘ Espacio"
  : "Ctrl+Espacio";

// ============================================
// HELPERS
// ============================================

/** Generar título predeterminado basado en fecha/hora actual */
const generateDefaultTitle = (): string => {
  const now = new Date();
  return now.toLocaleDateString("es-ES", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

/** Sanitizar título para nombre de archivo */
const sanitizeFilename = (title: string): string =>
  title.replace(/[/\\?%*:|"<>]/g, "-").trim() || "sin_titulo";

// ============================================
// SUB-COMPONENTS
// ============================================

/** Estado vacío cuando no hay contenido */
const EmptyState: React.FC<{
  isIdle: boolean;
  onStartRecording: (mode?: "replace" | "append") => void;
}> = React.memo(({ isIdle, onStartRecording }) => (
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
      <kbd>{RECORD_SHORTCUT}</kbd>
      <span className="shortcut-label">para capturar</span>
    </div>
  </div>
));
EmptyState.displayName = "EmptyState";

/** Animación de forma de onda de grabación */
const RecordingWaveform: React.FC = React.memo(() => (
  <div className="recording-waveform" aria-hidden="true">
    {[...Array(5)].map((_, i) => (
      <span
        key={i}
        className="waveform-bar"
        style={{ animationDelay: `${i * 0.1}s` }}
      />
    ))}
  </div>
));
RecordingWaveform.displayName = "RecordingWaveform";

// ============================================
// MAIN COMPONENT
// ============================================

/**
 * Studio - Espacio de trabajo principal para transcripción y procesamiento de audio.
 *
 * Características:
 * - Título de nota editable (vista previa - sin archivo hasta exportar)
 * - Controles de grabación prominentes con atajos de teclado
 * - Copia rápida con retroalimentación visual
 * - Exportación multiformato (TXT, MD, JSON)
 * - Conteo de palabras y estado en tiempo real
 * - Estado vacío pulido y micro-interacciones
 */
export const Studio: React.FC<StudioProps> = React.memo(
  ({
    status,
    transcription,
    timerFormatted,
    errorMessage,
    onStartRecording,
    onStopRecording,
    onClearError,
    onSaveSnippet,
    onTranscriptionChange,
    onTranslate,
  }) => {
    // --- Estado de Pestañas ---
    const {
      tabs,
      activeTabId,
      activeTab,
      addTab,
      removeTab,
      setActiveTab,
      updateTabContent,
      updateTabTitle,
      updateTabLanguage,
      reorderTabs,
    } = useNoteTabs();

    // --- Estado Local ---
    const [noteTitle, setNoteTitle] = useState(generateDefaultTitle);
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [copyState, setCopyState] = useState<CopyState>("idle");
    const [showExportMenu, setShowExportMenu] = useState(false);
    const [showSaveDialog, setShowSaveDialog] = useState(false);
    const [snippetTitle, setSnippetTitle] = useState("");
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [exportToast, setExportToast] = useState<string | null>(null);
    const [localContent, setLocalContent] = useState("");

    // Rastrear modo de grabación (agregar o reemplazar)
    const [recordingMode, setRecordingMode] = useState<"replace" | "append">(
      "replace"
    );
    // Almacenar contenido antes de iniciar grabación (para vista previa en modo append)
    const [preRecordingContent, setPreRecordingContent] = useState("");
    // Rastrear estado previo para detectar finalización de grabación
    const prevStatusRef = useRef<Status>(status);

    // --- Refs ---
    const titleInputRef = useRef<HTMLInputElement>(null);
    const exportMenuRef = useRef<HTMLDivElement>(null);
    const editorRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const copyTimeoutRef = useRef<number | null>(null);

    // --- Efectos ---

    // 1. Sincronizar título y contenido de pestaña activa
    useEffect(() => {
      if (activeTab) {
        setNoteTitle(activeTab.title);
        // Solo actualizar localContent desde la pestaña si no estamos grabando
        if (status !== "recording") {
          setLocalContent(activeTab.content || "");
        }
      }
    }, [activeTabId, activeTab, status]);

    // 2. Manejar Lógica de Inicio/Fin de Grabación
    useEffect(() => {
      const prevStatus = prevStatusRef.current;

      // Detectar Inicio de Grabación
      if (prevStatus !== "recording" && status === "recording") {
        setPreRecordingContent(localContent);
      }

      // Detectar Fin de Grabación O Procesamiento Completado
      if (
        (prevStatus === "recording" || prevStatus === "processing") &&
        status === "idle"
      ) {
        if (transcription) {
          setLocalContent(transcription);
          if (activeTabId) {
            updateTabContent(activeTabId, transcription);
          }
        }
      }

      prevStatusRef.current = status;
    }, [status, transcription, localContent, activeTabId, updateTabContent]);

    // --- Estado Derivado (Memoizado) ---
    const statusFlags = useMemo(
      () => ({
        isRecording: status === "recording",
        isTranscribing: status === "transcribing",
        isProcessing: status === "processing",
        isIdle: status === "idle",
        isBusy: status === "transcribing" || status === "processing",
        isError: status === "error",
      }),
      [status]
    );

    const {
      isRecording,
      isTranscribing,
      isProcessing,
      isIdle,
      isBusy,
      isError,
    } = statusFlags;

    // Lógica de Visualización de Contenido
    const displayContent = useMemo(() => {
      if (isRecording) {
        return recordingMode === "append"
          ? `${preRecordingContent}${
              preRecordingContent ? "\n\n" : ""
            }${transcription}`
          : transcription;
      }
      return localContent;
    }, [
      isRecording,
      recordingMode,
      preRecordingContent,
      transcription,
      localContent,
    ]);

    const hasContent = displayContent.length > 0;
    const wordCount = useMemo(
      () => (hasContent ? countWords(displayContent) : 0),
      [displayContent, hasContent]
    );
    const lines = useMemo(
      () => (displayContent ? displayContent.split("\n") : [""]),
      [displayContent]
    );

    // Idioma actual de la pestaña activa
    const currentLanguage = activeTab?.language ?? "es";

    // --- Efectos ---

    // Enfocar input de título al editar
    useEffect(() => {
      if (isEditingTitle && titleInputRef.current) {
        titleInputRef.current.focus();
        titleInputRef.current.select();
      }
    }, [isEditingTitle]);

    // Cerrar menú de exportación al hacer clic fuera
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

    // Manejar tecla escape para todos los diálogos
    useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          if (showSaveDialog) setShowSaveDialog(false);
          if (showExportMenu) setShowExportMenu(false);
          if (isEditingTitle) setIsEditingTitle(false);
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }, [showSaveDialog, showExportMenu, isEditingTitle]);

    // Auto-scroll del editor durante la grabación
    useEffect(() => {
      if (isRecording && editorRef.current) {
        requestAnimationFrame(() => {
          editorRef.current?.scrollTo({
            top: editorRef.current.scrollHeight,
            behavior: "smooth",
          });
        });
      }
    }, [displayContent, isRecording]);

    // Limpiar timeout de copia al desmontar
    useEffect(() => {
      return () => {
        if (copyTimeoutRef.current) {
          clearTimeout(copyTimeoutRef.current);
        }
      };
    }, []);

    // --- Handlers ---

    // Interceptar inicio de grabación para rastrear modo
    const handleStartRecording = useCallback(
      (mode: "replace" | "append" = "replace") => {
        setRecordingMode(mode);
        setPreRecordingContent(localContent);
        onStartRecording(mode);
      },
      [onStartRecording, localContent]
    );

    const handleTitleSubmit = useCallback(() => {
      setIsEditingTitle(false);
      if (!noteTitle.trim()) {
        setNoteTitle(generateDefaultTitle());
      }
    }, [noteTitle]);

    const handleTitleKeyDown = useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
          handleTitleSubmit();
        }
      },
      [handleTitleSubmit]
    );

    const handleCopy = useCallback(async () => {
      if (!hasContent || copyState === "copied") return;

      try {
        await navigator.clipboard.writeText(displayContent);
        setCopyState("copied");

        if (copyTimeoutRef.current) {
          clearTimeout(copyTimeoutRef.current);
        }

        copyTimeoutRef.current = window.setTimeout(() => {
          setCopyState("idle");
          copyTimeoutRef.current = null;
        }, COPY_FEEDBACK_DURATION_MS);
      } catch (err) {
        console.error("[Studio] Falló la copia:", err);
        setCopyState("error");
        setTimeout(() => setCopyState("idle"), 2000);
      }
    }, [displayContent, hasContent, copyState]);

    const handleExport = useCallback(
      (format: ExportFormat) => {
        if (!hasContent) return;

        const filename = sanitizeFilename(noteTitle);
        let content: string;

        switch (format) {
          case "md":
            content = `# ${noteTitle}\n\n${displayContent}\n\n---\n\n*Exportado desde Voice2Machine el ${new Date().toLocaleString()}*`;
            break;
          case "json":
            content = JSON.stringify(
              {
                title: noteTitle,
                content: displayContent,
                metadata: {
                  wordCount,
                  characterCount: displayContent.length,
                  language: currentLanguage,
                  exportedAt: new Date().toISOString(),
                  source: "voice2machine",
                },
              },
              null,
              2
            );
            break;
          default:
            content = displayContent;
        }

        const { mimeType } = EXPORT_FORMATS[format];
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = `${filename}.${format}`;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
        setShowExportMenu(false);

        setExportToast(`Exportado como ${filename}.${format}`);
        setTimeout(() => setExportToast(null), 3000);
      },
      [displayContent, noteTitle, wordCount, hasContent, currentLanguage]
    );

    // Manejar edición de contenido
    const handleContentChange = useCallback(
      (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newContent = e.target.value;
        setLocalContent(newContent);

        if (activeTabId) {
          updateTabContent(activeTabId, newContent);
        }

        onTranscriptionChange?.(newContent);
      },
      [activeTabId, updateTabContent, onTranscriptionChange]
    );

    // Manejar cambio de título
    const handleTitleChangeForTab = useCallback(
      (newTitle: string) => {
        setNoteTitle(newTitle);
        if (activeTabId) {
          updateTabTitle(activeTabId, newTitle);
        }
      },
      [activeTabId, updateTabTitle]
    );

    const handleSaveToLibrary = useCallback(() => {
      if (!hasContent) return;
      setSnippetTitle(noteTitle);
      setShowSaveDialog(true);
    }, [hasContent, noteTitle]);

    const handleConfirmSave = useCallback(() => {
      if (!onSaveSnippet || !displayContent.trim()) return;

      onSaveSnippet({
        title: snippetTitle || noteTitle,
        text: displayContent,
        language: currentLanguage,
      });

      setSaveSuccess(true);
      setTimeout(() => {
        setShowSaveDialog(false);
        setSnippetTitle("");
        setSaveSuccess(false);
      }, 1000);
    }, [
      onSaveSnippet,
      displayContent,
      snippetTitle,
      noteTitle,
      currentLanguage,
    ]);

    const handleCancelSave = useCallback(() => {
      setShowSaveDialog(false);
      setSnippetTitle("");
    }, []);

    // --- Render ---

    return (
      <div className={`studio-workspace ${isRecording ? "is-recording" : ""}`}>
        {/* === Barra Superior === */}
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
                onChange={(e) => handleTitleChangeForTab(e.target.value)}
                onBlur={handleTitleSubmit}
                onKeyDown={handleTitleKeyDown}
                placeholder="Nombra tu idea..."
                aria-label="Título de nota"
                maxLength={100}
                style={{ width: "100%" }}
              />
            ) : (
              <button
                className="studio-title-display"
                onClick={() => setIsEditingTitle(true)}
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
                <span
                  className="studio-title-edit-icon"
                  style={{ flexShrink: 0 }}
                >
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
              className={`studio-btn studio-btn-copy ${copyState}`}
              onClick={handleCopy}
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
                className={`semantic-toggle-option ${
                  currentLanguage === "en" ? "active" : ""
                }`}
                onClick={() => {
                  onTranslate && onTranslate("en");
                  if (activeTabId) updateTabLanguage(activeTabId, "en");
                }}
                disabled={isBusy}
                title="Traducir a Inglés"
              >
                <span className="toggle-label">EN</span>
              </button>
              <button
                className={`semantic-toggle-option ${
                  currentLanguage === "es" ? "active" : ""
                }`}
                onClick={() => {
                  onTranslate && onTranslate("es");
                  if (activeTabId) updateTabLanguage(activeTabId, "es");
                }}
                disabled={isBusy}
                title="Traducir a Español"
              >
                <span className="toggle-label">ES</span>
              </button>
              {/* Indicador Activo (Solo visual) */}
              <div
                className={`toggle-indicator ${currentLanguage}`}
                aria-hidden="true"
              />
            </div>

            <div className="studio-action-divider" />

            {/* Acción Primaria: Exportar */}
            <div className="studio-export-wrapper">
              <button
                className="studio-btn-primary-ghost"
                onClick={() => handleExport("txt")}
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
                      ExportFormat,
                      (typeof EXPORT_FORMATS)["txt"]
                    ][]
                  ).map(([format, { label, Icon, description }]) => (
                    <button
                      key={format}
                      className="spatial-dropdown-item"
                      onClick={() => handleExport(format)}
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
              onClick={handleSaveToLibrary}
              disabled={!hasContent || isBusy}
              title="Guardar en Librería"
            >
              <SaveIcon />
            </button>
          </div>
        </header>

        {/* === Barra de Pestañas === */}
        <TabBar
          tabs={tabs}
          activeTabId={activeTabId}
          onTabSelect={setActiveTab}
          onTabClose={removeTab}
          onTabAdd={() => addTab()}
          onTabReorder={reorderTabs}
        />

        {/* === Área del Editor === */}
        <div className="studio-editor-wrapper">
          {!hasContent && !isRecording ? (
            <EmptyState
              isIdle={isIdle}
              onStartRecording={handleStartRecording}
            />
          ) : (
            <div
              className={`studio-editor ${isRecording ? "recording" : ""}`}
              ref={editorRef}
            >
              {/* Barra superior del editor */}
              <div className="studio-editor-topbar">
                <div className="studio-traffic-lights" aria-hidden="true">
                  <span className="light red" />
                  <span className="light yellow" />
                  <span className="light green" />
                </div>

                <div className="studio-editor-status">
                  {isRecording && (
                    <div className="studio-live-badge">
                      <RecordingWaveform />
                      <span>Grabando</span>
                      <span className="live-timer">{timerFormatted}</span>
                    </div>
                  )}
                  {isTranscribing && (
                    <div className="studio-processing-badge">
                      <span className="processing-spinner" />
                      <span>Transcribiendo...</span>
                    </div>
                  )}
                  {isProcessing && (
                    <div className="studio-processing-badge">
                      <span className="processing-spinner" />
                      <span>Procesando...</span>
                    </div>
                  )}
                  {!isRecording && !isBusy && (
                    <div className="studio-editable-badge">
                      <EditIcon />
                      <span>editable</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Contenido - Textarea editable cuando no graba */}
              {isRecording || isBusy ? (
                /* Vista de solo lectura durante grabación/procesamiento */
                <div className="studio-editor-content">
                  {lines.map((line, i) => (
                    <div key={i} className="studio-line">
                      <span className="studio-line-number">{i + 1}</span>
                      <span className="studio-line-content">
                        {line || <span className="empty-line">&nbsp;</span>}
                      </span>
                    </div>
                  ))}
                  {isRecording && (
                    <div className="studio-line studio-cursor-line">
                      <span className="studio-line-number">
                        {lines.length + 1}
                      </span>
                      <span className="studio-line-content">
                        <span className="studio-cursor-blink" />
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                /* Textarea editable cuando está inactivo */
                <div className="studio-editor-with-lines">
                  <div className="studio-line-numbers" aria-hidden="true">
                    {lines.map((_, i) => (
                      <span key={i}>{i + 1}</span>
                    ))}
                    {/* Línea extra para cuando se escribe al final */}
                    <span>{lines.length + 1}</span>
                  </div>
                  <textarea
                    ref={textareaRef}
                    className="studio-editable-area"
                    value={localContent}
                    onChange={handleContentChange}
                    placeholder="Empieza a escribir o graba para transcribir..."
                    aria-label="Contenido de la nota"
                    spellCheck="true"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* === Pie de Página === */}
        <footer className="studio-footer">
          {/* Izquierda: Estadísticas */}
          <div className="studio-stats">
            <span className="studio-stat">
              <strong>{wordCount.toLocaleString()}</strong>
              <span className="stat-label">palabras</span>
            </span>
            <span className="studio-stat-divider" />
            <span className="studio-stat">
              <strong>{transcription.length.toLocaleString()}</strong>
              <span className="stat-label">caracteres</span>
            </span>
            <span className="studio-stat-divider" />
            <span className="studio-stat">
              <strong>{lines.length}</strong>
              <span className="stat-label">líneas</span>
            </span>
          </div>

          {/* Centro: Pista de atajo de teclado */}
          <div className="studio-shortcut-hint">
            <kbd>{RECORD_SHORTCUT}</kbd>
            <span>para {isRecording ? "parar" : "empezar"}</span>
          </div>

          {/* Derecha: Acción Primaria */}
          <div className="studio-primary-action">
            {(isIdle || isError) && (
              <>
                {/* Mostrar botón "Añadir" cuando hay contenido existente */}
                {hasContent && (
                  <button
                    className="studio-append-btn"
                    onClick={() => handleStartRecording("append")}
                    aria-label="Añadir a transcripción"
                    title="Grabar y añadir a la nota existente"
                  >
                    <span className="append-btn-icon">
                      <PlusIcon />
                    </span>
                    <span className="append-btn-text">Añadir</span>
                  </button>
                )}
                <button
                  className="studio-record-btn"
                  onClick={() => {
                    if (hasContent) {
                      // Crear nueva pestaña para acción "Nuevo" cuando hay contenido
                      addTab();
                    }
                    handleStartRecording("replace");
                  }}
                  aria-label={
                    hasContent
                      ? "Crear nueva nota e iniciar grabación"
                      : "Iniciar grabación"
                  }
                  title={
                    hasContent
                      ? "Crear nueva nota e iniciar grabación"
                      : "Iniciar grabación"
                  }
                >
                  <span className="record-btn-pulse" />
                  <span className="record-btn-icon">
                    <MicIcon />
                  </span>
                  <span className="record-btn-text">
                    {hasContent ? "Nuevo" : "Grabar"}
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

        {/* === Toast de Error === */}
        {isError && errorMessage && (
          <div
            className="studio-error-toast"
            role="alert"
            aria-live="assertive"
          >
            <span className="error-icon">⚠</span>
            <span className="error-text">{errorMessage}</span>
            <button
              onClick={onClearError}
              className="error-close-btn"
              aria-label="Descartar error"
            >
              ✕
            </button>
          </div>
        )}

        {/* === Modal de Guardar Diálogo === */}
        {showSaveDialog && (
          <div
            className="studio-modal-overlay"
            onClick={(e) => e.target === e.currentTarget && handleCancelSave()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="save-dialog-title"
          >
            <div className={`studio-modal ${saveSuccess ? "success" : ""}`}>
              {saveSuccess ? (
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
                        value={snippetTitle}
                        onChange={(e) => setSnippetTitle(e.target.value)}
                        placeholder="Ingresa un título..."
                        autoFocus
                        maxLength={100}
                      />
                    </div>

                    <div className="snippet-preview-box">
                      <p className="snippet-preview-text">
                        {displayContent.slice(0, 200)}
                        {displayContent.length > 200 ? "..." : ""}
                      </p>
                      <div className="snippet-preview-meta">
                        <span>{wordCount} palabras</span>
                        <span>•</span>
                        <span>{displayContent.length} caracteres</span>
                      </div>
                    </div>
                  </div>

                  <footer className="studio-modal-actions">
                    <button
                      onClick={handleCancelSave}
                      className="studio-btn-cancel"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleConfirmSave}
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
        )}

        {/* === Toast de Éxito de Exportación === */}
        {exportToast && (
          <div className="export-toast" role="status" aria-live="polite">
            <CheckIcon />
            <span>{exportToast}</span>
          </div>
        )}
      </div>
    );
  }
);

Studio.displayName = "Studio";
