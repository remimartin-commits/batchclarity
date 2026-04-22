import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { equipmentApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

type CalibrationScheduleRow = {
  equipment: any;
  nextCalibrationDue: string | null;
  isOverdue: boolean;
};

export default function EquipmentList() {
  const queryClient = useQueryClient();
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string | null>(null);
  const [form, setForm] = useState({
    performed_by: "",
    result: "pass",
    notes: "",
  });

  const { data: equipment = [], isLoading: loadingEquipment } = useQuery({
    queryKey: ["equipment-schedule"],
    queryFn: () => equipmentApi.listEquipment({ skip: 0, limit: 500 }),
  });

  const { data: calibrationMap = {}, isLoading: loadingCalibrations } = useQuery({
    queryKey: ["equipment-calibration-map", (equipment as any[]).map((e: any) => e.id)],
    enabled: (equipment as any[]).length > 0,
    queryFn: async () => {
      const map: Record<string, any[]> = {};
      await Promise.all(
        (equipment as any[]).map(async (eq: any) => {
          map[eq.id] = (await equipmentApi.listCalibrations(eq.id)) as any[];
        })
      );
      return map;
    },
  });

  const scheduleRows = useMemo<CalibrationScheduleRow[]>(() => {
    const now = new Date();
    const rows = (equipment as any[]).map((eq: any) => {
      const records = (calibrationMap as Record<string, any[]>)[eq.id] ?? [];
      const latest = [...records].sort(
        (a: any, b: any) =>
          new Date(b.next_calibration_due || 0).getTime() -
          new Date(a.next_calibration_due || 0).getTime()
      )[0];
      const due = latest?.next_calibration_due ?? null;
      const isOverdue = Boolean(due && new Date(due) < now);
      return { equipment: eq, nextCalibrationDue: due, isOverdue };
    });
    return rows.sort((a, b) => Number(b.isOverdue) - Number(a.isOverdue));
  }, [equipment, calibrationMap]);

  const recordCalibrationMutation = useMutation({
    mutationFn: () =>
      equipmentApi.addCalibration(selectedEquipmentId!, {
        calibration_type: "scheduled",
        performed_at: new Date().toISOString(),
        calibration_interval_days: 30,
        result: form.result,
        notes: `${form.notes}${form.performed_by ? ` | performed_by: ${form.performed_by}` : ""}`,
      }),
    onSuccess: async () => {
      toast.success("Calibration recorded.");
      setSelectedEquipmentId(null);
      setForm({ performed_by: "", result: "pass", notes: "" });
      await queryClient.invalidateQueries({ queryKey: ["equipment-calibration-map"] });
      await queryClient.invalidateQueries({ queryKey: ["equipment-schedule"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to record calibration.");
    },
  });

  const loading = loadingEquipment || loadingCalibrations;

  return (
    <div className="p-8 space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Calibration Schedule</h1>
        <p className="text-gray-500 text-sm mt-1">
          Overdue items are shown first. Due dates are color-coded for rapid review.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Equipment", "Location", "Next Calibration Due", "Status", "Action"].map((h) => (
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
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  Loading calibration schedule...
                </td>
              </tr>
            ) : scheduleRows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No equipment records found.
                </td>
              </tr>
            ) : (
              scheduleRows.map((row) => {
                const dueState = getDueState(row.nextCalibrationDue);
                return (
                  <tr key={row.equipment.id} className={row.isOverdue ? "bg-red-50/40" : ""}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{row.equipment.name}</div>
                      <div className="text-xs text-gray-500 font-mono">
                        {row.equipment.equipment_id}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{row.equipment.location ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-700">
                      {row.nextCalibrationDue
                        ? new Date(row.nextCalibrationDue).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${dueState.className}`}>
                        {dueState.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        className="text-xs font-semibold px-3 py-1.5 rounded bg-brand-600 text-white hover:bg-brand-700"
                        onClick={() => setSelectedEquipmentId(row.equipment.id)}
                      >
                        Record Calibration
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {selectedEquipmentId && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">Record Calibration</h2>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              placeholder="performed_by"
              value={form.performed_by}
              onChange={(e) => setForm((f) => ({ ...f, performed_by: e.target.value }))}
            />
            <select
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              value={form.result}
              onChange={(e) => setForm((f) => ({ ...f, result: e.target.value }))}
            >
              <option value="pass">pass</option>
              <option value="fail">fail</option>
              <option value="conditional_pass">conditional_pass</option>
            </select>
            <textarea
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              rows={3}
              placeholder="notes"
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            />
            <div className="flex gap-3 pt-1">
              <button
                className="flex-1 border border-gray-300 rounded-lg py-2 text-sm"
                onClick={() => setSelectedEquipmentId(null)}
              >
                Cancel
              </button>
              <button
                className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
                disabled={recordCalibrationMutation.isPending}
                onClick={() => recordCalibrationMutation.mutate()}
              >
                {recordCalibrationMutation.isPending ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getDueState(nextCalibrationDue: string | null): { label: string; className: string } {
  if (!nextCalibrationDue) {
    return { label: "No due date", className: "bg-gray-100 text-gray-700" };
  }
  const due = new Date(nextCalibrationDue);
  const now = new Date();
  const amberDate = new Date(now);
  amberDate.setDate(now.getDate() + 14);
  if (due < now) {
    return { label: "Overdue", className: "bg-red-100 text-red-700" };
  }
  if (due <= amberDate) {
    return { label: "Due Soon", className: "bg-amber-100 text-amber-700" };
  }
  return { label: "On Track", className: "bg-green-100 text-green-700" };
}

