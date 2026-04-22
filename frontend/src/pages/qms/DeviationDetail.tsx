import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";

type DeviationRecord = {
  id: string;
  deviation_number: string;
  title: string;
  deviation_type: string;
  category: string;
  description: string;
  risk_level: string;
  current_status: string;
  detection_date: string;
  batch_number?: string | null;
  immediate_action?: string | null;
  root_cause?: string | null;
  linked_capa_id?: string | null;
  created_at: string;
};

export default function DeviationDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [meaning, setMeaning] = useState("reviewed");
  const [comments, setComments] = useState("");
  const [form, setForm] = useState({
    description: "",
    immediate_action: "",
    root_cause: "",
  });

  const { data, isLoading } = useQuery<DeviationRecord>({
    queryKey: ["qms-deviation", id],
    queryFn: () => qmsApi.getDeviation(id),
    enabled: Boolean(id),
  });

  const canTransition = useMemo(() => {
    const s = data?.current_status;
    return {
      submit: s === "draft",
      approve: s === "under_review",
      close: s === "approved",
    };
  }, [data?.current_status]);

  const updateMutation = useMutation({
    mutationFn: () =>
      qmsApi.updateDeviation(id, {
        description: form.description || undefined,
        immediate_action: form.immediate_action || undefined,
        root_cause: form.root_cause || undefined,
      }),
    onSuccess: async () => {
      setError("");
      setMessage("Deviation updated.");
      await qc.invalidateQueries({ queryKey: ["qms-deviation", id] });
      await qc.invalidateQueries({ queryKey: ["deviations"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to update deviation.");
    },
  });

  const signMutation = useMutation({
    mutationFn: () => qmsApi.signDeviation(id, { password, meaning, comments }),
    onSuccess: async () => {
      setError("");
      setMessage("Electronic signature applied.");
      setPassword("");
      setComments("");
      await qc.invalidateQueries({ queryKey: ["qms-deviation", id] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to sign deviation.");
    },
  });

  const transitionMutation = useMutation({
    mutationFn: (action: "submit" | "approve" | "close") =>
      qmsApi.transitionDeviation(id, action),
    onSuccess: async () => {
      setError("");
      setMessage("Status transition completed.");
      await qc.invalidateQueries({ queryKey: ["qms-deviation", id] });
      await qc.invalidateQueries({ queryKey: ["deviations"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Transition failed.");
    },
  });

  if (isLoading) {
    return <div className="p-8 text-gray-500">Loading deviation...</div>;
  }
  if (!data) {
    return (
      <div className="p-8">
        <div className="text-gray-500 mb-3">Deviation not found.</div>
        <button className="text-brand-600" onClick={() => navigate("/qms/deviations")}>
          Back to list
        </button>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-4xl">
      <div className="text-sm text-gray-500">
        <Link to="/qms/deviations" className="text-brand-600 hover:underline">
          Deviations
        </Link>{" "}
        / {data.deviation_number}
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">{data.title}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data.deviation_number} • {data.deviation_type} • {data.category} • status:{" "}
          {data.current_status.replace(/_/g, " ")}
        </p>
      </div>

      {error && <div className="p-3 rounded border border-red-200 bg-red-50 text-red-700">{error}</div>}
      {message && (
        <div className="p-3 rounded border border-green-200 bg-green-50 text-green-700">{message}</div>
      )}

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-4">
        <h2 className="font-semibold">Record Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div><span className="text-gray-500">Risk:</span> {data.risk_level}</div>
          <div><span className="text-gray-500">Detection date:</span> {new Date(data.detection_date).toLocaleString()}</div>
          <div><span className="text-gray-500">Batch:</span> {data.batch_number || "—"}</div>
          <div><span className="text-gray-500">Created:</span> {new Date(data.created_at).toLocaleString()}</div>
        </div>
        <div>
          <p className="text-gray-500 text-sm mb-1">Description</p>
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{data.description}</p>
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Update Investigation Fields</h2>
        <textarea
          className="w-full border rounded p-2 text-sm"
          rows={3}
          placeholder={data.description}
          value={form.description}
          onChange={(e) => setForm((s) => ({ ...s, description: e.target.value }))}
        />
        <textarea
          className="w-full border rounded p-2 text-sm"
          rows={2}
          placeholder={data.immediate_action || "Immediate action"}
          value={form.immediate_action}
          onChange={(e) => setForm((s) => ({ ...s, immediate_action: e.target.value }))}
        />
        <textarea
          className="w-full border rounded p-2 text-sm"
          rows={2}
          placeholder={data.root_cause || "Root cause"}
          value={form.root_cause}
          onChange={(e) => setForm((s) => ({ ...s, root_cause: e.target.value }))}
        />
        <button
          className="px-4 py-2 rounded bg-brand-600 text-white disabled:opacity-50"
          disabled={updateMutation.isPending}
          onClick={() => updateMutation.mutate()}
        >
          {updateMutation.isPending ? "Saving..." : "Save Updates"}
        </button>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Workflow Transition</h2>
        <div className="flex flex-wrap gap-2">
          <button
            className="px-3 py-1.5 border rounded disabled:opacity-50"
            disabled={!canTransition.submit || transitionMutation.isPending}
            onClick={() => transitionMutation.mutate("submit")}
          >
            Submit
          </button>
          <button
            className="px-3 py-1.5 border rounded disabled:opacity-50"
            disabled={!canTransition.approve || transitionMutation.isPending}
            onClick={() => transitionMutation.mutate("approve")}
          >
            Approve
          </button>
          <button
            className="px-3 py-1.5 border rounded disabled:opacity-50"
            disabled={!canTransition.close || transitionMutation.isPending}
            onClick={() => transitionMutation.mutate("close")}
          >
            Close
          </button>
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Electronic Signature</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <select
            className="border rounded px-3 py-2"
            value={meaning}
            onChange={(e) => setMeaning(e.target.value)}
          >
            <option value="reviewed">Reviewed</option>
            <option value="approved">Approved</option>
            <option value="closed">Closed</option>
          </select>
          <input
            type="password"
            className="border rounded px-3 py-2"
            placeholder="Re-enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <input
            className="border rounded px-3 py-2"
            placeholder="Comment (optional)"
            value={comments}
            onChange={(e) => setComments(e.target.value)}
          />
        </div>
        <button
          className="px-4 py-2 rounded bg-gray-900 text-white disabled:opacity-50"
          disabled={signMutation.isPending || !password}
          onClick={() => signMutation.mutate()}
        >
          {signMutation.isPending ? "Signing..." : "Apply Signature"}
        </button>
      </section>
    </div>
  );
}
