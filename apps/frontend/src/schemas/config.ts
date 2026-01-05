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

import { z } from "zod";

/**
 * Esquema Zod para Configuración de Whisper.
 * Define la validación para los parámetros del motor de transcripción.
 */
const WhisperConfigSchema = z.object({
  model: z.string().default("large-v3-turbo"),
  language: z.string().optional(),
  device: z.string().optional(),
  compute_type: z
    .enum(["float16", "int8_float16", "int8"])
    .default("int8_float16"),
  vad_filter: z.boolean().default(true),
  beam_size: z.number().optional(),
  vad_parameters: z
    .object({
      min_silence_duration_ms: z.number().optional(),
      speech_pad_ms: z.number().optional(),
    })
    .optional(),
});

/**
 * Esquema Zod para Configuración de Gemini.
 */
const GeminiConfigSchema = z.object({
  api_key: z.string().optional(), // Generalmente cargada desde env, opcional en updates
  model: z.string().default("gemini-3-flash-preview"), // Coincide con backend config.toml
});

/**
 * Esquema Zod para Configuración de LLM Local.
 */
const LocalLLMConfigSchema = z.object({
  model_path: z.string().optional(),
  max_tokens: z.number().min(64).max(4096).default(512),
});

/**
 * Esquema Zod para Configuración de Ollama.
 */
const OllamaConfigSchema = z.object({
  host: z.string().default("http://localhost:11434"),
  model: z.string().default("gemma2:2b"),
  keep_alive: z.enum(["0m", "5m", "30m"]).default("5m"),
});

/**
 * Esquema Zod para Configuración General de LLM.
 */
const LLMConfigSchema = z.object({
  backend: z.enum(["local", "gemini", "ollama"]).default("local"),
  gemini: GeminiConfigSchema.optional(),
  local: LocalLLMConfigSchema.optional(),
  ollama: OllamaConfigSchema.optional(),
});

/**
 * Esquema Principal de Configuración de la Aplicación.
 *
 * Estructura jerárquica que mapea directamente con `config.toml` en el backend.
 * Se utiliza para validar formularios en el frontend antes de enviar actualizaciones.
 */
export const AppConfigSchema = z.object({
  whisper: WhisperConfigSchema.optional(),
  llm: LLMConfigSchema.optional(),
  paths: z
    .object({
      output_dir: z.string().optional(),
    })
    .optional(),
  notifications: z
    .object({
      auto_dismiss: z.boolean().optional(),
      expire_time_ms: z.number().optional(),
    })
    .optional(),
});

export type AppConfigSchemaType = z.infer<typeof AppConfigSchema>;
export type AppConfigSchemaInputType = z.input<typeof AppConfigSchema>;
