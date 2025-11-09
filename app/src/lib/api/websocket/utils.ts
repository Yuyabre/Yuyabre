import { getApiBaseUrl } from "../../utils";

export function buildWebSocketUrl(path: string): string {
  const baseUrl = getApiBaseUrl();

  if (baseUrl) {
    const wsUrl = baseUrl
      .replace(/^http:/, "ws:")
      .replace(/^https:/, "wss:")
      .replace(/\/$/, "");

    return `${wsUrl}${path}`;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;

  return `${protocol}//${host}${path}`;
}

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

