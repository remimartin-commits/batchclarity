import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { limsApi } from "@/lib/api";
import { Sample } from "@/types";
import { toast } from "@/stores/toastStore";

const statusColour: Record<string, string> = {
  registered:   "bg-gray-100 text-gray-600",
  in_testing:   "bg-blue-100 text-blue-700",
  pending_review: "bg-yellow-100 text-yellow-700",
  released:     "bg-green-100 text-green-700",
  rejected:     "bg-red-100 text-red-700",
  oos:          "bg-orange-100 text-orange-700",
};

function NewSampleModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    sample_type: "in_process",
    description: "",
    batch_number: "",
    required_by: "",
  });

  const SAMPLE_TYPES = [
    { value: "raw_material",      label: "Raw Material" },
    { value: "in_process",        label: "In-Process" },
    { value: "finished_product",  label: "Finished Product" },
    { value: "stability",         label: "Stability" },
    { value: "environmental",     label: "Environmental" },
    { value: "water",             label: "Water" },
    { value: "reference_standard",label: "Reference Standard" },
  ];

  const mutation = useMutation({
    mutationFn: () => limsApi.createSample(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["lims-samples"] });
      toast.success("Sample registered.");
      onClose();
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Failed to register sample."),
  });

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-4">
        <h2 className="text-lg font-bold text-gray-900">Register Sample</h2>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Sample Type
          </label>
          <select
            value={form.sample_type}
            onChange={(e) => setForm({ ...form, sample_type: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {SAMPLE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Batch Number
          </label>
          <input
            value={form.batch_number}
            onChange={(e) => setForm({ ...form, batch_number: e.target.value })}
            placeholder="e.g. BN-2026-001"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Description
          </label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={2}
            placeholder="Sample description, source, etc."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Results Required By
          </label>
          <input
            type="date"
            value={form.required_by}
            onChange={(e) => setForm({ ...form, required_by: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-300 rounded-lg py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !form.sample_type}
            className="flex-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {mutation.isPending ? "Registering…" : "Register Sample"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SampleList() {
  const [showNew, setShowNew] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");

  const { data: samples = [], isLoading } = useQuery<Sample[]>({
    queryKey: ["lims-samples", statusFilter],
    queryFn: () =>
      limsApi.listSamples(statusFilter ? { status_filter: statusFilter } : {}),
  });

  const filtered = samples.filter(
    (s) =>
      !search ||
      s.sample_number?.toLowerCase().includes(search.toLowerCase()) ||
      s.batch_number?.toLowerCase().includes(search.toLowerCase()) ||
      s.description?.toLowerCase().includes(search.toLowerCase())
  );

  // Stats
  const oosCount = samples.filter((s) => s.status === "oos").length;
  const pendingCount = samples.filter((s) => s.status === "pending_review").length;
  const inTestCount = samples.filter((s) => s.status === "in_testing").length;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">LIMS — Samples</h1>
          <p className="text-gray-500 text-sm mt-1">
            Sample registration, testing, and OOS investigation management
          </p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors"
        >
          + Register Sample
        </button>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm px-5 py-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
            <svg className="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">{inTestCount}</div>
            <div className="text-xs text-gray-500">In Testing</div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm px-5 py-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
            <svg className="w-5 h-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">{pendingCount}</div>
            <div className="text-xs text-gray-500">Pending Review</div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm px-5 py-4 flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
            <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">{oosCount}</div>
            <div className="text-xs text-gray-500">OOS Investigations</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap items-center">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search sample #, batch, description…"
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-64"
        />
        <div className="flex gap-2 flex-wrap">
          {["", "registered", "in_testing", "pending_review", "released", "rejected", "oos"].map(
            (s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                  statusFilter === s
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-white text-gray-600 border-gray-200 hover:border-brand-400"
                }`}
              >
                {s === "" ? "All" : s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </button>
            )
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Sample #", "Type", "Batch #", "Description", "Required By", "Received", "Status", "Results"].map(
                (h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="text-center py-8 text-gray-400">
                  Loading samples…
                </td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-8 text-gray-400">
                  No samples found.
                </td>
              </tr>
            ) : (
              filtered.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-4 py-3 font-mono text-brand-600 font-medium text-xs">
                    {s.sample_number}
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-xs capitalize">
                    {s.sample_type.replace(/_/g, " ")}
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-xs font-mono">
                    {s.batch_number ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-700 max-w-xs truncate text-xs">
                    {s.description ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {s.required_by ? new Date(s.required_by).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {s.received_at ? new Date(s.received_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        statusColour[s.status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {s.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {s.results?.length ?? 0} result{(s.results?.length ?? 0) !== 1 ? "s" : ""}
                    {s.results?.some((r) => r.is_oos) && (
                      <span className="ml-1 text-red-500 font-semibold">⚠ OOS</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewSampleModal onClose={() => setShowNew(false)} />}
    </div>
  );
}
