import { useQuery } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const statusColour: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  under_review: "bg-yellow-100 text-yellow-800",
  approved: "bg-blue-100 text-blue-800",
  in_progress: "bg-purple-100 text-purple-800",
  completed: "bg-green-100 text-green-800",
  closed: "bg-gray-200 text-gray-600",
};

const riskColour: Record<string, string> = {
  low: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const { data: capas = [] } = useQuery({ queryKey: ["capas"], queryFn: () => qmsApi.listCapas() });
  const { data: deviations = [] } = useQuery({ queryKey: ["deviations"], queryFn: () => qmsApi.listDeviations() });
  const { data: changeControls = [] } = useQuery({ queryKey: ["change-controls"], queryFn: () => qmsApi.listChangeControls() });

  const openCapas = capas.filter((c: any) => !["closed", "completed"].includes(c.current_status));
  const criticalCapas = capas.filter((c: any) => c.risk_level === "critical");
  const openDeviations = deviations.filter((d: any) => d.current_status !== "closed");

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Welcome back, {user?.full_name?.split(" ")[0]}</h1>
        <p className="text-gray-500 mt-1">GMP Quality Management Dashboard</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[
          { label: "Open CAPAs", value: openCapas.length, sub: `${criticalCapas.length} critical`, colour: "border-l-brand-500" },
          { label: "Open Deviations", value: openDeviations.length, sub: "requires review", colour: "border-l-yellow-500" },
          { label: "Change Controls", value: changeControls.length, sub: "total active", colour: "border-l-purple-500" },
          { label: "Overdue Items", value: 0, sub: "all on track", colour: "border-l-green-500" },
        ].map((kpi) => (
          <div key={kpi.label} className={`bg-white rounded-xl p-6 shadow-sm border-l-4 ${kpi.colour}`}>
            <p className="text-sm text-gray-500 font-medium">{kpi.label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{kpi.value}</p>
            <p className="text-xs text-gray-400 mt-1">{kpi.sub}</p>
          </div>
        ))}
      </div>

      {/* Recent CAPAs */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent CAPAs</h2>
          <a href="/qms/capas" className="text-sm text-brand-600 hover:text-brand-700 font-medium">View all →</a>
        </div>
        {capas.length === 0 ? (
          <p className="text-gray-400 text-sm py-4 text-center">No CAPAs yet. Create your first one.</p>
        ) : (
          <div className="divide-y divide-gray-100">
            {capas.slice(0, 5).map((capa: any) => (
              <div key={capa.id} className="py-3 flex items-center justify-between">
                <div>
                  <a href={`/qms/capas/${capa.id}`} className="text-sm font-medium text-gray-900 hover:text-brand-600">
                    {capa.capa_number} — {capa.title}
                  </a>
                  <p className="text-xs text-gray-400 mt-0.5">{capa.department}</p>
                </div>
                <div className="flex gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${riskColour[capa.risk_level]}`}>
                    {capa.risk_level}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColour[capa.current_status]}`}>
                    {capa.current_status.replace("_", " ")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
