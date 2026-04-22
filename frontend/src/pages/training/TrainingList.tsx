import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { trainingApi } from "@/lib/api";

export default function TrainingList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [showAssign, setShowAssign] = useState(false);
  const [form, setForm] = useState({ user_id: "", curriculum_item_id: "", due_date: "" });

  const { data: assignments = [], isLoading } = useQuery({
    queryKey: ["training-assignments", statusFilter],
    queryFn: () => trainingApi.listAssignments(statusFilter ? { status_filter: statusFilter } : {}),
  });
  const { data: curricula = [] } = useQuery({
    queryKey: ["training-curricula"],
    queryFn: trainingApi.listCurricula,
  });
  const items = (curricula as any[]).flatMap((c: any) =>
    (c.items || []).map((item: any) => ({ ...item, curriculum_name: c.name }))
  );

  const assignMutation = useMutation({
    mutationFn: () =>
      trainingApi.createAssignment({
        user_id: form.user_id,
        curriculum_item_id: form.curriculum_item_id,
        due_date: form.due_date || undefined,
      }),
    onSuccess: async () => {
      setShowAssign(false);
      setForm({ user_id: "", curriculum_item_id: "", due_date: "" });
      await qc.invalidateQueries({ queryKey: ["training-assignments"] });
    },
  });

  return (
    <div className="p-8 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Training</h1>
          <p className="text-gray-500 text-sm mt-1">Assignments and completion tracking.</p>
        </div>
        <button className="bg-brand-600 text-white px-4 py-2 rounded" onClick={() => setShowAssign(true)}>
          + Assign Training
        </button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["", "pending", "in_progress", "completed", "overdue", "waived"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 border rounded text-sm ${statusFilter === s ? "bg-brand-600 text-white" : ""}`}
          >
            {s || "all"}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {["Assignment ID", "User ID", "Curriculum Item", "Due Date", "Status"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
            ) : (assignments as any[]).length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No assignments.</td></tr>
            ) : (
              (assignments as any[]).map((a: any) => (
                <tr key={a.id} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/training/${a.id}`)}>
                  <td className="px-4 py-3 text-xs font-mono">{a.id}</td>
                  <td className="px-4 py-3 text-xs font-mono">{a.user_id}</td>
                  <td className="px-4 py-3 text-xs font-mono">{a.curriculum_item_id}</td>
                  <td className="px-4 py-3">{a.due_date ? new Date(a.due_date).toLocaleDateString() : "—"}</td>
                  <td className="px-4 py-3">{a.status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showAssign && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-6 space-y-3">
            <h2 className="text-lg font-semibold">Create Assignment</h2>
            <input className="border rounded px-3 py-2 w-full" placeholder="User ID" value={form.user_id} onChange={(e) => setForm((s) => ({ ...s, user_id: e.target.value }))} />
            <select className="border rounded px-3 py-2 w-full" value={form.curriculum_item_id} onChange={(e) => setForm((s) => ({ ...s, curriculum_item_id: e.target.value }))}>
              <option value="">Select curriculum item</option>
              {items.map((it: any) => (
                <option key={it.id} value={it.id}>{it.curriculum_name} - {it.title}</option>
              ))}
            </select>
            <input type="datetime-local" className="border rounded px-3 py-2 w-full" value={form.due_date} onChange={(e) => setForm((s) => ({ ...s, due_date: e.target.value }))} />
            <div className="flex justify-end gap-2">
              <button className="px-4 py-2 border rounded" onClick={() => setShowAssign(false)}>Cancel</button>
              <button className="px-4 py-2 bg-brand-600 text-white rounded disabled:opacity-50" disabled={assignMutation.isPending || !form.user_id || !form.curriculum_item_id} onClick={() => assignMutation.mutate()}>
                {assignMutation.isPending ? "Assigning..." : "Assign"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
