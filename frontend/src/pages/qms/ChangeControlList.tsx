import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { qmsApi } from "@/lib/api";

const categoryColour: Record<string, string> = {
  minor: "bg-gray-100 text-gray-600",
  major: "bg-yellow-100 text-yellow-700",
  critical: "bg-red-100 text-red-700",
};

export default function ChangeControlList() {
  const navigate = useNavigate();
  const { data: ccs = [], isLoading } = useQuery({
    queryKey: ["change-controls"],
    queryFn: () => qmsApi.listChangeControls(),
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Change Controls</h1>
          <p className="text-gray-500 text-sm mt-1">Process, equipment, material & software changes</p>
        </div>
        <button className="bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors">
          + New Change Control
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["CC #", "Title", "Type", "Category", "Regulatory Impact", "Validation Req.", "Status"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">Loading...</td></tr>
            ) : ccs.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">No change controls yet.</td></tr>
            ) : ccs.map((cc: any) => (
              <tr
                key={cc.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/qms/change-controls/${cc.id}`)}
              >
                <td className="px-4 py-3 font-mono text-brand-600 font-medium">{cc.change_number}</td>
                <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">{cc.title}</td>
                <td className="px-4 py-3 text-gray-600 capitalize">{cc.change_type.replace(/_/g, " ")}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${categoryColour[cc.change_category]}`}>
                    {cc.change_category}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">{cc.regulatory_impact ? "⚠️ Yes" : "No"}</td>
                <td className="px-4 py-3 text-center">{cc.validation_required ? "✓ Yes" : "No"}</td>
                <td className="px-4 py-3">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
                    {cc.current_status.replace(/_/g, " ")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
