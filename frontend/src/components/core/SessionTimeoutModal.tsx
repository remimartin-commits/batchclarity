import { useState } from "react";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

interface SessionTimeoutModalProps {
  isOpen: boolean;
  onSuccess: () => void;
}

export default function SessionTimeoutModal({ isOpen, onSuccess }: SessionTimeoutModalProps) {
  const user = useAuthStore((s) => s.user);
  const setAuth = useAuthStore((s) => s.setAuth);
  const logout = useAuthStore((s) => s.logout);
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen || !user) return null;

  async function handleRelogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await authApi.login(user.username, password);
      setAuth(data.user, data.tokens.access_token, data.tokens.refresh_token);
      const me = await authApi.me();
      setAuth(me, data.tokens.access_token, data.tokens.refresh_token);
      setPassword("");
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Re-login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await authApi.logout();
    } catch {
      // best-effort logout
    }
    logout();
    window.location.href = "/login";
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
      <form
        onSubmit={handleRelogin}
        className="w-full max-w-md rounded-2xl bg-white shadow-2xl p-6"
      >
        <h2 className="text-lg font-bold text-gray-900">Session Timed Out</h2>
        <p className="text-sm text-gray-500 mt-1">
          30 minutes of inactivity detected. Re-enter your password to continue.
        </p>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Username
          </label>
          <input
            type="text"
            value={user.username}
            disabled
            className="w-full rounded-lg border border-gray-200 bg-gray-100 px-3 py-2 text-sm text-gray-600"
          />
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Re-enter your password"
          />
        </div>

        <div className="mt-5 flex gap-3">
          <button
            type="button"
            onClick={handleLogout}
            className="flex-1 rounded-lg border border-gray-300 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Logout
          </button>
          <button
            type="submit"
            disabled={loading || !password}
            className="flex-1 rounded-lg bg-brand-600 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? "Unlocking..." : "Re-Login"}
          </button>
        </div>
      </form>
    </div>
  );
}

