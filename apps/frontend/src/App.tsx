import {
  useCallback,
  useEffect,
  lazy,
  Suspense,
  useMemo,
  useState,
} from "react";
import { Sidebar } from "./components/Sidebar";
import type { NavItem } from "./components/Sidebar";
import { Studio } from "./components/Studio";
import { Overview } from "./components/Overview";
import { Transcriptions } from "./components/Transcriptions";
import { SnippetsLibrary } from "./components/SnippetsLibrary";
import { Export } from "./components/Export";
import { BackendInitializer } from "./components/BackendInitializer";
import { useBackendStore } from "./stores/backendStore";
import { useUiStore } from "./stores/uiStore";
import { useTimer } from "./hooks/useTimer";
import { useSnippets } from "./hooks/useSnippets";
import { countWords } from "./utils";

const Settings = lazy(() =>
  import("./components/Settings").then((m) => ({ default: m.Settings }))
);

function AppContent() {
  const status = useBackendStore((state) => state.status);
  const transcription = useBackendStore((state) => state.transcription);
  const history = useBackendStore((state) => state.history);

  // Actions
  const startRecording = useBackendStore((state) => state.startRecording);
  const stopRecording = useBackendStore((state) => state.stopRecording);
  const setTranscription = useBackendStore((state) => state.setTranscription);

  const timer = useTimer(status);
  const { addSnippet } = useSnippets();

  const { activeView, setActiveView } = useUiStore();
  const [showSettings, setShowSettings] = useState(false);

  // Memoización del conteo de palabras
  const wordCount = useMemo(() => countWords(transcription), [transcription]);
  const sessionStats = useMemo(
    () => ({
      duration: timer.formatted,
      words: wordCount,
      confidence: "High",
      confidencePercent: 98,
    }),
    [wordCount, timer.formatted]
  );

  // Atajo global (Ctrl+Space)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.code === "Space") {
        e.preventDefault();
        const isDisabled =
          status === "transcribing" ||
          status === "processing" ||
          status === "disconnected" ||
          status === "paused";
        if (!isDisabled) {
          if (status === "recording") {
            stopRecording();
          } else {
            startRecording();
          }
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [startRecording, stopRecording, status]);

  const handleOpenSettings = useCallback(() => setShowSettings(true), []);
  const handleNavChange = useCallback((nav: NavItem) => setActiveView(nav), [setActiveView]);
  const handleSaveSnippet = useCallback(
    (snippet: { title: string; text: string }) => addSnippet(snippet),
    [addSnippet]
  );
  const handleUseSnippet = useCallback(
    (text: string) => {
      setTranscription(text);
      setActiveView("studio");
    },
    [setTranscription, setActiveView]
  );
  const handleDeleteHistoryItem = useCallback((id: string) => {
    console.log("[App] Eliminar elemento del historial:", id);
  }, []);
  const handleSelectHistoryItem = useCallback(
    (item: { text: string }) => {
      setTranscription(item.text);
      setActiveView("studio");
    },
    [setTranscription, setActiveView]
  );

  const renderView = () => {
    switch (activeView) {
      case "studio":
        return (
          <Studio
            timerFormatted={timer.formatted}
            onSaveSnippet={handleSaveSnippet}
          />
        );

      case "overview":
        return (
          <Overview />
        );

      case "transcriptions":
        return (
          <Transcriptions
            history={history}
            onDeleteItem={handleDeleteHistoryItem}
            onSelectItem={handleSelectHistoryItem}
          />
        );

      case "snippets":
        return <SnippetsLibrary onUseSnippet={handleUseSnippet} />;

      case "export":
        return <Export onTranscriptionComplete={handleUseSnippet} />;

      default:
        return null;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        sessionStats={sessionStats}
        activeNav={activeView as NavItem}
        onNavChange={handleNavChange}
        onOpenSettings={handleOpenSettings}
      />
      <main className="main-content">{renderView()}</main>
      {showSettings && (
        <Suspense fallback={<div className="modal-overlay modal-loading">Cargando...</div>}>
          <Settings onClose={() => setShowSettings(false)} />
        </Suspense>
      )}
    </div>
  );
}

function App() {
  return (
    <>
      <BackendInitializer>
        <AppContent />
      </BackendInitializer>
    </>
  );
}

export default App;
