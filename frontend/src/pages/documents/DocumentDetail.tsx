import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/lib/api";

export default function DocumentDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [versionForm, setVersionForm] = useState({
    version_number: "",
    content: "",
    change_summary: "",
    change_reason: "",
  });
  const [signForm, setSignForm] = useState({
    version_id: "",
    password: "",
    meaning: "reviewed",
    comments: "",
  });

  const { data: doc, isLoading } = useQuery({
    queryKey: ["document", id],
    queryFn: () => documentsApi.getDocument(id),
    enabled: Boolean(id),
  });
  const { data: versions = [] } = useQuery({
    queryKey: ["document-versions", id],
    queryFn: () => documentsApi.listVersions(id),
    enabled: Boolean(id),
  });

  const createVersion = useMutation({
    mutationFn: () => documentsApi.createVersion(id, versionForm),
    onSuccess: async () => {
      setError("");
      setMessage("New version created.");
      setVersionForm({ version_number: "", content: "", change_summary: "", change_reason: "" });
      await qc.invalidateQueries({ queryKey: ["document-versions", id] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to create version.");
    },
  });

  const signVersion = useMutation({
    mutationFn: () =>
      documentsApi.signVersion(id, signForm.version_id, {
        password: signForm.password,
        meaning: signForm.meaning,
        comments: signForm.comments,
      }),
    onSuccess: async () => {
      setError("");
      setMessage("Version signed.");
      setSignForm((s) => ({ ...s, password: "", comments: "" }));
      await qc.invalidateQueries({ queryKey: ["document-versions", id] });
      await qc.invalidateQueries({ queryKey: ["document", id] });
      await qc.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to sign version.");
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading document...</div>;
  if (!doc) {
    return (
      <div className="p-8">
        <div className="text-gray-500 mb-3">Document not found.</div>
        <button className="text-brand-600" onClick={() => navigate("/documents")}>Back to list</button>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-4xl">
      <div className="text-sm text-gray-500">
        <Link to="/documents" className="text-brand-600 hover:underline">Documents</Link> / {(doc as any).document_number}
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">{(doc as any).title}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {(doc as any).document_number} • department: {(doc as any).department || "—"} • obsolete: {(doc as any).is_obsolete ? "Yes" : "No"}
        </p>
      </div>

      {error && <div className="p-3 rounded border border-red-200 bg-red-50 text-red-700">{error}</div>}
      {message && <div className="p-3 rounded border border-green-200 bg-green-50 text-green-700">{message}</div>}

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Versions</h2>
        <div className="border rounded">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {["Version", "Status", "Authored", "Approved", "Effective", "ID"].map((h) => (
                  <th key={h} className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(versions as any[]).length === 0 ? (
                <tr><td colSpan={6} className="px-3 py-6 text-center text-gray-400">No versions yet.</td></tr>
              ) : (
                (versions as any[]).map((v: any) => (
                  <tr key={v.id} className="border-b">
                    <td className="px-3 py-2 font-mono">v{v.version_number}</td>
                    <td className="px-3 py-2">{v.status}</td>
                    <td className="px-3 py-2">{v.authored_date ? new Date(v.authored_date).toLocaleString() : "—"}</td>
                    <td className="px-3 py-2">{v.approved_date ? new Date(v.approved_date).toLocaleString() : "—"}</td>
                    <td className="px-3 py-2">{v.effective_date ? new Date(v.effective_date).toLocaleString() : "—"}</td>
                    <td className="px-3 py-2 text-xs font-mono">{v.id}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Create Version</h2>
        <input className="border rounded px-3 py-2 w-full" placeholder="Version number (e.g. 1.0)" value={versionForm.version_number} onChange={(e) => setVersionForm((s) => ({ ...s, version_number: e.target.value }))} />
        <textarea className="border rounded px-3 py-2 w-full" rows={3} placeholder="Content (optional)" value={versionForm.content} onChange={(e) => setVersionForm((s) => ({ ...s, content: e.target.value }))} />
        <input className="border rounded px-3 py-2 w-full" placeholder="Change summary" value={versionForm.change_summary} onChange={(e) => setVersionForm((s) => ({ ...s, change_summary: e.target.value }))} />
        <input className="border rounded px-3 py-2 w-full" placeholder="Change reason (required for revision)" value={versionForm.change_reason} onChange={(e) => setVersionForm((s) => ({ ...s, change_reason: e.target.value }))} />
        <button className="px-4 py-2 bg-brand-600 text-white rounded disabled:opacity-50" disabled={createVersion.isPending || !versionForm.version_number} onClick={() => createVersion.mutate()}>
          {createVersion.isPending ? "Creating..." : "Create Version"}
        </button>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Sign Version</h2>
        <select className="border rounded px-3 py-2 w-full" value={signForm.version_id} onChange={(e) => setSignForm((s) => ({ ...s, version_id: e.target.value }))}>
          <option value="">Select version</option>
          {(versions as any[]).map((v: any) => (
            <option key={v.id} value={v.id}>{v.version_number} ({v.status})</option>
          ))}
        </select>
        <select className="border rounded px-3 py-2 w-full" value={signForm.meaning} onChange={(e) => setSignForm((s) => ({ ...s, meaning: e.target.value }))}>
          <option value="reviewed">reviewed</option>
          <option value="approved">approved</option>
          <option value="effective">effective</option>
          <option value="obsolete">obsolete</option>
        </select>
        <input type="password" className="border rounded px-3 py-2 w-full" placeholder="Re-enter password" value={signForm.password} onChange={(e) => setSignForm((s) => ({ ...s, password: e.target.value }))} />
        <input className="border rounded px-3 py-2 w-full" placeholder="Comment (optional)" value={signForm.comments} onChange={(e) => setSignForm((s) => ({ ...s, comments: e.target.value }))} />
        <button className="px-4 py-2 bg-gray-900 text-white rounded disabled:opacity-50" disabled={signVersion.isPending || !signForm.version_id || !signForm.password} onClick={() => signVersion.mutate()}>
          {signVersion.isPending ? "Signing..." : "Apply Signature"}
        </button>
      </section>
    </div>
  );
}
