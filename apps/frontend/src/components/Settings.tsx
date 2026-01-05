import React from "react";
import { SettingsModal } from "./settings/SettingsModal";

interface SettingsProps {
  onClose: () => void;
}

/**
 * Punto de Entrada de Configuración.
 *
 * Envuelve el componente modular `SettingsModal`.
 * Actúa como una fachada para el sistema de configuración del frontend.
 */
export const Settings: React.FC<SettingsProps> = (props) => {
  return <SettingsModal {...props} />;
};

Settings.displayName = "Settings";
