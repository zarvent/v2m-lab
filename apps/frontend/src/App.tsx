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
import { useBackend } from "./hooks/useBackend";
import { useTimer } from "./hooks/useTimer";
import { useSnippets } from "./hooks/useSnippets";
import { countWords } from "./utils";
import "./App.css";

const Settings = lazy(() =>
  import("./components/Settings").then((m) => ({ default: m.Settings }))
);

function App() {
  const [backendState, actions] = useBackend();
  const {
    status,
    transcription,
    errorMessage,
    isConnected,
    lastPingTime,
    telemetry,
    cpuHistory,
    ramHistory,
    history,
  } = backendState;
  const timer = useTimer(status);
  const { addSnippet } = useSnippets();

  const [activeView, setActiveView] = useState<NavItem>("studio");
  const [showSettings, setShowSettings] = useState(false);

  // Memoización separada del conteo de palabras para evitar O(n) en cada tick del temporizador
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

  // Referencias directas a métodos de acción estables (sin overhead de wrappers)
  const handleStartRecording = actions.startRecording;
  const handleStopRecording = actions.stopRecording;

  // Atajo global para alternar grabación (Ctrl+Space)
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

  const handleNavChange = useCallback((nav: NavItem) => {
    setActiveView(nav);
  }, []);

  // Guardar fragmento en la biblioteca
  const handleSaveSnippet = useCallback(
    (snippet: { title: string; text: string }) => {
      addSnippet(snippet);
    },
    [addSnippet]
  );

  // Usar fragmento en Studio (desde SnippetsLibrary o Transcriptions)
  const handleUseSnippet = useCallback(
    (text: string) => {
      actions.setTranscription(text);
      setActiveView("studio");
    },
    [actions]
  );

  // Eliminar elemento del historial
  const handleDeleteHistoryItem = useCallback((id: string) => {
    // Esto requiere agregar una acción deleteHistoryItem a useBackend
    // Por ahora, solo lo registramos en consola
    console.log("[App] Eliminar elemento del historial:", id);
  }, []);

  // Seleccionar elemento del historial -> abrir en Studio
  const handleSelectHistoryItem = useCallback(
    (item: { text: string }) => {
      actions.setTranscription(item.text);
      setActiveView("studio");
    },
    [actions]
  );

  // Renderizar contenido de la vista activa
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
            telemetry={telemetry}
            cpuHistory={cpuHistory}
            ramHistory={ramHistory}
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

      default:
        return null;
    }
  };

  return (
    <div className="app-layout">
      {/* Barra lateral con navegación y estadísticas */}
      <Sidebar
        sessionStats={sessionStats}
        activeNav={activeView}
        onNavChange={handleNavChange}
        onOpenSettings={handleOpenSettings}
      />

      {/* Área de contenido principal */}
      <main className="main-content">{renderView()}</main>

      {/* Modal de Configuración */}
      {showSettings && (
        <Suspense
          fallback={
            <div className="modal-overlay modal-loading">Cargando...</div>
          }
        >
          <Settings onClose={() => setShowSettings(false)} />
        </Suspense>
      )}
    </div>
  );
}

export default App;
