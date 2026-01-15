import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

type View = "studio" | "overview" | "transcriptions" | "snippets" | "export" | "settings";

interface UiState {
  activeView: View;
  modals: {
    [key: string]: boolean;
  };
  setActiveView: (view: View) => void;
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
}

export const useUiStore = create<UiState>()(
  devtools(
    (set) => ({
      activeView: "studio",
      modals: {},
      setActiveView: (view) => set({ activeView: view }),
      openModal: (modalId) => set((state) => ({ modals: { ...state.modals, [modalId]: true } })),
      closeModal: (modalId) => set((state) => ({ modals: { ...state.modals, [modalId]: false } })),
    }),
    { name: 'UiStore' }
  )
);
