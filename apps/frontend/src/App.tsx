import {
  useState,
  useCallback,
  useEffect,
  lazy,
  Suspense,
  useMemo,
} from "react";
import { Sidebar } from "./components/Sidebar";
import type { NavItem } from "./components/Sidebar";
import { Studio } from "./components/Studio";
import { Overview } from "./components/Overview";
import { Transcriptions } from "./components/Transcriptions";
import { SnippetsLibrary } from "./components/SnippetsLibrary";
import { Export } from "./components/Export";
import { BackendProvider, useBackendState } from "./context/BackendProvider";
import { useTimer } from "./hooks/useTimer";
import { useSnippets } from "./hooks/useSnippets";
import { countWords } from "./utils";
import "./App.css";

const Settings = lazy(() =>
  import("./components/Settings").then((m) => ({ default: m.Settings }))
);

function AppContent() {
  const {
    status,
    transcription,
    errorMessage,
    isConnected,
    lastPingTime,
    history,
    actions
  } = useBackendState();

  const timer = useTimer(status);
  const { addSnippet } = useSnippets();

  const [activeView, setActiveView] = useState<NavItem>("studio");
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

  // Referencias a acciones
  const handleStartRecording = actions.startRecording;
  const handleStopRecording = actions.stopRecording;

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
            handleStopRecording();
          } else {
            handleStartRecording();
          }
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleStartRecording, handleStopRecording, status]);

  const handleOpenSettings = useCallback(() => setShowSettings(true), []);
  const handleNavChange = useCallback((nav: NavItem) => setActiveView(nav), []);
  const handleSaveSnippet = useCallback(
    (snippet: { title: string; text: string }) => addSnippet(snippet),
    [addSnippet]
  );
  const handleUseSnippet = useCallback(
    (text: string) => {
      actions.setTranscription(text);
      setActiveView("studio");
    },
    [actions]
  );
  const handleDeleteHistoryItem = useCallback((id: string) => {
    console.log("[App] Eliminar elemento del historial:", id);
  }, []);
  const handleSelectHistoryItem = useCallback(
    (item: { text: string }) => {
      actions.setTranscription(item.text);
      setActiveView("studio");
    },
    [actions]
  );

  const renderView = () => {
    switch (activeView) {
      case "studio":
        return (
          <Studio
            status={status}
            transcription={transcription}
            timerFormatted={timer.formatted}
            errorMessage={errorMessage}
            onStartRecording={handleStartRecording}
            onStopRecording={handleStopRecording}
            onClearError={actions.clearError}
            onSaveSnippet={handleSaveSnippet}
            onTranslate={actions.translateText}
          />
        );

      case "overview":
        return (
          <Overview
            status={status}
            isConnected={isConnected}
            lastPingTime={lastPingTime}
            onRestart={actions.restartDaemon}
            onShutdown={actions.shutdownDaemon}
            onResume={actions.togglePause}
          />
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
        activeNav={activeView}
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
    <BackendProvider>
      <AppContent />
    </BackendProvider>
  );
}

export default App;
