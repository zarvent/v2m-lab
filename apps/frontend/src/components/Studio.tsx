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
  TranslateIcon,
} from "../assets/Icons";
import { TabBar } from "./TabBar";
import { useNoteTabs } from "../hooks/useNoteTabs";

// ============================================
// TYPES
// ============================================

/** Snippet item stored in localStorage */
export interface SnippetItem {
  id: string;
  timestamp: number;
  text: string;
  title: string;
  language?: "es" | "en";
}

/** Export format options */
type ExportFormat = "txt" | "md" | "json";

/** Copy button state */
type CopyState = "idle" | "copied" | "error";

interface StudioProps {
  status: Status;
  transcription: string;
  timerFormatted: string;
  errorMessage: string;
  onStartRecording: (mode?: "replace" | "append") => void;
  onStopRecording: () => void;
  onClearError: () => void;
  /** Callback to save snippet to library */
  onSaveSnippet?: (snippet: Omit<SnippetItem, "id" | "timestamp">) => void;
  /** Callback to update transcription in parent state */
  onTranscriptionChange?: (text: string) => void;
}

// ============================================
// CONSTANTS
// ============================================

/** File extension info for export formats */
const EXPORT_FORMATS: Record<
  ExportFormat,
  { label: string; Icon: React.FC; mimeType: string; description: string }
> = {
  txt: {
    label: "Plain Text",
    Icon: FileTextIcon,
    mimeType: "text/plain",
    description: "Simple text file",
  },
  md: {
    label: "Markdown",
    Icon: FileCodeIcon,
    mimeType: "text/markdown",
    description: "Formatted document",
  },
  json: {
    label: "JSON",
    Icon: FileJsonIcon,
    mimeType: "application/json",
    description: "Structured data",
  },
};

/** Keyboard shortcut for recording toggle */
const RECORD_SHORTCUT = navigator.platform.includes("Mac")
  ? "⌘ Space"
  : "Ctrl+Space";

// ============================================
// HELPERS
// ============================================

/** Generate default note title based on current date/time */
const generateDefaultTitle = (): string => {
  const now = new Date();
  return now.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

/** Sanitize title for filename */
const sanitizeFilename = (title: string): string =>
  title.replace(/[/\\?%*:|"<>]/g, "-").trim() || "untitled";

// ============================================
// SUB-COMPONENTS
// ============================================

/** Empty state when no content */
const EmptyState: React.FC<{
  isIdle: boolean;
  onStartRecording: (mode?: "replace" | "append") => void;
}> = React.memo(({ isIdle, onStartRecording }) => (
  <div className="studio-empty-state">
    <div className="empty-state-icon">
      <MicIcon />
    </div>
    <h2 className="empty-state-title">Capture your thoughts</h2>
    <p className="empty-state-description">
      Just speak. Your voice becomes text, instantly.
      <br />
      Local, private, and fast.
    </p>
    {isIdle && (
      <button
        className="studio-empty-cta"
        onClick={() => onStartRecording("replace")}
        aria-label="Start recording"
      >
        <MicIcon />
        <span>Start Capture</span>
      </button>
    )}
    <div className="studio-empty-shortcut">
      <span className="shortcut-label">Press</span>
      <kbd>{RECORD_SHORTCUT}</kbd>
      <span className="shortcut-label">to capture</span>
    </div>
  </div>
));
EmptyState.displayName = "EmptyState";

/** Recording waveform animation */
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
 * Studio - Primary workspace for audio transcription and processing.
 *
 * Features:
 * - Editable conceptual note title (preview only - no file until export)
 * - Prominent recording controls with keyboard shortcuts
 * - Quick copy with visual feedback
 * - Multi-format export (TXT, MD, JSON)
 * - Real-time word count and status
 * - Polished empty state and micro-interactions
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
  }) => {
    // --- Tabs State ---
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

    // --- Local State ---
    const [noteTitle, setNoteTitle] = useState(generateDefaultTitle);
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [copyState, setCopyState] = useState<CopyState>("idle");
    const [showExportMenu, setShowExportMenu] = useState(false);
    const [showSaveDialog, setShowSaveDialog] = useState(false);
    const [snippetTitle, setSnippetTitle] = useState("");
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [exportToast, setExportToast] = useState<string | null>(null);
    const [localContent, setLocalContent] = useState(transcription);

    // --- Refs ---
    const titleInputRef = useRef<HTMLInputElement>(null);
    const exportMenuRef = useRef<HTMLDivElement>(null);
    const editorRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const copyTimeoutRef = useRef<number | null>(null);

    // Sync transcription from props to local content
    useEffect(() => {
      setLocalContent(transcription);
    }, [transcription]);

    // Sync active tab title with noteTitle
    useEffect(() => {
      if (activeTab) {
        setNoteTitle(activeTab.title);
        setLocalContent(activeTab.content || transcription);
      }
    }, [activeTabId, activeTab, transcription]);

    // --- Derived state (memoized) ---
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

    // Use localContent for display, transcription for recording sync
    const displayContent = isRecording ? transcription : localContent;
    const hasContent = displayContent.length > 0;
    const wordCount = useMemo(
      () => (hasContent ? countWords(displayContent) : 0),
      [displayContent, hasContent]
    );
    const lines = useMemo(
      () => (displayContent ? displayContent.split("\n") : [""]),
      [displayContent]
    );

    // Current language from active tab
    const currentLanguage = activeTab?.language ?? "es";

    // --- Effects ---

    // Focus title input when editing
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

    // Handle escape key for all dialogs
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

    // Auto-scroll editor during recording
    useEffect(() => {
      if (isRecording && editorRef.current) {
        requestAnimationFrame(() => {
          editorRef.current?.scrollTo({
            top: editorRef.current.scrollHeight,
            behavior: "smooth",
          });
        });
      }
    }, [transcription, isRecording]);

    // Cleanup copy timeout on unmount
    useEffect(() => {
      return () => {
        if (copyTimeoutRef.current) {
          clearTimeout(copyTimeoutRef.current);
        }
      };
    }, []);

    // --- Handlers ---

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
        await navigator.clipboard.writeText(transcription);
        setCopyState("copied");

        // Clear any existing timeout
        if (copyTimeoutRef.current) {
          clearTimeout(copyTimeoutRef.current);
        }

        copyTimeoutRef.current = window.setTimeout(() => {
          setCopyState("idle");
          copyTimeoutRef.current = null;
        }, COPY_FEEDBACK_DURATION_MS);
      } catch (err) {
        console.error("[Studio] Copy failed:", err);
        setCopyState("error");
        setTimeout(() => setCopyState("idle"), 2000);
      }
    }, [transcription, hasContent, copyState]);

    const handleExport = useCallback(
      (format: ExportFormat) => {
        if (!hasContent) return;

        const filename = sanitizeFilename(noteTitle);
        let content: string;

        switch (format) {
          case "md":
            content = `# ${noteTitle}\n\n${displayContent}\n\n---\n\n*Exported from Voice2Machine on ${new Date().toLocaleString()}*`;
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

        // Fix: Append to body, click, then remove for better browser compatibility
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
        setShowExportMenu(false);

        // Show success toast
        setExportToast(`Exported as ${filename}.${format}`);
        setTimeout(() => setExportToast(null), 3000);
      },
      [displayContent, noteTitle, wordCount, hasContent, currentLanguage]
    );

    // Handle content editing
    const handleContentChange = useCallback(
      (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newContent = e.target.value;
        setLocalContent(newContent);

        // Update active tab content
        if (activeTabId) {
          updateTabContent(activeTabId, newContent);
        }

        // Notify parent if callback provided
        onTranscriptionChange?.(newContent);
      },
      [activeTabId, updateTabContent, onTranscriptionChange]
    );

    // Handle title change updates
    const handleTitleChangeForTab = useCallback(
      (newTitle: string) => {
        setNoteTitle(newTitle);
        if (activeTabId) {
          updateTabTitle(activeTabId, newTitle);
        }
      },
      [activeTabId, updateTabTitle]
    );

    // Handle translate button (conceptual - placeholder)
    const handleTranslate = useCallback(() => {
      const targetLang = currentLanguage === "es" ? "en" : "es";

      // Update language in tab
      if (activeTabId) {
        updateTabLanguage(activeTabId, targetLang);
      }

      // TODO: Integrate with LLM for actual translation
      console.log(
        `[Studio] Translation requested: ${currentLanguage} -> ${targetLang}`
      );

      // For now, just toggle the language indicator
      // Future: Call backend translateText API
    }, [currentLanguage, activeTabId, updateTabLanguage]);

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
        {/* === Header Bar === */}
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
                placeholder="Name your thought..."
                aria-label="Note title"
                maxLength={100}
                style={{ width: "100%" }}
              />
            ) : (
              <button
                className="studio-title-display"
                onClick={() => setIsEditingTitle(true)}
                aria-label="Click to edit note title"
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
              Draft
            </span>
          </div>

          <div className="studio-header-actions">
            {/* Copy Button */}
            <button
              className={`studio-btn studio-btn-copy ${copyState}`}
              onClick={handleCopy}
              disabled={!hasContent || isBusy}
              aria-label={
                copyState === "copied" ? "Copied!" : "Copy to clipboard"
              }
            >
              {copyState === "copied" ? <CheckIcon /> : <CopyIcon />}
              <span>{copyState === "copied" ? "Copied!" : "Copy"}</span>
            </button>

            {/* Export Dropdown */}
            <div className="studio-dropdown" ref={exportMenuRef}>
              <button
                className={`studio-btn studio-btn-export ${
                  showExportMenu ? "active" : ""
                }`}
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={!hasContent || isBusy}
                aria-expanded={showExportMenu}
                aria-haspopup="menu"
                aria-label="Export transcription"
              >
                <ExportIcon />
                <span>Export</span>
                <span
                  className={`dropdown-chevron ${showExportMenu ? "open" : ""}`}
                >
                  ▾
                </span>
              </button>

              {showExportMenu && (
                <div className="studio-dropdown-menu" role="menu">
                  <div className="dropdown-menu-header">Export as</div>
                  {(
                    Object.entries(EXPORT_FORMATS) as [
                      ExportFormat,
                      (typeof EXPORT_FORMATS)["txt"]
                    ][]
                  ).map(([format, { label, Icon, description }]) => (
                    <button
                      key={format}
                      className="studio-dropdown-item"
                      onClick={() => handleExport(format)}
                      role="menuitem"
                    >
                      <span className="dropdown-item-icon">
                        <Icon />
                      </span>
                      <span className="dropdown-item-content">
                        <span className="dropdown-item-label">{label}</span>
                        <span className="dropdown-item-desc">
                          {description}
                        </span>
                      </span>
                      <span className="dropdown-item-ext">.{format}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Translate Button */}
            <button
              className="studio-btn studio-btn-translate"
              onClick={handleTranslate}
              disabled={!hasContent || isBusy}
              aria-label={`Translate to ${
                currentLanguage === "es" ? "English" : "Spanish"
              }`}
              title={`Translate to ${
                currentLanguage === "es" ? "English" : "Spanish"
              }`}
            >
              <TranslateIcon />
              <span>{currentLanguage === "es" ? "EN" : "ES"}</span>
            </button>

            {/* Save to Library */}
            <button
              className="studio-btn studio-btn-save"
              onClick={handleSaveToLibrary}
              disabled={!hasContent || isBusy}
              aria-label="Save to Snippets Library"
            >
              <SaveIcon />
              <span>Save</span>
            </button>
          </div>
        </header>

        {/* === Tab Bar === */}
        <TabBar
          tabs={tabs}
          activeTabId={activeTabId}
          onTabSelect={setActiveTab}
          onTabClose={removeTab}
          onTabAdd={() => addTab()}
          onTabReorder={reorderTabs}
        />

        {/* === Editor Area === */}
        <div className="studio-editor-wrapper">
          {!hasContent && !isRecording ? (
            <EmptyState isIdle={isIdle} onStartRecording={onStartRecording} />
          ) : (
            <div
              className={`studio-editor ${isRecording ? "recording" : ""}`}
              ref={editorRef}
            >
              {/* Top bar */}
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
                      <span>Recording</span>
                      <span className="live-timer">{timerFormatted}</span>
                    </div>
                  )}
                  {isTranscribing && (
                    <div className="studio-processing-badge">
                      <span className="processing-spinner" />
                      <span>Transcribing...</span>
                    </div>
                  )}
                  {isProcessing && (
                    <div className="studio-processing-badge">
                      <span className="processing-spinner" />
                      <span>Processing...</span>
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

              {/* Content - Editable textarea when not recording */}
              {isRecording || isBusy ? (
                /* Read-only view during recording/processing */
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
                /* Editable textarea when idle */
                <div className="studio-editor-with-lines">
                  <div className="studio-line-numbers" aria-hidden="true">
                    {lines.map((_, i) => (
                      <span key={i}>{i + 1}</span>
                    ))}
                    {/* Extra line for when typing at end */}
                    <span>{lines.length + 1}</span>
                  </div>
                  <textarea
                    ref={textareaRef}
                    className="studio-editable-area"
                    value={localContent}
                    onChange={handleContentChange}
                    placeholder="Start typing or record to transcribe..."
                    aria-label="Note content"
                    spellCheck="true"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* === Footer === */}
        <footer className="studio-footer">
          {/* Left: Stats */}
          <div className="studio-stats">
            <span className="studio-stat">
              <strong>{wordCount.toLocaleString()}</strong>
              <span className="stat-label">words</span>
            </span>
            <span className="studio-stat-divider" />
            <span className="studio-stat">
              <strong>{transcription.length.toLocaleString()}</strong>
              <span className="stat-label">chars</span>
            </span>
            <span className="studio-stat-divider" />
            <span className="studio-stat">
              <strong>{lines.length}</strong>
              <span className="stat-label">lines</span>
            </span>
          </div>

          {/* Center: Keyboard shortcut hint */}
          <div className="studio-shortcut-hint">
            <kbd>{RECORD_SHORTCUT}</kbd>
            <span>to {isRecording ? "stop" : "start"}</span>
          </div>

          {/* Right: Primary Action */}
          <div className="studio-primary-action">
            {(isIdle || isError) && (
              <>
                {/* Show "Add to Note" button when there's existing content */}
                {hasContent && (
                  <button
                    className="studio-append-btn"
                    onClick={() => onStartRecording("append")}
                    aria-label="Add to transcription"
                    title="Record and append to existing note"
                  >
                    <span className="append-btn-icon">
                      <PlusIcon />
                    </span>
                    <span className="append-btn-text">Add</span>
                  </button>
                )}
                <button
                  className="studio-record-btn"
                  onClick={() => onStartRecording("replace")}
                  aria-label={
                    hasContent
                      ? "Start new recording (replaces current)"
                      : "Start recording"
                  }
                  title={
                    hasContent
                      ? "Start new recording (replaces current content)"
                      : "Start recording"
                  }
                >
                  <span className="record-btn-pulse" />
                  <span className="record-btn-icon">
                    <MicIcon />
                  </span>
                  <span className="record-btn-text">
                    {hasContent ? "New" : "Record"}
                  </span>
                </button>
              </>
            )}

            {isRecording && (
              <button
                className="studio-stop-btn"
                onClick={onStopRecording}
                aria-label="Stop recording"
              >
                <span className="stop-btn-icon" />
                <span className="stop-btn-text">Stop</span>
              </button>
            )}

            {isBusy && (
              <button
                className="studio-busy-btn"
                disabled
                aria-label="Processing"
              >
                <span className="processing-spinner" />
                <span>Processing</span>
              </button>
            )}
          </div>
        </footer>

        {/* === Error Toast === */}
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
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        {/* === Save Dialog Modal === */}
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
                  <span>Saved!</span>
                </div>
              ) : (
                <>
                  <header className="studio-modal-header">
                    <h2 id="save-dialog-title" className="studio-modal-title">
                      Save to Library
                    </h2>
                  </header>

                  <div className="studio-modal-body">
                    <div className="form-field">
                      <label htmlFor="snippet-title-input">Title</label>
                      <input
                        id="snippet-title-input"
                        type="text"
                        value={snippetTitle}
                        onChange={(e) => setSnippetTitle(e.target.value)}
                        placeholder="Enter a title..."
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
                        <span>{wordCount} words</span>
                        <span>•</span>
                        <span>{displayContent.length} characters</span>
                      </div>
                    </div>
                  </div>

                  <footer className="studio-modal-actions">
                    <button
                      onClick={handleCancelSave}
                      className="studio-btn-cancel"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirmSave}
                      className="studio-btn-confirm"
                    >
                      <SaveIcon />
                      <span>Save Snippet</span>
                    </button>
                  </footer>
                </>
              )}
            </div>
          </div>
        )}

        {/* === Export Success Toast === */}
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
