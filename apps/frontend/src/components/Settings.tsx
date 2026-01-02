import React from "react";
import { SettingsModal } from "./settings/SettingsModal";

// Re-export interface for compatibility if used elsewhere, though usually just the component is used.
interface SettingsProps {
  onClose: () => void;
}

/**
 * Settings Entry Point.
 * Wraps the new modular SettingsModal.
 */
export const Settings: React.FC<SettingsProps> = (props) => {
  return <SettingsModal {...props} />;
};

Settings.displayName = "Settings";
