import React, { useState, useCallback, useMemo, useEffect } from "react";
import { CopyIcon, TrashIcon, CodeIcon } from "../assets/Icons";
import { COPY_FEEDBACK_DURATION_MS } from "../constants";

/** Snippet item stored in localStorage */
export interface SnippetItem {
  id: string;
  timestamp: number;
  text: string;
  title: string;
  language?: "es" | "en";
}

const SNIPPETS_STORAGE_KEY = "v2m_snippets_v1";
const MAX_SNIPPETS = 100;

interface SnippetsLibraryProps {
  /** Callback when user wants to use a snippet in Studio */
  onUseSnippet?: (text: string) => void;
}

/**
 * SnippetsLibrary - Saved fragments collection.
 *
 * Manages snippets saved by the user from the Studio:
 * - View all saved snippets
 * - Search and filter
 * - Edit title
 * - Copy or delete snippets
 * - Use in Studio
 */
export const SnippetsLibrary: React.FC<SnippetsLibraryProps> = React.memo(
  ({ onUseSnippet }) => {
    const [snippets, setSnippets] = useState<SnippetItem[]>([]);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

    // Load snippets from localStorage on mount
    useEffect(() => {
      try {
        const saved = localStorage.getItem(SNIPPETS_STORAGE_KEY);
        if (saved) {
          setSnippets(JSON.parse(saved));
        }
      } catch (e) {
        console.error("Failed to load snippets from localStorage:", e);
      }
    }, []);

    // Save snippets to localStorage
    const saveSnippets = useCallback((newSnippets: SnippetItem[]) => {
      setSnippets(newSnippets);
      localStorage.setItem(SNIPPETS_STORAGE_KEY, JSON.stringify(newSnippets));
    }, []);

    // Filter snippets based on search query
    const filteredSnippets = useMemo(() => {
      if (!searchQuery.trim()) return snippets;
      const query = searchQuery.toLowerCase();
      return snippets.filter(
        (item) =>
          item.title.toLowerCase().includes(query) ||
          item.text.toLowerCase().includes(query)
      );
    }, [snippets, searchQuery]);

    const handleCopy = useCallback((item: SnippetItem) => {
      navigator.clipboard.writeText(item.text);
      setCopiedId(item.id);
      setTimeout(() => setCopiedId(null), COPY_FEEDBACK_DURATION_MS);
    }, []);

    const handleDelete = useCallback(
      (id: string) => {
        const newSnippets = snippets.filter((s) => s.id !== id);
        saveSnippets(newSnippets);
        setDeleteConfirmId(null);
      },
      [snippets, saveSnippets]
    );

    const handleStartEdit = useCallback((item: SnippetItem) => {
      setEditingId(item.id);
      setEditTitle(item.title);
    }, []);

    const handleSaveEdit = useCallback(() => {
      if (!editingId) return;
      const newSnippets = snippets.map((s) =>
        s.id === editingId ? { ...s, title: editTitle } : s
      );
      saveSnippets(newSnippets);
      setEditingId(null);
      setEditTitle("");
    }, [editingId, editTitle, snippets, saveSnippets]);

    const handleCancelEdit = useCallback(() => {
      setEditingId(null);
      setEditTitle("");
    }, []);

    const handleUse = useCallback(
      (item: SnippetItem) => {
        onUseSnippet?.(item.text);
      },
      [onUseSnippet]
    );

    // Close delete confirmation on Escape
    useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          if (deleteConfirmId) setDeleteConfirmId(null);
          if (editingId) handleCancelEdit();
        }
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }, [deleteConfirmId, editingId, handleCancelEdit]);

    if (snippets.length === 0) {
      return (
        <div className="snippets-empty">
          <div className="empty-icon">
            <CodeIcon />
          </div>
          <h3>No snippets saved</h3>
          <p>
            Save transcriptions from the Studio to build your snippet library.
            Use the "Save" button after recording to save a snippet.
          </p>
        </div>
      );
    }

    return (
      <div className="snippets-container">
        {/* Search Bar */}
        <div className="snippets-search">
          <input
            type="text"
            placeholder="Search snippets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            aria-label="Search snippets"
          />
          <span className="search-count">
            {filteredSnippets.length} of {snippets.length}
          </span>
        </div>

        {/* Snippets Grid */}
        <div className="snippets-grid">
          {filteredSnippets.map((item) => {
            const isCopied = copiedId === item.id;
            const isEditing = editingId === item.id;
            const isDeleteConfirm = deleteConfirmId === item.id;

            return (
              <div key={item.id} className="snippet-card">
                {/* Card Header */}
                <div className="snippet-header">
                  {isEditing ? (
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleSaveEdit();
                        if (e.key === "Escape") handleCancelEdit();
                      }}
                      className="snippet-title-input"
                      autoFocus
                    />
                  ) : (
                    <h3
                      className="snippet-title"
                      onClick={() => handleStartEdit(item)}
                      title="Click to edit title"
                    >
                      {item.title}
                    </h3>
                  )}
                  <span className="snippet-date">
                    {new Date(item.timestamp).toLocaleDateString()}
                  </span>
                </div>

                {/* Card Content */}
                <div className="snippet-content">
                  <p className="snippet-preview">
                    {item.text.slice(0, 150)}
                    {item.text.length > 150 ? "..." : ""}
                  </p>
                </div>

                {/* Card Actions */}
                <div className="snippet-actions">
                  {isEditing ? (
                    <>
                      <button
                        className="btn-snippet-action"
                        onClick={handleSaveEdit}
                      >
                        Save
                      </button>
                      <button
                        className="btn-snippet-action"
                        onClick={handleCancelEdit}
                      >
                        Cancel
                      </button>
                    </>
                  ) : isDeleteConfirm ? (
                    <>
                      <span className="delete-confirm-text">Delete?</span>
                      <button
                        className="btn-snippet-action btn-danger"
                        onClick={() => handleDelete(item.id)}
                      >
                        Yes
                      </button>
                      <button
                        className="btn-snippet-action"
                        onClick={() => setDeleteConfirmId(null)}
                      >
                        No
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn-snippet-action"
                        onClick={() => handleCopy(item)}
                        aria-label="Copy snippet"
                      >
                        <CopyIcon />
                        <span>{isCopied ? "Copied!" : "Copy"}</span>
                      </button>
                      {onUseSnippet && (
                        <button
                          className="btn-snippet-action"
                          onClick={() => handleUse(item)}
                          aria-label="Use in Studio"
                        >
                          Use
                        </button>
                      )}
                      <button
                        className="btn-snippet-action btn-delete"
                        onClick={() => setDeleteConfirmId(item.id)}
                        aria-label="Delete snippet"
                      >
                        <TrashIcon />
                      </button>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {filteredSnippets.length === 0 && searchQuery && (
          <div className="snippets-no-results">
            <p>No snippets match "{searchQuery}"</p>
          </div>
        )}
      </div>
    );
  }
);

SnippetsLibrary.displayName = "SnippetsLibrary";

// --- HELPER FUNCTIONS FOR EXTERNAL USE ---

/**
 * Add a new snippet to localStorage.
 * Called from Studio component when user saves.
 */
export function addSnippet(
  snippet: Omit<SnippetItem, "id" | "timestamp">
): SnippetItem {
  const newSnippet: SnippetItem = {
    ...snippet,
    id: crypto.randomUUID(),
    timestamp: Date.now(),
  };

  try {
    const saved = localStorage.getItem(SNIPPETS_STORAGE_KEY);
    const snippets: SnippetItem[] = saved ? JSON.parse(saved) : [];
    const updated = [newSnippet, ...snippets].slice(0, MAX_SNIPPETS);
    localStorage.setItem(SNIPPETS_STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {
    console.error("Failed to save snippet:", e);
  }

  return newSnippet;
}

/**
 * Get all snippets from localStorage.
 */
export function getSnippets(): SnippetItem[] {
  try {
    const saved = localStorage.getItem(SNIPPETS_STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}
