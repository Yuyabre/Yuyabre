import type {
  CreateHouseholdRequest,
  Household,
  JoinHouseholdRequest,
  LoginRequest,
  SignupRequest,
  User,
} from "@/types/users";
import { getApiBaseUrl } from "../utils";

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

export const authApi = {
  signup: (payload: SignupRequest) =>
    request<User>("/auth/signup", {
      method: "POST",
      body: payload,
    }),

  login: (payload: LoginRequest) =>
    request<User>("/auth/login", {
      method: "POST",
      body: payload,
    }),

  getUser: (userId: string) =>
    request<User>(`/auth/users/${encodeURIComponent(userId)}`),

  createHousehold: (userId: string, payload: CreateHouseholdRequest) =>
    request<Household>(`/auth/users/${encodeURIComponent(userId)}/households`, {
      method: "POST",
      body: payload,
    }),

  joinHousehold: (userId: string, payload: JoinHouseholdRequest) =>
    request<unknown>(
      `/auth/users/${encodeURIComponent(userId)}/join-household`,
      {
        method: "POST",
        body: payload,
      }
    ),

  getHousehold: (householdId: string) =>
    request<Household>(`/auth/households/${encodeURIComponent(householdId)}`),

  // Splitwise OAuth methods
  getSplitwiseAuthorizeUrl: (userId: string, callbackUrl: string) => {
    const params = new URLSearchParams({
      user_id: userId,
      callback_url: callbackUrl,
    });
    return request<{ authorize_url: string }>(
      `/auth/splitwise/authorize?${params.toString()}`
    );
  },

  checkSplitwiseStatus: (userId: string) =>
    request<{ user_id: string; authorized: boolean }>(
      `/auth/splitwise/status/${encodeURIComponent(userId)}`
    ),

  handleSplitwiseCallback: (
    userId: string,
    oauthToken: string,
    oauthVerifier: string
  ) =>
    request<{ success: boolean; message: string }>("/auth/splitwise", {
      method: "POST",
      body: {
        user_id: userId,
        oauth_token: oauthToken,
        oauth_verifier: oauthVerifier,
      },
    }),
};

export type { ApiError };
