import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { qmsApi, usersApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

type CapaCreatePayload = {
  title: string;
  capa_type: string;
  source: string;
  product_material_affected: string;
  batch_lot_number: string;
  gmp_classification: string;
  risk_level: string;
  product_impact: boolean;
  patient_safety_impact: boolean;
  regulatory_reportable: boolean;
  regulatory_reporting_justification?: string;
  root_cause_category?: string;
  root_cause?: string;
  problem_description: string;
  immediate_actions?: string;
  department: string;
  identified_date: string;
  target_completion_date?: string;
  actions: [];
};

const statusStyles: Record<string, string> = {
  open: "bg-gray-100 text-gray-700",
  investigation: "bg-yellow-100 text-yellow-800",
  action_plan_approved: "bg-blue-100 text-blue-800",
  in_progress: "bg-purple-100 text-purple-800",
  effectiveness_check: "bg-orange-100 text-orange-800",
  closed: "bg-green-100 text-green-700",
};

export default function CAPAList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState<CapaCreatePayload>({
    title: "",
    capa_type: "corrective_and_preventive",
    source: "deviation",
    product_material_affected: "",
    batch_lot_number: "",
    gmp_classification: "major",
    risk_level: "medium",
    product_impact: false,
    patient_safety_impact: false,
    regulatory_reportable: true,
    regulatory_reporting_justification: "",
    root_cause_category: "unknown",
    root_cause: "",
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

  const { data: users = [] } = useQuery({
    queryKey: ["users-list"],
    queryFn: usersApi.listUsers,
    staleTime: 300_000,
  });

  const resolveOwner = (ownerId: string) => {
    const u = users.find((x: { id: string; full_name?: string }) => x.id === ownerId);
    return u?.full_name ?? `${ownerId.slice(0, 8)}…`;
  };

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
          + Create CAPA
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
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="investigation">Investigation</option>
          <option value="action_plan_approved">Action plan approved</option>
          <option value="in_progress">In progress</option>
          <option value="effectiveness_check">Effectiveness check</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {isLoading ? (
        <div className="bg-white rounded-xl shadow-sm p-12 flex flex-col items-center gap-3 text-gray-400">
          <svg className="w-6 h-6 animate-spin text-brand-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
          </svg>
          <span className="text-sm">Loading CAPAs…</span>
        </div>
      ) : visibleCapas.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-14 flex flex-col items-center gap-4">
          <svg
            className="w-14 h-14 text-gray-200"
            fill="none"
            viewBox="0 0 64 64"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <rect x="10" y="8" width="44" height="48" rx="4" />
            <path strokeLinecap="round" d="M20 22h24M20 30h16M20 38h10" />
            <circle cx="48" cy="48" r="10" fill="white" stroke="currentColor" strokeWidth="1.5" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M44 48l3 3 5-5" />
          </svg>
          <div className="text-center">
            <p className="text-base font-semibold text-gray-700">
              {statusFilter ? `No "${statusFilter.replaceAll("_", " ")}" CAPAs` : "No CAPAs yet"}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              {statusFilter
                ? "Try changing or clearing the status filter."
                : "Create your first corrective or preventive action to start tracking quality issues."}
            </p>
          </div>
          {!statusFilter && (
            <button
              onClick={() => setCreateOpen(true)}
              className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-5 py-2 rounded-lg"
            >
              + Create first CAPA
            </button>
          )}
        </div>
      ) : (
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
              {visibleCapas.map((capa: any) => (
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
                  <td className="px-4 py-3 text-gray-600">
                    {capa.owner_id ? resolveOwner(capa.owner_id) : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

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
                placeholder="Title (min 5 characters)"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              />
              <div className="col-span-2">
                <label className="block text-xs text-gray-500 mb-1">CAPA Type</label>
                <select
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  value={form.capa_type}
                  onChange={(e) => setForm((f) => ({ ...f, capa_type: e.target.value }))}
                >
                  <option value="corrective">Corrective</option>
                  <option value="preventive">Preventive</option>
                  <option value="corrective_and_preventive">Corrective and Preventive</option>
                </select>
              </div>
              <div className="col-span-2">
                <label className="block text-xs text-gray-500 mb-1">Source</label>
                <select
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  value={form.source}
                  onChange={(e) => setForm((f) => ({ ...f, source: e.target.value }))}
                >
                  <option value="deviation">Deviation</option>
                  <option value="audit_finding">Audit Finding</option>
                  <option value="customer_complaint">Customer Complaint</option>
                  <option value="oos">OOS</option>
                  <option value="self_inspection">Self-Inspection</option>
                  <option value="risk_assessment">Risk Assessment</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Product/Material affected"
                value={form.product_material_affected}
                onChange={(e) => setForm((f) => ({ ...f, product_material_affected: e.target.value }))}
              />
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Batch/Lot number"
                value={form.batch_lot_number}
                onChange={(e) => setForm((f) => ({ ...f, batch_lot_number: e.target.value }))}
              />
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={form.gmp_classification}
                onChange={(e) => setForm((f) => ({ ...f, gmp_classification: e.target.value }))}
              >
                <option value="critical">Critical</option>
                <option value="major">Major</option>
                <option value="minor">Minor</option>
                <option value="observation">Observation</option>
              </select>
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
                <option value="low">Low risk</option>
                <option value="medium">Medium risk</option>
                <option value="high">High risk</option>
                <option value="critical">Critical risk</option>
              </select>
              <label className="col-span-2 flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded border-gray-300 text-brand-600"
                  checked={form.regulatory_reportable}
                  onChange={(e) => setForm((f) => ({ ...f, regulatory_reportable: e.target.checked }))}
                />
                <span className="text-sm text-gray-700">Regulatory Reportable</span>
              </label>
              {form.regulatory_reportable && (
                <textarea
                  className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                  rows={2}
                  placeholder="Regulatory reporting justification"
                  value={form.regulatory_reporting_justification}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, regulatory_reporting_justification: e.target.value }))
                  }
                />
              )}
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                value={form.root_cause_category}
                onChange={(e) => setForm((f) => ({ ...f, root_cause_category: e.target.value }))}
              >
                <option value="human_error">Human Error</option>
                <option value="equipment">Equipment</option>
                <option value="process">Process</option>
                <option value="material">Material</option>
                <option value="environment">Environment</option>
                <option value="documentation">Documentation</option>
                <option value="software_it">Software-IT</option>
                <option value="unknown">Unknown</option>
              </select>
              <textarea
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                rows={2}
                placeholder="Root cause description"
                value={form.root_cause}
                onChange={(e) => setForm((f) => ({ ...f, root_cause: e.target.value }))}
              />
              <textarea
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                rows={4}
                placeholder="Problem description (minimum 20 characters)"
                value={form.problem_description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, problem_description: e.target.value }))
                }
              />
              <textarea
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                rows={2}
                placeholder="Immediate actions taken (optional)"
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
                  form.problem_description.trim().length < 20 ||
                  (form.regulatory_reportable &&
                    (form.regulatory_reporting_justification || "").trim().length < 5)
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
                {createMutation.isPending ? "Creating…" : "Create CAPA"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
