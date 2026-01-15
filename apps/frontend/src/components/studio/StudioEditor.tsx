import React, { useRef, useEffect } from "react";
import { cn } from "../../utils/classnames";
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
        className={cn(
          "flex-1 bg-surface border border-subtle rounded-lg shadow-sm flex flex-col overflow-hidden transition-all min-h-0", // .studio-editor base
          "focus-within:border-strong focus-within:shadow-glow", // &:focus-within
          isRecording && "border-error shadow-[0_0_0_1px_var(--color-error)] animate-pulse-border" // &.recording
        )}
        ref={editorRef}
      >
        {/* Barra superior del editor */}
        <div className="h-12 px-md bg-surface border-b border-subtle flex items-center justify-end shrink-0"> {/* .studio-editor-topbar */}
          <div className="flex items-center gap-sm"> {/* .studio-editor-status */}
            {isRecording && (
              <div
                className={cn(
                  "flex items-center gap-[6px] text-xs px-[10px] py-[4px] rounded-pill font-medium", // .studio-live-badge base
                  "bg-[oklch(0.6_0.2_25/0.15)] text-error border border-[oklch(0.6_0.2_25/0.3)]" // .studio-live-badge colors
                )}
              >
                <RecordingWaveform />
                <span>Grabando</span>
                <span className="font-mono font-semibold">{timerFormatted}</span>
              </div>
            )}
            {isTranscribing && (
              <div
                className={cn(
                  "flex items-center gap-[6px] text-xs px-[10px] py-[4px] rounded-pill font-medium", // .studio-processing-badge base
                  "bg-[oklch(0.6_0.2_250/0.15)] text-primary font-mono border border-[oklch(0.6_0.2_250/0.3)]" // .studio-processing-badge colors
                )}
              >
                <span className="processing-spinner" />
                <span>Transcribiendo...</span>
              </div>
            )}
            {isProcessing && (
              <div
                className={cn(
                  "flex items-center gap-[6px] text-xs px-[10px] py-[4px] rounded-pill font-medium", // .studio-processing-badge base
                  "bg-[oklch(0.6_0.2_250/0.15)] text-primary font-mono border border-[oklch(0.6_0.2_250/0.3)]"
                )}
              >
                <span className="processing-spinner" />
                <span>Procesando...</span>
              </div>
            )}
            {!isRecording && !isBusy && (
              <div
                className={cn(
                  "flex items-center gap-[6px] text-xs px-[10px] py-[4px] rounded-pill font-medium", // .studio-editable-badge base
                  "bg-surface-hover text-muted border border-subtle" // .studio-editable-badge colors
                )}
              >
                <EditIcon className="w-3 h-3" />
                <span>editable</span>
              </div>
            )}
          </div>
        </div>

        {/* Contenido - Textarea editable cuando no graba */}
        {isRecording ? (
          /* Vista de solo lectura EXCLUSIVAMENTE durante grabación activa de audio */
          <div className="flex-1 px-lg py-md font-body text-base leading-relaxed text-primary overflow-y-auto"> {/* .studio-editor-content */}
            {lines.map((line, i) => (
              <div key={i} className="flex gap-md py-[2px]"> {/* .studio-line */}
                <span className="min-w-[32px] font-mono text-sm text-muted text-right select-none opacity-50"> {/* .studio-line-number */}
                  {i + 1}
                </span>
                <span className="flex-1 font-mono text-base leading-[1.6] text-primary"> {/* .studio-line-content */}
                  {line || <span className="empty-line">&nbsp;</span>}
                </span>
              </div>
            ))}
            <div className="flex gap-md py-[2px]"> {/* .studio-cursor-line */}
              <span className="min-w-[32px] font-mono text-sm text-muted text-right select-none opacity-50">
                {lines.length + 1}
              </span>
              <span className="flex-1 font-mono text-base leading-[1.6] text-primary">
                <span className="inline-block w-[2px] h-[1.2em] bg-primary align-text-bottom animate-[blink_1s_infinite]" /> {/* .studio-cursor-blink */}
              </span>
            </div>
          </div>
        ) : (
          /* Textarea editable (o readonly si procesa) */
          <div className="flex-1 px-lg py-md font-body text-base leading-relaxed text-primary overflow-y-auto flex h-full"> {/* .studio-editor-with-lines */}
            <div
              className="text-muted border-r border-subtle pr-md text-right select-none" // .studio-line-numbers
              aria-hidden="true"
            >
              {lines.map((_, i) => (
                <div key={i}>{i + 1}</div>
              ))}
              {/* Línea extra para cuando se escribe al final */}
              <div>{lines.length + 1}</div>
            </div>
            <textarea
              ref={textareaRef}
              className="flex-1 bg-transparent border-none outline-none text-primary font-mono text-base leading-[1.6] resize-none p-sm placeholder:text-muted w-full h-full" // .studio-editable-area
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
