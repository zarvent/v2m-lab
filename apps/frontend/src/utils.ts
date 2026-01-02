/**
 * O(n) single-pass word counter - no intermediate arrays
 * Handles spaces, tabs, newlines, and carriage returns.
 */
export function countWords(text: string): number {
  let count = 0;
  let inWord = false;
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    // Space, tab, newline, carriage return
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
 * Format timestamp to relative time string (e.g. "2h ago", "Just now")
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "Just now";
}
