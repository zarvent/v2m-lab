/**
 * Contador de palabras O(n) de una sola pasada - sin arrays intermedios.
 * Maneja espacios, tabulaciones, saltos de línea y retornos de carro.
 */
export function countWords(text: string): number {
  let count = 0;
  let inWord = false;
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    // Espacio, tabulación, salto de línea, retorno de carro
    const isSpace = c === 32 || c === 9 || c === 10 || c === 13;
    if (isSpace) {
      inWord = false;
    } else if (!inWord) {
      inWord = true;
      count++;
    }
  }
  return count;
}

/**
 * Formatea un timestamp a una cadena de tiempo relativa (ej. "hace 2h", "justo ahora").
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `hace ${days}d`;
  if (hours > 0) return `hace ${hours}h`;
  if (minutes > 0) return `hace ${minutes}m`;
  return "justo ahora";
}
