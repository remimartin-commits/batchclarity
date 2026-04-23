import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { trainingApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { toast } from "@/stores/toastStore";

export default function TrainingList() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [signAssignmentId, setSignAssignmentId] = useState<string | null>(null);

  const { data: assignments = [], isLoading } = useQuery({
    queryKey: ["training-my-assignments"],
    queryFn: trainingApi.myAssignments,
  });

  const completeMutation = useMutation({
    mutationFn: async (payload: { assignmentId: string; username: string; password: string; comments: string }) => {
      await trainingApi.readAndUnderstood(payload.assignmentId, {
        password: payload.password,
        notes: payload.comments || "Read and understood acknowledgement.",
      });
    },
    onSuccess: async () => {
      toast.success("Training assignment completed with e-signature.");
      setSignAssignmentId(null);
      await queryClient.invalidateQueries({ queryKey: ["training-my-assignments"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Assignment completion failed.");
    },
  });

  const visibleAssignments = (assignments as any[]).filter((a: any) =>
    statusFilter === "all" ? true : a.status === statusFilter
  );

  return (
    <div className="p-8 space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Assignments</h1>
        <p className="text-gray-500 text-sm mt-1">
          Complete pending items using electronic signature (read_and_understood).
        </p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["all", "pending", "overdue", "completed"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 border rounded text-sm ${
              statusFilter === s ? "bg-brand-600 text-white border-brand-600" : "bg-white"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Assignment", "Curriculum Item", "Due Date", "Status", "Action"].map((h) => (
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
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  Loading assignments...
                </td>
              </tr>
            ) : visibleAssignments.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No assignments in this status.
                </td>
              </tr>
            ) : (
              visibleAssignments.map((assignment: any) => {
                const isLocked = assignment.status === "completed";
                return (
                  <tr key={assignment.id} className={isLocked ? "bg-gray-50" : ""}>
                    <td className="px-4 py-3 font-mono text-xs text-gray-600">{assignment.id}</td>
                    <td className="px-4 py-3 text-gray-700">
                      {assignment.curriculum_item_id ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {assignment.due_date
                        ? new Date(assignment.due_date).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3">{assignment.status}</td>
                    <td className="px-4 py-3">
                      {isLocked ? (
                        <span className="text-xs px-2 py-1 rounded bg-gray-200 text-gray-600">
                          Locked
                        </span>
                      ) : assignment.status === "pending" || assignment.status === "overdue" ? (
                        <button
                          className="text-xs font-semibold px-3 py-1.5 rounded bg-brand-600 text-white hover:bg-brand-700"
                          onClick={() => setSignAssignmentId(assignment.id)}
                        >
                          Complete
                        </button>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <ESignatureModal
        isOpen={Boolean(signAssignmentId)}
        isLoading={completeMutation.isPending}
        title="Complete Training Assignment"
        description="Apply your signature as read_and_understood to complete this assignment."
        meaning="read_and_understood"
        availableMeanings={["read_and_understood"]}
        onClose={() => setSignAssignmentId(null)}
        onConfirm={async ({ username, password, comments }) => {
          if (!signAssignmentId) return;
          await completeMutation.mutateAsync({
            assignmentId: signAssignmentId,
            username,
            password,
            comments,
          });
        }}
      />
    </div>
  );
}

