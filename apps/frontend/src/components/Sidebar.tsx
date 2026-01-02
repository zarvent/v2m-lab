import React, { useCallback, useState, useEffect } from "react";
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
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  MicIcon,
  DashboardIcon,
  DescriptionIcon,
  CodeIcon,
  SettingsIcon,
  DragHandleIcon,
  StudioIcon,
  GithubIcon,
} from "../assets/Icons";

export type NavItem =
  | "studio"
  | "overview"
  | "transcriptions"
  | "snippets"
  | "settings";

interface SessionStats {
  duration: string;
  words: number;
  confidence: string;
  confidencePercent: number;
}

interface SidebarProps {
  sessionStats: SessionStats;
  activeNav?: NavItem;
  onNavChange?: (nav: NavItem) => void;
  onOpenSettings?: () => void;
}

// Nav item definition
interface NavItemDef {
  id: NavItem;
  label: string;
  Icon: React.FC;
}

// Static nav items - Settings is fixed at bottom, not draggable
const SORTABLE_NAV_ITEMS: NavItemDef[] = [
  { id: "studio", label: "Studio", Icon: StudioIcon },
  { id: "overview", label: "Overview", Icon: DashboardIcon },
  { id: "transcriptions", label: "Transcriptions", Icon: DescriptionIcon },
  { id: "snippets", label: "Snippets Library", Icon: CodeIcon },
];

const FIXED_NAV_ITEM: NavItemDef = {
  id: "settings",
  label: "Settings",
  Icon: SettingsIcon,
};

const NAV_ORDER_STORAGE_KEY = "v2m_nav_order_v1";

// Get default order as IDs
const getDefaultOrder = (): NavItem[] =>
  SORTABLE_NAV_ITEMS.map((item) => item.id);

// Load order from localStorage
const loadNavOrder = (): NavItem[] => {
  try {
    const saved = localStorage.getItem(NAV_ORDER_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as NavItem[];
      // Validate that all items exist
      const validIds = new Set(SORTABLE_NAV_ITEMS.map((i) => i.id));
      if (
        parsed.every((id) => validIds.has(id)) &&
        parsed.length === SORTABLE_NAV_ITEMS.length
      ) {
        return parsed;
      }
    }
  } catch {
    // Ignore parse errors
  }
  return getDefaultOrder();
};

// Save order to localStorage
const saveNavOrder = (order: NavItem[]) => {
  localStorage.setItem(NAV_ORDER_STORAGE_KEY, JSON.stringify(order));
};

// --- SORTABLE NAV ITEM COMPONENT ---

interface SortableNavItemProps {
  item: NavItemDef;
  isActive: boolean;
  onClick: (e: React.MouseEvent<HTMLAnchorElement>) => void;
}

const SortableNavItem: React.FC<SortableNavItemProps> = ({
  item,
  isActive,
  onClick,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: item.id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1000 : "auto",
  };

  const { Icon } = item;

  return (
    <a
      ref={setNodeRef}
      style={style}
      href="#"
      data-nav={item.id}
      className={`nav-item${isActive ? " active" : ""}${
        isDragging ? " dragging" : ""
      }`}
      onClick={onClick}
      aria-current={isActive ? "page" : undefined}
    >
      <span
        className="nav-drag-handle"
        {...attributes}
        {...listeners}
        aria-label={`Drag to reorder ${item.label}`}
      >
        <DragHandleIcon />
      </span>
      <Icon />
      <span>{item.label}</span>
    </a>
  );
};

// --- MAIN SIDEBAR COMPONENT ---

export const Sidebar: React.FC<SidebarProps> = React.memo(
  ({ sessionStats, activeNav = "studio", onNavChange, onOpenSettings }) => {
    const [navOrder, setNavOrder] = useState<NavItem[]>(loadNavOrder);

    // Persist order changes
    useEffect(() => {
      saveNavOrder(navOrder);
    }, [navOrder]);

    // DnD sensors
    const sensors = useSensors(
      useSensor(PointerSensor, {
        activationConstraint: {
          distance: 8, // 8px movement before drag starts
        },
      }),
      useSensor(KeyboardSensor, {
        coordinateGetter: sortableKeyboardCoordinates,
      })
    );

    // Handle drag end
    const handleDragEnd = useCallback((event: DragEndEvent) => {
      const { active, over } = event;

      if (over && active.id !== over.id) {
        setNavOrder((items) => {
          const oldIndex = items.indexOf(active.id as NavItem);
          const newIndex = items.indexOf(over.id as NavItem);
          return arrayMove(items, oldIndex, newIndex);
        });
      }
    }, []);

    // Single event handler using data attribute
    const handleNavClick = useCallback(
      (e: React.MouseEvent<HTMLAnchorElement>) => {
        e.preventDefault();
        const nav = e.currentTarget.dataset.nav as NavItem;
        if (nav === "settings") {
          onOpenSettings?.();
        } else {
          onNavChange?.(nav);
        }
      },
      [onNavChange, onOpenSettings]
    );

    // Get ordered nav items
    const orderedNavItems = navOrder
      .map((id) => SORTABLE_NAV_ITEMS.find((item) => item.id === id)!)
      .filter(Boolean);

    return (
      <aside className="app-sidebar">
        {/* Logo / Brand */}
        <div className="sidebar-brand">
          <div className="brand-logo">
            <MicIcon />
          </div>
          <span className="brand-text">Voice2Machine</span>
        </div>

        {/* Navigation - Sortable Items */}
        <nav className="sidebar-nav">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={navOrder}
              strategy={verticalListSortingStrategy}
            >
              {orderedNavItems.map((item) => (
                <SortableNavItem
                  key={item.id}
                  item={item}
                  isActive={activeNav === item.id}
                  onClick={handleNavClick}
                />
              ))}
            </SortableContext>
          </DndContext>

          {/* Fixed Settings Item (not draggable) */}
          <div className="nav-separator" />
          <a
            href="#"
            data-nav={FIXED_NAV_ITEM.id}
            className={`nav-item nav-item-fixed${
              activeNav === "settings" ? " active" : ""
            }`}
            onClick={handleNavClick}
            aria-current={activeNav === "settings" ? "page" : undefined}
          >
            <FIXED_NAV_ITEM.Icon />
            <span>{FIXED_NAV_ITEM.label}</span>
          </a>
        </nav>

        {/* Session Stats */}
        <div className="session-stats">
          <h3 className="stats-title">Current Session</h3>

          <div className="stat-row">
            <span className="stat-label">Duration</span>
            <span className="stat-value mono">{sessionStats.duration}</span>
          </div>

          <div className="stat-row">
            <span className="stat-label">Words</span>
            <span className="stat-value mono">{sessionStats.words}</span>
          </div>

          <div className="stat-row">
            <span className="stat-label">Confidence</span>
            <div className="confidence-meter">
              <div className="meter-track">
                <div
                  className="meter-fill"
                  style={{ width: `${sessionStats.confidencePercent}%` }}
                />
              </div>
              <span className="confidence-value">
                {sessionStats.confidence}
              </span>
            </div>
          </div>
        </div>

        {/* GitHub Footer */}
        <div className="sidebar-footer">
          <a
            href="https://github.com/zarvent/voice2machine"
            target="_blank"
            rel="noopener noreferrer"
            className="github-link"
            aria-label="View source on GitHub"
          >
            <GithubIcon />
            <span>GitHub</span>
          </a>
        </div>
      </aside>
    );
  }
);

Sidebar.displayName = "Sidebar";
