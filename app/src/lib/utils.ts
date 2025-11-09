import { clsx, type ClassValue } from "clsx"

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

/**
 * Get the API base URL from environment variables.
 * Falls back to empty string (relative path) if not set.
 */
export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL || "";
}

