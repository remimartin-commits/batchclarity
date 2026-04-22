import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { mesApi } from "@/lib/api";
import { BatchRecord, MasterBatchRecord } from "@/types";
import { toast } from "@/stores/toastStore";

const statusColour: Record<string, string> = {
  in_progress:     "bg-blue-100 text-blue-700",
  pending_release: "bg-yellow-100 text-yellow-800",
  released:        "bg-green-100 text-green-700",
  rejected:        "bg-red-100 text-red-700",
};

function NewBatchModal({
  mbrs,
  onClose,
}: {
  mbrs: MasterBatchRecord[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    mbr_id: mbrs[0]?.id ?? "",
    batch_number: "",
    batch_size: "",
    batch_size_unit: "kg",
  });

  const mutation = useMutation({
    mutationFn: () =>
      mesApi.createBatchRecord({
        ...form,
        batch_size: parseFloat(form.batch_size),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["batch-records"] });
      toast.success("Batch record opened.");
      onClose();
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Failed to create batch record."),
  });

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-4">
        <h2 className="text-lg font-bold text-gray-900">Open Batch Record</h2>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Master Batch Record
          </label>
          <select
            value={form.mbr_id}
            onChange={(e) => setForm({ ...form, mbr_id: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {mbrs
              .filter((m) => m.status === "approved")
              .map((m) => (
                <option key={m.id} value={m.id}>
                  {m.mbr_number} — v{m.version} ({m.batch_size} {m.batch_size_unit})
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

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Batch Size
            </label>
            <input
              type="number"
              value={form.batch_size}
              onChange={(e) => setForm({ ...form, batch_size: e.target.value })}
              placeholder="0.0"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="w-24">
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Unit
            </label>
            <select
              value={form.batch_size_unit}
              onChange={(e) => setForm({ ...form, batch_size_unit: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              {["kg", "L", "units", "g"].map((u) => (
                <option key={u}>{u}</option>
              ))}
            </select>
          </div>
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
            disabled={mutation.isPending || !form.mbr_id || !form.batch_number || !form.batch_size}
            className="flex-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {mutation.isPending ? "Opening…" : "Open Batch"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BatchRecordList() {
  const [showNew, setShowNew] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");

  const { data: batches = [], isLoading } = useQuery<BatchRecord[]>({
    queryKey: ["batch-records", statusFilter],
    queryFn: () =>
      mesApi.listBatchRecords(statusFilter ? { status_filter: statusFilter } : {}),
  });

  const { data: mbrs = [] } = useQuery<MasterBatchRecord[]>({
    queryKey: ["mbrs"],
    queryFn: () => mesApi.listMBRs(),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Batch Records</h1>
          <p className="text-gray-500 text-sm mt-1">
            Electronic batch manufacturing records — ALCOA+ compliant
          </p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors"
        >
          + Open Batch
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {["", "in_progress", "pending_release", "released", "rejected"].map((s) => (
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
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Batch #", "MBR Ref", "Batch Size", "Started", "Status", "Decision"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  Loading batch records…
                </td>
              </tr>
            ) : batches.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  No batch records found.
                </td>
              </tr>
            ) : (
              batches.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-brand-600 font-medium">
                    {b.batch_number}
                  </td>
                  <td className="px-4 py-3 text-gray-600 font-mono text-xs">
                    {/* mbr_id short ref */}
                    {b.mbr_id?.slice(0, 8)}…
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {b.batch_size} {b.batch_size_unit}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {b.started_at
                      ? new Date(b.started_at).toLocaleDateString()
                      : b.created_at
                      ? new Date(b.created_at).toLocaleDateString()
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        statusColour[b.status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {b.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs capitalize">
                    {b.release_decision ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewBatchModal mbrs={mbrs} onClose={() => setShowNew(false)} />}
    </div>
  );
}
