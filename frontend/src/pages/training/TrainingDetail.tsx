import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { trainingApi } from "@/lib/api";

export default function TrainingDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [completeForm, setCompleteForm] = useState({
    completion_method: "self_study",
    assessment_score: "",
    passed: true,
    notes: "",
  });
  const [signPassword, setSignPassword] = useState("");
  const [signNotes, setSignNotes] = useState("");

  const { data: assignment, isLoading } = useQuery({
    queryKey: ["training-assignment", id],
    queryFn: () => trainingApi.getAssignment(id),
    enabled: Boolean(id),
  });

  const completeMutation = useMutation({
    mutationFn: () =>
      trainingApi.complete(id, {
        completion_method: completeForm.completion_method,
        assessment_score: completeForm.assessment_score ? Number(completeForm.assessment_score) : undefined,
        passed: completeForm.passed,
        notes: completeForm.notes || undefined,
      }),
    onSuccess: async () => {
      setError("");
      setMessage("Assignment completion recorded.");
      await qc.invalidateQueries({ queryKey: ["training-assignment", id] });
      await qc.invalidateQueries({ queryKey: ["training-assignments"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to complete assignment.");
    },
  });

  const rauMutation = useMutation({
    mutationFn: () => trainingApi.readAndUnderstood(id, { password: signPassword, notes: signNotes || undefined }),
    onSuccess: async () => {
      setError("");
      setMessage("Read and understood signature recorded.");
      setSignPassword("");
      setSignNotes("");
      await qc.invalidateQueries({ queryKey: ["training-assignment", id] });
      await qc.invalidateQueries({ queryKey: ["training-assignments"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to sign.");
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading assignment...</div>;
  if (!assignment) {
    return (
      <div className="p-8">
        <div className="text-gray-500 mb-3">Assignment not found.</div>
        <button className="text-brand-600" onClick={() => navigate("/training")}>Back to list</button>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-3xl">
      <div className="text-sm text-gray-500">
        <Link to="/training" className="text-brand-600 hover:underline">Training</Link> / {(assignment as any).id}
      </div>
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Training Assignment</h1>
        <p className="text-sm text-gray-500 mt-1">
          user: {(assignment as any).user_id} • item: {(assignment as any).curriculum_item_id} • status: {(assignment as any).status}
        </p>
      </div>

      {error && <div className="p-3 rounded border border-red-200 bg-red-50 text-red-700">{error}</div>}
      {message && <div className="p-3 rounded border border-green-200 bg-green-50 text-green-700">{message}</div>}

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-2 text-sm">
        <div><span className="text-gray-500">Assigned at:</span> {(assignment as any).assigned_at ? new Date((assignment as any).assigned_at).toLocaleString() : "—"}</div>
        <div><span className="text-gray-500">Due date:</span> {(assignment as any).due_date ? new Date((assignment as any).due_date).toLocaleString() : "—"}</div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Complete Assignment</h2>
        <select className="border rounded px-3 py-2 w-full" value={completeForm.completion_method} onChange={(e) => setCompleteForm((s) => ({ ...s, completion_method: e.target.value }))}>
          <option value="self_study">self_study</option>
          <option value="classroom">classroom</option>
          <option value="on_job">on_job</option>
        </select>
        <input className="border rounded px-3 py-2 w-full" placeholder="Assessment score (optional)" value={completeForm.assessment_score} onChange={(e) => setCompleteForm((s) => ({ ...s, assessment_score: e.target.value }))} />
        <select className="border rounded px-3 py-2 w-full" value={completeForm.passed ? "true" : "false"} onChange={(e) => setCompleteForm((s) => ({ ...s, passed: e.target.value === "true" }))}>
          <option value="true">passed</option>
          <option value="false">failed</option>
        </select>
        <textarea className="border rounded px-3 py-2 w-full" rows={3} placeholder="Notes (optional)" value={completeForm.notes} onChange={(e) => setCompleteForm((s) => ({ ...s, notes: e.target.value }))} />
        <button className="px-4 py-2 bg-brand-600 text-white rounded disabled:opacity-50" disabled={completeMutation.isPending} onClick={() => completeMutation.mutate()}>
          {completeMutation.isPending ? "Saving..." : "Record Completion"}
        </button>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Read & Understood Signature</h2>
        <input type="password" className="border rounded px-3 py-2 w-full" placeholder="Re-enter password" value={signPassword} onChange={(e) => setSignPassword(e.target.value)} />
        <textarea className="border rounded px-3 py-2 w-full" rows={2} placeholder="Notes (optional)" value={signNotes} onChange={(e) => setSignNotes(e.target.value)} />
        <button className="px-4 py-2 bg-gray-900 text-white rounded disabled:opacity-50" disabled={rauMutation.isPending || !signPassword} onClick={() => rauMutation.mutate()}>
          {rauMutation.isPending ? "Signing..." : "Sign Read & Understood"}
        </button>
      </section>
    </div>
  );
}
