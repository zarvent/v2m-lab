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

import { useState, useEffect, useCallback } from "react";
import { useForm, type UseFormReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { invoke } from "@tauri-apps/api/core";
import { AppConfigSchema, type AppConfigSchemaInputType } from "../schemas/config";

interface UseConfigFormReturn {
  // Use Input type for the form to handle optional/defaults correctly
  form: UseFormReturn<AppConfigSchemaInputType>;
  isLoading: boolean;
  isSaving: boolean;
  saveConfig: () => Promise<void>;
  error: string | null;
}

export function useConfigForm(onSaveSuccess?: () => void): UseConfigFormReturn {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<AppConfigSchemaInputType>({
    resolver: zodResolver(AppConfigSchema),
    mode: "onBlur",
  });

  // Load config
  useEffect(() => {
    let mounted = true;
    const loadConfig = async () => {
      try {
        const res = await invoke<string>("get_config");
        if (!mounted) return;

        let loadedConfig = {};
        if (typeof res === "string") {
             const data = JSON.parse(res);
             loadedConfig = data.config || {};
        } else {
             loadedConfig = (res as any).config || {};
        }

        form.reset(loadedConfig);
      } catch (e) {
        console.error("Error loading config:", e);
        if (mounted) setError("Error loading configuration");
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    loadConfig();
    return () => { mounted = false; };
  }, []);

  const saveConfig = useCallback(async () => {
    // getValues returns the current form state (Input type)
    // When sending to backend, we assume it matches what update_config expects.
    // Zod's .parse() would ensure Output type, but here we take form values directly.
    const data = form.getValues();
    setIsSaving(true);
    setError(null);
    try {
      await invoke("update_config", { updates: data });
      if (onSaveSuccess) onSaveSuccess();
    } catch (e) {
      console.error("Failed to update config:", e);
      setError(`Error saving: ${e}`);
    } finally {
      setIsSaving(false);
    }
  }, [form, onSaveSuccess]);

  return {
    form,
    isLoading,
    isSaving,
    saveConfig,
    error,
  };
}
