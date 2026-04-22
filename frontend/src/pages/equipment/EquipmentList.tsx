import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { equipmentApi } from "@/lib/api";

export default function EquipmentList() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({
    equipment_id: "",
    name: "",
    equipment_type: "instrument",
    site_id: "",
    location: "",
    manufacturer: "",
    model: "",
    serial_number: "",
  });

  const { data: equipment = [], isLoading } = useQuery({
    queryKey: ["equipment", search],
    queryFn: () => equipmentApi.listEquipment(),
  });

  const createMutation = useMutation({
    mutationFn: () => equipmentApi.createEquipment(form),
    onSuccess: async () => {
      setShowNew(false);
      setForm({
        equipment_id: "",
        name: "",
        equipment_type: "instrument",
        site_id: "",
        location: "",
        manufacturer: "",
        model: "",
        serial_number: "",
      });
      await qc.invalidateQueries({ queryKey: ["equipment"] });
    },
  });

  const filtered = (equipment as any[]).filter((e: any) => {
    const q = search.toLowerCase().trim();
    if (!q) return true;
    return `${e.equipment_id} ${e.name} ${e.serial_number || ""}`.toLowerCase().includes(q);
  });

  return (
    <div className="p-8 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Equipment</h1>
          <p className="text-gray-500 text-sm mt-1">Equipment records and lifecycle status.</p>
        </div>
        <button className="bg-brand-600 text-white px-4 py-2 rounded" onClick={() => setShowNew(true)}>
          + Register Equipment
        </button>
      </div>

      <input className="border rounded px-3 py-2 w-full max-w-md" placeholder="Search equipment id / name / serial" value={search} onChange={(e) => setSearch(e.target.value)} />

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {["Equipment ID", "Name", "Type", "Location", "Status", "Qualification"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No equipment found.</td></tr>
            ) : (
              filtered.map((e: any) => (
                <tr key={e.id} className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/equipment/${e.id}`)}>
                  <td className="px-4 py-3 font-mono text-brand-600">{e.equipment_id}</td>
                  <td className="px-4 py-3">{e.name}</td>
                  <td className="px-4 py-3">{e.equipment_type}</td>
                  <td className="px-4 py-3">{e.location || "—"}</td>
                  <td className="px-4 py-3">{e.status}</td>
                  <td className="px-4 py-3">{e.qualification_status}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showNew && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-md p-6 space-y-3">
            <h2 className="text-lg font-semibold">Register Equipment</h2>
            <input className="border rounded px-3 py-2 w-full" placeholder="Equipment ID" value={form.equipment_id} onChange={(e) => setForm((s) => ({ ...s, equipment_id: e.target.value }))} />
            <input className="border rounded px-3 py-2 w-full" placeholder="Name" value={form.name} onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))} />
            <input className="border rounded px-3 py-2 w-full" placeholder="Site ID" value={form.site_id} onChange={(e) => setForm((s) => ({ ...s, site_id: e.target.value }))} />
            <input className="border rounded px-3 py-2 w-full" placeholder="Type" value={form.equipment_type} onChange={(e) => setForm((s) => ({ ...s, equipment_type: e.target.value }))} />
            <input className="border rounded px-3 py-2 w-full" placeholder="Location" value={form.location} onChange={(e) => setForm((s) => ({ ...s, location: e.target.value }))} />
            <input className="border rounded px-3 py-2 w-full" placeholder="Manufacturer" value={form.manufacturer} onChange={(e) => setForm((s) => ({ ...s, manufacturer: e.target.value }))} />
            <input className="border rounded px-3 py-2 w-full" placeholder="Model" value={form.model} onChange={(e) => setForm((s) => ({ ...s, model: e.target.value }))} />
            <input className="border rounded px-3 py-2 w-full" placeholder="Serial number" value={form.serial_number} onChange={(e) => setForm((s) => ({ ...s, serial_number: e.target.value }))} />
            <div className="flex justify-end gap-2">
              <button className="px-4 py-2 border rounded" onClick={() => setShowNew(false)}>Cancel</button>
              <button className="px-4 py-2 bg-brand-600 text-white rounded disabled:opacity-50" disabled={createMutation.isPending || !form.equipment_id || !form.name || !form.site_id} onClick={() => createMutation.mutate()}>
                {createMutation.isPending ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
