import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { rolesApi } from "@/lib/api";

export default function RolesAdmin() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedCodes, setSelectedCodes] = useState<string[]>([]);
  const [apiError, setApiError] = useState("");
  const [apiMessage, setApiMessage] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 8;

  const { data: roles = [] } = useQuery({ queryKey: ["admin-roles"], queryFn: rolesApi.listRoles });
  const { data: permissions = [] } = useQuery({
    queryKey: ["admin-permissions"],
    queryFn: rolesApi.listPermissions,
  });

  const createRole = useMutation({
    mutationFn: rolesApi.createRole,
    onSuccess: () => {
      setApiError("");
      setApiMessage("Role created.");
      setName("");
      setDescription("");
      setSelectedCodes([]);
      qc.invalidateQueries({ queryKey: ["admin-roles"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setApiError(Array.isArray(d) ? d.join("; ") : d || "Failed to create role.");
    },
  });

  const deleteRole = useMutation({
    mutationFn: rolesApi.deleteRole,
    onSuccess: () => {
      setApiError("");
      setApiMessage("Role deleted.");
      qc.invalidateQueries({ queryKey: ["admin-roles"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setApiError(Array.isArray(d) ? d.join("; ") : d || "Failed to delete role.");
    },
  });

  const updateRole = useMutation({
    mutationFn: ({ roleId, payload }: { roleId: string; payload: unknown }) =>
      rolesApi.updateRole(roleId, payload),
    onSuccess: () => {
      setApiError("");
      setApiMessage("Role updated.");
      qc.invalidateQueries({ queryKey: ["admin-roles"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setApiError(Array.isArray(d) ? d.join("; ") : d || "Failed to update role.");
    },
  });
  const filteredRoles = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (roles as any[]).filter((r: any) => {
      if (!q) return true;
      return `${r.name} ${r.description || ""}`.toLowerCase().includes(q);
    });
  }, [roles, search]);
  const totalPages = Math.max(1, Math.ceil(filteredRoles.length / pageSize));
  const pagedRoles = filteredRoles.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin — Roles</h1>
        <p className="text-gray-500 mt-1">Define roles and attach permission codes.</p>
      </div>
      {apiError && <div className="p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">{apiError}</div>}
      {apiMessage && (
        <div className="p-3 rounded-lg bg-green-50 text-green-700 border border-green-200">{apiMessage}</div>
      )}

      <section className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Create role</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createRole.mutate({
              name,
              description,
              permission_codes: selectedCodes,
              is_system_role: false,
            });
          }}
          className="space-y-3"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input className="border rounded px-3 py-2" placeholder="Role name" value={name} onChange={(e) => setName(e.target.value)} required />
            <input className="border rounded px-3 py-2" placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="border rounded-lg p-3 max-h-48 overflow-auto grid grid-cols-1 md:grid-cols-2 gap-2">
            {permissions.map((p: any) => (
              <label key={p.id} className="text-sm flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedCodes.includes(p.code)}
                  onChange={(e) => {
                    setSelectedCodes((prev) =>
                      e.target.checked ? [...prev, p.code] : prev.filter((x) => x !== p.code)
                    );
                  }}
                />
                <span>{p.code}</span>
              </label>
            ))}
          </div>
          <button className="bg-brand-600 text-white px-4 py-2 rounded disabled:opacity-50" disabled={createRole.isPending}>
            {createRole.isPending ? "Creating..." : "Create role"}
          </button>
        </form>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Existing roles</h2>
        <div className="mb-4 flex flex-wrap gap-2">
          <input
            className="border rounded px-3 py-2 text-sm min-w-[220px]"
            placeholder="Search role name / description"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
          <div className="text-sm text-gray-500 self-center">{filteredRoles.length} roles</div>
        </div>
        <div className="space-y-3">
          {pagedRoles.map((r: any) => (
            <div key={r.id} className="border rounded-lg p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold">{r.name}</p>
                  <p className="text-sm text-gray-500">{r.description || "No description"}</p>
                  <p className="text-xs mt-1">Permissions: {(r.permissions || []).join(", ") || "none"}</p>
                </div>
                <div className="flex gap-2">
                  {!r.is_system_role && (
                    <button
                      className="text-sm px-3 py-1.5 border rounded hover:bg-gray-50 disabled:opacity-50"
                      disabled={updateRole.isPending}
                      onClick={() =>
                        updateRole.mutate({
                          roleId: r.id,
                          payload: { description: r.description, permission_codes: r.permissions || [] },
                        })
                      }
                    >
                      Re-save
                    </button>
                  )}
                  {!r.is_system_role && (
                    <button
                      className="text-sm px-3 py-1.5 border rounded text-red-700 hover:bg-red-50 disabled:opacity-50"
                      disabled={deleteRole.isPending}
                      onClick={() => {
                        if (!window.confirm(`Delete role '${r.name}'? This cannot be undone.`)) return;
                        deleteRole.mutate(r.id);
                      }}
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          {pagedRoles.length === 0 && (
            <div className="text-sm text-gray-500 text-center py-6 border rounded-lg">
              No roles match your search.
            </div>
          )}
          <div className="flex items-center justify-between pt-2">
            <button
              className="px-3 py-1.5 border rounded text-sm disabled:opacity-50"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <div className="text-sm text-gray-500">
              Page {page} / {totalPages}
            </div>
            <button
              className="px-3 py-1.5 border rounded text-sm disabled:opacity-50"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
