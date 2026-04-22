import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { envMonitoringApi } from "@/lib/api";
import { MonitoringResult, MonitoringLocation, EMStatus } from "@/types";
import { toast } from "@/stores/toastStore";

const statusColour: Record<EMStatus, string> = {
  within_limits: "bg-green-100 text-green-700",
  alert:         "bg-yellow-100 text-yellow-700",
  action:        "bg-orange-100 text-orange-700",
  oot:           "bg-purple-100 text-purple-700",
  oos:           "bg-red-100 text-red-700",
};

const gradeColour: Record<string, string> = {
  A: "bg-red-100 text-red-700",
  B: "bg-orange-100 text-orange-700",
  C: "bg-yellow-100 text-yellow-700",
  D: "bg-gray-100 text-gray-600",
};

function RecordResultModal({
  locations,
  onClose,
}: {
  locations: MonitoringLocation[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    location_id: locations[0]?.id ?? "",
    parameter: "total_aerobic_count",
    result_value: "",
    unit: "CFU/m³",
    sampling_date: new Date().toISOString().split("T")[0],
    comments: "",
  });

  const PARAMETERS = [
    { value: "total_aerobic_count", label: "Total Aerobic Count (CFU/m³)" },
    { value: "total_yeast_mould",   label: "Total Yeast & Mould (CFU/m³)" },
    { value: "particle_0_5um",      label: "Particles ≥0.5 µm (per m³)" },
    { value: "particle_5um",        label: "Particles ≥5.0 µm (per m³)" },
    { value: "temperature",         label: "Temperature (°C)" },
    { value: "relative_humidity",   label: "Relative Humidity (%)" },
    { value: "differential_pressure", label: "Differential Pressure (Pa)" },
  ];

  const mutation = useMutation({
    mutationFn: () =>
      envMonitoringApi.recordResult({
        ...form,
        result_value: parseFloat(form.result_value),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["em-results"] });
      toast.success("Monitoring result recorded.");
      onClose();
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Failed to record result."),
  });

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-4">
        <h2 className="text-lg font-bold text-gray-900">Record EM Result</h2>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Monitoring Location
          </label>
          <select
            value={form.location_id}
            onChange={(e) => setForm({ ...form, location_id: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {locations.map((l) => (
              <option key={l.id} value={l.id}>
                {l.code} — {l.name} (Grade {l.gmp_grade})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Parameter
          </label>
          <select
            value={form.parameter}
            onChange={(e) => setForm({ ...form, parameter: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {PARAMETERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Result Value
            </label>
            <input
              type="number"
              value={form.result_value}
              onChange={(e) => setForm({ ...form, result_value: e.target.value })}
              placeholder="0"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="w-28">
            <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
              Unit
            </label>
            <input
              value={form.unit}
              onChange={(e) => setForm({ ...form, unit: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Sampling Date
          </label>
          <input
            type="date"
            value={form.sampling_date}
            onChange={(e) => setForm({ ...form, sampling_date: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
            Comments
          </label>
          <textarea
            value={form.comments}
            onChange={(e) => setForm({ ...form, comments: e.target.value })}
            rows={2}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
          />
        </div>

        <div className="flex gap-3 pt-1">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-300 rounded-lg py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !form.location_id || !form.result_value}
            className="flex-1 bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
          >
            {mutation.isPending ? "Recording…" : "Record Result"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function EnvMonitoringList() {
  const [showRecord, setShowRecord] = useState(false);
  const [locationFilter, setLocationFilter] = useState("");
  const [view, setView] = useState<"results" | "locations">("results");

  const { data: results = [], isLoading: loadingResults } = useQuery<MonitoringResult[]>({
    queryKey: ["em-results", locationFilter],
    queryFn: () =>
      envMonitoringApi.listResults(locationFilter ? { location_id: locationFilter } : {}),
    enabled: view === "results",
  });

  const { data: locations = [], isLoading: loadingLocations } = useQuery<MonitoringLocation[]>({
    queryKey: ["em-locations"],
    queryFn: () => envMonitoringApi.listLocations(),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Environmental Monitoring</h1>
          <p className="text-gray-500 text-sm mt-1">
            Cleanroom EM results — auto-classified vs. alert and action limits
          </p>
        </div>
        <button
          onClick={() => setShowRecord(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors"
        >
          + Record Result
        </button>
      </div>

      {/* Summary cards */}
      {view === "results" && (
        <div className="grid grid-cols-5 gap-3 mb-6">
          {(["within_limits", "alert", "action", "oot", "oos"] as EMStatus[]).map((s) => {
            const count = results.filter((r) => r.status === s).length;
            return (
              <div
                key={s}
                className={`rounded-xl px-4 py-3 text-center cursor-pointer border-2 transition-colors ${
                  statusColour[s]
                } ${locationFilter === s ? "border-current" : "border-transparent"}`}
              >
                <div className="text-2xl font-bold">{count}</div>
                <div className="text-xs font-medium capitalize mt-0.5">
                  {s.replace(/_/g, " ")}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* View toggle */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 w-fit">
        {(["results", "locations"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors capitalize ${
              view === v ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      {view === "results" && (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {["Result #", "Location", "Grade", "Parameter", "Value", "Unit", "Sampled", "Status"].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loadingResults ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-gray-400">
                    Loading results…
                  </td>
                </tr>
              ) : results.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-gray-400">
                    No results recorded yet.
                  </td>
                </tr>
              ) : (
                results.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-brand-600 font-medium text-xs">
                      {r.result_number}
                    </td>
                    <td className="px-4 py-3 text-gray-700 text-xs">
                      {r.location?.code ?? r.location_id?.slice(0, 8)}
                    </td>
                    <td className="px-4 py-3">
                      {r.location?.gmp_grade && (
                        <span
                          className={`text-xs px-1.5 py-0.5 rounded font-bold ${
                            gradeColour[r.location.gmp_grade]
                          }`}
                        >
                          {r.location.gmp_grade}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs capitalize">
                      {r.parameter.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 font-semibold text-gray-900">{r.result_value}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{r.unit}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(r.result_entered_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                          statusColour[r.status as EMStatus] ?? "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {r.status.replace(/_/g, " ")}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {view === "locations" && (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {["Code", "Name", "GMP Grade", "Room", "Alert Limits Defined", "Active"].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loadingLocations ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-400">
                    Loading locations…
                  </td>
                </tr>
              ) : locations.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-400">
                    No monitoring locations defined.
                  </td>
                </tr>
              ) : (
                locations.map((l) => (
                  <tr key={l.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-brand-600 font-medium text-xs">
                      {l.code}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900">{l.name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-bold ${
                          gradeColour[l.gmp_grade] ?? "bg-gray-100 text-gray-600"
                        }`}
                      >
                        Grade {l.gmp_grade}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{l.room ?? "—"}</td>
                    <td className="px-4 py-3 text-gray-600 text-xs">
                      {l.alert_limits?.length ?? 0} parameter(s)
                    </td>
                    <td className="px-4 py-3 text-center">
                      {l.is_active ? (
                        <span className="text-green-500">●</span>
                      ) : (
                        <span className="text-gray-300">●</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showRecord && locations.length > 0 && (
        <RecordResultModal locations={locations} onClose={() => setShowRecord(false)} />
      )}
    </div>
  );
}
