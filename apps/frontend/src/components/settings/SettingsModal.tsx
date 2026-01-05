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

import React, { useState, useEffect } from "react";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { invoke } from "@tauri-apps/api/core";
import { AppConfigSchema, type AppConfigSchemaInputType } from "../../schemas/config";
import { SettingsLayout } from "./SettingsLayout";
import { GeneralSection } from "./GeneralSection";
import { AdvancedSection } from "./AdvancedSection";
import { Toast } from "../Toast";
import { SETTINGS_CLOSE_DELAY_MS } from "../../constants";

interface SettingsModalProps {
  onClose: () => void;
}

const SettingsSkeleton = () => (
  <div className="modal-overlay">
    <div className="modal-content settings-modal">
      <div className="settings-sidebar">
        <div className="settings-sidebar-header">
          <div className="skeleton skeleton-text" style={{ width: "60%" }}></div>
        </div>
        <div className="settings-nav">
          <div className="skeleton" style={{ height: "40px", width: "100%" }}></div>
          <div className="skeleton" style={{ height: "40px", width: "100%" }}></div>
        </div>
      </div>
      <div className="settings-main">
        <div className="settings-header">
          <div className="skeleton skeleton-text" style={{ width: "40%" }}></div>
        </div>
        <div className="settings-body">
          <div className="skeleton skeleton-input" style={{ marginBottom: "20px" }}></div>
          <div className="skeleton skeleton-input"></div>
        </div>
      </div>
    </div>
  </div>
);

/**
 * Modal de Configuración (SettingsModal).
 *
 * Gestiona el estado global del formulario de configuración, la carga inicial
 * desde el backend y el guardado de cambios. Utiliza `react-hook-form` con
 * validación Zod para asegurar la integridad de los datos.
 */
export const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState<"general" | "advanced">("general");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const methods = useForm<AppConfigSchemaInputType>({
    resolver: zodResolver(AppConfigSchema),
    mode: "onBlur",
  });

  // Cargar configuración al montar
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await invoke<string | { config: AppConfigSchemaInputType }>("get_config");

        let loadedConfig = {};
        if (typeof res === "string") {
             const data = JSON.parse(res);
             loadedConfig = data.config || {};
        } else {
             loadedConfig = (res as any).config || {};
        }

        methods.reset(loadedConfig);
      } catch (e) {
        console.error("Error cargando configuración:", e);
        setToast({ message: "Error cargando configuración", type: "error" });
      } finally {
        setIsLoading(false);
      }
    };
    loadConfig();
  }, []);

  // Manejar tecla ESC para cerrar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const onSubmit = async (data: AppConfigSchemaInputType) => {
    setIsSaving(true);
    try {
      await invoke("update_config", { updates: data });
      setToast({ message: "Configuración guardada", type: "success" });
      setTimeout(() => {
        setIsSaving(false);
        onClose();
      }, SETTINGS_CLOSE_DELAY_MS);
    } catch (error) {
      console.error("Fallo al actualizar configuración:", error);
      setIsSaving(false);
      setToast({ message: `Error al guardar: ${error}`, type: "error" });
    }
  };

  if (isLoading) return <SettingsSkeleton />;

  return (
    <FormProvider {...methods}>
      <SettingsLayout
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onClose={onClose}
        isSaving={isSaving}
        onSave={methods.handleSubmit(onSubmit)}
      >
        {toast && (
          <div className="settings-toast-container">
            <Toast
              message={toast.message}
              type={toast.type}
              onDismiss={() => setToast(null)}
              duration={3000}
            />
          </div>
        )}

        {activeTab === "general" ? <GeneralSection /> : <AdvancedSection />}
      </SettingsLayout>
    </FormProvider>
  );
};
