/**
 * useNoteTabs - Hook for managing multiple note tabs
 *
 * Features:
 * - CRUD operations for tabs
 * - Drag & drop reordering
 * - Keyboard shortcuts (Ctrl+T, Ctrl+W)
 * - Persistence in localStorage
 */

import { useState, useCallback, useEffect, useRef } from "react";

// ============================================
// TYPES
// ============================================

export interface NoteTab {
  id: string;
  title: string;
  content: string;
  language: "es" | "en";
  createdAt: number;
  modifiedAt: number;
  isDirty: boolean;
}

export interface UseNoteTabsReturn {
  tabs: NoteTab[];
  activeTabId: string | null;
  activeTab: NoteTab | null;

  // Tab operations
  addTab: (initialContent?: string) => string;
  removeTab: (id: string) => void;
  setActiveTab: (id: string) => void;
  updateTabContent: (id: string, content: string) => void;
  updateTabTitle: (id: string, title: string) => void;
  updateTabLanguage: (id: string, language: "es" | "en") => void;
  reorderTabs: (oldIndex: number, newIndex: number) => void;
  markTabClean: (id: string) => void;

  // Bulk operations
  closeAllTabs: () => void;
  closeOtherTabs: (keepId: string) => void;
}

// ============================================
// CONSTANTS
// ============================================

const STORAGE_KEY = "v2m_note_tabs_v1";
const MAX_TABS = 20;

// ============================================
// HELPERS
// ============================================

/** Generate unique ID */
const generateId = (): string => crypto.randomUUID();

/** Generate default title based on date/time */
const generateDefaultTitle = (): string => {
  const now = new Date();
  return now.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

/** Create a new empty tab */
const createTab = (content = ""): NoteTab => ({
  id: generateId(),
  title: generateDefaultTitle(),
  content,
  language: "es",
  createdAt: Date.now(),
  modifiedAt: Date.now(),
  isDirty: content.length > 0,
});

/** Load tabs from localStorage */
const loadTabs = (): { tabs: NoteTab[]; activeId: string | null } => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as {
        tabs: NoteTab[];
        activeId: string | null;
      };
      if (Array.isArray(parsed.tabs) && parsed.tabs.length > 0) {
        return parsed;
      }
    }
  } catch (e) {
    console.error("[useNoteTabs] Failed to load from localStorage:", e);
  }

  // Create default tab if nothing saved
  const defaultTab = createTab();
  return { tabs: [defaultTab], activeId: defaultTab.id };
};

/** Save tabs to localStorage */
const saveTabs = (tabs: NoteTab[], activeId: string | null): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ tabs, activeId }));
  } catch (e) {
    console.error("[useNoteTabs] Failed to save to localStorage:", e);
  }
};

// ============================================
// HOOK
// ============================================

export function useNoteTabs(): UseNoteTabsReturn {
  // Initialize from localStorage (single parse)
  const [state] = useState(loadTabs);
  const [tabs, setTabs] = useState<NoteTab[]>(state.tabs);
  const [activeTabId, setActiveTabId] = useState<string | null>(state.activeId);

  // Ref to avoid stale closure in keyboard handler
  const tabsRef = useRef(tabs);
  const activeTabIdRef = useRef(activeTabId);

  useEffect(() => {
    tabsRef.current = tabs;
    activeTabIdRef.current = activeTabId;
  }, [tabs, activeTabId]);

  // Persist on change
  useEffect(() => {
    saveTabs(tabs, activeTabId);
  }, [tabs, activeTabId]);

  // --- COMPUTED ---

  const activeTab = tabs.find((t) => t.id === activeTabId) ?? null;

  // --- OPERATIONS ---

  const addTab = useCallback((initialContent = ""): string => {
    const newTab = createTab(initialContent);

    setTabs((prev) => {
      if (prev.length >= MAX_TABS) {
        console.warn(`[useNoteTabs] Max tabs (${MAX_TABS}) reached`);
        return prev;
      }
      return [...prev, newTab];
    });

    setActiveTabId(newTab.id);
    return newTab.id;
  }, []);

  const removeTab = useCallback((id: string) => {
    setTabs((prev) => {
      const idx = prev.findIndex((t) => t.id === id);
      if (idx === -1) return prev;

      const next = prev.filter((t) => t.id !== id);

      // Ensure at least one tab exists
      if (next.length === 0) {
        const newTab = createTab();
        setActiveTabId(newTab.id);
        return [newTab];
      }

      // If closing active tab, switch to adjacent
      if (id === activeTabIdRef.current) {
        const newActiveIdx = Math.min(idx, next.length - 1);
        const newActiveTab = next[newActiveIdx];
        if (newActiveTab) {
          setActiveTabId(newActiveTab.id);
        }
      }

      return next;
    });
  }, []);

  const setActiveTab = useCallback((id: string) => {
    setActiveTabId(id);
  }, []);

  const updateTabContent = useCallback((id: string, content: string) => {
    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === id
          ? { ...tab, content, modifiedAt: Date.now(), isDirty: true }
          : tab
      )
    );
  }, []);

  const updateTabTitle = useCallback((id: string, title: string) => {
    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === id ? { ...tab, title, modifiedAt: Date.now() } : tab
      )
    );
  }, []);

  const updateTabLanguage = useCallback((id: string, language: "es" | "en") => {
    setTabs((prev) =>
      prev.map((tab) =>
        tab.id === id ? { ...tab, language, modifiedAt: Date.now() } : tab
      )
    );
  }, []);

  const reorderTabs = useCallback((oldIndex: number, newIndex: number) => {
    setTabs((prev) => {
      if (oldIndex < 0 || oldIndex >= prev.length) return prev;
      if (newIndex < 0 || newIndex >= prev.length) return prev;
      if (oldIndex === newIndex) return prev;

      const result = [...prev];
      const removed = result.splice(oldIndex, 1)[0];
      if (removed) {
        result.splice(newIndex, 0, removed);
      }
      return result;
    });
  }, []);

  const markTabClean = useCallback((id: string) => {
    setTabs((prev) =>
      prev.map((tab) => (tab.id === id ? { ...tab, isDirty: false } : tab))
    );
  }, []);

  const closeAllTabs = useCallback(() => {
    const newTab = createTab();
    setTabs([newTab]);
    setActiveTabId(newTab.id);
  }, []);

  const closeOtherTabs = useCallback((keepId: string) => {
    setTabs((prev) => {
      const keep = prev.find((t) => t.id === keepId);
      return keep ? [keep] : prev;
    });
    setActiveTabId(keepId);
  }, []);

  // --- KEYBOARD SHORTCUTS ---

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMod = e.ctrlKey || e.metaKey;

      // Ctrl+T: New tab
      if (isMod && e.key === "t") {
        e.preventDefault();
        const newTab = createTab();
        setTabs((prev) => [...prev.slice(0, MAX_TABS - 1), newTab]);
        setActiveTabId(newTab.id);
      }

      // Ctrl+W: Close current tab
      if (isMod && e.key === "w") {
        e.preventDefault();
        const currentId = activeTabIdRef.current;
        if (currentId) {
          removeTab(currentId);
        }
      }

      // Ctrl+Tab: Next tab
      if (isMod && e.key === "Tab" && !e.shiftKey) {
        e.preventDefault();
        const current = tabsRef.current;
        const currentIdx = current.findIndex(
          (t) => t.id === activeTabIdRef.current
        );
        const nextIdx = (currentIdx + 1) % current.length;
        const nextTab = current[nextIdx];
        if (nextTab) {
          setActiveTabId(nextTab.id);
        }
      }

      // Ctrl+Shift+Tab: Previous tab
      if (isMod && e.key === "Tab" && e.shiftKey) {
        e.preventDefault();
        const current = tabsRef.current;
        const currentIdx = current.findIndex(
          (t) => t.id === activeTabIdRef.current
        );
        const prevIdx = (currentIdx - 1 + current.length) % current.length;
        const prevTab = current[prevIdx];
        if (prevTab) {
          setActiveTabId(prevTab.id);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [removeTab]);

  return {
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
    markTabClean,
    closeAllTabs,
    closeOtherTabs,
  };
}
