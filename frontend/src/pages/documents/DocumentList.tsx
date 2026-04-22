import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/lib/api";

export default function DocumentList() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({ title: "", document_type_id: "", department: "" });

  const { data: types = [] } = useQuery({
    queryKey: ["document-types"],
    queryFn: documentsApi.listTypes,
  });
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ["documents", search],
    queryFn: () => documentsApi.listDocuments(search ? { search } : {}),
  });

  const createMutation = useMutation({
    mutationFn: () => documentsApi.createDocument(form),
    onSuccess: async () => {
      setShowNew(false);
      setForm({ title: "", document_type_id: "", department: "" });
      await qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const typeMap = useMemo(() => new Map((types as any[]).map((t) => [t.id, t])), [types]);

  return (
    <div className="p-8 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Document Control</h1>
          <p className="text-gray-500 text-sm mt-1">Controlled GMP documents and versions.</p>
        </div>
        <button className="bg-brand-600 text-white px-4 py-2 rounded" onClick={() => setShowNew(true)}>
          + New Document
        </button>
      </div>

      <input
        className="border rounded px-3 py-2 w-full max-w-md"
        placeholder="Search title or document number"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {["Document #", "Title", "Type", "Department", "Obsolete"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
            ) : (documents as any[]).length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No documents found.</td></tr>
            ) : (
              (documents as any[]).map((d: any) => (
                <tr key={d.id} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/documents/${d.id}`)}>
                  <td className="px-4 py-3 font-mono text-brand-600">{d.document_number}</td>
                  <td className="px-4 py-3">{d.title}</td>
                  <td className="px-4 py-3">{typeMap.get(d.document_type_id)?.prefix || "—"}</td>
                  <td className="px-4 py-3">{d.department || "—"}</td>
                  <td className="px-4 py-3">{d.is_obsolete ? "Yes" : "No"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showNew && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-6 space-y-3">
            <h2 className="text-lg font-semibold">Create Document</h2>
            <input
              className="border rounded px-3 py-2 w-full"
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm((s) => ({ ...s, title: e.target.value }))}
            />
            <select
              className="border rounded px-3 py-2 w-full"
              value={form.document_type_id}
              onChange={(e) => setForm((s) => ({ ...s, document_type_id: e.target.value }))}
            >
              <option value="">Select document type</option>
              {(types as any[]).map((t: any) => (
                <option key={t.id} value={t.id}>{t.prefix} - {t.name}</option>
              ))}
            </select>
            <input
              className="border rounded px-3 py-2 w-full"
              placeholder="Department (optional)"
              value={form.department}
              onChange={(e) => setForm((s) => ({ ...s, department: e.target.value }))}
            />
            <div className="flex gap-2 justify-end pt-2">
              <button className="px-4 py-2 border rounded" onClick={() => setShowNew(false)}>Cancel</button>
              <button
                className="px-4 py-2 bg-brand-600 text-white rounded disabled:opacity-50"
                disabled={createMutation.isPending || !form.title || !form.document_type_id}
                onClick={() => createMutation.mutate()}
              >
                {createMutation.isPending ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
