import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { qmsApi } from "@/lib/api";

const statusColour: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  under_review: "bg-yellow-100 text-yellow-800",
  approved: "bg-blue-100 text-blue-800",
  in_progress: "bg-purple-100 text-purple-800",
  effectiveness_check: "bg-orange-100 text-orange-800",
  completed: "bg-green-100 text-green-800",
  closed: "bg-gray-200 text-gray-500",
};

const riskColour: Record<string, string> = {
  low: "text-green-700",
  medium: "text-yellow-700",
  high: "text-orange-700",
  critical: "text-red-700 font-bold",
};

export default function CAPAList() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("");
  const { data: capas = [], isLoading } = useQuery({
    queryKey: ["capas", statusFilter],
    queryFn: () => qmsApi.listCapas(statusFilter ? { status_filter: statusFilter } : undefined),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CAPAs</h1>
          <p className="text-gray-500 text-sm mt-1">Corrective & Preventive Actions</p>
        </div>
        <button
          onClick={() => navigate("/qms/capas/new")}
          className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New CAPA
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-4 flex gap-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:border-brand-500"
        >
          <option value="">All statuses</option>
          {Object.keys(statusColour).map((s) => (
            <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["CAPA #", "Title", "Type", "Risk", "Department", "Status", "Target Date"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">Loading...</td></tr>
            ) : capas.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">No CAPAs found. Create your first one.</td></tr>
            ) : capas.map((capa: any) => (
              <tr
                key={capa.id}
                onClick={() => navigate(`/qms/capas/${capa.id}`)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                <td className="px-4 py-3 font-mono text-brand-600 font-medium">{capa.capa_number}</td>
                <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">{capa.title}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{capa.capa_type}</td>
                <td className={`px-4 py-3 capitalize ${riskColour[capa.risk_level]}`}>{capa.risk_level}</td>
                <td className="px-4 py-3 text-gray-600">{capa.department}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColour[capa.current_status]}`}>
                    {capa.current_status.replace(/_/g, " ")}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {capa.target_completion_date
                    ? new Date(capa.target_completion_date).toLocaleDateString()
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
