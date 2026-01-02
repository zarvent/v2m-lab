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
 * Transcriptions - History view of past transcriptions.
 *
 * Displays all transcriptions stored in localStorage with:
 * - Timestamp (relative time)
 * - Word count
 * - Source badge (recording vs refinement)
 * - Copy and delete actions
 */
export const Transcriptions: React.FC<TranscriptionsProps> = React.memo(
  ({ history, onDeleteItem, onSelectItem }) => {
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");

    // Filter history based on search query
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
          <h3>No transcriptions yet</h3>
          <p>
            Your transcription history will appear here. Start recording in the
            Studio to create your first transcription.
          </p>
        </div>
      );
    }

    return (
      <div className="transcriptions-container">
        {/* Search Bar */}
        <div className="transcriptions-search">
          <input
            type="text"
            placeholder="Search transcriptions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            aria-label="Search transcriptions"
          />
          <span className="search-count">
            {filteredHistory.length} of {history.length}
          </span>
        </div>

        {/* Transcription List */}
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
                {/* Header */}
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
                      {item.source === "recording" ? "Recording" : "Refined"}
                    </span>
                    <span className="transcription-words mono">
                      {wordCount} words
                    </span>
                  </div>
                  <div className="transcription-preview">
                    {item.text.slice(0, 80)}
                    {item.text.length > 80 ? "..." : ""}
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="transcription-content">
                    <pre className="transcription-text">{item.text}</pre>
                    <div className="transcription-actions">
                      <button
                        className="btn-transcription-action"
                        onClick={() => handleCopy(item)}
                        aria-label="Copy transcription"
                      >
                        <CopyIcon />
                        <span>{isCopied ? "Copied!" : "Copy"}</span>
                      </button>
                      <button
                        className="btn-transcription-action"
                        onClick={() => handleSelect(item)}
                        aria-label="Open in Studio"
                      >
                        <DescriptionIcon />
                        <span>Open in Studio</span>
                      </button>
                      {onDeleteItem && (
                        <button
                          className="btn-transcription-action btn-delete"
                          onClick={() => handleDelete(item.id)}
                          aria-label="Delete transcription"
                        >
                          <TrashIcon />
                          <span>Delete</span>
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
            <p>No transcriptions match "{searchQuery}"</p>
          </div>
        )}
      </div>
    );
  }
);

Transcriptions.displayName = "Transcriptions";
