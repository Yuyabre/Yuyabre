import { getApiBaseUrl } from "../utils";
import type { Order } from "../../types/orders";

type HttpMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

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
  const baseUrl = getApiBaseUrl();
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = buildUrl(path);
  const { method = "GET", body, headers, ...restOptions } = options;

  const config: RequestInit = {
    method,
    headers: {
      ...defaultHeaders,
      ...headers,
    },
    ...restOptions,
  };

  if (body !== undefined) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      try {
        const errorData: ApiError = await response.json();
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
          errorMessage = errorData.detail[0].msg || errorMessage;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        }
      } catch {
        // If JSON parsing fails, use default error message
      }
      throw new Error(errorMessage);
    }

    // Handle empty responses
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await response.json();
      return data as T;
    }

    // Return empty object for successful responses without body
    return {} as T;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("An unknown error occurred");
  }
}

/**
 * Orders API - Create and track orders
 */
export const ordersApi = {
  /**
   * Get recent order history
   */
  getAll: async (limit: number = 20): Promise<Order[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    return request<Order[]>(`/orders?${params.toString()}`);
  },

  /**
   * Get a specific order by ID
   */
  getById: async (orderId: string): Promise<Order> => {
    return request<Order>(`/orders/${encodeURIComponent(orderId)}`);
  },

  /**
   * Get all orders for a specific user
   */
  getUserOrders: async (userId: string, limit: number = 50): Promise<Order[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    return request<Order[]>(
      `/orders/users/${encodeURIComponent(userId)}?${params.toString()}`
    );
  },

  /**
   * Cancel an order
   */
  cancel: async (orderId: string): Promise<void> => {
    return request<void>(`/orders/${encodeURIComponent(orderId)}/cancel`, {
      method: "POST",
    });
  },
};
