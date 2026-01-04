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

import React from "react";
import { useFormContext } from "react-hook-form";
import type { AppConfigSchemaInputType } from "../../schemas/config";

export const GeneralSection: React.FC = () => {
  const { register, watch } = useFormContext<AppConfigSchemaInputType>();
  const llmBackend = watch("llm.backend");

  return (
    <div className="settings-section">
      {/* WHISPER MODEL */}
      <div className="form-group">
        <label className="label" htmlFor="whisper-model">
          modelo whisper (transcripción)
        </label>
        <p className="form-hint">
          seleccione el modelo que mejor se adapte a su hardware
        </p>
        <select
          id="whisper-model"
          className="select"
          {...register("whisper.model")}
        >
          <option value="tiny">tiny (rápido, baja precisión)</option>
          <option value="base">base</option>
          <option value="small">small</option>
          <option value="medium">medium</option>
          <option value="large-v3-turbo">large v3 turbo (recomendado)</option>
        </select>
      </div>

      <hr className="divider" />

      {/* LLM BACKEND */}
      <div className="form-group">
        <label className="label" htmlFor="llm-backend">
          backend de inteligencia artificial
        </label>
        <p className="form-hint">
          el motor utilizado para refinar y corregir el texto transcrito
        </p>
        <select
          id="llm-backend"
          className="select"
          {...register("llm.backend")}
        >
          <option value="local">local (privado - llama/qwen)</option>
          <option value="gemini">google gemini (nube - mayor calidad)</option>
          <option value="ollama">ollama (local - estructurado)</option>
        </select>
      </div>

      {llmBackend === "gemini" && (
        <div className="form-group bg-surface-alt p-4 rounded-md mt-2">
          <label className="label" htmlFor="gemini-api-key">
            gemini api key
          </label>
          <input
            id="gemini-api-key"
            className="input"
            type="password"
            placeholder="cargada desde variable de entorno"
            disabled
          />
          <small className="text-xs text-muted mt-1 block">
            configure <code>GOOGLE_API_KEY</code> en su archivo{" "}
            <code>.env</code>
          </small>
        </div>
      )}

      {llmBackend === "ollama" && (
        <div className="form-group bg-surface-alt p-4 rounded-md mt-2">
          <label className="label" htmlFor="ollama-model">
            modelo ollama
          </label>
          <p className="form-hint">
            seleccione según su disponibilidad de VRAM
          </p>
          <select
            id="ollama-model"
            className="select"
            {...register("llm.ollama.model")}
          >
            <option value="gemma2:2b">gemma2:2b (grammar, 2GB)</option>
            <option value="phi3.5-mini">phi3.5-mini (versátil, 3GB)</option>
            <option value="qwen2.5-coder:7b">
              qwen2.5-coder:7b (código, 5GB)
            </option>
          </select>

          <label className="label mt-3" htmlFor="ollama-keep-alive">
            modo VRAM
          </label>
          <p className="form-hint">cuánto tiempo mantener el modelo cargado</p>
          <select
            id="ollama-keep-alive"
            className="select"
            {...register("llm.ollama.keep_alive")}
          >
            <option value="0m">liberar inmediatamente (bajo consumo)</option>
            <option value="5m">5 minutos (balance)</option>
            <option value="30m">30 minutos (mínima latencia)</option>
          </select>

          <label className="label mt-3" htmlFor="ollama-host">
            host ollama
          </label>
          <input
            id="ollama-host"
            className="input"
            type="text"
            placeholder="http://localhost:11434"
            {...register("llm.ollama.host")}
          />
        </div>
      )}
    </div>
  );
};
