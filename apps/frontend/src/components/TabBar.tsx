/**
 * TabBar - Chrome-style tab bar with drag & drop
 *
 * Features:
 * - Drag to reorder tabs
 * - Close button per tab
 * - New tab button
 * - Dirty indicator (unsaved changes)
 * - Truncated titles with tooltip
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
// TYPES
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
// SORTABLE TAB COMPONENT
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
        {/* Dirty indicator */}
        {tab.isDirty && (
          <span className="tab-dirty-dot" aria-label="Unsaved changes" />
        )}

        {/* Title */}
        <span className="tab-title" title={tab.title}>
          {tab.title || "Untitled"}
        </span>

        {/* Language badge */}
        <span className="tab-language">{tab.language.toUpperCase()}</span>

        {/* Close button */}
        <button
          className="tab-close"
          onClick={onClose}
          aria-label={`Close ${tab.title}`}
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
// MAIN COMPONENT
// ============================================

export const TabBar: React.FC<TabBarProps> = React.memo(
  ({ tabs, activeTabId, onTabSelect, onTabClose, onTabAdd, onTabReorder }) => {
    // DnD sensors
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

    // Handle drag end
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

    // Handle close with stop propagation
    const handleClose = useCallback(
      (id: string) => (e: React.MouseEvent) => {
        e.stopPropagation();
        onTabClose(id);
      },
      [onTabClose]
    );

    return (
      <div className="studio-tabbar" role="tablist" aria-label="Note tabs">
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

        {/* Add new tab button */}
        <button
          className="studio-tab-add"
          onClick={onTabAdd}
          aria-label="New note (Ctrl+T)"
          title="New note (Ctrl+T)"
        >
          <PlusIcon />
        </button>

        {/* Keyboard hints */}
        <div className="tabbar-hints">
          <kbd>Ctrl+T</kbd> new
          <kbd>Ctrl+W</kbd> close
        </div>
      </div>
    );
  }
);

TabBar.displayName = "TabBar";
