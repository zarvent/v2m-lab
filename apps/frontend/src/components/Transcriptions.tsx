import React, { useState, useCallback, useMemo } from "react";
import type { HistoryItem } from "../types";
import { CopyIcon, TrashIcon, DescriptionIcon } from "../assets/Icons";
import { COPY_FEEDBACK_DURATION_MS } from "../constants";
import { countWords, formatRelativeTime } from "../utils";

interface TranscriptionsProps {
  history: HistoryItem[];
  onDeleteItem?: (id: string) => void;
  onSelectItem?: (item: HistoryItem) => void;
}

/**
 * Transcriptions - Vista de historial de transcripciones pasadas.
 *
 * Muestra todas las transcripciones almacenadas en localStorage con:
 * - Marca de tiempo (relativa)
 * - Conteo de palabras
 * - Etiqueta de fuente (grabación vs refinamiento)
 * - Acciones de copiar y eliminar
 */
export const Transcriptions: React.FC<TranscriptionsProps> = React.memo(
  ({ history, onDeleteItem, onSelectItem }) => {
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");

    // Filtrar historial basado en la búsqueda
    const filteredHistory = useMemo(() => {
      if (!searchQuery.trim()) return history;
      const query = searchQuery.toLowerCase();
      return history.filter((item) => item.text.toLowerCase().includes(query));
    }, [history, searchQuery]);

    const handleCopy = useCallback((item: HistoryItem) => {
      navigator.clipboard.writeText(item.text);
      setCopiedId(item.id);
      setTimeout(() => setCopiedId(null), COPY_FEEDBACK_DURATION_MS);
    }, []);

    const handleToggleExpand = useCallback((id: string) => {
      setExpandedId((prev) => (prev === id ? null : id));
    }, []);

    const handleDelete = useCallback(
      (id: string) => {
        onDeleteItem?.(id);
      },
      [onDeleteItem]
    );

    const handleSelect = useCallback(
      (item: HistoryItem) => {
        onSelectItem?.(item);
      },
      [onSelectItem]
    );

    if (history.length === 0) {
      return (
        <div className="transcriptions-empty">
          <div className="empty-icon">
            <DescriptionIcon />
          </div>
          <h3>Aún no hay transcripciones</h3>
          <p>
            Tu historial de transcripciones aparecerá aquí. Empieza a grabar en el
            Studio para crear tu primera transcripción.
          </p>
        </div>
      );
    }

    return (
      <div className="transcriptions-container">
        {/* Barra de Búsqueda */}
        <div className="transcriptions-search">
          <input
            type="text"
            placeholder="Buscar transcripciones..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            aria-label="Buscar transcripciones"
          />
          <span className="search-count">
            {filteredHistory.length} de {history.length}
          </span>
        </div>

        {/* Lista de Transcripciones */}
        <div className="transcriptions-list">
          {filteredHistory.map((item) => {
            const wordCount = countWords(item.text);
            const isExpanded = expandedId === item.id;
            const isCopied = copiedId === item.id;

            return (
              <div
                key={item.id}
                className={`transcription-item ${isExpanded ? "expanded" : ""}`}
              >
                {/* Cabecera */}
                <div
                  className="transcription-header"
                  onClick={() => handleToggleExpand(item.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleToggleExpand(item.id);
                    }
                  }}
                  aria-expanded={isExpanded}
                >
                  <div className="transcription-meta">
                    <span className="transcription-time">
                      {formatRelativeTime(item.timestamp)}
                    </span>
                    <span className={`transcription-source ${item.source}`}>
                      {item.source === "recording" ? "Grabación" : "Refinado"}
                    </span>
                    <span className="transcription-words mono">
                      {wordCount} palabras
                    </span>
                  </div>
                  <div className="transcription-preview">
                    {item.text.slice(0, 80)}
                    {item.text.length > 80 ? "..." : ""}
                  </div>
                </div>

                {/* Contenido Expandido */}
                {isExpanded && (
                  <div className="transcription-content">
                    <pre className="transcription-text">{item.text}</pre>
                    <div className="transcription-actions">
                      <button
                        className="btn-transcription-action"
                        onClick={() => handleCopy(item)}
                        aria-label="Copiar transcripción"
                      >
                        <CopyIcon />
                        <span>{isCopied ? "¡Copiado!" : "Copiar"}</span>
                      </button>
                      <button
                        className="btn-transcription-action"
                        onClick={() => handleSelect(item)}
                        aria-label="Abrir en Studio"
                      >
                        <DescriptionIcon />
                        <span>Abrir en Studio</span>
                      </button>
                      {onDeleteItem && (
                        <button
                          className="btn-transcription-action btn-delete"
                          onClick={() => handleDelete(item.id)}
                          aria-label="Eliminar transcripción"
                        >
                          <TrashIcon />
                          <span>Eliminar</span>
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {filteredHistory.length === 0 && searchQuery && (
          <div className="transcriptions-no-results">
            <p>No hay transcripciones que coincidan con "{searchQuery}"</p>
          </div>
        )}
      </div>
    );
  }
);

Transcriptions.displayName = "Transcriptions";
