import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";

type ChangeControlRecord = {
  id: string;
  change_number: string;
  title: string;
  change_type: string;
  change_category: string;
  description: string;
  justification: string;
  risk_assessment?: string | null;
  regulatory_impact: boolean;
  validation_required: boolean;
  current_status: string;
  proposed_implementation_date?: string | null;
  actual_implementation_date?: string | null;
  created_at: string;
};

export default function ChangeControlDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [password, setPassword] = useState("");
  const [meaning, setMeaning] = useState("approved");
  const [comments, setComments] = useState("");
  const [form, setForm] = useState({
    title: "",
    description: "",
    risk_assessment: "",
  });

  const { data, isLoading } = useQuery<ChangeControlRecord>({
    queryKey: ["qms-change-control", id],
    queryFn: () => qmsApi.getChangeControl(id),
    enabled: Boolean(id),
  });

  const canTransition = useMemo(() => {
    const s = data?.current_status;
    return {
      submit: s === "draft",
      approve: s === "under_review",
      implement: s === "approved",
      close: s === "implementation",
    };
  }, [data?.current_status]);

  const updateMutation = useMutation({
    mutationFn: () =>
      qmsApi.updateChangeControl(id, {
        title: form.title || undefined,
        description: form.description || undefined,
        risk_assessment: form.risk_assessment || undefined,
      }),
    onSuccess: async () => {
      setError("");
      setMessage("Change control updated.");
      await qc.invalidateQueries({ queryKey: ["qms-change-control", id] });
      await qc.invalidateQueries({ queryKey: ["change-controls"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to update change control.");
    },
  });

  const signMutation = useMutation({
    mutationFn: () => qmsApi.signChangeControl(id, { password, meaning, comments }),
    onSuccess: async () => {
      setError("");
      setMessage("Electronic signature applied.");
      setPassword("");
      setComments("");
      await qc.invalidateQueries({ queryKey: ["qms-change-control", id] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to sign change control.");
    },
  });

  const transitionMutation = useMutation({
    mutationFn: (action: "submit" | "approve" | "implement" | "close") =>
      qmsApi.transitionChangeControl(id, action),
    onSuccess: async () => {
      setError("");
      setMessage("Status transition completed.");
      await qc.invalidateQueries({ queryKey: ["qms-change-control", id] });
      await qc.invalidateQueries({ queryKey: ["change-controls"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Transition failed.");
    },
  });

  if (isLoading) {
    return <div className="p-8 text-gray-500">Loading change control...</div>;
  }
  if (!data) {
    return (
      <div className="p-8">
        <div className="text-gray-500 mb-3">Change control not found.</div>
        <button className="text-brand-600" onClick={() => navigate("/qms/change-controls")}>
          Back to list
        </button>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-4xl">
      <div className="text-sm text-gray-500">
        <Link to="/qms/change-controls" className="text-brand-600 hover:underline">
          Change Controls
        </Link>{" "}
        / {data.change_number}
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">{data.title}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data.change_number} • {data.change_type} • {data.change_category} • status:{" "}
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
          <div><span className="text-gray-500">Regulatory impact:</span> {data.regulatory_impact ? "Yes" : "No"}</div>
          <div><span className="text-gray-500">Validation required:</span> {data.validation_required ? "Yes" : "No"}</div>
          <div><span className="text-gray-500">Proposed implementation:</span> {data.proposed_implementation_date ? new Date(data.proposed_implementation_date).toLocaleString() : "—"}</div>
          <div><span className="text-gray-500">Actual implementation:</span> {data.actual_implementation_date ? new Date(data.actual_implementation_date).toLocaleString() : "—"}</div>
        </div>
        <div>
          <p className="text-gray-500 text-sm mb-1">Description</p>
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{data.description}</p>
        </div>
        <div>
          <p className="text-gray-500 text-sm mb-1">Justification</p>
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{data.justification}</p>
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Update Fields</h2>
        <input
          className="w-full border rounded p-2 text-sm"
          placeholder={data.title}
          value={form.title}
          onChange={(e) => setForm((s) => ({ ...s, title: e.target.value }))}
        />
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
          placeholder={data.risk_assessment || "Risk assessment"}
          value={form.risk_assessment}
          onChange={(e) => setForm((s) => ({ ...s, risk_assessment: e.target.value }))}
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
            disabled={!canTransition.implement || transitionMutation.isPending}
            onClick={() => transitionMutation.mutate("implement")}
          >
            Implement
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
