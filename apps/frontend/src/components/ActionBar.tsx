import React, { useMemo } from "react";
import type { Status } from "../types";
import { CopyIcon, DownloadIcon, MicIcon, LoaderIcon } from "../assets/Icons";

interface ActionBarProps {
  status: Status;
  transcription: string;
  timerFormatted: string;
  llmProgress: number | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onCopy: () => void;
  onDownload: () => void;
  copyFeedback?: boolean;
}

export const ActionBar: React.FC<ActionBarProps> = React.memo(
  ({
    status,
    transcription,
    timerFormatted,
    llmProgress,
    onStartRecording,
    onStopRecording,
    onCopy,
    onDownload,
    copyFeedback = false,
  }) => {
    // Single useMemo for all derived state - computed once per status change
    const flags = useMemo(() => {
      const isRecording = status === "recording";
      const isTranscribing = status === "transcribing";
      const isProcessing = status === "processing";
      return {
        isRecording,
        isTranscribing,
        isProcessing,
        isIdle: status === "idle",
        isBusy: isTranscribing || isProcessing,
      };
    }, [status]);

    const { isRecording, isTranscribing, isProcessing, isIdle, isBusy } = flags;
    const hasContent = transcription.length > 0; // Skip trim() - empty string check is enough
    const canInteract = !isBusy;

    // Inline toggle - no useCallback overhead for simple conditional
    const handleToggleRecord = isRecording ? onStopRecording : onStartRecording;

    return (
      <footer className="action-bar-container">
        {/* Left: Copy & Download */}
        <div className="action-bar-left">
          <button
            className="btn-action-bar"
            onClick={onCopy}
            disabled={!hasContent || !canInteract}
            aria-label="Copy all transcription to clipboard"
          >
            <CopyIcon />
            <span>{copyFeedback ? "Copied!" : "Copy All"}</span>
          </button>
          <button
            className="btn-action-bar btn-icon-only"
            onClick={onDownload}
            disabled={!hasContent || !canInteract}
            aria-label="Download transcription"
          >
            <DownloadIcon />
          </button>
        </div>

        {/* Center: Progress indicator */}
        <div className="action-bar-center">
          {isTranscribing && (
            <div className="progress-status">
              <span className="progress-dot transcribing" />
              <span className="progress-label">Transcribing Audio...</span>
              <div className="progress-bar indeterminate">
                <div className="progress-fill" />
              </div>
            </div>
          )}
          {isProcessing && (
            <div className="progress-status">
              <span className="progress-dot processing" />
              <span className="progress-label">
                LLM Processing: Contextualizing...
              </span>
              <span className="progress-percent">{llmProgress ?? 45}%</span>
              <div className="progress-bar">
                <div
                  className="progress-fill shimmer"
                  style={{ width: `${llmProgress ?? 45}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Right: Recording controls */}
        <div className="action-bar-right">
          {isRecording && (
            <div className="listening-indicator">
              <div className="listening-icon-wrapper">
                <div className="listening-icon">
                  <MicIcon />
                </div>
                <div className="pulse-ring" />
              </div>
              <div className="listening-info">
                <span className="listening-label">Listening...</span>
                <span className="listening-timer">{timerFormatted}</span>
              </div>
            </div>
          )}

          {isTranscribing && (
            <div className="status-indicator transcribing">
              <div className="status-icon spin-anim">
                <LoaderIcon />
              </div>
              <div className="status-info">
                <span className="status-label">Processing</span>
                <span className="status-timer">{timerFormatted}</span>
              </div>
            </div>
          )}

          {isRecording && (
            <button
              className="btn-stop-session"
              onClick={handleToggleRecord}
              aria-label="Stop recording session"
            >
              <div className="stop-icon-square" />
              <span>Stop Session</span>
            </button>
          )}

          {isIdle && (
            <button
              className="btn-start-session"
              onClick={handleToggleRecord}
              disabled={!canInteract}
              aria-label="Start recording session"
            >
              <MicIcon />
              <span>Start Session</span>
            </button>
          )}
        </div>
      </footer>
    );
  }
);

ActionBar.displayName = "ActionBar";
