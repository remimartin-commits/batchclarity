import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function Security() {
  const user = useAuthStore((s) => s.user);
  const accessToken = useAuthStore((s) => s.accessToken);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const setUser = useAuthStore((s) => s.setUser);
  const setAuth = useAuthStore((s) => s.setAuth);
  const [code, setCode] = useState("");
  const [uri, setUri] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const enroll = useMutation({
    mutationFn: authApi.mfaEnroll,
    onSuccess: (data: any) => {
      setError("");
      setMessage("MFA secret generated. Add it to your authenticator app, then verify below.");
      setUri(data.provisioning_uri || "");
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to enroll MFA.");
    },
  });

  const verify = useMutation({
    mutationFn: () => authApi.mfaVerify(code),
    onSuccess: async () => {
      setError("");
      setMessage("MFA enabled successfully.");
      const me = await authApi.me();
      if (accessToken && refreshToken) {
        setAuth(me, accessToken, refreshToken);
      } else {
        setUser(me);
      }
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "MFA verification failed.");
    },
  });

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Security</h1>
        <p className="text-gray-500 mt-1">Manage account security controls.</p>
      </div>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-4">
        <div>
          <p className="text-sm text-gray-500">User</p>
          <p className="font-medium text-gray-900">{user?.username}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">MFA status</p>
          <p className={`font-medium ${user?.is_mfa_enabled ? "text-green-700" : "text-amber-700"}`}>
            {user?.is_mfa_enabled ? "Enabled" : "Not enabled"}
          </p>
        </div>

        {error && <div className="p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">{error}</div>}
        {message && (
          <div className="p-3 rounded-lg bg-green-50 text-green-700 border border-green-200">{message}</div>
        )}

        {!user?.is_mfa_enabled && (
          <>
            <button
              className="bg-brand-600 text-white px-4 py-2 rounded disabled:opacity-50"
              disabled={enroll.isPending}
              onClick={() => enroll.mutate()}
            >
              {enroll.isPending ? "Generating..." : "Enroll MFA"}
            </button>

            {uri && (
              <div className="space-y-2">
                <p className="text-sm text-gray-700">
                  Add this URI to your authenticator app (or generate a QR from it):
                </p>
                <textarea
                  className="w-full border rounded p-2 text-xs font-mono text-gray-700"
                  rows={3}
                  value={uri}
                  readOnly
                />
                <div className="flex gap-2 items-center">
                  <input
                    className="border rounded px-3 py-2"
                    placeholder="Enter 6-digit code"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                  />
                  <button
                    className="px-4 py-2 rounded bg-gray-900 text-white disabled:opacity-50"
                    disabled={verify.isPending || !code}
                    onClick={() => verify.mutate()}
                  >
                    {verify.isPending ? "Verifying..." : "Verify MFA"}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
