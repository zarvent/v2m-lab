import React, { useRef, useEffect, useCallback, useMemo } from "react";
import { cn } from "../../utils/classnames";
import "../../styles/components/studio-editor.css";
import { EditIcon } from "../../assets/Icons";
import { RecordingWaveform } from "./RecordingWaveform";

export interface StudioEditorProps {
  content: string;
  lines: string[];
  isRecording: boolean;
  isTranscribing: boolean;
  isProcessing: boolean;
  isBusy: boolean;
  timerFormatted: string;
  onContentChange: (content: string) => void;
}

export const StudioEditor: React.FC<StudioEditorProps> = React.memo(
  ({
    content,
    lines,
    isRecording,
    isTranscribing,
    isProcessing,
    isBusy,
    timerFormatted,
    onContentChange,
  }) => {
    const editorRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll
    useEffect(() => {
      if (isRecording && editorRef.current) {
        requestAnimationFrame(() => {
          editorRef.current?.scrollTo({
            top: editorRef.current.scrollHeight,
            behavior: "smooth",
          });
        });
      }
    }, [content, isRecording]);

    return (
      <div
        className={`studio-editor ${isRecording ? "recording" : ""}`}
        ref={editorRef}
      >
        {/* Barra superior del editor */}
        <div className="studio-editor-topbar">
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
        {isRecording ? (
          /* Vista de solo lectura EXCLUSIVAMENTE durante grabación activa de audio */
          <div className="studio-editor-content">
            {lines.map((line, i) => (
              <div key={i} className="studio-line">
                <span className="studio-line-number">{i + 1}</span>
                <span className="studio-line-content">
                  {line || <span className="empty-line">&nbsp;</span>}
                </span>
              </div>
            ))}
            <div className="studio-line studio-cursor-line">
              <span className="studio-line-number">{lines.length + 1}</span>
              <span className="studio-line-content">
                <span className="studio-cursor-blink" />
              </span>
            </div>
          </div>
        ) : (
          /* Textarea editable (o readonly si procesa) */
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
              value={content}
              onChange={(e) => onContentChange(e.target.value)}
              readOnly={isBusy}
              placeholder="Escribe aquí o empieza a grabar..."
              aria-label="Contenido de la nota"
              spellCheck="true"
              style={{
                pointerEvents: isBusy ? "none" : "auto",
                opacity: isBusy ? 0.7 : 1,
                cursor: isBusy ? "wait" : "text",
              }}
            />
          </div>
        )}
      </div>
    );
  }
);

StudioEditor.displayName = "StudioEditor";
