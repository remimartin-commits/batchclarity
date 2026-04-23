import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { qmsApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

const categoryColour: Record<string, string> = {
  minor: "bg-gray-100 text-gray-600",
  major: "bg-yellow-100 text-yellow-700",
  critical: "bg-red-100 text-red-700",
};

export default function ChangeControlList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({
    title: "",
    change_type: "process",
    change_category: "major",
    description: "",
    justification: "",
    regulatory_impact: false,
    regulatory_filing_required: false,
    regulatory_filing_type: "other",
    affected_document_ids: "",
    affected_equipment_ids: "",
    affected_sop_document_ids: "",
    implementation_plan: "",
    implementation_target_date: "",
    validation_qualification_required: false,
    validation_scope_description: "",
    pre_change_verification_checklist: "Training complete|yes\nBackup validated|na",
  });
  const { data: ccs = [], isLoading } = useQuery({
    queryKey: ["change-controls"],
    queryFn: () => qmsApi.listChangeControls(),
  });

  const createMutation = useMutation({
    mutationFn: (payload: any) => qmsApi.createChangeControl(payload),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["change-controls"] });
      setCreateOpen(false);
      toast.success(`Change control ${created.change_number} created.`);
      navigate(`/qms/change-controls/${created.id}`);
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to create change control.");
    },
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Change Controls</h1>
          <p className="text-gray-500 text-sm mt-1">Process, equipment, material & software changes</p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors"
        >
          + New Change Control
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["CC #", "Title", "Type", "Category", "Regulatory Impact", "Validation Req.", "Status"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">Loading...</td></tr>
            ) : ccs.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">No change controls yet.</td></tr>
            ) : ccs.map((cc: any) => (
              <tr
                key={cc.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/qms/change-controls/${cc.id}`)}
              >
                <td className="px-4 py-3 font-mono text-brand-600 font-medium">{cc.change_number}</td>
                <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">{cc.title}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{cc.change_type.replace(/_/g, " ")}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${categoryColour[cc.change_category]}`}>
                    {cc.change_category}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">{cc.regulatory_impact ? "⚠️ Yes" : "No"}</td>
                <td className="px-4 py-3 text-center">{cc.validation_required ? "✓ Yes" : "No"}</td>
                <td className="px-4 py-3">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                    {cc.current_status.replace(/_/g, " ")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {createOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold text-gray-900">Create Change Control</h2>
            <div className="grid grid-cols-2 gap-3 mt-4">
              <input className="border rounded px-3 py-2 text-sm col-span-2" placeholder="Title" value={form.title} onChange={(e) => setForm((s) => ({ ...s, title: e.target.value }))} />
              <select className="border rounded px-3 py-2 text-sm" value={form.change_type} onChange={(e) => setForm((s) => ({ ...s, change_type: e.target.value }))}>
                <option value="equipment">Equipment</option><option value="process">Process</option><option value="material">Material</option><option value="software">Software</option><option value="facility">Facility</option><option value="documentation">Documentation</option><option value="supplier">Supplier</option><option value="regulatory">Regulatory</option><option value="other">Other</option>
              </select>
              <select className="border rounded px-3 py-2 text-sm" value={form.change_category} onChange={(e) => setForm((s) => ({ ...s, change_category: e.target.value }))}>
                <option value="major">Major</option><option value="minor">Minor</option><option value="emergency">Emergency</option>
              </select>
              <textarea className="border rounded px-3 py-2 text-sm col-span-2" rows={3} placeholder="Description" value={form.description} onChange={(e) => setForm((s) => ({ ...s, description: e.target.value }))} />
              <textarea className="border rounded px-3 py-2 text-sm col-span-2" rows={2} placeholder="Justification" value={form.justification} onChange={(e) => setForm((s) => ({ ...s, justification: e.target.value }))} />
              <label className="col-span-2 flex items-center gap-2 text-sm"><input type="checkbox" checked={form.regulatory_filing_required} onChange={(e) => setForm((s) => ({ ...s, regulatory_filing_required: e.target.checked }))} />Regulatory filing required</label>
              {form.regulatory_filing_required && (
                <select className="border rounded px-3 py-2 text-sm col-span-2" value={form.regulatory_filing_type} onChange={(e) => setForm((s) => ({ ...s, regulatory_filing_type: e.target.value }))}>
                  <option value="cbe_30">CBE-30</option><option value="pas">PAS</option><option value="annual_report">Annual Report</option><option value="variation">Variation</option><option value="other">Other</option>
                </select>
              )}
              <input className="border rounded px-3 py-2 text-sm col-span-2" placeholder="Affected documents IDs (comma-separated)" value={form.affected_document_ids} onChange={(e) => setForm((s) => ({ ...s, affected_document_ids: e.target.value }))} />
              <input className="border rounded px-3 py-2 text-sm col-span-2" placeholder="Affected equipment IDs (comma-separated)" value={form.affected_equipment_ids} onChange={(e) => setForm((s) => ({ ...s, affected_equipment_ids: e.target.value }))} />
              <input className="border rounded px-3 py-2 text-sm col-span-2" placeholder="Affected SOP document IDs (comma-separated)" value={form.affected_sop_document_ids} onChange={(e) => setForm((s) => ({ ...s, affected_sop_document_ids: e.target.value }))} />
              <textarea className="border rounded px-3 py-2 text-sm col-span-2" rows={2} placeholder="Implementation plan" value={form.implementation_plan} onChange={(e) => setForm((s) => ({ ...s, implementation_plan: e.target.value }))} />
              <input type="datetime-local" className="border rounded px-3 py-2 text-sm col-span-2" value={form.implementation_target_date} onChange={(e) => setForm((s) => ({ ...s, implementation_target_date: e.target.value }))} />
              <label className="col-span-2 flex items-center gap-2 text-sm"><input type="checkbox" checked={form.validation_qualification_required} onChange={(e) => setForm((s) => ({ ...s, validation_qualification_required: e.target.checked }))} />Validation/qualification required</label>
              {form.validation_qualification_required && <textarea className="border rounded px-3 py-2 text-sm col-span-2" rows={2} placeholder="Validation scope description" value={form.validation_scope_description} onChange={(e) => setForm((s) => ({ ...s, validation_scope_description: e.target.value }))} />}
              <textarea className="border rounded px-3 py-2 text-sm col-span-2" rows={3} placeholder="Pre-change checklist (one per line: item|yes/no/na)" value={form.pre_change_verification_checklist} onChange={(e) => setForm((s) => ({ ...s, pre_change_verification_checklist: e.target.value }))} />
            </div>
            <div className="flex gap-3 mt-5">
              <button className="flex-1 border rounded py-2 text-sm" onClick={() => setCreateOpen(false)}>Cancel</button>
              <button
                className="flex-1 bg-brand-600 text-white rounded py-2 text-sm font-semibold disabled:opacity-50"
                disabled={createMutation.isPending || form.title.trim().length < 5 || form.description.trim().length < 20 || form.justification.trim().length < 20}
                onClick={() =>
                  createMutation.mutate({
                    title: form.title,
                    change_type: form.change_type,
                    change_category: form.change_category,
                    description: form.description,
                    justification: form.justification,
                    regulatory_impact: form.regulatory_filing_required,
                    regulatory_filing_required: form.regulatory_filing_required,
                    regulatory_filing_type: form.regulatory_filing_required ? form.regulatory_filing_type : undefined,
                    validation_required: form.validation_qualification_required,
                    validation_qualification_required: form.validation_qualification_required,
                    validation_scope_description: form.validation_scope_description || undefined,
                    affected_document_ids: form.affected_document_ids.split(",").map((x) => x.trim()).filter(Boolean),
                    affected_equipment_ids: form.affected_equipment_ids.split(",").map((x) => x.trim()).filter(Boolean),
                    affected_sop_document_ids: form.affected_sop_document_ids.split(",").map((x) => x.trim()).filter(Boolean),
                    implementation_plan: form.implementation_plan,
                    implementation_target_date: new Date(form.implementation_target_date || new Date().toISOString()).toISOString(),
                    pre_change_verification_checklist: form.pre_change_verification_checklist
                      .split("\n")
                      .map((line) => line.trim())
                      .filter(Boolean)
                      .map((line) => {
                        const [item, result] = line.split("|");
                        return { item: (item || "").trim(), result: ((result || "na").trim().toLowerCase()) };
                      }),
                    proposed_implementation_date: form.implementation_target_date ? new Date(form.implementation_target_date).toISOString() : undefined,
                  })
                }
              >
                {createMutation.isPending ? "Creating..." : "Create Change Control"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
