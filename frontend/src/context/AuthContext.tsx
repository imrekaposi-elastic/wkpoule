import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import api from "../api/client";
import i18n from "../i18n/i18n";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (
    username: string,
    email: string,
    password: string,
    preferredLanguage?: string
  ) => Promise<void>;
  logout: () => void;
  /** Reload /auth/me (e.g. after admin role change). */
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const userRef = useRef<User | null>(null);
  userRef.current = user;

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      api
        .get("/auth/me")
        .then((r) => setUser(r.data))
        .catch(() => {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const onLang = (lng: string) => {
      const u = userRef.current;
      if (!u || lng === u.preferred_language) return;
      api
        .patch<User>("/auth/me/language", { language: lng })
        .then((r) => setUser(r.data))
        .catch(() => {});
    };
    i18n.on("languageChanged", onLang);
    return () => i18n.off("languageChanged", onLang);
  }, []);

  useEffect(() => {
    if (!user?.preferred_language) return;
    const resolved = i18n.resolvedLanguage ?? i18n.language;
    if (resolved !== user.preferred_language) {
      void i18n.changeLanguage(user.preferred_language);
    }
  }, [user?.id, user?.preferred_language]);

  const login = async (username: string, password: string) => {
    const { data } = await api.post("/auth/login", { username, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await api.get("/auth/me");
    setUser(me.data);
  };

  const register = async (
    username: string,
    email: string,
    password: string,
    preferredLanguage = "en"
  ) => {
    await api.post("/auth/register", {
      username,
      email,
      password,
      preferred_language: preferredLanguage,
    });
    await login(username, password);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  const refreshUser = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      const me = await api.get<User>("/auth/me");
      setUser(me.data);
    } catch {
      logout();
    }
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
