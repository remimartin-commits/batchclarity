import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { qmsApi } from "@/lib/api";

export default function DeviationList() {
  const navigate = useNavigate();
  const { data: deviations = [], isLoading } = useQuery({
    queryKey: ["deviations"],
    queryFn: () => qmsApi.listDeviations({ skip: 0, limit: 200 }),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Deviations</h1>
          <p className="text-gray-500 text-sm mt-1">Manufacturing & process deviations</p>
        </div>
        <button className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors">
          + New Deviation
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Status", "Description", "Site ID", "Created At"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={4} className="text-center py-8 text-gray-400">Loading...</td></tr>
            ) : deviations.length === 0 ? (
              <tr><td colSpan={4} className="text-center py-8 text-gray-400">No deviations recorded yet.</td></tr>
            ) : deviations.map((d: any) => (
              <tr
                key={d.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/qms/deviations/${d.id}`)}
              >
                <td className="px-4 py-3">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-800 font-medium">
                    {d.current_status.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-700 max-w-lg truncate">{d.description ?? d.title}</td>
                <td className="px-4 py-3 text-gray-600 font-mono text-xs">{d.site_id ?? "—"}</td>
                <td className="px-4 py-3 text-gray-600 text-xs">
                  {d.created_at ? new Date(d.created_at).toLocaleString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
