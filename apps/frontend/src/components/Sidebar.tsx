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

// Definición de ítem de navegación
interface NavItemDef {
  id: NavItem;
  label: string;
  Icon: React.FC;
}

// Ítems de navegación estáticos - Ajustes es fijo al final, no arrastrable
const SORTABLE_NAV_ITEMS: NavItemDef[] = [
  { id: "studio", label: "Studio", Icon: StudioIcon },
  { id: "overview", label: "Vista General", Icon: DashboardIcon },
  { id: "transcriptions", label: "Transcripciones", Icon: DescriptionIcon },
  { id: "snippets", label: "Biblioteca", Icon: CodeIcon },
];

const FIXED_NAV_ITEM: NavItemDef = {
  id: "settings",
  label: "Ajustes",
  Icon: SettingsIcon,
};

const NAV_ORDER_STORAGE_KEY = "v2m_nav_order_v1";

// Obtener orden predeterminado como IDs
const getDefaultOrder = (): NavItem[] =>
  SORTABLE_NAV_ITEMS.map((item) => item.id);

// Cargar orden de localStorage
const loadNavOrder = (): NavItem[] => {
  try {
    const saved = localStorage.getItem(NAV_ORDER_STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved) as NavItem[];
      // Validar que todos los ítems existen
      const validIds = new Set(SORTABLE_NAV_ITEMS.map((i) => i.id));
      if (
        parsed.every((id) => validIds.has(id)) &&
        parsed.length === SORTABLE_NAV_ITEMS.length
      ) {
        return parsed;
      }
    }
  } catch {
    // Ignorar errores de análisis
  }
  return getDefaultOrder();
};

// Guardar orden en localStorage
const saveNavOrder = (order: NavItem[]) => {
  localStorage.setItem(NAV_ORDER_STORAGE_KEY, JSON.stringify(order));
};

// --- COMPONENTE NAV ITEM ORDENABLE ---

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
        aria-label={`Arrastrar para reordenar ${item.label}`}
      >
        <DragHandleIcon />
      </span>
      <Icon />
      <span>{item.label}</span>
    </a>
  );
};

// --- COMPONENTE BARRA LATERAL PRINCIPAL ---

export const Sidebar: React.FC<SidebarProps> = React.memo(
  ({ sessionStats, activeNav = "studio", onNavChange, onOpenSettings }) => {
    const [navOrder, setNavOrder] = useState<NavItem[]>(loadNavOrder);

    // Persistir cambios de orden
    useEffect(() => {
      saveNavOrder(navOrder);
    }, [navOrder]);

    // Sensores DnD
    const sensors = useSensors(
      useSensor(PointerSensor, {
        activationConstraint: {
          distance: 8, // 8px de movimiento antes de iniciar arrastre
        },
      }),
      useSensor(KeyboardSensor, {
        coordinateGetter: sortableKeyboardCoordinates,
      })
    );

    // Manejar fin de arrastre
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

    // Manejador de evento único usando atributo data
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

    // Obtener ítems de navegación ordenados
    const orderedNavItems = navOrder
      .map((id) => SORTABLE_NAV_ITEMS.find((item) => item.id === id)!)
      .filter(Boolean);

    return (
      <aside className="app-sidebar">
        {/* Logo / Marca */}
        <div className="sidebar-brand">
          <div className="brand-logo">
            <MicIcon />
          </div>
          <span className="brand-text">Voice2Machine</span>
        </div>

        {/* Navegación - Ítems Ordenables */}
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

          {/* Ítem de Ajustes Fijo (no arrastrable) */}
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

        {/* Estadísticas de Sesión */}
        <div className="session-stats">
          <h3 className="stats-title">Sesión Actual</h3>

          <div className="stat-row">
            <span className="stat-label">Duración</span>
            <span className="stat-value mono">{sessionStats.duration}</span>
          </div>

          <div className="stat-row">
            <span className="stat-label">Palabras</span>
            <span className="stat-value mono">{sessionStats.words}</span>
          </div>

          <div className="stat-row">
            <span className="stat-label">Confianza</span>
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

        {/* Pie de página GitHub */}
        <div className="sidebar-footer">
          <a
            href="https://github.com/zarvent/voice2machine"
            target="_blank"
            rel="noopener noreferrer"
            className="github-link"
            aria-label="Ver código fuente en GitHub"
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
