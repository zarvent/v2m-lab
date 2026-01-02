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
          precisión de cómputo (quantization)
        </label>
        <p className="form-hint">
          afecta el uso de vram y la velocidad (int8 es más ligero pero
          ligeramente menos preciso)
        </p>
        <select
          id="compute-type"
          className="select"
          {...register("whisper.compute_type")}
        >
          <option value="float16">float16 (alta calidad, mayor vram)</option>
          <option value="int8_float16">int8_float16 (balanceado)</option>
          <option value="int8">int8 (rápido, menor vram)</option>
        </select>
      </div>

      <hr className="divider" />

      {/* VAD FILTER */}
      <div className="form-group form-group--row">
        <div>
          <label className="label" htmlFor="vad-filter">
            filtro de silencio (vad)
          </label>
          <p className="form-hint">
            elimina segmentos de audio sin voz antes de transcribir
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
          máximo de tokens (llm local)
        </label>
        <p className="form-hint">
          longitud máxima de la respuesta generada (valores altos pueden
          ralentizar)
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
