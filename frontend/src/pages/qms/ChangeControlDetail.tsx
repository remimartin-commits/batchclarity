import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { toast } from "@/stores/toastStore";

const NEXT_MEANING_BY_STATUS: Record<string, string[]> = {
  draft: ["under_review"],
  under_review: ["initiator_approved", "qa_approved"],
  approved: ["in_implementation"],
  in_implementation: ["effectiveness_review"],
  effectiveness_review: ["closed"],
};

export default function ChangeControlDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [pendingMeaning, setPendingMeaning] = useState<string | null>(null);
  const [postReviewDate, setPostReviewDate] = useState("");
  const [postReviewOutcome, setPostReviewOutcome] = useState("");

  const { data, isLoading } = useQuery<any>({
    queryKey: ["qms-change-control", id],
    queryFn: () => qmsApi.getChangeControl(id),
    enabled: Boolean(id),
  });
  const { data: auditTrail = [] } = useQuery({
    queryKey: ["qms-change-control-audit", id],
    queryFn: () => qmsApi.listChangeControlAuditTrail(id),
    enabled: Boolean(id),
  });

  const availableMeanings = useMemo(
    () => NEXT_MEANING_BY_STATUS[data?.current_status || ""] || [],
    [data?.current_status]
  );

  const updateMutation = useMutation({
    mutationFn: (payload: any) => qmsApi.updateChangeControl(id, payload),
    onSuccess: async () => {
      toast.success("Change control updated.");
      await qc.invalidateQueries({ queryKey: ["qms-change-control", id] });
      await qc.invalidateQueries({ queryKey: ["change-controls"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      toast.error(Array.isArray(d) ? d.join("; ") : d || "Failed to update change control.");
    },
  });

  const signMutation = useMutation({
    mutationFn: (payload: { username: string; password: string; meaning: string; comments: string }) =>
      qmsApi.signChangeControl(id, payload),
    onSuccess: async () => {
      toast.success("Electronic signature applied.");
      setPendingMeaning(null);
      await qc.invalidateQueries({ queryKey: ["qms-change-control", id] });
      await qc.invalidateQueries({ queryKey: ["qms-change-control-audit", id] });
      await qc.invalidateQueries({ queryKey: ["change-controls"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      toast.error(Array.isArray(d) ? d.join("; ") : d || "Failed to sign change control.");
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading change control...</div>;
  if (!data) {
    return (
      <div className="p-8">
        <div className="text-gray-500 mb-3">Change control not found.</div>
        <button className="text-brand-600" onClick={() => navigate("/qms/change-controls")}>Back to list</button>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      <div className="text-sm text-gray-500">
        <Link to="/qms/change-controls" className="text-brand-600 hover:underline">Change Controls</Link> / {data.change_number}
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">{data.title}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data.change_number} • {data.change_type} • {data.change_category} • status: {data.current_status.replace(/_/g, " ")}
        </p>
      </div>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Record Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div><span className="text-gray-500">Regulatory filing:</span> {data.regulatory_filing_required ? `Yes (${data.regulatory_filing_type || "—"})` : "No"}</div>
          <div><span className="text-gray-500">Validation/qualification:</span> {data.validation_qualification_required ? "Yes" : "No"}</div>
          <div><span className="text-gray-500">Implementation target:</span> {data.implementation_target_date ? new Date(data.implementation_target_date).toLocaleString() : "—"}</div>
          <div><span className="text-gray-500">Actual implementation:</span> {data.actual_implementation_date ? new Date(data.actual_implementation_date).toLocaleString() : "—"}</div>
          <div className="md:col-span-2"><span className="text-gray-500">Implementation plan:</span> {data.implementation_plan || "—"}</div>
          <div className="md:col-span-2"><span className="text-gray-500">Affected docs/equipment/SOPs:</span> {JSON.stringify({ documents: data.affected_document_ids || [], equipment: data.affected_equipment_ids || [], sops: data.affected_sop_document_ids || [] })}</div>
          <div className="md:col-span-2"><span className="text-gray-500">Approval signatures:</span> {(data.approval_signature_roles || []).join(", ") || "—"}</div>
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Post-change Effectiveness Review</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <input type="datetime-local" className="border rounded px-3 py-2 text-sm" value={postReviewDate} onChange={(e) => setPostReviewDate(e.target.value)} />
          <input className="border rounded px-3 py-2 text-sm" placeholder="Outcome" value={postReviewOutcome} onChange={(e) => setPostReviewOutcome(e.target.value)} />
        </div>
        <button
          className="px-4 py-2 rounded bg-brand-600 text-white disabled:opacity-50"
          disabled={updateMutation.isPending}
          onClick={() =>
            updateMutation.mutate({
              post_change_effectiveness_date: postReviewDate ? new Date(postReviewDate).toISOString() : undefined,
              post_change_effectiveness_outcome: postReviewOutcome || undefined,
            })
          }
        >
          {updateMutation.isPending ? "Saving..." : "Save Effectiveness Review"}
        </button>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Signed Workflow Transitions</h2>
        <div className="flex flex-wrap gap-2">
          {availableMeanings.length === 0 ? (
            <span className="text-sm text-gray-500">No transition available.</span>
          ) : (
            availableMeanings.map((m) => (
              <button key={m} className="px-3 py-1.5 border rounded text-sm" onClick={() => setPendingMeaning(m)}>
                {m.replaceAll("_", " ")}
              </button>
            ))
          )}
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="font-semibold mb-2">Audit Trail</h2>
        {!auditTrail.length ? (
          <p className="text-sm text-gray-400">No audit events found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="text-gray-500"><th className="text-left py-2">User</th><th className="text-left py-2">Role</th><th className="text-left py-2">Action</th><th className="text-left py-2">Old</th><th className="text-left py-2">New</th><th className="text-left py-2">UTC</th><th className="text-left py-2">IP</th></tr></thead>
              <tbody>
                {(auditTrail as any[]).map((e: any, i: number) => (
                  <tr key={i} className="border-t border-gray-100">
                    <td className="py-2">{e.user_full_name || "—"}</td>
                    <td className="py-2">{e.role_at_time || "—"}</td>
                    <td className="py-2">{e.action || "—"}</td>
                    <td className="py-2 break-all">{e.old_value ? JSON.stringify(e.old_value) : "—"}</td>
                    <td className="py-2 break-all">{e.new_value ? JSON.stringify(e.new_value) : "—"}</td>
                    <td className="py-2">{e.timestamp_utc ? new Date(e.timestamp_utc).toISOString() : "—"}</td>
                    <td className="py-2">{e.ip_address || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <ESignatureModal
        isOpen={Boolean(pendingMeaning)}
        isLoading={signMutation.isPending}
        title="Change Control Transition Signature"
        description={pendingMeaning ? `Apply signature for '${pendingMeaning.replaceAll("_", " ")}'.` : undefined}
        meaning={pendingMeaning || undefined}
        onClose={() => setPendingMeaning(null)}
        onConfirm={async ({ username, password, meaning, comments }) => {
          await signMutation.mutateAsync({ username, password, meaning, comments });
        }}
      />
    </div>
  );
}
