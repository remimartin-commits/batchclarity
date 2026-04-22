import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { qmsApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

type CapaCreatePayload = {
  title: string;
  capa_type: string;
  source: string;
  risk_level: string;
  product_impact: boolean;
  patient_safety_impact: boolean;
  regulatory_reportable: boolean;
  problem_description: string;
  immediate_actions?: string;
  department: string;
  identified_date: string;
  target_completion_date?: string;
  actions: [];
};

const statusStyles: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  under_review: "bg-yellow-100 text-yellow-800",
  approved: "bg-blue-100 text-blue-800",
  in_progress: "bg-purple-100 text-purple-800",
  effectiveness_check: "bg-orange-100 text-orange-800",
  completed: "bg-green-100 text-green-800",
  closed: "bg-gray-200 text-gray-600",
};

export default function CAPAList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState<CapaCreatePayload>({
    title: "",
    capa_type: "corrective",
    source: "internal_audit",
    risk_level: "medium",
    product_impact: false,
    patient_safety_impact: false,
    regulatory_reportable: false,
    problem_description: "",
    immediate_actions: "",
    department: "Quality",
    identified_date: new Date().toISOString(),
    target_completion_date: "",
    actions: [],
  });

  const { data: capas = [], isLoading } = useQuery({
    queryKey: ["qms-capas", statusFilter],
    queryFn: () =>
      qmsApi.listCapas({
        ...(statusFilter ? { status_filter: statusFilter } : {}),
        skip: 0,
        limit: 20,
      }),
  });

  const createMutation = useMutation({
    mutationFn: (payload: CapaCreatePayload) => qmsApi.createCapa(payload),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["qms-capas"] });
      setCreateOpen(false);
      toast.success(`CAPA ${created.capa_number} created.`);
      navigate(`/qms/capas/${created.id}`);
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to create CAPA.");
    },
  });

  const visibleCapas = useMemo(() => capas ?? [], [capas]);

  return (
    <div className="p-8 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CAPA Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Corrective and preventive action tracking for open quality items.
          </p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg"
        >
          Create CAPA
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-4">
        <label className="block text-xs uppercase tracking-wide text-gray-500 mb-1">
          Status Filter
        </label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
        >
          <option value="">Open and all statuses</option>
          <option value="draft">Draft</option>
          <option value="under_review">Under review</option>
          <option value="approved">Approved</option>
          <option value="in_progress">In progress</option>
          <option value="effectiveness_check">Effectiveness check</option>
          <option value="completed">Completed</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                CAPA #
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                Title
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                Due Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">
                Assigned To
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  Loading CAPAs...
                </td>
              </tr>
            ) : visibleCapas.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No CAPAs found for this filter.
                </td>
              </tr>
            ) : (
              visibleCapas.map((capa: any) => (
                <tr
                  key={capa.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/qms/capas/${capa.id}`)}
                >
                  <td className="px-4 py-3 font-mono text-brand-700">{capa.capa_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{capa.title}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        statusStyles[capa.current_status] ?? "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {String(capa.current_status).replaceAll("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {capa.target_completion_date
                      ? new Date(capa.target_completion_date).toLocaleDateString()
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{capa.owner_id ?? "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {createOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-6">
            <h2 className="text-lg font-semibold text-gray-900">Create CAPA</h2>
            <p className="text-xs text-gray-500 mt-1 mb-4">
              Minimal CAPA create flow for customer demo readiness.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                placeholder="Title"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              />
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Department"
                value={form.department}
                onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
              />
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={form.risk_level}
                onChange={(e) => setForm((f) => ({ ...f, risk_level: e.target.value }))}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
              <textarea
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                rows={4}
                placeholder="Problem description (minimum 20 chars)"
                value={form.problem_description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, problem_description: e.target.value }))
                }
              />
              <textarea
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                rows={2}
                placeholder="Immediate actions"
                value={form.immediate_actions}
                onChange={(e) =>
                  setForm((f) => ({ ...f, immediate_actions: e.target.value }))
                }
              />
            </div>
            <div className="flex gap-3 mt-5">
              <button
                className="flex-1 border border-gray-300 rounded-lg py-2 text-sm"
                onClick={() => setCreateOpen(false)}
              >
                Cancel
              </button>
              <button
                disabled={
                  createMutation.isPending ||
                  form.title.trim().length < 5 ||
                  form.problem_description.trim().length < 20
                }
                onClick={() =>
                  createMutation.mutate({
                    ...form,
                    target_completion_date: form.target_completion_date || undefined,
                    immediate_actions: form.immediate_actions || undefined,
                  })
                }
                className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
              >
                {createMutation.isPending ? "Creating..." : "Create CAPA"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
