import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { mesApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

const statusColour: Record<string, string> = {
  in_progress: "bg-blue-100 text-blue-700",
  pending_release: "bg-yellow-100 text-yellow-800",
  released: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function BatchRecordDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: batch, isLoading } = useQuery({
    queryKey: ["batch-record", id],
    queryFn: () => mesApi.getBatchRecord(id!),
    enabled: Boolean(id),
  });

  const executeStepMutation = useMutation({
    mutationFn: (stepId: string) =>
      mesApi.executeStep(id!, stepId, {
        recorded_value: "Executed",
        is_na: false,
        comments: "Executed from MES detail screen.",
      }),
    onSuccess: () => {
      toast.success("Step executed.");
      queryClient.invalidateQueries({ queryKey: ["batch-record", id] });
      queryClient.invalidateQueries({ queryKey: ["batch-records"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Step execution failed.");
    },
  });

  const steps = useMemo(() => (batch?.steps as any[]) ?? [], [batch]);

  if (isLoading) return <div className="p-8 text-gray-500">Loading batch detail...</div>;
  if (!batch) return <div className="p-8 text-gray-500">Batch record not found.</div>;

  return (
    <div className="p-8 space-y-5">
      <button
        className="text-sm text-gray-500 hover:text-gray-800"
        onClick={() => navigate("/mes/batch-records")}
      >
        ← Back to batch records
      </button>

      <div className="bg-white rounded-xl shadow-sm p-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{batch.batch_number}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Product: {batch.product_name ?? batch.product_id ?? "—"}
          </p>
          <p className="text-sm text-gray-500 mt-0.5">
            Started at:{" "}
            {batch.actual_start
              ? new Date(batch.actual_start).toLocaleString()
              : batch.created_at
              ? new Date(batch.created_at).toLocaleString()
              : "—"}
          </p>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            statusColour[batch.status] ?? "bg-gray-100 text-gray-700"
          }`}
        >
          {String(batch.status).replaceAll("_", " ")}
        </span>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Batch Steps
          </h2>
          <span className="text-xs text-gray-400">
            {steps.filter((s: any) => s.status === "completed").length}/{steps.length} complete
          </span>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["#", "Status", "Recorded Value", "Performed At", "Action"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {steps.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No steps found for this batch.
                </td>
              </tr>
            ) : (
              steps.map((step: any) => {
                const isExecuted = Boolean(step.performed_at) || step.status === "completed";
                return (
                  <tr key={step.id} className={isExecuted ? "bg-gray-50" : ""}>
                    <td className="px-4 py-3 font-mono text-gray-600">{step.step_number}</td>
                    <td className="px-4 py-3">{step.status}</td>
                    <td className="px-4 py-3">{step.recorded_value ?? "—"}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {step.performed_at ? new Date(step.performed_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-4 py-3">
                      {isExecuted ? (
                        <span className="text-xs px-2 py-1 rounded bg-gray-200 text-gray-600">
                          Locked
                        </span>
                      ) : (
                        <button
                          onClick={() => executeStepMutation.mutate(step.id)}
                          disabled={executeStepMutation.isPending}
                          className="text-xs font-semibold px-3 py-1.5 rounded bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50"
                        >
                          Execute Step
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-gray-500">
        Batch release is handled from this flow once all steps are executed and locked.
        <Link to="/mes/batch-records" className="text-brand-600 hover:text-brand-700 ml-1">
          Return to list
        </Link>
      </div>
    </div>
  );
}

