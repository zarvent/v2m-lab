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

export const AdvancedSection: React.FC = () => {
  const {
    register,
    formState: { errors },
  } = useFormContext<AppConfigSchemaInputType>();

  return (
    <div className="settings-section">
      {/* COMPUTE TYPE */}
      <div className="form-group">
        <label className="label" htmlFor="compute-type">
          Precisión de Cómputo (Cuantización)
        </label>
        <p className="form-hint">
          Afecta el uso de VRAM y la velocidad. 'int8' es más ligero pero
          ligeramente menos preciso que 'float16'.
        </p>
        <select
          id="compute-type"
          className="select"
          {...register("whisper.compute_type")}
        >
          <option value="float16">float16 (Alta calidad, mayor VRAM)</option>
          <option value="int8_float16">int8_float16 (Balanceado)</option>
          <option value="int8">int8 (Rápido, menor VRAM)</option>
        </select>
      </div>

      <hr className="divider" />

      {/* VAD FILTER */}
      <div className="form-group form-group--row">
        <div>
          <label className="label" htmlFor="vad-filter">
            Filtro de Silencio (VAD)
          </label>
          <p className="form-hint">
            Elimina segmentos de audio sin voz antes de transcribir para reducir alucinaciones.
          </p>
        </div>
        <label className="toggle-switch">
          <input
            id="vad-filter"
            type="checkbox"
            {...register("whisper.vad_filter")}
          />
          <span className="toggle-track" />
        </label>
      </div>

      <hr className="divider" />

      {/* MAX TOKENS */}
      <div className="form-group">
        <label className="label" htmlFor="max-tokens">
          Máximo de Tokens (LLM Local)
        </label>
        <p className="form-hint">
          Longitud máxima de la respuesta generada. Valores muy altos pueden
          aumentar la latencia.
        </p>
        <input
          id="max-tokens"
          className={`input ${
            errors.llm?.local?.max_tokens ? "input-error" : ""
          }`}
          type="number"
          step="64"
          {...register("llm.local.max_tokens", { valueAsNumber: true })}
        />
        {errors.llm?.local?.max_tokens && (
          <span className="error-message">
            {errors.llm.local.max_tokens.message}
          </span>
        )}
      </div>
    </div>
  );
};
