import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { qmsApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { toast } from "@/stores/toastStore";

export default function CAPADetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isSignOpen, setIsSignOpen] = useState(false);

  const { data: capa, isLoading } = useQuery({
    queryKey: ["qms-capa-detail", id],
    queryFn: () => qmsApi.getCapa(id!),
    enabled: Boolean(id),
  });

  const signMutation = useMutation({
    mutationFn: (payload: { password: string; meaning: string; comments: string }) =>
      qmsApi.signCapa(id!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["qms-capa-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["qms-capas"] });
      setIsSignOpen(false);
      toast.success("CAPA signature applied successfully.");
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "CAPA signature failed.");
    },
  });

  if (isLoading) {
    return <div className="p-8 text-gray-500">Loading CAPA detail...</div>;
  }

  if (!capa) {
    return <div className="p-8 text-gray-500">CAPA not found.</div>;
  }

  return (
    <div className="p-8 max-w-5xl space-y-5">
      <button
        onClick={() => navigate("/qms/capas")}
        className="text-sm text-gray-500 hover:text-gray-800"
      >
        ← Back to CAPA dashboard
      </button>

      <div className="bg-white rounded-xl shadow-sm p-6 flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-brand-700 font-semibold">{capa.capa_number}</p>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{capa.title}</h1>
          <p className="text-sm text-gray-500 mt-2">
            {capa.capa_type} • {capa.department} • {String(capa.current_status).replaceAll("_", " ")}
          </p>
        </div>
        <button
          onClick={() => setIsSignOpen(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg"
        >
          Close CAPA
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Risk Level">{capa.risk_level}</Card>
        <Card title="Target Completion Date">
          {capa.target_completion_date
            ? new Date(capa.target_completion_date).toLocaleDateString()
            : "-"}
        </Card>
        <Card title="Source">{capa.source}</Card>
        <Card title="Owner">{capa.owner_id ?? "-"}</Card>
      </div>

      <Card title="Problem Description">{capa.problem_description}</Card>
      <Card title="Immediate Actions">{capa.immediate_actions ?? "-"}</Card>
      <Card title="Root Cause">{capa.root_cause ?? "-"}</Card>

      <Card title={`Action Plan (${capa.actions?.length ?? 0})`}>
        {!capa.actions?.length ? (
          <p className="text-sm text-gray-500">No action items yet.</p>
        ) : (
          <div className="space-y-2">
            {capa.actions.map((action: any) => (
              <div
                key={action.id}
                className="border border-gray-100 rounded-lg px-3 py-2 text-sm"
              >
                <div className="font-medium text-gray-800">
                  {action.sequence_number}. {action.description}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Status: {action.status}{" "}
                  {action.due_date
                    ? `• Due ${new Date(action.due_date).toLocaleDateString()}`
                    : ""}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <ESignatureModal
        isOpen={isSignOpen}
        isLoading={signMutation.isPending}
        title="Close CAPA"
        description="Apply an electronic signature to close/approve this CAPA."
        meaning="approved"
        onClose={() => setIsSignOpen(false)}
        onConfirm={async ({ password, meaning, comments }) => {
          await signMutation.mutateAsync({ password, meaning, comments });
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
      <div className="text-sm text-gray-800">{children}</div>
    </div>
  );
}
