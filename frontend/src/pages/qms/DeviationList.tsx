import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { qmsApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

export default function DeviationList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({
    title: "",
    deviation_type: "process",
    gmp_impact_classification: "major",
    potential_patient_impact: false,
    potential_patient_impact_justification: "",
    batches_affected: "",
    product_affected: "",
    description: "",
    detected_during: "manufacturing",
    immediate_containment_actions: "",
    root_cause_category: "unknown",
    root_cause: "",
    requires_capa: false,
    regulatory_notification_required: false,
    regulatory_authority_name: "",
    regulatory_notification_deadline: "",
  });

  const { data: deviations = [], isLoading } = useQuery({
    queryKey: ["deviations"],
    queryFn: () => qmsApi.listDeviations({ skip: 0, limit: 200 }),
  });

  const createMutation = useMutation({
    mutationFn: (payload: any) => qmsApi.createDeviation(payload),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["deviations"] });
      setCreateOpen(false);
      toast.success(`Deviation ${created.deviation_number} created.`);
      navigate(`/qms/deviations/${created.id}`);
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to create deviation.");
    },
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Deviations</h1>
          <p className="text-gray-500 text-sm mt-1">Manufacturing & process deviations</p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors"
        >
          + New Deviation
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Status", "Description", "Site ID", "Created At"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={4} className="text-center py-8 text-gray-400">Loading...</td></tr>
            ) : deviations.length === 0 ? (
              <tr><td colSpan={4} className="text-center py-8 text-gray-400">No deviations recorded yet.</td></tr>
            ) : deviations.map((d: any) => (
              <tr
                key={d.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/qms/deviations/${d.id}`)}
              >
                <td className="px-4 py-3">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-800 font-medium">
                    {d.current_status.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-700 max-w-lg truncate">{d.description ?? d.title}</td>
                <td className="px-4 py-3 text-gray-600 font-mono text-xs">{d.site_id ?? "—"}</td>
                <td className="px-4 py-3 text-gray-600 text-xs">
                  {d.created_at ? new Date(d.created_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {createOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold text-gray-900">Create Deviation</h2>
            <div className="grid grid-cols-2 gap-3 mt-4">
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                placeholder="Title"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              />
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={form.deviation_type}
                onChange={(e) => setForm((f) => ({ ...f, deviation_type: e.target.value }))}
              >
                <option value="process">Process</option>
                <option value="equipment">Equipment</option>
                <option value="environmental">Environmental</option>
                <option value="material">Material</option>
                <option value="documentation">Documentation</option>
                <option value="personnel">Personnel</option>
                <option value="laboratory">Laboratory</option>
                <option value="other">Other</option>
              </select>
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                value={form.gmp_impact_classification}
                onChange={(e) => setForm((f) => ({ ...f, gmp_impact_classification: e.target.value }))}
              >
                <option value="critical">Critical</option>
                <option value="major">Major</option>
                <option value="minor">Minor</option>
              </select>
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Product affected"
                value={form.product_affected}
                onChange={(e) => setForm((f) => ({ ...f, product_affected: e.target.value }))}
              />
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Batch(es) affected (comma-separated lot numbers)"
                value={form.batches_affected}
                onChange={(e) => setForm((f) => ({ ...f, batches_affected: e.target.value }))}
              />
              <label className="col-span-2 flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.potential_patient_impact}
                  onChange={(e) => setForm((f) => ({ ...f, potential_patient_impact: e.target.checked }))}
                />
                Potential patient impact
              </label>
              {form.potential_patient_impact && (
                <textarea
                  className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                  rows={2}
                  placeholder="Patient impact justification"
                  value={form.potential_patient_impact_justification}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, potential_patient_impact_justification: e.target.value }))
                  }
                />
              )}
              <textarea
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                rows={3}
                placeholder="Description"
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
              <textarea
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm col-span-2"
                rows={3}
                placeholder="Immediate containment actions (required)"
                value={form.immediate_containment_actions}
                onChange={(e) => setForm((f) => ({ ...f, immediate_containment_actions: e.target.value }))}
              />
              <select
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
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
              <input
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Root cause description"
                value={form.root_cause}
                onChange={(e) => setForm((f) => ({ ...f, root_cause: e.target.value }))}
              />
              <label className="col-span-2 flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.requires_capa}
                  onChange={(e) => setForm((f) => ({ ...f, requires_capa: e.target.checked }))}
                />
                Root cause requires CAPA
              </label>
              <label className="col-span-2 flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.regulatory_notification_required}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, regulatory_notification_required: e.target.checked }))
                  }
                />
                Regulatory notification required
              </label>
              {form.regulatory_notification_required && (
                <>
                  <input
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                    placeholder="Regulatory authority name"
                    value={form.regulatory_authority_name}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, regulatory_authority_name: e.target.value }))
                    }
                  />
                  <input
                    type="datetime-local"
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                    value={form.regulatory_notification_deadline}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, regulatory_notification_deadline: e.target.value }))
                    }
                  />
                </>
              )}
            </div>
            <div className="flex gap-3 mt-5">
              <button
                className="flex-1 border border-gray-300 rounded-lg py-2 text-sm"
                onClick={() => setCreateOpen(false)}
              >
                Cancel
              </button>
              <button
                className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
                disabled={
                  createMutation.isPending ||
                  form.title.trim().length < 5 ||
                  form.description.trim().length < 20 ||
                  form.immediate_containment_actions.trim().length < 10
                }
                onClick={() =>
                  createMutation.mutate({
                    title: form.title,
                    deviation_type: form.deviation_type,
                    gmp_impact_classification: form.gmp_impact_classification,
                    potential_patient_impact: form.potential_patient_impact,
                    potential_patient_impact_justification:
                      form.potential_patient_impact_justification || undefined,
                    batches_affected: form.batches_affected
                      .split(",")
                      .map((x) => x.trim())
                      .filter(Boolean),
                    product_affected: form.product_affected || undefined,
                    description: form.description,
                    detected_during: form.detected_during,
                    detection_date: new Date().toISOString(),
                    risk_level: "high",
                    immediate_containment_actions: form.immediate_containment_actions,
                    immediate_action: form.immediate_containment_actions,
                    root_cause_category: form.root_cause_category || undefined,
                    root_cause: form.root_cause || undefined,
                    requires_capa: form.requires_capa,
                    regulatory_notification_required: form.regulatory_notification_required,
                    regulatory_authority_name: form.regulatory_authority_name || undefined,
                    regulatory_notification_deadline: form.regulatory_notification_deadline
                      ? new Date(form.regulatory_notification_deadline).toISOString()
                      : undefined,
                  })
                }
              >
                {createMutation.isPending ? "Creating..." : "Create Deviation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
