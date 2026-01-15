import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility for merging Tailwind classes with conflict resolution.
 * Uses `clsx` for conditional classes and `tailwind-merge` to handle
 * Tailwind-specific class conflicts (e.g., 'p-2 p-4' -> 'p-4').
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
