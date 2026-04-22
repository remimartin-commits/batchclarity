import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { rolesApi, usersApi } from "@/lib/api";

export default function UsersAdmin() {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    username: "",
    email: "",
    full_name: "",
    password: "",
    site_id: "",
    is_active: true,
  });
  const [selectedRoleByUser, setSelectedRoleByUser] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState("");
  const [apiMessage, setApiMessage] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");
  const [page, setPage] = useState(1);
  const pageSize = 8;

  const { data: users = [] } = useQuery({ queryKey: ["admin-users"], queryFn: usersApi.listUsers });
  const { data: roles = [] } = useQuery({ queryKey: ["admin-roles"], queryFn: rolesApi.listRoles });

  const createUser = useMutation({
    mutationFn: usersApi.createUser,
    onSuccess: () => {
      setApiError("");
      setApiMessage("User created successfully.");
      setForm({ username: "", email: "", full_name: "", password: "", site_id: "", is_active: true });
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setApiError(Array.isArray(d) ? d.join("; ") : d || "Failed to create user.");
    },
  });

  const deactivateUser = useMutation({
    mutationFn: usersApi.deactivateUser,
    onSuccess: () => {
      setApiError("");
      setApiMessage("User deactivated.");
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setApiError(Array.isArray(d) ? d.join("; ") : d || "Failed to deactivate user.");
    },
  });

  const assignRole = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) => usersApi.assignRole(userId, roleId),
    onSuccess: () => {
      setApiError("");
      setApiMessage("Role assigned.");
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setApiError(Array.isArray(d) ? d.join("; ") : d || "Failed to assign role.");
    },
  });

  const revokeRole = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) => usersApi.revokeRole(userId, roleId),
    onSuccess: () => {
      setApiError("");
      setApiMessage("Role revoked.");
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setApiError(Array.isArray(d) ? d.join("; ") : d || "Failed to revoke role.");
    },
  });

  const roleOptions = useMemo(() => roles.map((r: any) => ({ id: r.id, name: r.name })), [roles]);
  const filteredUsers = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (users as any[]).filter((u: any) => {
      const statusOk =
        statusFilter === "all" ||
        (statusFilter === "active" && u.is_active) ||
        (statusFilter === "inactive" && !u.is_active);
      const text = `${u.username} ${u.full_name} ${u.email}`.toLowerCase();
      return statusOk && (!q || text.includes(q));
    });
  }, [users, search, statusFilter]);
  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / pageSize));
  const pagedUsers = filteredUsers.slice((page - 1) * pageSize, page * pageSize);

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin — Users</h1>
        <p className="text-gray-500 mt-1">Create, deactivate, and manage role assignment for users.</p>
      </div>
      {apiError && <div className="p-3 rounded-lg bg-red-50 text-red-700 border border-red-200">{apiError}</div>}
      {apiMessage && (
        <div className="p-3 rounded-lg bg-green-50 text-green-700 border border-green-200">{apiMessage}</div>
      )}

      <section className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Create user</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createUser.mutate({
              ...form,
              site_id: form.site_id || null,
            });
          }}
          className="grid grid-cols-1 md:grid-cols-2 gap-3"
        >
          <input className="border rounded px-3 py-2" placeholder="Username" value={form.username} onChange={(e) => setForm((s) => ({ ...s, username: e.target.value }))} required />
          <input className="border rounded px-3 py-2" placeholder="Email" value={form.email} onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))} required />
          <input className="border rounded px-3 py-2" placeholder="Full name" value={form.full_name} onChange={(e) => setForm((s) => ({ ...s, full_name: e.target.value }))} required />
          <input className="border rounded px-3 py-2" placeholder="Initial password" type="password" value={form.password} onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))} required />
          <input className="border rounded px-3 py-2" placeholder="Site ID (optional)" value={form.site_id} onChange={(e) => setForm((s) => ({ ...s, site_id: e.target.value }))} />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm((s) => ({ ...s, is_active: e.target.checked }))} />
            Active
          </label>
          <div className="md:col-span-2">
            <button className="bg-brand-600 text-white px-4 py-2 rounded disabled:opacity-50" disabled={createUser.isPending}>
              {createUser.isPending ? "Creating..." : "Create user"}
            </button>
          </div>
        </form>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Users</h2>
        <div className="mb-4 flex flex-wrap gap-2">
          <input
            className="border rounded px-3 py-2 text-sm min-w-[220px]"
            placeholder="Search username / name / email"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
          <select
            className="border rounded px-3 py-2 text-sm"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as any);
              setPage(1);
            }}
          >
            <option value="all">All statuses</option>
            <option value="active">Active only</option>
            <option value="inactive">Inactive only</option>
          </select>
          <div className="text-sm text-gray-500 self-center">
            {filteredUsers.length} users
          </div>
        </div>
        <div className="space-y-4">
          {pagedUsers.map((u: any) => (
            <div key={u.id} className="border rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900">{u.full_name} <span className="text-gray-500 text-sm">({u.username})</span></p>
                  <p className="text-sm text-gray-500">{u.email}</p>
                  <p className="text-xs mt-1">{u.is_active ? "Active" : "Inactive"} · Roles: {(u.roles || []).map((r: any) => r.name).join(", ") || "none"}</p>
                </div>
                <div className="flex gap-2">
                  {u.is_active && (
                    <button
                      className="text-sm px-3 py-1.5 border rounded hover:bg-gray-50 disabled:opacity-50"
                      disabled={deactivateUser.isPending}
                      onClick={() => {
                        if (!window.confirm(`Deactivate user '${u.username}'?`)) return;
                        deactivateUser.mutate(u.id);
                      }}
                    >
                      Deactivate
                    </button>
                  )}
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 items-center">
                <select
                  className="border rounded px-2 py-1.5 text-sm"
                  value={selectedRoleByUser[u.id] || ""}
                  onChange={(e) => setSelectedRoleByUser((s) => ({ ...s, [u.id]: e.target.value }))}
                >
                  <option value="">Select role</option>
                  {roleOptions.map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
                <button
                  className="text-sm px-3 py-1.5 bg-gray-900 text-white rounded disabled:opacity-50"
                  disabled={assignRole.isPending}
                  onClick={() => {
                    const roleId = selectedRoleByUser[u.id];
                    if (!roleId) return;
                    assignRole.mutate({ userId: u.id, roleId });
                  }}
                >
                  Assign role
                </button>
                {(u.roles || []).map((r: any) => (
                  <button
                    key={r.id}
                    className="text-xs px-2 py-1 rounded border hover:bg-gray-50 disabled:opacity-50"
                    disabled={revokeRole.isPending}
                    onClick={() => {
                      if (!window.confirm(`Revoke role '${r.name}' from '${u.username}'?`)) return;
                      revokeRole.mutate({ userId: u.id, roleId: r.id });
                    }}
                  >
                    Revoke {r.name}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {pagedUsers.length === 0 && (
            <div className="text-sm text-gray-500 text-center py-6 border rounded-lg">
              No users match the current filters.
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
