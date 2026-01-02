import React, { useEffect, useRef, useMemo } from "react";
import type { Status } from "../types";
import { LockIcon } from "../assets/Icons";

interface TranscriptionEditorProps {
  text: string;
  status: Status;
  isReadOnly?: boolean;
  fileName?: string;
  fileType?: string;
}

/** Memoized line component - prevents re-render of unchanged lines */
const CodeLine = React.memo<{ num: number; content: string }>(
  ({ num, content }) => (
    <div className="code-line">
      <span className="line-number">{num}</span>
      <span className="line-content">
        {content || <span className="empty-line">&nbsp;</span>}
      </span>
    </div>
  )
);
CodeLine.displayName = "CodeLine";

export const TranscriptionEditor: React.FC<TranscriptionEditorProps> =
  React.memo(
    ({
      text,
      status,
      isReadOnly = true,
      fileName = "dictation_session.txt",
      fileType = "Plain Text",
    }) => {
      const scrollRef = useRef<HTMLDivElement>(null);
      const isRecording = status === "recording";

      // RAF-batched scroll for smooth 60fps updates
      useEffect(() => {
        const el = scrollRef.current;
        if (el) {
          requestAnimationFrame(() => {
            el.scrollTop = el.scrollHeight;
          });
        }
      }, [text]);

      // Memoized line splitting - only recomputes when text changes
      const lines = useMemo(() => (text ? text.split("\n") : [""]), [text]);

      return (
        <div className="editor-outer">
          {/* Top bar with file info */}
          <header className="editor-top-bar">
            <div className="editor-file-info">
              <h1 className="editor-file-name">{fileName}</h1>
              <span className="editor-file-type">{fileType}</span>
              {isRecording && (
                <span className="editor-live-badge">
                  <span className="live-dot" />
                  Live
                </span>
              )}
            </div>
          </header>

          {/* Editor wrapper with gradient background */}
          <div className="editor-wrapper" ref={scrollRef}>
            <div className="editor-container">
              {/* Traffic lights header */}
              <div className="editor-header">
                <div className="traffic-lights" aria-hidden="true">
                  <div className="light red" />
                  <div className="light yellow" />
                  <div className="light green" />
                </div>
                {isReadOnly && (
                  <div className="readonly-badge">
                    <LockIcon />
                    <span>read-only</span>
                  </div>
                )}
              </div>

              {/* Content area with line numbers */}
              <div className="editor-content">
                {lines.map((line, i) => (
                  <CodeLine key={i} num={i + 1} content={line} />
                ))}
                {isRecording && (
                  <div className="code-line cursor-line">
                    <span className="line-number">{lines.length + 1}</span>
                    <span className="line-content">
                      <span className="cursor-blink" />
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }
  );

TranscriptionEditor.displayName = "TranscriptionEditor";
