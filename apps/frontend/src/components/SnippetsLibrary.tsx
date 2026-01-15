import React, { useState, useCallback, useMemo, useEffect } from "react";
import { CopyIcon, TrashIcon, CodeIcon } from "../assets/Icons";
import { COPY_FEEDBACK_DURATION_MS } from "../constants";
import "../styles/components/snippets.css";

/** Ítem de fragmento almacenado en localStorage */
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
  /** Callback cuando el usuario quiere usar un fragmento en el Studio */
  onUseSnippet?: (text: string) => void;
}

/**
 * SnippetsLibrary - Colección de fragmentos guardados.
 *
 * Gestiona los fragmentos guardados por el usuario desde el Studio:
 * - Ver todos los fragmentos guardados
 * - Buscar y filtrar
 * - Editar título
 * - Copiar o eliminar fragmentos
 * - Usar en Studio
 */
export const SnippetsLibrary: React.FC<SnippetsLibraryProps> = React.memo(
  ({ onUseSnippet }) => {
    const [snippets, setSnippets] = useState<SnippetItem[]>([]);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

    // Cargar fragmentos de localStorage al montar
    useEffect(() => {
      try {
        const saved = localStorage.getItem(SNIPPETS_STORAGE_KEY);
        if (saved) {
          setSnippets(JSON.parse(saved));
        }
      } catch (e) {
        console.error("Fallo al cargar fragmentos de localStorage:", e);
      }
    }, []);

    // Guardar fragmentos en localStorage
    const saveSnippets = useCallback((newSnippets: SnippetItem[]) => {
      setSnippets(newSnippets);
      localStorage.setItem(SNIPPETS_STORAGE_KEY, JSON.stringify(newSnippets));
    }, []);

    // Filtrar fragmentos basado en la búsqueda
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

    // Cerrar confirmación de eliminación con Escape
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
          <h3>No hay fragmentos guardados</h3>
          <p>
            Guarda transcripciones desde el Studio para construir tu biblioteca.
            Usa el botón "Guardar" después de grabar para crear un fragmento.
          </p>
        </div>
      );
    }

    return (
      <div className="snippets-container">
        {/* Barra de Búsqueda */}
        <div className="snippets-search">
          <input
            type="text"
            placeholder="Buscar fragmentos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            aria-label="Buscar fragmentos"
          />
          <span className="search-count">
            {filteredSnippets.length} de {snippets.length}
          </span>
        </div>

        {/* Rejilla de Fragmentos */}
        <div className="snippets-grid">
          {filteredSnippets.map((item) => {
            const isCopied = copiedId === item.id;
            const isEditing = editingId === item.id;
            const isDeleteConfirm = deleteConfirmId === item.id;

            return (
              <div key={item.id} className="snippet-card">
                {/* Cabecera de la Tarjeta */}
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
                      title="Clic para editar título"
                    >
                      {item.title}
                    </h3>
                  )}
                  <span className="snippet-date">
                    {new Date(item.timestamp).toLocaleDateString()}
                  </span>
                </div>

                {/* Contenido de la Tarjeta */}
                <div className="snippet-content">
                  <p className="snippet-preview">
                    {item.text.slice(0, 150)}
                    {item.text.length > 150 ? "..." : ""}
                  </p>
                </div>

                {/* Acciones de la Tarjeta */}
                <div className="snippet-actions">
                  {isEditing ? (
                    <>
                      <button
                        className="btn-snippet-action"
                        onClick={handleSaveEdit}
                      >
                        Guardar
                      </button>
                      <button
                        className="btn-snippet-action"
                        onClick={handleCancelEdit}
                      >
                        Cancelar
                      </button>
                    </>
                  ) : isDeleteConfirm ? (
                    <>
                      <span className="delete-confirm-text">¿Borrar?</span>
                      <button
                        className="btn-snippet-action btn-danger"
                        onClick={() => handleDelete(item.id)}
                      >
                        Sí
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
                        aria-label="Copiar fragmento"
                      >
                        <CopyIcon />
                        <span>{isCopied ? "¡Copiado!" : "Copiar"}</span>
                      </button>
                      {onUseSnippet && (
                        <button
                          className="btn-snippet-action"
                          onClick={() => handleUse(item)}
                          aria-label="Usar en Studio"
                        >
                          Usar
                        </button>
                      )}
                      <button
                        className="btn-snippet-action btn-delete"
                        onClick={() => setDeleteConfirmId(item.id)}
                        aria-label="Eliminar fragmento"
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
            <p>No hay fragmentos que coincidan con "{searchQuery}"</p>
          </div>
        )}
      </div>
    );
  }
);

SnippetsLibrary.displayName = "SnippetsLibrary";

// --- FUNCIONES AUXILIARES PARA USO EXTERNO ---

/**
 * Agrega un nuevo fragmento a localStorage.
 * Llamado desde el componente Studio cuando el usuario guarda.
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
    console.error("Fallo al guardar fragmento:", e);
  }

  return newSnippet;
}

/**
 * Obtiene todos los fragmentos de localStorage.
 */
export function getSnippets(): SnippetItem[] {
  try {
    const saved = localStorage.getItem(SNIPPETS_STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}
