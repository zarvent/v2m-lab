import React, { useMemo, useCallback } from "react";
import { cn } from "../utils/classnames";
import { TabBar } from "./TabBar";
import { StudioHeader } from "./studio/StudioHeader";
import { StudioEditor } from "./studio/StudioEditor";
import { StudioFooter } from "./studio/StudioFooter";
import { StudioEmptyState } from "./studio/StudioEmptyState";
import { SaveDialog } from "./studio/SaveDialog";
import { useStudio } from "../hooks/useStudio";
import { CheckIcon } from "../assets/Icons";
import { useBackendStore } from "../stores/backendStore";

export interface SnippetItem {
  id: string;
  timestamp: number;
  text: string;
  title: string;
  language?: "es" | "en";
}

interface StudioProps {
  timerFormatted: string;
  onSaveSnippet?: (snippet: Omit<SnippetItem, "id" | "timestamp">) => void;
}

const RECORD_SHORTCUT = navigator.platform.includes("Mac")
  ? "⌘ Espacio"
  : "Ctrl+Espacio";

export const Studio: React.FC<StudioProps> = React.memo(
  ({
    timerFormatted,
    onSaveSnippet,
  }) => {
    const status = useBackendStore((state) => state.status);
    const errorMessage = useBackendStore((state) => state.errorMessage);
    const stopRecording = useBackendStore((state) => state.stopRecording);
    const clearError = useBackendStore((state) => state.clearError);

    const {
      localContent,
      noteTitle,
      currentLanguage,
      hasContent,
      wordCount,
      lines,
      tabs,
      activeTabId,
      isEditingTitle,
      copyState,
      exportToast,
      showSaveDialog,
      setLocalContent,
      setNoteTitle,
      setIsEditingTitle,
      handleStartRecording,
      handleNewNoteAndRecord,
      handleTitleSubmit,
      handleCopy,
      handleTranslate,
      handleExport,
      handleSaveToLibrary,
      handleConfirmSave,
      handleCancelSave,
      setActiveTab,
      removeTab,
      addTab,
      reorderTabs,
    } = useStudio(
      onSaveSnippet
    );

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

    const handleEditTitle = useCallback(
      () => setIsEditingTitle(true),
      [setIsEditingTitle]
    );

    const handleAddTab = useCallback(() => addTab(), [addTab]);

    return (
      <div
        className={cn("studio-workspace", isRecording && "is-recording")}
      >
        <StudioHeader
          noteTitle={noteTitle}
          isEditingTitle={isEditingTitle}
          hasContent={hasContent}
          isBusy={isBusy}
          currentLanguage={currentLanguage}
          copyState={copyState}
          onTitleChange={setNoteTitle}
          onTitleSubmit={handleTitleSubmit}
          onEditTitle={handleEditTitle}
          onCopy={handleCopy}
          onTranslate={handleTranslate}
          onExport={handleExport}
          onSaveToLibrary={handleSaveToLibrary}
        />

        <TabBar
          tabs={tabs}
          activeTabId={activeTabId}
          onTabSelect={setActiveTab}
          onTabClose={removeTab}
          onTabAdd={handleAddTab}
          onTabReorder={reorderTabs}
        />

        <div className="studio-editor-wrapper">
          {!hasContent && !isRecording ? (
            <StudioEmptyState
              isIdle={isIdle}
              recordShortcut={RECORD_SHORTCUT}
              onStartRecording={handleStartRecording}
            />
          ) : (
            <StudioEditor
              content={localContent}
              lines={lines}
              isRecording={isRecording}
              isTranscribing={isTranscribing}
              isProcessing={isProcessing}
              isBusy={isBusy}
              timerFormatted={timerFormatted}
              onContentChange={setLocalContent}
            />
          )}
        </div>

        <StudioFooter
          wordCount={wordCount}
          charCount={localContent.length}
          lineCount={lines.length}
          isRecording={isRecording}
          isBusy={isBusy}
          isIdle={isIdle}
          isError={isError}
          hasContent={hasContent}
          recordShortcut={RECORD_SHORTCUT}
          onStartRecording={handleStartRecording}
          onStopRecording={stopRecording}
          onNewNote={handleNewNoteAndRecord}
        />

        {isError && errorMessage && (
          <div
            className="studio-error-toast"
            role="alert"
            aria-live="assertive"
          >
            <span className="error-icon">⚠</span>
            <span className="error-text">{errorMessage}</span>
            <button
              onClick={clearError}
              className="error-close-btn"
              aria-label="Descartar error"
            >
              ✕
            </button>
          </div>
        )}

        {showSaveDialog && (
          <SaveDialog
            initialTitle={noteTitle}
            content={localContent}
            wordCount={wordCount}
            currentLanguage={currentLanguage}
            onConfirm={handleConfirmSave}
            onCancel={handleCancelSave}
          />
        )}

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
