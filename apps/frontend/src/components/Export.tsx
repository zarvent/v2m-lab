import React, { useState, useRef, useCallback, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { open } from "@tauri-apps/plugin-dialog";
import "../styles/components/export.css";

import {
  VideoIcon,
  AudioIcon,
  DownloadIcon,
  CopyIcon,
  CheckIcon,
  LoaderIcon,
  FileTextIcon,
  UploadIcon,
} from "../assets/Icons";
import { countWords } from "../utils";

// ============================================
// TYPES
// ============================================

type ExportStatus =
  | "idle"
  | "selecting"
  | "extracting"
  | "transcribing"
  | "complete"
  | "error";

interface FileInfo {
  path: string;
  name: string;
  extension: string;
  isVideo: boolean;
}

interface ExportResult {
  state: string;
  transcription?: string;
  refined_text?: string;
  message?: string;
}

// ============================================
// CONSTANTS
// ============================================

const VIDEO_EXTENSIONS = new Set([".mp4", ".mov", ".mkv", ".avi", ".webm"]);
const AUDIO_EXTENSIONS = new Set([
  ".wav",
  ".mp3",
  ".flac",
  ".ogg",
  ".m4a",
  ".aac",
  ".aiff",
]);
const ALL_EXTENSIONS = [...VIDEO_EXTENSIONS, ...AUDIO_EXTENSIONS];

const FORMAT_LABELS: Record<string, { label: string; color: string }> = {
  ".mp4": { label: "MP4", color: "var(--color-accent-primary)" },
  ".mov": { label: "MOV", color: "var(--color-accent-primary)" },
  ".mkv": { label: "MKV", color: "var(--color-accent-primary)" },
  ".avi": { label: "AVI", color: "var(--color-accent-primary)" },
  ".webm": { label: "WEBM", color: "var(--color-accent-primary)" },
  ".wav": { label: "WAV", color: "var(--color-accent-secondary)" },
  ".mp3": { label: "MP3", color: "var(--color-accent-secondary)" },
  ".flac": { label: "FLAC", color: "var(--color-accent-secondary)" },
  ".ogg": { label: "OGG", color: "var(--color-accent-secondary)" },
  ".m4a": { label: "M4A", color: "var(--color-accent-secondary)" },
  ".aac": { label: "AAC", color: "var(--color-accent-secondary)" },
  ".aiff": { label: "AIFF", color: "var(--color-accent-secondary)" },
};

// ============================================
// HELPERS
// ============================================

const getExtension = (path: string): string => {
  const match = path.match(/\.[^.]+$/);
  return match ? match[0].toLowerCase() : "";
};

const getFileName = (path: string): string => {
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1] || path;
};

const sanitizeFilename = (title: string): string =>
  title.replace(/[/\\?%*:|"<>]/g, "-").trim() || "transcription";

/**
 * Extracts error message from various error types.
 * Optimized for Tauri IPC errors which are plain objects.
 */
const extractErrorMessage = (err: unknown): string => {
  if (typeof err === "string") return err;
  if (err && typeof err === "object" && "message" in err) {
    return String((err as { message: unknown }).message);
  }
  return "Error desconocido";
};

// ============================================
// COMPONENT
// ============================================

interface ExportProps {
  onTranscriptionComplete?: (text: string) => void;
}

export const Export: React.FC<ExportProps> = React.memo(
  ({ onTranscriptionComplete }) => {
    // State
    const [status, setStatus] = useState<ExportStatus>("idle");
    const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
    const [transcription, setTranscription] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
    const [isDragOver, setIsDragOver] = useState(false);
    const [elapsedSeconds, setElapsedSeconds] = useState(0);

    // Refs
    const dropZoneRef = useRef<HTMLDivElement>(null);
    const copyTimeoutRef = useRef<number | null>(null);
    const timerRef = useRef<number | null>(null);
    const startTimeRef = useRef<number>(0);

    // Computed
    const wordCount = transcription ? countWords(transcription) : 0;
    const charCount = transcription.length;

    // Cleanup
    useEffect(() => {
      return () => {
        if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
        if (timerRef.current) clearInterval(timerRef.current);
      };
    }, []);

    // Common file processing logic
    const processFile = useCallback(
      async (path: string) => {
        const ext = getExtension(path);
        const name = getFileName(path);
        const isVideo = VIDEO_EXTENSIONS.has(ext);

        if (!VIDEO_EXTENSIONS.has(ext) && !AUDIO_EXTENSIONS.has(ext)) {
          setErrorMessage(`Formato no soportado: ${ext}`);
          setStatus("error");
          return;
        }

        setFileInfo({ path, name, extension: ext, isVideo });
        // Optimistic update: if video, assume extracting first.
        // Real event from Rust will confirm/correct this milliseconds later.
        setStatus(isVideo ? "extracting" : "transcribing");
        setErrorMessage("");
        setElapsedSeconds(0);

        // Start elapsed timer (updates every 500ms for smooth display)
        startTimeRef.current = Date.now();
        timerRef.current = window.setInterval(() => {
          setElapsedSeconds(
            Math.floor((Date.now() - startTimeRef.current) / 1000)
          );
        }, 500);

        // Call backend to transcribe
        try {
          const result = await invoke<{
            state: string;
            transcription?: string;
            error?: string;
          }>("transcribe_file", { filePath: path });

          if (result.transcription) {
            if (timerRef.current) clearInterval(timerRef.current);
            setTranscription(result.transcription);
            setStatus("complete");
            onTranscriptionComplete?.(result.transcription);
          } else {
            setErrorMessage(
              result.error || "No se pudo transcribir el archivo"
            );
            setStatus("error");
          }
        } catch (err) {
          if (timerRef.current) clearInterval(timerRef.current);
          console.error("[Export] Error:", err);
          setErrorMessage(extractErrorMessage(err));
          setStatus("error");
        }
      },
      [onTranscriptionComplete]
    );

    // Initial listener setup for Tauri file drop (static import - faster)
    useEffect(() => {
      // PERSISTENCE CHECK: Recover state if job finished while we were away
      invoke<ExportResult | null>("get_last_export")
        .then((lastExport) => {
          if (lastExport && lastExport.transcription && status === "idle") {
            console.log("Persistence: Recovered last export", lastExport);
            setTranscription(lastExport.transcription);
            setStatus("complete");
            setFileInfo({
              name: "Exportación Recuperada",
              path: "",
              extension: ".txt",
              isVideo: false,
            });
          }
        })
        .catch(console.error);

      const unlistenStatus = listen<{ step: string; progress: number }>(
        "v2m://export-status",
        (event) => {
          console.log("Export status event:", event.payload);
          if (event.payload.step === "extracting") {
            setStatus("extracting");
            setElapsedSeconds(0);
            startTimeRef.current = Date.now();
          } else if (event.payload.step === "transcribing") {
            setStatus("transcribing");
          }
        }
      );

      // Listen for explicit completion event (Remote Control Pattern)
      // This ensures we update even if the invoke promise hangs or times out silently
      const unlistenComplete = listen<{
        encryption?: string;
        transcription?: string;
        state: string;
      }>("v2m://transcription-complete", (event) => {
        console.log("Remote Control: Job Complete", event.payload);
        if (event.payload.transcription) {
          if (timerRef.current) clearInterval(timerRef.current);
          setTranscription(event.payload.transcription);
          setStatus("complete");
          onTranscriptionComplete?.(event.payload.transcription);
        }
      });

      const unlistenDrop = listen<string[]>("tauri://file-drop", (event) => {
        if (event.payload && event.payload.length > 0) {
          const path = event.payload[0];
          if (path) {
            processFile(path);
          }
        }
      });

      const unlistenHover = listen("tauri://file-drop-hover", () => {
        setIsDragOver(true);
      });

      const unlistenCancel = listen("tauri://file-drop-cancelled", () => {
        setIsDragOver(false);
      });

      // Cleanup function
      return () => {
        unlistenStatus.then((f) => f());
        unlistenComplete.then((f) => f()); // Clean up completion listener
        unlistenDrop.then((f) => f());
        unlistenHover.then((f) => f());
        unlistenCancel.then((f) => f());
      };
    }, [processFile, onTranscriptionComplete]); // Added onTranscriptionComplete dependency

    // Handle file selection via dialog
    const handleSelectFile = useCallback(async () => {
      setStatus("selecting");
      setErrorMessage("");

      try {
        const selected = await open({
          multiple: false,
          title: "Seleccionar archivo de audio o video",
          filters: [
            {
              name: "Media Files",
              extensions: ALL_EXTENSIONS.map((ext) => ext.slice(1)),
            },
          ],
        });

        if (!selected) {
          setStatus("idle");
          return;
        }

        const path = typeof selected === "string" ? selected : selected;
        await processFile(path);
      } catch (err) {
        console.error("[Export] Error:", err);
        setErrorMessage(extractErrorMessage(err));
        setStatus("error");
      }
    }, [processFile]);

    // Drag and drop handlers (Web events - mainly for visual feedback or preventing defaults)
    const handleDragOver = useCallback((e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      // Visual feedback handled by Tauri event, but this keeps React happy
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
    }, []);

    const handleDrop = useCallback(async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      // We ignore the web file object because it lacks the path.
      // The 'tauri://file-drop' event handles the actual logic.
      setIsDragOver(false);
    }, []);

    // Copy transcription
    const handleCopy = useCallback(async () => {
      if (!transcription || copyState === "copied") return;

      try {
        await navigator.clipboard.writeText(transcription);
        setCopyState("copied");

        if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
        copyTimeoutRef.current = window.setTimeout(() => {
          setCopyState("idle");
        }, 2000);
      } catch (err) {
        console.error("[Export] Copy failed:", err);
      }
    }, [transcription, copyState]);

    // Download transcription
    const handleDownload = useCallback(() => {
      if (!transcription) return;

      const filename = fileInfo
        ? sanitizeFilename(fileInfo.name.replace(/\.[^.]+$/, ""))
        : "transcription";

      const blob = new Blob([transcription], { type: "text/plain" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = `${filename}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(url);
    }, [transcription, fileInfo]);

    // Reset to initial state
    const handleReset = useCallback(() => {
      setStatus("idle");
      setFileInfo(null);
      setTranscription("");
      setErrorMessage("");
    }, []);

    // Render
    return (
      <div className="export-workspace">
        {/* Header */}
        <header className="export-header">
          <div className="export-title-section">
            <h1 className="export-title">Exportar Transcripción</h1>
            <p className="export-subtitle">
              Convierte archivos de video y audio a texto usando IA local
            </p>
          </div>

          {/* Format badges */}
          <div className="export-format-badges">
            <span className="format-group-label">Video</span>
            {[".mp4", ".mov", ".mkv"].map((ext) => (
              <span key={ext} className="format-badge format-badge-video">
                {FORMAT_LABELS[ext]?.label ?? ext}
              </span>
            ))}
            <span className="format-group-label">Audio</span>
            {[".wav", ".mp3", ".m4a", ".flac"].map((ext) => (
              <span key={ext} className="format-badge format-badge-audio">
                {FORMAT_LABELS[ext]?.label ?? ext}
              </span>
            ))}
          </div>
        </header>

        {/* Main Content Area */}
        <div className="export-content">
          {/* === Idle/Drop Zone State === */}
          {(status === "idle" || status === "selecting") && (
            <div
              ref={dropZoneRef}
              className={`export-drop-zone ${isDragOver ? "drag-over" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleSelectFile}
              role="button"
              tabIndex={0}
              aria-label="Seleccionar archivo de audio o video"
            >
              <div className="drop-zone-icon">
                <UploadIcon />
              </div>
              <h2 className="drop-zone-title">Suelta tu archivo aquí</h2>
              <p className="drop-zone-subtitle">o haz clic para seleccionar</p>

              <div className="drop-zone-formats">
                <div className="format-row">
                  <VideoIcon />
                  <span>Video: MP4, MOV, MKV, AVI, WebM</span>
                </div>
                <div className="format-row">
                  <AudioIcon />
                  <span>Audio: WAV, MP3, FLAC, M4A, OGG, AAC</span>
                </div>
              </div>

              <button
                className="drop-zone-button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleSelectFile();
                }}
                disabled={status === "selecting"}
              >
                {status === "selecting" ? (
                  <>
                    <LoaderIcon />
                    <span>Seleccionando...</span>
                  </>
                ) : (
                  <>
                    <UploadIcon />
                    <span>Seleccionar Archivo</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* === Processing State (Extracting or Transcribing) === */}
          {(status === "transcribing" || status === "extracting") &&
            fileInfo && (
              <div className="export-processing">
                <div className="processing-animation">
                  <div className="processing-ring" />
                  <div className="processing-icon">
                    {status === "extracting" ? <VideoIcon /> : <FileTextIcon />}
                  </div>
                </div>

                <h2 className="processing-title">Procesando Inteligencia...</h2>
                <p className="processing-file">{fileInfo.name}</p>

                <div className="processing-single-indicator">
                  <div className="pulse-bar" />
                  <p className="processing-status-text">
                    {status === "extracting"
                      ? "Extrayendo audio y optimizando entrada..."
                      : "Transcribiendo con modelo Whisper local..."}
                  </p>
                </div>

                <p className="processing-hint">
                  ⏱️ {elapsedSeconds}s — El rendimiento es diseño
                </p>
              </div>
            )}

          {/* === Complete State === */}
          {status === "complete" && (
            <div className="export-result">
              {/* Result Header */}
              <div className="result-header">
                <div className="result-info">
                  <h2 className="result-title">
                    <CheckIcon />
                    <span>Transcripción Completa</span>
                  </h2>
                  {fileInfo && <p className="result-file">{fileInfo.name}</p>}
                </div>

                <div className="result-stats">
                  <span className="stat">
                    <strong>{wordCount}</strong> palabras
                  </span>
                  <span className="stat">
                    <strong>{charCount}</strong> caracteres
                  </span>
                </div>
              </div>

              {/* Transcription Preview */}
              <div className="result-content">
                <pre className="result-text">{transcription}</pre>
              </div>

              {/* Actions */}
              <div className="result-actions">
                <button
                  className={`result-btn result-btn-primary ${
                    copyState === "copied" ? "copied" : ""
                  }`}
                  onClick={handleCopy}
                >
                  {copyState === "copied" ? <CheckIcon /> : <CopyIcon />}
                  <span>{copyState === "copied" ? "¡Copiado!" : "Copiar"}</span>
                </button>

                <button
                  className="result-btn result-btn-secondary"
                  onClick={handleDownload}
                >
                  <DownloadIcon />
                  <span>Descargar .txt</span>
                </button>

                <button
                  className="result-btn result-btn-ghost"
                  onClick={handleReset}
                >
                  <FileTextIcon />
                  <span>Nuevo Archivo</span>
                </button>
              </div>
            </div>
          )}

          {/* === Error State === */}
          {status === "error" && (
            <div className="export-error">
              <div className="error-icon">⚠️</div>
              <h2 className="error-title">Error al procesar</h2>
              <p className="error-message">{errorMessage}</p>

              <button className="error-retry-btn" onClick={handleReset}>
                Intentar de nuevo
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }
);

Export.displayName = "Export";
