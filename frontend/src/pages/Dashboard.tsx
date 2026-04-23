import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api";
import { mockGetDashboardSummary } from "@/lib/mock-api";
import { useAuthStore } from "@/stores/authStore";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const useMock = Boolean(import.meta.env.VITE_USE_MOCK);
  const { data: summary, isLoading } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => (useMock ? mockGetDashboardSummary() : dashboardApi.summary()),
    refetchInterval: 60_000,
  });

  const kpis = [
    { title: "Open CAPAs", value: summary?.open_capas ?? 0, to: "/qms/capas?status_filter=open" },
    { title: "Overdue CAPAs", value: summary?.overdue_capas ?? 0, to: "/qms/capas" },
    { title: "Open Deviations", value: summary?.open_deviations ?? 0, to: "/qms/deviations" },
    { title: "Overdue Deviations", value: summary?.overdue_deviations ?? 0, to: "/qms/deviations" },
    { title: "Pending Change Controls", value: summary?.pending_change_controls ?? 0, to: "/qms/change-controls" },
    { title: "Calibrations Due (30d)", value: summary?.calibrations_due_30_days ?? 0, to: "/equipment" },
    { title: "Calibrations Overdue", value: summary?.calibrations_overdue ?? 0, to: "/equipment" },
    { title: "Open OOS Investigations", value: summary?.open_oos_investigations ?? 0, to: "/lims/samples" },
    { title: "Documents Expiring (60d)", value: summary?.documents_expiring_60_days ?? 0, to: "/documents" },
    { title: "Training Overdue", value: summary?.training_overdue ?? 0, to: "/training" },
    { title: "Pending My Signatures", value: summary?.pending_my_signatures ?? 0, to: "/security" },
  ];

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome back, {user?.full_name?.split(" ")[0]}</h1>
        <p className="text-gray-500 mt-1">Live GMP KPI summary, refreshed every minute.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <Link key={kpi.title} to={kpi.to}>
            <Card className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-2">
                <CardDescription>{kpi.title}</CardDescription>
              </CardHeader>
              <CardContent>
                <CardTitle className="text-3xl">{isLoading ? "..." : kpi.value}</CardTitle>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">My Actions</CardTitle>
          <CardDescription>Items requiring your signature or action today.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {!summary?.pending_my_actions?.length ? (
            <p className="text-sm text-gray-500">No pending actions.</p>
          ) : (
            summary.pending_my_actions.map((item: any) => (
              <div key={item.id} className="flex items-center justify-between border rounded-md p-2">
                <div>
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-xs text-gray-500">
                    {item.due_date ? new Date(item.due_date).toLocaleDateString() : "No due date"}
                  </p>
                </div>
                <Badge variant="secondary">{item.type}</Badge>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
