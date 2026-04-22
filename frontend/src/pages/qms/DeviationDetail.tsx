import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { toast } from "@/stores/toastStore";

type TransitionAction = "submit" | "approve" | "close";

export default function DeviationDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pendingAction, setPendingAction] = useState<TransitionAction | null>(null);

  const { data: deviation, isLoading } = useQuery({
    queryKey: ["qms-deviation", id],
    queryFn: () => qmsApi.getDeviation(id),
    enabled: Boolean(id),
  });

  const transitionMutation = useMutation({
    mutationFn: async (payload: { action: TransitionAction; password: string; comments: string }) => {
      const meaningMap: Record<TransitionAction, string> = {
        submit: "reviewed",
        approve: "approved",
        close: "closed",
      };
      await qmsApi.signDeviation(id, {
        password: payload.password,
        meaning: meaningMap[payload.action],
        comments: payload.comments,
      });
      return qmsApi.transitionDeviation(id, payload.action);
    },
    onSuccess: async () => {
      toast.success("Deviation transition completed.");
      setPendingAction(null);
      await queryClient.invalidateQueries({ queryKey: ["qms-deviation", id] });
      await queryClient.invalidateQueries({ queryKey: ["deviations"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Transition failed.");
    },
  });

  const availableActions = useMemo(() => {
    const status = deviation?.current_status;
    if (status === "draft") return ["submit"] as TransitionAction[];
    if (status === "under_review") return ["approve"] as TransitionAction[];
    if (status === "approved") return ["close"] as TransitionAction[];
    return [] as TransitionAction[];
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
        <p className="text-sm text-gray-700 whitespace-pre-wrap">{deviation.description}</p>
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
        <div className="flex gap-2">
          <button
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-50"
            disabled={!availableActions.includes("submit")}
            onClick={() => setPendingAction("submit")}
          >
            Submit
          </button>
          <button
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-50"
            disabled={!availableActions.includes("approve")}
            onClick={() => setPendingAction("approve")}
          >
            Approve
          </button>
          <button
            className="px-3 py-1.5 border rounded text-sm disabled:opacity-50"
            disabled={!availableActions.includes("close")}
            onClick={() => setPendingAction("close")}
          >
            Close
          </button>
        </div>
      </div>

      <button
        className="text-sm text-gray-500 hover:text-gray-800"
        onClick={() => navigate("/qms/deviations")}
      >
        ← Back to deviations
      </button>

      <ESignatureModal
        isOpen={Boolean(pendingAction)}
        isLoading={transitionMutation.isPending}
        title="Deviation State Transition"
        description={
          pendingAction
            ? `Apply signature and transition deviation via '${pendingAction}'.`
            : undefined
        }
        meaning={pendingAction === "approve" ? "approved" : pendingAction === "close" ? "closed" : "reviewed"}
        onClose={() => setPendingAction(null)}
        onConfirm={async ({ password, comments }) => {
          if (!pendingAction) return;
          await transitionMutation.mutateAsync({ action: pendingAction, password, comments });
        }}
      />
    </div>
  );
}

