import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";

const api = axios.create({ baseURL: "/api" });

let refreshPromise: Promise<string> | null = null;
let redirectingToLogin = false;

function shouldAttemptRefresh(url: string | undefined): boolean {
  if (!url) return true;
  return (
    !url.includes("/auth/login") &&
    !url.includes("/auth/register") &&
    !url.includes("/auth/refresh")
  );
}

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

function clearSessionAndRedirectToLogin(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  if (!redirectingToLogin) {
    redirectingToLogin = true;
    window.location.href = "/login";
  }
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("access_token");
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
