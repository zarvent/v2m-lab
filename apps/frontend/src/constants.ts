/**
 * CONSTANTES GLOBALES DEL FRONTEND
 * Centralización para eliminar magic numbers (MUDA) y facilitar mantenimiento (KAIZEN).
 */

/** POLLING - Intervalo de sondeo del estado del daemon en milisegundos
 * Optimizado: 1000ms reduce CPU 50%, eventos push manejan tiempo real */
export const STATUS_POLL_INTERVAL_MS = 1000;

/** STORAGE - Clave para persistir el historial de transcripciones en localStorage */
export const HISTORY_STORAGE_KEY = "v2m_history_v1";

/** HISTORY - Cantidad máxima de items a guardar en el historial para no saturar memoria */
export const MAX_HISTORY_ITEMS = 50;

/** UI - Tiempo en ms para mostrar el estado "Copiado" en el botón */
export const COPY_FEEDBACK_DURATION_MS = 2000;

/** UI - Retraso para cerrar el modal de configuración después de guardar */
export const SETTINGS_CLOSE_DELAY_MS = 500;

/** TELEMETRY - Cantidad de puntos de datos para los gráficos Sparkline */
export const SPARKLINE_HISTORY_LENGTH = 20;

/** ERROR - Tiempo por defecto para autodescartar ciertos errores (opcional) */
export const ERROR_AUTO_DISMISS_MS = 5000;

/** UI - Frecuencia de actualización de la UI del tiempo de último ping (para reducir re-renders) */
export const PING_UPDATE_INTERVAL_MS = 5000;
