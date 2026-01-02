import { useState, useCallback, useEffect } from "react";

export interface SnippetItem {
  id: string;
  timestamp: number;
  text: string;
  title: string;
  language?: "es" | "en";
}

const SNIPPETS_STORAGE_KEY = "v2m_snippets_v1";
const MAX_SNIPPETS = 100;

/**
 * Hook to manage snippets library persistence and operations.
 * Centralizes localStorage logic for snippets.
 */
export function useSnippets() {
  const [snippets, setSnippets] = useState<SnippetItem[]>([]);

  // Load on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(SNIPPETS_STORAGE_KEY);
      if (saved) {
        setSnippets(JSON.parse(saved));
      }
    } catch (e) {
      console.error("Failed to load snippets:", e);
    }
  }, []);

  // Save helper
  const persistSnippets = useCallback((newSnippets: SnippetItem[]) => {
    setSnippets(newSnippets);
    localStorage.setItem(SNIPPETS_STORAGE_KEY, JSON.stringify(newSnippets));
  }, []);

  const addSnippet = useCallback(
    (snippet: Omit<SnippetItem, "id" | "timestamp">) => {
      const newSnippet: SnippetItem = {
        ...snippet,
        id: crypto.randomUUID(),
        timestamp: Date.now(),
      };

      setSnippets((prev) => {
        const updated = [newSnippet, ...prev].slice(0, MAX_SNIPPETS);
        localStorage.setItem(SNIPPETS_STORAGE_KEY, JSON.stringify(updated));
        return updated;
      });

      return newSnippet;
    },
    []
  );

  const deleteSnippet = useCallback(
    (id: string) => {
      const newSnippets = snippets.filter((s) => s.id !== id);
      persistSnippets(newSnippets);
    },
    [snippets, persistSnippets]
  );

  const updateSnippet = useCallback(
    (id: string, updates: Partial<SnippetItem>) => {
      const newSnippets = snippets.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      );
      persistSnippets(newSnippets);
    },
    [snippets, persistSnippets]
  );

  return {
    snippets,
    addSnippet,
    deleteSnippet,
    updateSnippet,
  };
}
