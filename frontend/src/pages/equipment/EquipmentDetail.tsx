import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { equipmentApi } from "@/lib/api";

export default function EquipmentDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("qualified");
  const [reason, setReason] = useState("");

  const { data: equipment, isLoading } = useQuery({
    queryKey: ["equipment", id],
    queryFn: () => equipmentApi.getEquipment(id),
    enabled: Boolean(id),
  });
  const { data: calibrations = [] } = useQuery({
    queryKey: ["equipment-calibrations", id],
    queryFn: () => equipmentApi.listCalibrations(id),
    enabled: Boolean(id),
  });
  const { data: qualifications = [] } = useQuery({
    queryKey: ["equipment-qualifications", id],
    queryFn: () => equipmentApi.listQualifications(id),
    enabled: Boolean(id),
  });
  const { data: maintenance = [] } = useQuery({
    queryKey: ["equipment-maintenance", id],
    queryFn: () => equipmentApi.listMaintenance(id),
    enabled: Boolean(id),
  });

  const updateStatus = useMutation({
    mutationFn: () => equipmentApi.updateStatus(id, { status, reason }),
    onSuccess: async () => {
      setError("");
      setMessage("Status updated.");
      setReason("");
      await qc.invalidateQueries({ queryKey: ["equipment", id] });
      await qc.invalidateQueries({ queryKey: ["equipment"] });
    },
    onError: (err: any) => {
      const d = err?.response?.data?.detail;
      setError(Array.isArray(d) ? d.join("; ") : d || "Failed to update status.");
    },
  });

  if (isLoading) return <div className="p-8 text-gray-500">Loading equipment...</div>;
  if (!equipment) {
    return (
      <div className="p-8">
        <div className="text-gray-500 mb-3">Equipment not found.</div>
        <button className="text-brand-600" onClick={() => navigate("/equipment")}>Back to list</button>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      <div className="text-sm text-gray-500">
        <Link to="/equipment" className="text-brand-600 hover:underline">Equipment</Link> / {(equipment as any).equipment_id}
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">{(equipment as any).name}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {(equipment as any).equipment_id} • {(equipment as any).equipment_type} • status: {(equipment as any).status}
        </p>
      </div>

      {error && <div className="p-3 rounded border border-red-200 bg-red-50 text-red-700">{error}</div>}
      {message && <div className="p-3 rounded border border-green-200 bg-green-50 text-green-700">{message}</div>}

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-2 text-sm">
        <div><span className="text-gray-500">Qualification status:</span> {(equipment as any).qualification_status}</div>
        <div><span className="text-gray-500">Location:</span> {(equipment as any).location || "—"}</div>
        <div><span className="text-gray-500">Manufacturer / model:</span> {[(equipment as any).manufacturer, (equipment as any).model].filter(Boolean).join(" / ") || "—"}</div>
        <div><span className="text-gray-500">Serial:</span> {(equipment as any).serial_number || "—"}</div>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-3">
        <h2 className="font-semibold">Change Status</h2>
        <select className="border rounded px-3 py-2 w-full" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="qualified">qualified</option>
          <option value="under_maintenance">under_maintenance</option>
          <option value="out_of_service">out_of_service</option>
          <option value="retired">retired</option>
        </select>
        <textarea className="border rounded px-3 py-2 w-full" rows={2} placeholder="Reason (required)" value={reason} onChange={(e) => setReason(e.target.value)} />
        <button className="px-4 py-2 bg-brand-600 text-white rounded disabled:opacity-50" disabled={updateStatus.isPending || !reason.trim()} onClick={() => updateStatus.mutate()}>
          {updateStatus.isPending ? "Updating..." : "Update Status"}
        </button>
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-2">
        <h2 className="font-semibold">Calibration Records</h2>
        {(calibrations as any[]).length === 0 ? <p className="text-sm text-gray-500">No calibrations.</p> : (
          <ul className="space-y-1 text-sm">
            {(calibrations as any[]).map((c: any) => (
              <li key={c.id} className="border rounded px-3 py-2">
                {c.calibration_number} • {c.result} • performed {new Date(c.performed_at).toLocaleDateString()}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-2">
        <h2 className="font-semibold">Qualification Records</h2>
        {(qualifications as any[]).length === 0 ? <p className="text-sm text-gray-500">No qualifications.</p> : (
          <ul className="space-y-1 text-sm">
            {(qualifications as any[]).map((q: any) => (
              <li key={q.id} className="border rounded px-3 py-2">
                {q.qualification_number} • {q.qualification_type} • {q.result}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-white rounded-xl shadow-sm p-6 space-y-2">
        <h2 className="font-semibold">Maintenance Records</h2>
        {(maintenance as any[]).length === 0 ? <p className="text-sm text-gray-500">No maintenance.</p> : (
          <ul className="space-y-1 text-sm">
            {(maintenance as any[]).map((m: any) => (
              <li key={m.id} className="border rounded px-3 py-2">
                {m.maintenance_number} • {m.maintenance_type} • {new Date(m.performed_at).toLocaleDateString()}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
