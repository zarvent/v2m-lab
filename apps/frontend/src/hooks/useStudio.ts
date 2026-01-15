import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useNoteTabs } from "./useNoteTabs";
import { countWords } from "../utils";
import { useBackendStore } from "../stores/backendStore";
import type { Status } from "../types";

export interface UseStudioReturn {
  // Data
  localContent: string;
  noteTitle: string;
  currentLanguage: "es" | "en";
  hasContent: boolean;
  wordCount: number;
  lines: string[];

  // Tabs State
  tabs: any[]; // Typed in useNoteTabs, but exposed here
  activeTabId: string | null;

  // UI State
  isEditingTitle: boolean;
  copyState: "idle" | "copied" | "error";
  exportToast: string | null;
  showSaveDialog: boolean;

  // Recording State
  recordingMode: "replace" | "append";

  // Actions
  setLocalContent: (content: string) => void;
  setNoteTitle: (title: string) => void;
  setIsEditingTitle: (isEditing: boolean) => void;
  handleStartRecording: (mode?: "replace" | "append") => void;
  handleNewNoteAndRecord: () => void;
  handleTitleSubmit: () => void;
  handleCopy: () => Promise<void>;
  handleTranslate: (lang: "es" | "en") => void;
  handleExport: (format: "txt" | "md" | "json") => void;
  handleSaveToLibrary: () => void;
  handleConfirmSave: (title: string, text: string, lang: "es" | "en") => void;
  handleCancelSave: () => void;

  // Tab Actions exposed
  setActiveTab: (id: string) => void;
  removeTab: (id: string) => void;
  addTab: () => void;
  reorderTabs: (oldIndex: number, newIndex: number) => void;
}

const COPY_FEEDBACK_DURATION_MS = 2000;

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

const sanitizeFilename = (title: string): string =>
  title.replace(/[/\\?%*:|"<>]/g, "-").trim() || "sin_titulo";

export function useStudio(
  onSaveSnippet?: (snippet: any) => void
): UseStudioReturn {
  const status = useBackendStore((state) => state.status);
  const transcription = useBackendStore((state) => state.transcription);
  const startRecording = useBackendStore((state) => state.startRecording);
  const setTranscription = useBackendStore((state) => state.setTranscription);
  const translateText = useBackendStore((state) => state.translateText);

  // --- STATE ---
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

  // Local State (Single Source of Truth for Editor)
  const [localContent, setLocalContent] = useState("");
  const [noteTitle, setNoteTitle] = useState(generateDefaultTitle);

  // Recording State
  const [recordingMode, setRecordingMode] = useState<"replace" | "append">("replace");
  const [preRecordingContent, setPreRecordingContent] = useState("");
  const prevStatusRef = useRef<Status>(status);

  // UI State
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">("idle");
  const [exportToast, setExportToast] = useState<string | null>(null);
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Refs
  const activeTabIdRef = useRef<string | null>(null);
  const saveTimeoutRef = useRef<number | null>(null);
  const copyTimeoutRef = useRef<number | null>(null);

  // --- SYNCHRONIZATION LOGIC ---

  // 1. LOAD: Tabs -> Local (Only on explicit tab switch)
  useEffect(() => {
    // Determine if tab actually changed
    if (activeTabId && activeTabId !== activeTabIdRef.current) {
      const currentTab = tabs.find((t) => t.id === activeTabId);
      if (currentTab) {
        setLocalContent(currentTab.content || "");
        setNoteTitle(currentTab.title);
        activeTabIdRef.current = activeTabId;
      }
    } else if (activeTabId && !activeTabIdRef.current) {
      // Init case
      const currentTab = tabs.find((t) => t.id === activeTabId);
      if (currentTab) {
        setLocalContent(currentTab.content || "");
        setNoteTitle(currentTab.title);
        activeTabIdRef.current = activeTabId;
      }
    }
  }, [activeTabId, tabs]);

  // 2. SAVE: Local -> Tabs (Debounced)
  useEffect(() => {
    if (!activeTabId) return;

    if (saveTimeoutRef.current) window.clearTimeout(saveTimeoutRef.current);

    saveTimeoutRef.current = window.setTimeout(() => {
      // Only update if content differs (avoid cycles, though useNoteTabs handles it)
      updateTabContent(activeTabId, localContent);
    }, 500);

    return () => {
      if (saveTimeoutRef.current) window.clearTimeout(saveTimeoutRef.current);
    };
  }, [localContent, activeTabId, updateTabContent]);

  // 3. RECORDING SYNC: Backend -> Local + Tabs
  useEffect(() => {
    const prevStatus = prevStatusRef.current;

    // Start Recording: Snapshot
    if (prevStatus !== "recording" && status === "recording") {
      setPreRecordingContent(localContent);
    }

    // Stop/Finish: Update
    if (
      (prevStatus === "recording" || prevStatus === "processing" || prevStatus === "transcribing") &&
      status === "idle"
    ) {
      if (transcription) {
        const finalContent =
          recordingMode === "append"
            ? `${preRecordingContent}\n\n${transcription}`.trim()
            : transcription;

        setLocalContent(finalContent);

        // Immediate save to tabs
        if (activeTabId) {
          if (saveTimeoutRef.current) window.clearTimeout(saveTimeoutRef.current);
          updateTabContent(activeTabId, finalContent);
        }
      }
    }
    prevStatusRef.current = status;
  }, [status, transcription, activeTabId, updateTabContent, recordingMode, preRecordingContent, localContent]);

  // --- ACTIONS ---

  const handleStartRecording = useCallback(
    (mode: "replace" | "append" = "replace") => {
      setRecordingMode(mode);
      setPreRecordingContent(localContent);
      startRecording(mode);
    },
    [startRecording, localContent]
  );

  const handleNewNoteAndRecord = useCallback(() => {
    const newTabId = addTab();
    setLocalContent("");
    setNoteTitle(generateDefaultTitle());
    activeTabIdRef.current = newTabId;

    setPreRecordingContent("");
    setRecordingMode("replace");
    startRecording("replace");
  }, [addTab, startRecording]);

  const handleTitleSubmit = useCallback(() => {
    setIsEditingTitle(false);
    if (!noteTitle.trim()) {
      setNoteTitle(generateDefaultTitle());
    } else if (activeTabId) {
      updateTabTitle(activeTabId, noteTitle);
    }
  }, [noteTitle, activeTabId, updateTabTitle]);

  const handleCopy = useCallback(async () => {
    const textToCopy = localContent; 

    if (!textToCopy || copyState === "copied") return;

    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopyState("copied");
      if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current);
      copyTimeoutRef.current = window.setTimeout(() => {
        setCopyState("idle");
      }, COPY_FEEDBACK_DURATION_MS);
    } catch (err) {
      console.error("[Studio] Copy failed:", err);
      setCopyState("error");
      setTimeout(() => setCopyState("idle"), 2000);
    }
  }, [localContent, copyState]);

  const handleTranslate = useCallback((lang: "es" | "en") => {
    translateText(lang);
    if (activeTabId) {
      updateTabLanguage(activeTabId, lang);
    }
  }, [translateText, activeTabId, updateTabLanguage]);

  const handleExport = useCallback((format: "txt" | "md" | "json") => {
    if (!localContent) return;

    const filename = sanitizeFilename(noteTitle);
    let content: string;

    switch (format) {
      case "md":
        content = `# ${noteTitle}\n\n${localContent}\n\n---\n\n*Exportado desde Voice2Machine*`;
        break;
      case "json":
        content = JSON.stringify({
          title: noteTitle,
          content: localContent,
          metadata: {
            wordCount: countWords(localContent),
            characterCount: localContent.length,
            language: activeTab?.language ?? "es",
            exportedAt: new Date().toISOString(),
            source: "voice2machine",
          },
        }, null, 2);
        break;
      default:
        content = localContent;
    }

    // Restore specific mime types
    const mimeMap = {
      txt: "text/plain",
      md: "text/markdown",
      json: "application/json"
    };

    const blob = new Blob([content], { type: mimeMap[format] });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setExportToast(`Exportado como ${filename}.${format}`);
    setTimeout(() => setExportToast(null), 3000);
  }, [localContent, noteTitle]);

  const handleSaveToLibrary = useCallback(() => {
    if (!localContent) return;
    setShowSaveDialog(true);
  }, [localContent]);

  const handleConfirmSave = useCallback((title: string, text: string, lang: "es" | "en") => {
    if (onSaveSnippet) {
      onSaveSnippet({ title, text, language: lang });
      setShowSaveDialog(false);
      // Optional: success toast logic handled in component or here
    }
  }, [onSaveSnippet]);

  const handleCancelSave = useCallback(() => {
    setShowSaveDialog(false);
  }, []);

  // --- DERIVED STATE ---

  const displayContent = useMemo(() => {
    if (status === "recording") {
      return recordingMode === "append"
        ? `${preRecordingContent}${preRecordingContent ? "\n\n" : ""}${transcription}`
        : transcription;
    }
    return localContent;
  }, [status, recordingMode, preRecordingContent, transcription, localContent]);

  const hasContent = displayContent.length > 0;
  const wordCount = useMemo(() => (hasContent ? countWords(displayContent) : 0), [displayContent, hasContent]);
  const lines = useMemo(() => (displayContent ? displayContent.split("\n") : [""]), [displayContent]);

  return {
    localContent: displayContent, 
    noteTitle,
    currentLanguage: activeTab?.language ?? "es",
    hasContent,
    wordCount,
    lines,

    tabs,
    activeTabId,

    isEditingTitle,
    copyState,
    exportToast,
    showSaveDialog,

    recordingMode,

    setLocalContent: (c) => {
        setLocalContent(c);
        if (activeTabId) updateTabContent(activeTabId, c);
        setTranscription(c);
    },
    setNoteTitle: (t) => {
        setNoteTitle(t);
        if (activeTabId) updateTabTitle(activeTabId, t);
    },
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
    reorderTabs
  };
}
