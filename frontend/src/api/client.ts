import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

import { isAuthEndpoint, shouldAttemptRefresh } from "./clientUtils";
import {
  getAccessTokenExpiryMs,
  hasStoredAuthTokens,
  isAccessTokenExpiringSoon,
} from "./tokenStorage";

export { hasStoredAuthTokens } from "./tokenStorage";

const api = axios.create({ baseURL: "/api" });

let refreshPromise: Promise<string> | null = null;
let redirectingToLogin = false;

function refreshAccessToken(): Promise<string> {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) {
    return Promise.reject(new Error("No refresh token"));
  }

  const promise = axios
    .post<{ access_token: string; refresh_token: string }>("/api/auth/refresh", {
      refresh_token: refresh,
    })
    .then(({ data }: AxiosResponse<{ access_token: string; refresh_token: string }>) => {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      return data.access_token;
    })
    .finally(() => {
      refreshPromise = null;
    });

  refreshPromise = promise;
  return promise;
}

/** Refresh before access token expiry so API calls avoid a 401 round-trip. */
export async function ensureFreshAccessToken(): Promise<string | null> {
  const access = localStorage.getItem("access_token");
  const refresh = localStorage.getItem("refresh_token");

  if (!access && !refresh) {
    return null;
  }

  if (access && !isAccessTokenExpiringSoon(access)) {
    return access;
  }

  if (!refresh) {
    return access;
  }

  try {
    return await refreshAccessToken();
  } catch {
    return null;
  }
}

/** Milliseconds until proactive refresh should run (2 min before access token expiry). */
export function msUntilAccessTokenRefresh(): number | null {
  const access = localStorage.getItem("access_token");
  if (!access) return null;
  const expMs = getAccessTokenExpiryMs(access);
  if (expMs === null) return null;
  const refreshAt = expMs - 2 * 60 * 1000;
  return Math.max(0, refreshAt - Date.now());
}

function clearSessionAndRedirectToLogin(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  if (!redirectingToLogin) {
    redirectingToLogin = true;
    window.location.href = "/login";
  }
}

api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  if (isAuthEndpoint(config.url)) {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }

  const token = await ensureFreshAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      shouldAttemptRefresh(original.url)
    ) {
      original._retry = true;
      if (!localStorage.getItem("refresh_token")) {
        return Promise.reject(error);
      }
      try {
        const accessToken = await refreshAccessToken();
        original.headers.Authorization = `Bearer ${accessToken}`;
        return api(original);
      } catch {
        clearSessionAndRedirectToLogin();
      }
    }
    return Promise.reject(error);
  },
);

export default api;
