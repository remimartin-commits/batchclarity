import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { qmsApi, usersApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { toast } from "@/stores/toastStore";

const STATUS_STYLES: Record<string, string> = {
  open: "bg-gray-100 text-gray-600",
  investigation: "bg-yellow-100 text-yellow-800",
  action_plan_approved: "bg-blue-100 text-blue-800",
  in_progress: "bg-purple-100 text-purple-800",
  effectiveness_check: "bg-orange-100 text-orange-800",
  closed: "bg-green-100 text-green-700",
};

const NEXT_MEANING_BY_STATUS: Record<string, string | undefined> = {
  open: "investigation",
  investigation: "action_plan_approved",
  action_plan_approved: "in_progress",
  in_progress: "effectiveness_check",
  effectiveness_check: "closed",
};

const RISK_STYLES: Record<string, string> = {
  low: "text-green-700 bg-green-50",
  medium: "text-yellow-700 bg-yellow-50",
  high: "text-orange-700 bg-orange-50",
  critical: "text-red-700 bg-red-50",
};

export default function CAPADetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isSignOpen, setIsSignOpen] = useState(false);
  const { data: auditTrail = [] } = useQuery({
    queryKey: ["qms-capa-audit", id],
    queryFn: () => qmsApi.listCapaAuditTrail(id!),
    enabled: Boolean(id),
  });


  const { data: capa, isLoading } = useQuery({
    queryKey: ["qms-capa-detail", id],
    queryFn: () => qmsApi.getCapa(id!),
    enabled: Boolean(id),
  });

  // Fetch users list once (stale for 5 min) to resolve owner UUID → full name
  const { data: users = [] } = useQuery({
    queryKey: ["users-list"],
    queryFn: usersApi.listUsers,
    staleTime: 300_000,
  });

  const ownerUser = users.find((u: any) => u.id === capa?.owner_id);
  const ownerLabel = ownerUser
    ? `${ownerUser.full_name} (${ownerUser.username})`
    : capa?.owner_id ?? "—";

  const signMutation = useMutation({
    mutationFn: (payload: { username: string; password: string; meaning: string; comments: string }) =>
      qmsApi.signCapa(id!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["qms-capa-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["qms-capas"] });
      setIsSignOpen(false);
      toast.success("CAPA closed and signature recorded.");
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "CAPA signature failed.");
    },
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center gap-3 text-gray-400">
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        Loading CAPA detail…
      </div>
    );
  }

  if (!capa) {
    return <div className="p-8 text-gray-500">CAPA not found.</div>;
  }

  const isClosed = ["closed", "completed", "cancelled"].includes(capa.current_status);
  const transitionMeaning = NEXT_MEANING_BY_STATUS[capa.current_status] ?? "closed";

  return (
    <div className="p-8 max-w-5xl space-y-5">
      {/* Back nav */}
      <button
        onClick={() => navigate("/qms/capas")}
        className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to CAPA dashboard
      </button>

      {/* Header card */}
      <div className="bg-white rounded-xl shadow-sm p-6 flex items-start justify-between gap-4">
        <div className="space-y-2 min-w-0">
          <p className="font-mono text-brand-700 font-semibold text-sm">{capa.capa_number}</p>
          <h1 className="text-2xl font-bold text-gray-900">{capa.title}</h1>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-gray-500">
              {capa.capa_type
                .split("_")
                .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(" ")}
            </span>
            <span className="text-gray-300">•</span>
            <span className="text-gray-500">{capa.department}</span>
            <span className="text-gray-300">•</span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[capa.current_status] ?? "bg-gray-100 text-gray-600"}`}
            >
              {String(capa.current_status).replaceAll("_", " ")}
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${RISK_STYLES[capa.risk_level] ?? ""}`}
            >
              {capa.risk_level} risk
            </span>
          </div>
          <p className="text-xs text-gray-400">
            Created {new Date(capa.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
            {capa.actual_completion_date && (
              <> · Closed {new Date(capa.actual_completion_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</>
            )}
          </p>
        </div>
        {!isClosed ? (
          <button
            onClick={() => setIsSignOpen(true)}
            className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg whitespace-nowrap flex-shrink-0"
          >
            {transitionMeaning === "closed"
              ? "Close CAPA"
              : `Move to ${transitionMeaning.replaceAll("_", " ")}`}
          </button>
        ) : (
          <span className="inline-flex items-center gap-1.5 bg-green-50 text-green-700 text-sm font-medium px-3 py-1.5 rounded-lg border border-green-200 flex-shrink-0">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            Closed
          </span>
        )}
      </div>

      {/* Meta grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <Card title="Owner">{ownerLabel}</Card>
        <Card title="Source">
          {capa.source
            .split("_")
            .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(" ")}
        </Card>
        <Card title="Department">{capa.department}</Card>
        <Card title="GMP Classification">{String(capa.gmp_classification || "—").toUpperCase()}</Card>
        <Card title="Product/Material Affected">{capa.product_material_affected || "—"}</Card>
        <Card title="Batch/Lot Number">{capa.batch_lot_number || "—"}</Card>
        <Card title="Identified Date">
          {new Date(capa.identified_date).toLocaleDateString("en-GB", {
            day: "numeric", month: "short", year: "numeric",
          })}
        </Card>
        <Card title="Target Completion Date">
          {capa.target_completion_date
            ? new Date(capa.target_completion_date).toLocaleDateString("en-GB", {
                day: "numeric", month: "short", year: "numeric",
              })
            : "—"}
        </Card>
        <Card title="Actual Completion Date">
          {capa.actual_completion_date
            ? new Date(capa.actual_completion_date).toLocaleDateString("en-GB", {
                day: "numeric", month: "short", year: "numeric",
              })
            : "—"}
        </Card>
      </div>

      {/* Impact flags */}
      <div className="bg-white rounded-xl shadow-sm p-5">
        <h2 className="text-xs uppercase tracking-wide text-gray-500 font-semibold mb-3">
          Impact Assessment
        </h2>
        <div className="flex flex-wrap gap-3">
          <Flag active={capa.product_impact} label="Product Impact" />
          <Flag active={capa.patient_safety_impact} label="Patient Safety Impact" />
          <Flag active={capa.regulatory_reportable} label="Regulatory Reportable" />
        </div>
      </div>

      {/* Description fields */}
      <Card title="Problem Description">{capa.problem_description}</Card>

      <Card title="Immediate Actions">
        {capa.immediate_actions?.trim() ? capa.immediate_actions : "—"}
      </Card>

      <Card title="Root Cause">
        {capa.root_cause?.trim() ? (
          <>
            {capa.root_cause}
            {capa.root_cause_method && (
              <span className="ml-2 text-xs text-gray-400">
                (method: {capa.root_cause_method})
              </span>
            )}
          </>
        ) : "—"}
      </Card>

      <Card title="Root Cause Category">
        {capa.root_cause_category
          ? String(capa.root_cause_category)
              .split("_")
              .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
              .join(" ")
          : "—"}
      </Card>

      <Card title="Regulatory Reporting Justification">
        {capa.regulatory_reporting_justification?.trim() ? capa.regulatory_reporting_justification : "—"}
      </Card>

      {/* Effectiveness */}
      {(capa.effectiveness_criteria || capa.effectiveness_result) && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <Card title="Effectiveness Criteria">
            {capa.effectiveness_criteria ?? "—"}
          </Card>
          <Card title="Effectiveness Result">
            {capa.effectiveness_result ?? "—"}
          </Card>
          <Card title="Effectiveness Check Date">
            {capa.effectiveness_check_date
              ? new Date(capa.effectiveness_check_date).toLocaleDateString("en-GB")
              : "—"}
          </Card>
          <Card title="Effectiveness Method">
            {capa.effectiveness_check_method ?? "—"}
          </Card>
          <Card title="Effectiveness Evidence">
            {capa.effectiveness_evidence_note ?? "—"}
          </Card>
        </div>
      )}

      {/* Action Plan */}
      <Card title={`Action Plan (${capa.actions?.length ?? 0})`}>
        {!capa.actions?.length ? (
          <p className="text-sm text-gray-400 italic">No action items defined yet.</p>
        ) : (
          <div className="space-y-2 mt-1">
            {capa.actions.map((action: any) => (
              <div
                key={action.id}
                className="border border-gray-100 rounded-lg px-3 py-2.5 text-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-gray-800">
                    {action.sequence_number}. {action.description}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded whitespace-nowrap">
                    {action.status}
                  </span>
                </div>
                {action.due_date && (
                  <p className="text-xs text-gray-400 mt-1">
                    Due: {new Date(action.due_date).toLocaleDateString("en-GB")}
                  </p>
                )}
                {action.completion_evidence && (
                  <p className="text-xs text-gray-500 mt-1">
                    Evidence: {action.completion_evidence}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title={`Audit Trail (${auditTrail.length})`}>
        {!auditTrail.length ? (
          <p className="text-sm text-gray-400 italic">No audit events found.</p>
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
      </Card>

      {/* E-Signature modal */}
      <ESignatureModal
        isOpen={isSignOpen}
        isLoading={signMutation.isPending}
        title="Close CAPA"
        description="Apply your electronic signature to permanently close this CAPA. The actual completion date will be recorded and the record locked."
        meaning={transitionMeaning}
        onClose={() => setIsSignOpen(false)}
        onConfirm={async ({ username, password, meaning, comments }) => {
          await signMutation.mutateAsync({ username, password, meaning, comments });
        }}
      />
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-5">
      <h2 className="text-xs uppercase tracking-wide text-gray-500 font-semibold mb-2">
        {title}
      </h2>
      <div className="text-sm text-gray-800 leading-relaxed">{children}</div>
    </div>
  );
}

function Flag({ active, label }: { active: boolean; label: string }) {
  return (
    <div
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
        active
          ? "bg-red-50 text-red-700 border border-red-200"
          : "bg-gray-50 text-gray-400 border border-gray-200"
      }`}
    >
      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        {active ? (
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        )}
      </svg>
      {label}
    </div>
  );
}
