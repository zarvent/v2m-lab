/*
 * Voice2Machine (V2M) - GUI for voice2machine
 * Copyright (C) 2026 Cesar Sebastian
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

import React, { useEffect, useRef } from "react";
import { Settings, Sliders } from "lucide-react";

interface SettingsLayoutProps {
  activeTab: "general" | "advanced";
  onTabChange: (tab: "general" | "advanced") => void;
  children: React.ReactNode;
  onClose: () => void;
  isSaving: boolean;
  onSave: () => void;
}

export const SettingsLayout: React.FC<SettingsLayoutProps> = ({
  activeTab,
  onTabChange,
  children,
  onClose,
  isSaving,
  onSave,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // Focus Trap Logic
  useEffect(() => {
    const modal = modalRef.current;
    if (!modal) return;

    const focusableElementsString =
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableElements = modal.querySelectorAll<HTMLElement>(
      focusableElementsString
    );

    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key === "Tab") {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }
    };

    modal.addEventListener("keydown", handleTabKey);
    // Initial focus on the active tab or close button if sidebar is hidden
    if (firstElement) firstElement.focus();

    return () => modal.removeEventListener("keydown", handleTabKey);
  }, []);

  return (
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
    >
      <div className="modal-content settings-modal" ref={modalRef}>
        {/* SIDEBAR */}
        <div className="settings-sidebar">
          <div className="settings-sidebar-header">
            <h2 className="settings-title">configuración</h2>
          </div>
          <div role="tablist" aria-orientation="vertical" className="settings-nav">
            <button
              role="tab"
              aria-selected={activeTab === "general"}
              aria-controls="panel-general"
              id="tab-general"
              className={`settings-nav-item ${
                activeTab === "general" ? "active" : ""
              }`}
              onClick={() => onTabChange("general")}
              tabIndex={activeTab === "general" ? 0 : -1}
            >
              <Settings size={18} />
              <span>general</span>
            </button>
            <button
              role="tab"
              aria-selected={activeTab === "advanced"}
              aria-controls="panel-advanced"
              id="tab-advanced"
              className={`settings-nav-item ${
                activeTab === "advanced" ? "active" : ""
              }`}
              onClick={() => onTabChange("advanced")}
              tabIndex={activeTab === "advanced" ? 0 : -1}
            >
              <Sliders size={18} />
              <span>avanzado</span>
            </button>
          </div>
        </div>

        {/* MAIN CONTENT AREA */}
        <div className="settings-main">
          <div className="settings-header">
            <h3>
              {activeTab === "general"
                ? "preferencias generales"
                : "opciones avanzadas"}
            </h3>
            <button onClick={onClose} className="btn-icon" aria-label="cerrar">
              ✕
            </button>
          </div>

          <div
            className="settings-body scrollable"
            role="tabpanel"
            id={`panel-${activeTab}`}
            aria-labelledby={`tab-${activeTab}`}
          >
            {children}
          </div>

          <div className="settings-footer">
            <button
              className="btn-secondary"
              onClick={onClose}
              disabled={isSaving}
            >
              cancelar
            </button>
            <button
              className="btn-primary"
              onClick={onSave}
              disabled={isSaving}
            >
              {isSaving ? "guardando..." : "guardar cambios"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
