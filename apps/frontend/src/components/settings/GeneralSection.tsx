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
          Modelo Whisper (Transcripción)
        </label>
        <p className="form-hint">
          Seleccione el modelo que mejor se adapte a su hardware.
        </p>
        <select
          id="whisper-model"
          className="select"
          {...register("whisper.model")}
        >
          <option value="tiny">Tiny (Rápido, baja precisión)</option>
          <option value="base">Base (Uso general ligero)</option>
          <option value="small">Small (Equilibrado)</option>
          <option value="medium">Medium (Preciso)</option>
          <option value="large-v3-turbo">Large V3 Turbo (Recomendado, alta precisión)</option>
        </select>
      </div>

      <hr className="divider" />

      {/* LLM BACKEND */}
      <div className="form-group">
        <label className="label" htmlFor="llm-backend">
          Backend de Inteligencia Artificial
        </label>
        <p className="form-hint">
          El motor utilizado para refinar y corregir el texto transcrito.
        </p>
        <select
          id="llm-backend"
          className="select"
          {...register("llm.backend")}
        >
          <option value="local">Local (Privado - Llama/Qwen)</option>
          <option value="gemini">Google Gemini (Nube - Mayor calidad)</option>
          <option value="ollama">Ollama (Local - Estructurado)</option>
        </select>
      </div>

      {llmBackend === "gemini" && (
        <div className="form-group bg-surface-alt p-4 rounded-md mt-2">
          <label className="label" htmlFor="gemini-api-key">
            Gemini API Key
          </label>
          <input
            id="gemini-api-key"
            className="input"
            type="password"
            placeholder="Cargada desde variable de entorno"
            disabled
          />
          <small className="text-xs text-muted mt-1 block">
            Configure <code>GOOGLE_API_KEY</code> en su archivo{" "}
            <code>.env</code>.
          </small>
        </div>
      )}

      {llmBackend === "ollama" && (
        <div className="form-group bg-surface-alt p-4 rounded-md mt-2">
          <label className="label" htmlFor="ollama-model">
            Modelo Ollama
          </label>
          <p className="form-hint">
            Seleccione según su disponibilidad de VRAM.
          </p>
          <select
            id="ollama-model"
            className="select"
            {...register("llm.ollama.model")}
          >
            <option value="gemma2:2b">Gemma 2 2B (Gramática, 2GB)</option>
            <option value="phi3.5-mini">Phi 3.5 Mini (Versátil, 3GB)</option>
            <option value="qwen2.5-coder:7b">
              Qwen 2.5 Coder 7B (Código, 5GB)
            </option>
          </select>

          <label className="label mt-3" htmlFor="ollama-keep-alive">
            Gestión de VRAM
          </label>
          <p className="form-hint">Tiempo para mantener el modelo en memoria.</p>
          <select
            id="ollama-keep-alive"
            className="select"
            {...register("llm.ollama.keep_alive")}
          >
            <option value="0m">Liberar inmediatamente (Bajo consumo)</option>
            <option value="5m">5 minutos (Balanceado)</option>
            <option value="30m">30 minutos (Mínima latencia)</option>
          </select>

          <label className="label mt-3" htmlFor="ollama-host">
            Host Ollama
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
