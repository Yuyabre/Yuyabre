import type { InventoryItem, InventoryItemCreate, InventoryItemUpdate } from "../../types";
import { getApiBaseUrl } from "../utils";

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

interface RequestOptions extends Omit<RequestInit, "body" | "method"> {
  method?: HttpMethod;
  body?: unknown;
}

interface ApiError {
  detail?: Array<{ msg?: string; loc?: (string | number)[] }> | string;
  message?: string;
  error?: string;
}

const defaultHeaders: HeadersInit = {
  "Content-Type": "application/json",
};

const buildUrl = (path: string): string => {
  const baseUrl = getApiBaseUrl().replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
};

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const data = (await response.json()) as ApiError;
    if (typeof data.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      return data.detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join(", ");
    }
    if (data.message) {
      return data.message;
    }
    if (data.error) {
      return data.error;
    }
  } catch (error) {
    console.warn("Failed to parse error response", error);
  }

  return `Request failed with status ${response.status}`;
};

const request = async <T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> => {
  const { method = "GET", body, headers, ...rest } = options;
  const url = buildUrl(path);
  const init: RequestInit = {
    method,
    credentials: "omit",
    headers: {
      ...defaultHeaders,
      ...(headers ?? {}),
    },
    ...rest,
  };

  if (body !== undefined) {
    init.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  const response = await fetch(url, init);
  if (!response.ok) {
    const message = await parseErrorMessage(response);
    throw new Error(message);
  }

  if (response.status === 204 || method === "DELETE") {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
};

/**
 * Inventory API - CRUD operations for inventory items
 */
export const inventoryApi = {
  getAll: async (): Promise<InventoryItem[]> => {
    return request<InventoryItem[]>("/inventory");
  },

  getById: async (itemId: string): Promise<InventoryItem> => {
    return request<InventoryItem>(`/inventory/${encodeURIComponent(itemId)}`);
  },

  create: async (item: InventoryItemCreate): Promise<InventoryItem> => {
    return request<InventoryItem>("/inventory", {
      method: "POST",
      body: item,
    });
  },

  update: async (
    itemId: string,
    updates: InventoryItemUpdate
  ): Promise<InventoryItem> => {
    return request<InventoryItem>(`/inventory/${encodeURIComponent(itemId)}`, {
      method: "PATCH",
      body: updates,
    });
  },

  delete: async (itemId: string): Promise<void> => {
    return request<void>(`/inventory/${encodeURIComponent(itemId)}`, {
      method: "DELETE",
    });
  },

  getLowStock: async (): Promise<InventoryItem[]> => {
    return request<InventoryItem[]>("/inventory/low-stock");
  },
};

