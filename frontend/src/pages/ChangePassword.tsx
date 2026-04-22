import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function ChangePassword() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    setLoading(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      setSuccess("Password updated. Redirecting to dashboard...");
      setTimeout(() => navigate("/"), 700);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.join("; ") : detail || "Password update failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <form onSubmit={onSubmit} className="w-full max-w-lg bg-gray-800 rounded-2xl p-8 shadow-xl">
        <h1 className="text-2xl font-bold text-white">Change Password</h1>
        <p className="text-gray-400 text-sm mt-1">
          {user?.must_change_password
            ? "You must change your password before continuing."
            : "Update your account password."}
        </p>

        {error && <div className="mt-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200">{error}</div>}
        {success && (
          <div className="mt-4 p-3 bg-green-900/40 border border-green-700 rounded-lg text-green-200">{success}</div>
        )}

        <div className="mt-6 space-y-4">
          <div>
            <label className="block text-sm text-gray-300 mb-1">Current password</label>
            <input
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1">New password</label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1">Confirm new password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg"
        >
          {loading ? "Updating..." : "Update password"}
        </button>
      </form>
    </div>
  );
}
