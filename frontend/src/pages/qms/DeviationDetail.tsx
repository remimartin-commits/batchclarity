import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { toast } from "@/stores/toastStore";

type TransitionMeaning = "under_investigation" | "pending_approval" | "closed";

export default function DeviationDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pendingMeaning, setPendingMeaning] = useState<TransitionMeaning | null>(null);
  const [noCapaConfirmed, setNoCapaConfirmed] = useState(false);
  const [noCapaJustification, setNoCapaJustification] = useState("");

  const { data: deviation, isLoading } = useQuery({
    queryKey: ["qms-deviation", id],
    queryFn: () => qmsApi.getDeviation(id),
    enabled: Boolean(id),
  });
  const { data: auditTrail = [] } = useQuery({
    queryKey: ["qms-deviation-audit", id],
    queryFn: () => qmsApi.listDeviationAuditTrail(id),
    enabled: Boolean(id),
  });

  const transitionMutation = useMutation({
    mutationFn: async (payload: {
      username: string;
      password: string;
      meaning: TransitionMeaning;
      comments: string;
    }) => {
      return qmsApi.signDeviation(id, {
        username: payload.username,
        password: payload.password,
        meaning: payload.meaning,
        comments: payload.comments,
        no_capa_needed_confirmed: payload.meaning === "closed" ? noCapaConfirmed : undefined,
        no_capa_needed_justification:
          payload.meaning === "closed" ? noCapaJustification : undefined,
      });
    },
    onSuccess: async () => {
      toast.success("Deviation transition completed.");
      setPendingMeaning(null);
      setNoCapaConfirmed(false);
      setNoCapaJustification("");
      await queryClient.invalidateQueries({ queryKey: ["qms-deviation", id] });
      await queryClient.invalidateQueries({ queryKey: ["qms-deviation-audit", id] });
      await queryClient.invalidateQueries({ queryKey: ["deviations"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Transition failed.");
    },
  });

  const nextMeaning = useMemo(() => {
    const status = deviation?.current_status;
    if (status === "open") return "under_investigation" as TransitionMeaning;
    if (status === "under_investigation") return "pending_approval" as TransitionMeaning;
    if (status === "pending_approval") return "closed" as TransitionMeaning;
    return null;
  }, [deviation?.current_status]);

  const limsOriginHint = useMemo(() => {
    const description: string = deviation?.description ?? "";
    return description.includes("Sample ID:") || description.includes("Result ID:");
  }, [deviation?.description]);

  if (isLoading) return <div className="p-8 text-gray-500">Loading deviation...</div>;
  if (!deviation) return <div className="p-8 text-gray-500">Deviation not found.</div>;

  return (
    <div className="p-8 max-w-4xl space-y-5">
      <div className="text-sm text-gray-500">
        <Link to="/qms/deviations" className="text-brand-600 hover:underline">
          Deviations
        </Link>{" "}
        / {deviation.deviation_number}
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 space-y-2">
        <h1 className="text-2xl font-bold text-gray-900">{deviation.title}</h1>
        <p className="text-sm text-gray-500">
          Status: {deviation.current_status} • Site ID: {deviation.site_id ?? "—"} • Created:{" "}
          {deviation.created_at ? new Date(deviation.created_at).toLocaleString() : "—"}
        </p>
        <p className="text-sm text-gray-600">
          Type: {deviation.deviation_type?.replaceAll("_", " ")} • GMP impact:{" "}
          {deviation.gmp_impact_classification}
        </p>
        <p className="text-sm text-gray-600">
          Product affected: {deviation.product_affected || "—"} • Batches:{" "}
          {deviation.batches_affected?.length ? deviation.batches_affected.join(", ") : "—"}
        </p>
        <p className="text-sm text-gray-600">
          Patient impact: {deviation.potential_patient_impact ? "Yes" : "No"}{" "}
          {deviation.potential_patient_impact_justification
            ? `(${deviation.potential_patient_impact_justification})`
            : ""}
        </p>
        <p className="text-sm text-gray-600">
          Regulatory notification required:{" "}
          {deviation.regulatory_notification_required ? "Yes" : "No"}
          {deviation.regulatory_notification_required && (
            <>
              {" "}
              • Authority: {deviation.regulatory_authority_name || "—"} • Deadline:{" "}
              {deviation.regulatory_notification_deadline
                ? new Date(deviation.regulatory_notification_deadline).toLocaleString()
                : "—"}
            </>
          )}
        </p>
        <p className="text-sm text-gray-700 whitespace-pre-wrap">{deviation.description}</p>
        <p className="text-sm text-gray-700 whitespace-pre-wrap">
          Immediate containment: {deviation.immediate_containment_actions || "—"}
        </p>
        <p className="text-sm text-gray-700 whitespace-pre-wrap">
          Root cause:{" "}
          {deviation.root_cause
            ? `${deviation.root_cause_category || "unknown"} - ${deviation.root_cause}`
            : "—"}
        </p>
        <p className="text-sm text-gray-700">
          Linked CAPA: {deviation.linked_capa_id || "None"}
        </p>
      </div>

      {limsOriginHint && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          Originating OOS investigation detected from LIMS-linked description.
          <Link
            to="/lims/samples"
            className="ml-1 text-brand-600 hover:text-brand-700 font-medium"
          >
            Open LIMS samples
          </Link>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold text-gray-900">State Transitions</h2>
        <div className="flex gap-2 items-center">
          <button
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-50"
            disabled={!nextMeaning}
            onClick={() => nextMeaning && setPendingMeaning(nextMeaning)}
          >
            {nextMeaning
              ? `Move to ${nextMeaning.replaceAll("_", " ")}`
              : "No transition available"}
          </button>
        </div>
        {nextMeaning === "closed" && !deviation.linked_capa_id && (
          <div className="space-y-2 border border-amber-200 bg-amber-50 rounded-lg p-3">
            <label className="flex items-center gap-2 text-sm text-amber-900">
              <input
                type="checkbox"
                checked={noCapaConfirmed}
                onChange={(e) => setNoCapaConfirmed(e.target.checked)}
              />
              Confirm no CAPA is needed for closure
            </label>
            <textarea
              className="w-full border border-amber-300 rounded-lg px-3 py-2 text-sm"
              rows={2}
              placeholder="Mandatory justification for closing without CAPA"
              value={noCapaJustification}
              onChange={(e) => setNoCapaJustification(e.target.value)}
            />
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="font-semibold text-gray-900 mb-3">Audit Trail</h2>
        {!auditTrail.length ? (
          <p className="text-sm text-gray-400">No audit events found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-gray-500">
                <tr>
                  <th className="text-left py-2">User</th>
                  <th className="text-left py-2">Role at Time</th>
                  <th className="text-left py-2">Action</th>
                  <th className="text-left py-2">Old Value</th>
                  <th className="text-left py-2">New Value</th>
                  <th className="text-left py-2">UTC Timestamp</th>
                  <th className="text-left py-2">IP</th>
                </tr>
              </thead>
              <tbody>
                {auditTrail.map((event: any, idx: number) => (
                  <tr key={idx} className="border-t border-gray-100">
                    <td className="py-2">{event.user_full_name || "—"}</td>
                    <td className="py-2">{event.role_at_time || "—"}</td>
                    <td className="py-2">{event.action || "—"}</td>
                    <td className="py-2 break-all">{event.old_value ? JSON.stringify(event.old_value) : "—"}</td>
                    <td className="py-2 break-all">{event.new_value ? JSON.stringify(event.new_value) : "—"}</td>
                    <td className="py-2">{event.timestamp_utc ? new Date(event.timestamp_utc).toISOString() : "—"}</td>
                    <td className="py-2">{event.ip_address || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <button
        className="text-sm text-gray-500 hover:text-gray-800"
        onClick={() => navigate("/qms/deviations")}
      >
        ← Back to deviations
      </button>

      <ESignatureModal
        isOpen={Boolean(pendingMeaning)}
        isLoading={transitionMutation.isPending}
        title="Deviation State Transition"
        description={
          pendingMeaning
            ? `Apply signature and transition deviation to '${pendingMeaning}'.`
            : undefined
        }
        meaning={pendingMeaning || undefined}
        onClose={() => setPendingMeaning(null)}
        onConfirm={async ({ username, password, meaning, comments }) => {
          if (!pendingMeaning) return;
          await transitionMutation.mutateAsync({
            username,
            password,
            meaning: meaning as TransitionMeaning,
            comments,
          });
        }}
      />
    </div>
  );
}

