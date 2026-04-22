import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { envMonitoringApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

export default function EnvMonitoringList() {
  const queryClient = useQueryClient();
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [selectedLocationId, setSelectedLocationId] = useState<string>("");
  const [form, setForm] = useState({
    value: "",
    unit: "CFU/m3",
    notes: "",
  });

  const { data: locations = [], isLoading: loadingLocations } = useQuery({
    queryKey: ["env-locations"],
    queryFn: () => envMonitoringApi.listLocations({}),
  });

  const { data: results = [], isLoading: loadingResults } = useQuery({
    queryKey: ["env-results"],
    queryFn: () => envMonitoringApi.listResults({ skip: 0, limit: 500 }),
  });

  const latestByLocation = useMemo(() => {
    const map = new Map<string, any>();
    for (const result of results as any[]) {
      const current = map.get(result.location_id);
      if (!current) {
        map.set(result.location_id, result);
        continue;
      }
      const currentTs = new Date(current.sampled_at || current.created_at || 0).getTime();
      const nextTs = new Date(result.sampled_at || result.created_at || 0).getTime();
      if (nextTs > currentTs) map.set(result.location_id, result);
    }
    return map;
  }, [results]);

  const recordMutation = useMutation({
    mutationFn: () =>
      envMonitoringApi.recordResult(selectedLocationId, {
        parameter: "total_viable_count",
        sampling_method: "settle_plate",
        sampled_at: new Date().toISOString(),
        result_value: Number(form.value),
        unit: form.unit,
        comments: form.notes,
      }),
    onSuccess: async () => {
      toast.success("Monitoring result recorded.");
      setShowRecordModal(false);
      setSelectedLocationId("");
      setForm({ value: "", unit: "CFU/m3", notes: "" });
      await queryClient.invalidateQueries({ queryKey: ["env-results"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to record result.");
    },
  });

  const loading = loadingLocations || loadingResults;

  return (
    <div className="p-8 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">ENV Monitoring</h1>
          <p className="text-gray-500 text-sm mt-1">
            Location overview with latest result and alert classification.
          </p>
        </div>
        <button
          className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-lg"
          onClick={() => setShowRecordModal(true)}
        >
          Record Result
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Location", "Latest Result", "Alert Status"].map((h) => (
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
                <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                  Loading monitoring locations...
                </td>
              </tr>
            ) : (locations as any[]).length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                  No monitoring locations available.
                </td>
              </tr>
            ) : (
              (locations as any[]).map((location: any) => {
                const latest = latestByLocation.get(location.id);
                const status = latest?.status ?? "normal";
                const statusClass =
                  status === "action"
                    ? "bg-red-100 text-red-700"
                    : status === "alert"
                    ? "bg-amber-100 text-amber-700"
                    : "bg-green-100 text-green-700";
                const rowClass =
                  status === "action" ? "bg-red-50" : status === "alert" ? "bg-amber-50" : "";
                return (
                  <tr key={location.id} className={rowClass}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{location.name}</div>
                      <div className="text-xs text-gray-500">{location.code}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {latest
                        ? `${latest.result_value} ${latest.unit} (${new Date(
                            latest.sampled_at || latest.created_at
                          ).toLocaleString()})`
                        : "No result recorded"}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusClass}`}>
                        {status === "action"
                          ? "action limit"
                          : status === "alert"
                          ? "alert limit"
                          : "normal"}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {showRecordModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">Record Result</h2>
            <select
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              value={selectedLocationId}
              onChange={(e) => setSelectedLocationId(e.target.value)}
            >
              <option value="">Select location</option>
              {(locations as any[]).map((location: any) => (
                <option key={location.id} value={location.id}>
                  {location.code} - {location.name}
                </option>
              ))}
            </select>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              placeholder="value"
              value={form.value}
              onChange={(e) => setForm((f) => ({ ...f, value: e.target.value }))}
            />
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              placeholder="unit"
              value={form.unit}
              onChange={(e) => setForm((f) => ({ ...f, unit: e.target.value }))}
            />
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
                onClick={() => setShowRecordModal(false)}
              >
                Cancel
              </button>
              <button
                className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
                disabled={recordMutation.isPending || !selectedLocationId || !form.value}
                onClick={() => recordMutation.mutate()}
              >
                {recordMutation.isPending ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

