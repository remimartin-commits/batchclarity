import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";

export default function CAPADetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [signModal, setSignModal] = useState(false);
  const [sigPassword, setSigPassword] = useState("");
  const [sigMeaning, setSigMeaning] = useState("approved");
  const [sigComments, setSigComments] = useState("");
  const [sigError, setSigError] = useState("");

  const { data: capa, isLoading } = useQuery({
    queryKey: ["capa", id],
    queryFn: () => qmsApi.getCapa(id!),
    enabled: !!id,
  });

  const signMutation = useMutation({
    mutationFn: () => qmsApi.signCapa(id!, { password: sigPassword, meaning: sigMeaning, comments: sigComments }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["capa", id] });
      queryClient.invalidateQueries({ queryKey: ["capas"] });
      setSignModal(false);
      setSigPassword("");
      setSigError("");
    },
    onError: (err: any) => setSigError(err.response?.data?.detail ?? "Signature failed."),
  });

  if (isLoading) return <div className="p-8 text-gray-400">Loading...</div>;
  if (!capa) return <div className="p-8 text-gray-400">CAPA not found.</div>;

  const riskBadge: Record<string, string> = {
    low: "bg-green-100 text-green-700", medium: "bg-yellow-100 text-yellow-700",
    high: "bg-orange-100 text-orange-700", critical: "bg-red-100 text-red-700",
  };

  return (
    <div className="p-8 max-w-4xl">
      {/* Back */}
      <button onClick={() => navigate("/qms/capas")} className="text-sm text-gray-400 hover:text-gray-600 mb-4 flex items-center gap-1">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to CAPAs
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="font-mono text-brand-600 font-semibold">{capa.capa_number}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riskBadge[capa.risk_level]}`}>{capa.risk_level}</span>
            {capa.patient_safety_impact && <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">Patient Safety</span>}
          </div>
          <h1 className="text-xl font-bold text-gray-900">{capa.title}</h1>
          <p className="text-gray-500 text-sm mt-1">{capa.capa_type} · {capa.department} · {capa.current_status.replace(/_/g, " ")}</p>
        </div>
        <button
          onClick={() => setSignModal(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          Sign / Approve
        </button>
      </div>

      {/* Details */}
      <div className="space-y-6">
        <Section title="Problem Description"><p className="text-gray-700 text-sm leading-relaxed">{capa.problem_description}</p></Section>
        {capa.immediate_actions && <Section title="Immediate Actions"><p className="text-gray-700 text-sm">{capa.immediate_actions}</p></Section>}
        {capa.root_cause && <Section title="Root Cause"><p className="text-gray-700 text-sm">{capa.root_cause}</p></Section>}

        {/* Actions */}
        <Section title={`Action Plan (${capa.actions?.length ?? 0} items)`}>
          {!capa.actions?.length ? (
            <p className="text-gray-400 text-sm">No actions defined yet.</p>
          ) : (
            <div className="space-y-3">
              {capa.actions.map((action: any) => (
                <div key={action.id} className={`border rounded-lg p-4 ${action.is_frozen ? "border-orange-200 bg-orange-50" : "border-gray-100 bg-gray-50"}`}>
                  <div className="flex justify-between items-start">
                    <p className="text-sm font-medium text-gray-900">{action.sequence_number}. {action.description}</p>
                    <div className="flex gap-2 ml-4">
                      {action.is_frozen && <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">Frozen</span>}
                      <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{action.status}</span>
                    </div>
                  </div>
                  {action.freeze_reason && <p className="text-xs text-orange-600 mt-1">Freeze reason: {action.freeze_reason}</p>}
                  {action.due_date && <p className="text-xs text-gray-400 mt-1">Due: {new Date(action.due_date).toLocaleDateString()}</p>}
                </div>
              ))}
            </div>
          )}
        </Section>
      </div>

      {/* E-Signature Modal */}
      {signModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Electronic Signature</h3>
            <p className="text-xs text-gray-400 mb-4">21 CFR Part 11 — password re-entry required</p>
            {sigError && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{sigError}</div>}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Signature meaning</label>
                <select value={sigMeaning} onChange={(e) => setSigMeaning(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500">
                  <option value="reviewed">Reviewed</option>
                  <option value="approved">Approved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Your password</label>
                <input type="password" value={sigPassword} onChange={(e) => setSigPassword(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
                  placeholder="Re-enter your password to sign" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Comments (optional)</label>
                <textarea value={sigComments} onChange={(e) => setSigComments(e.target.value)} rows={2}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500" />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => { setSignModal(false); setSigError(""); }} className="flex-1 border border-gray-200 text-gray-700 font-medium py-2 rounded-lg text-sm hover:bg-gray-50">Cancel</button>
              <button onClick={() => signMutation.mutate()} disabled={!sigPassword || signMutation.isPending}
                className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-2 rounded-lg text-sm">
                {signMutation.isPending ? "Signing..." : "Apply Signature"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">{title}</h3>
      {children}
    </div>
  );
}
