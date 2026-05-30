import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

function parseApiDetail(err: unknown): string | undefined {
  const raw = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
    ?.detail;
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) {
    const msgs = raw
      .map((item) =>
        typeof item === "object" && item !== null && "msg" in item
          ? String((item as { msg: string }).msg)
          : null
      )
      .filter(Boolean) as string[];
    if (msgs.length) return msgs.join(" ");
  }
  return undefined;
}

export default function ForgotPassword() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError(t("register.passwordsMismatch"));
      return;
    }
    if (password.length < 8) {
      setError(t("adminSettings.passwordTooShort"));
      return;
    }
    setLoading(true);
    try {
      await axios.post("/api/auth/reset-password", {
        username,
        email,
        new_password: password,
      });
      setSuccess(true);
    } catch (err: unknown) {
      setError(
        parseApiDetail(err) ?? t("forgotPassword.failed")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <span className="text-6xl">⚽</span>
          <h1 className="mt-4 text-3xl font-bold text-gray-900">
            {t("forgotPassword.title")}
          </h1>
          <p className="mt-2 text-gray-600">{t("forgotPassword.subtitle")}</p>
        </div>

        {success ? (
          <div className="bg-white rounded-xl shadow-lg p-8 space-y-5 text-center">
            <p className="text-emerald-800 text-sm">{t("forgotPassword.success")}</p>
            <Link
              to="/login"
              className="inline-block w-full text-center bg-pitch-600 hover:bg-pitch-700 text-white py-2.5 rounded-lg font-medium transition-colors"
            >
              {t("forgotPassword.backToLogin")}
            </Link>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="bg-white rounded-xl shadow-lg p-8 space-y-5"
          >
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t("login.username")}
              </label>
              <input
                type="text"
                required
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase())}
                autoCapitalize="off"
                autoCorrect="off"
                spellCheck={false}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pitch-600 focus:border-transparent outline-none transition"
                placeholder={t("login.usernamePlaceholder")}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t("register.email")}
              </label>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pitch-600 focus:border-transparent outline-none transition"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t("forgotPassword.newPassword")}
              </label>
              <input
                type="password"
                required
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pitch-600 focus:border-transparent outline-none transition"
                placeholder={t("login.passwordPlaceholder")}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t("register.confirmPassword")}
              </label>
              <input
                type="password"
                required
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pitch-600 focus:border-transparent outline-none transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-pitch-600 hover:bg-pitch-700 text-white py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? t("forgotPassword.submitting") : t("forgotPassword.submit")}
            </button>

            <p className="text-center text-sm text-gray-600">
              <Link to="/login" className="text-pitch-600 hover:text-pitch-700 font-medium">
                {t("forgotPassword.backToLogin")}
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
