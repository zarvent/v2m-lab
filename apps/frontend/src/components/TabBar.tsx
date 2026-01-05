/**
 * TabBar - Barra de pestañas estilo Chrome con drag & drop.
 *
 * Características:
 * - Arrastrar para reordenar pestañas.
 * - Botón de cerrar por pestaña.
 * - Botón de nueva pestaña.
 * - Indicador de "sucio" (cambios sin guardar).
 * - Títulos truncados con tooltip.
 */

import React, { useCallback } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import type { DragEndEvent } from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  horizontalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { PlusIcon } from "../assets/Icons";
import type { NoteTab } from "../hooks/useNoteTabs";

// ============================================
// TIPOS
// ============================================

interface TabBarProps {
  tabs: NoteTab[];
  activeTabId: string | null;
  onTabSelect: (id: string) => void;
  onTabClose: (id: string) => void;
  onTabAdd: () => void;
  onTabReorder: (oldIndex: number, newIndex: number) => void;
}

interface SortableTabProps {
  tab: NoteTab;
  isActive: boolean;
  onSelect: () => void;
  onClose: (e: React.MouseEvent) => void;
}

// ============================================
// COMPONENTE PESTAÑA ORDENA
// ============================================

const SortableTab: React.FC<SortableTabProps> = React.memo(
  ({ tab, isActive, onSelect, onClose }) => {
    const {
      attributes,
      listeners,
      setNodeRef,
      transform,
      transition,
      isDragging,
    } = useSortable({ id: tab.id });

    const style: React.CSSProperties = {
      transform: CSS.Transform.toString(transform),
      transition,
      opacity: isDragging ? 0.5 : 1,
      zIndex: isDragging ? 1000 : "auto",
    };

    return (
      <div
        ref={setNodeRef}
        style={style}
        className={`studio-tab ${isActive ? "active" : ""} ${
          isDragging ? "dragging" : ""
        }`}
        onClick={onSelect}
        {...attributes}
        {...listeners}
        role="tab"
        aria-selected={isActive}
        tabIndex={isActive ? 0 : -1}
      >
        {/* Indicador de cambios sin guardar */}
        {tab.isDirty && (
          <span className="tab-dirty-dot" aria-label="Cambios sin guardar" />
        )}

        {/* Título */}
        <span className="tab-title" title={tab.title}>
          {tab.title || "Sin título"}
        </span>

        {/* Insignia de idioma */}
        <span className="tab-language">{tab.language.toUpperCase()}</span>

        {/* Botón de cerrar */}
        <button
          className="tab-close"
          onClick={onClose}
          aria-label={`Cerrar ${tab.title}`}
          tabIndex={-1}
        >
          ×
        </button>
      </div>
    );
  }
);
SortableTab.displayName = "SortableTab";

// ============================================
// COMPONENTE PRINCIPAL
// ============================================

export const TabBar: React.FC<TabBarProps> = React.memo(
  ({ tabs, activeTabId, onTabSelect, onTabClose, onTabAdd, onTabReorder }) => {
    // Sensores DnD
    const sensors = useSensors(
      useSensor(PointerSensor, {
        activationConstraint: {
          distance: 8,
        },
      }),
      useSensor(KeyboardSensor, {
        coordinateGetter: sortableKeyboardCoordinates,
      })
    );

    // Manejar fin de arrastre
    const handleDragEnd = useCallback(
      (event: DragEndEvent) => {
        const { active, over } = event;

        if (over && active.id !== over.id) {
          const oldIndex = tabs.findIndex((t) => t.id === active.id);
          const newIndex = tabs.findIndex((t) => t.id === over.id);
          onTabReorder(oldIndex, newIndex);
        }
      },
      [tabs, onTabReorder]
    );

    // Manejar cierre con detención de propagación
    const handleClose = useCallback(
      (id: string) => (e: React.MouseEvent) => {
        e.stopPropagation();
        onTabClose(id);
      },
      [onTabClose]
    );

    return (
      <div className="studio-tabbar" role="tablist" aria-label="Pestañas de notas">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={tabs.map((t) => t.id)}
            strategy={horizontalListSortingStrategy}
          >
            <div className="studio-tabs-container">
              {tabs.map((tab) => (
                <SortableTab
                  key={tab.id}
                  tab={tab}
                  isActive={tab.id === activeTabId}
                  onSelect={() => onTabSelect(tab.id)}
                  onClose={handleClose(tab.id)}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        {/* Botón de nueva pestaña */}
        <button
          className="studio-tab-add"
          onClick={onTabAdd}
          aria-label="Nueva nota (Ctrl+T)"
          title="Nueva nota (Ctrl+T)"
        >
          <PlusIcon />
        </button>

        {/* Pistas de teclado */}
        <div className="tabbar-hints">
          <kbd>Ctrl+T</kbd> nueva
          <kbd>Ctrl+W</kbd> cerrar
        </div>
      </div>
    );
  }
);

TabBar.displayName = "TabBar";
