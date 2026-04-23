import { useState, useRef, useEffect } from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (username: string, password: string, meaning: string, comments: string) => Promise<void>;
  title?: string;
  description?: string;
  meaning?: string;               // Pre-selected meaning (locks the dropdown)
  availableMeanings?: string[];   // If not pre-selected, user picks from this list
  isLoading?: boolean;
}

const MEANING_LABELS: Record<string, string> = {
  approved:     "I approve this record",
  reviewed:     "I have reviewed this record",
  authored:     "I am the author of this record",
  closed:       "I authorise closing this record",
  released:     "I authorise release of this batch",
  rejected:     "I reject this record",
  witnessed:    "I witnessed this action",
  acknowledged: "I acknowledge this record",
};

// Stable default — must live outside the component so it never creates a new
// array reference on each render (which would re-trigger the reset effect and
// clear the password field after every keystroke).
const DEFAULT_MEANINGS = ["approved", "reviewed"];

export default function SignatureModal({
  isOpen,
  onClose,
  onConfirm,
  title = "Electronic Signature Required",
  description,
  meaning: fixedMeaning,
  availableMeanings = DEFAULT_MEANINGS,
  isLoading = false,
}: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [selectedMeaning, setSelectedMeaning] = useState(
    fixedMeaning ?? availableMeanings[0]
  );
  const [comments, setComments] = useState("");
  const [error, setError] = useState("");
  const passwordRef = useRef<HTMLInputElement>(null);

  // Reset fields and focus password ONLY when the modal opens/closes.
  // Do NOT include availableMeanings or fixedMeaning — those changing at runtime
  // while the modal is open should NOT wipe the password the user is typing.
  useEffect(() => {
    if (isOpen) {
      setPassword("");
      setUsername("");
      setComments("");
      setError("");
      setSelectedMeaning(fixedMeaning ?? availableMeanings[0]);
      setTimeout(() => passwordRef.current?.focus(), 50);
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Username and password are required to apply an electronic signature.");
      return;
    }
    setError("");
    try {
      await onConfirm(username, password, selectedMeaning, comments);
      setPassword("");
      setUsername("");
      setComments("");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Signature failed. Check your password and try again.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop — stop propagation so clicks inside the modal don't bubble to it */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* Modal panel — relative so it stacks above the absolute backdrop */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-gray-900 px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </div>
          <div>
            <h2 className="text-white font-semibold text-sm">{title}</h2>
            <p className="text-gray-400 text-xs">21 CFR Part 11 / EU Annex 11 compliant</p>
          </div>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4" onClick={(e) => e.stopPropagation()}>
          {description && (
            <p className="text-sm text-gray-600 bg-gray-50 rounded-lg px-3 py-2.5">{description}</p>
          )}

          {/* Meaning */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1">
              Signature Meaning
            </label>
            {fixedMeaning ? (
              <div className="px-3 py-2 bg-gray-100 rounded-lg text-sm text-gray-800 font-medium">
                {MEANING_LABELS[fixedMeaning] ?? fixedMeaning}
              </div>
            ) : (
              <select
                value={selectedMeaning}
                onChange={(e) => setSelectedMeaning(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {availableMeanings.map((m) => (
                  <option key={m} value={m}>
                    {MEANING_LABELS[m] ?? m}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Username */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1">
              Username <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Your GMP Platform username"
              autoComplete="username"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1">
              Re-enter Password <span className="text-red-500">*</span>
            </label>
            <input
              ref={passwordRef}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your GMP Platform password"
              autoComplete="current-password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>

          {/* Comments (optional) */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-1">
              Comments <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={2}
              placeholder="Reason for signature, exceptions noted, etc."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Notice */}
          <p className="text-xs text-gray-400 leading-relaxed">
            By submitting this signature you confirm that the information is accurate and you are
            the authorised signatory. This action is cryptographically logged and cannot be undone.
          </p>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="flex-1 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Signing…" : "Apply Signature"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
