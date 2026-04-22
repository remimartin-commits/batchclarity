import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { equipmentApi, qmsApi, trainingApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);
  const { data: capas = [], isLoading: loadingCapas } = useQuery({
    queryKey: ["dashboard-capas"],
    queryFn: () => qmsApi.listCapas({ skip: 0, limit: 500 }),
  });
  const { data: deviations = [], isLoading: loadingDeviations } = useQuery({
    queryKey: ["dashboard-deviations"],
    queryFn: () => qmsApi.listDeviations({ skip: 0, limit: 500 }),
  });
  const { data: myAssignments = [], isLoading: loadingAssignments } = useQuery({
    queryKey: ["dashboard-training-my-assignments"],
    queryFn: trainingApi.myAssignments,
  });
  const { data: equipment = [], isLoading: loadingEquipment } = useQuery({
    queryKey: ["dashboard-equipment"],
    queryFn: () => equipmentApi.listEquipment({ skip: 0, limit: 500 }),
  });

  const { data: calibrationCounts = { dueThisWeek: 0 }, isLoading: loadingCalibrations } = useQuery({
    queryKey: ["dashboard-calibration-due-this-week", (equipment as any[]).map((e: any) => e.id)],
    enabled: (equipment as any[]).length > 0,
    queryFn: async () => {
      const now = new Date();
      const weekAhead = new Date(now);
      weekAhead.setDate(now.getDate() + 7);
      const all = await Promise.all(
        (equipment as any[]).map(async (e: any) => {
          const records = (await equipmentApi.listCalibrations(e.id)) as any[];
          return records;
        })
      );
      const flattened = all.flat();
      const dueThisWeek = flattened.filter((record: any) => {
        if (!record.next_calibration_due) return false;
        const due = new Date(record.next_calibration_due);
        return due >= now && due <= weekAhead;
      }).length;
      return { dueThisWeek };
    },
  });

  const overdueCapas = useMemo(
    () =>
      (capas as any[]).filter((capa: any) => {
        if (!capa.target_completion_date) return false;
        if (["closed", "completed", "cancelled"].includes(capa.current_status)) return false;
        return new Date(capa.target_completion_date) < new Date();
      }).length,
    [capas]
  );

  const openDeviations = useMemo(
    () =>
      (deviations as any[]).filter(
        (d: any) => !["closed", "completed", "cancelled"].includes(d.current_status)
      ).length,
    [deviations]
  );

  const pendingAssignments = useMemo(
    () =>
      (myAssignments as any[]).filter((a: any) =>
        ["pending", "overdue", "in_progress"].includes(a.status)
      ).length,
    [myAssignments]
  );

  const isLoadingAny =
    loadingCapas ||
    loadingDeviations ||
    loadingAssignments ||
    loadingEquipment ||
    loadingCalibrations;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Welcome back, {user?.full_name?.split(" ")[0]}</h1>
        <p className="text-gray-500 mt-1">Live operations summary from validated module APIs.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <SummaryCard
          title="Open CAPAs Overdue"
          value={overdueCapas}
          loading={isLoadingAny}
          accent="border-l-red-500"
          to="/qms/capas"
        />
        <SummaryCard
          title="Open Deviations"
          value={openDeviations}
          loading={isLoadingAny}
          accent="border-l-amber-500"
          to="/qms/deviations"
        />
        <SummaryCard
          title="Pending Training Assignments"
          value={pendingAssignments}
          loading={isLoadingAny}
          accent="border-l-indigo-500"
          to="/training"
        />
        <SummaryCard
          title="Calibration Due This Week"
          value={calibrationCounts.dueThisWeek}
          loading={isLoadingAny}
          accent="border-l-emerald-500"
          to="/equipment"
        />
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  loading,
  accent,
  to,
}: {
  title: string;
  value: number;
  loading: boolean;
  accent: string;
  to: string;
}) {
  return (
    <Link to={to} className={`bg-white rounded-xl p-6 shadow-sm border-l-4 ${accent} hover:shadow-md transition-shadow`}>
      <p className="text-sm text-gray-500 font-medium">{title}</p>
      <p className="text-3xl font-bold text-gray-900 mt-2">{loading ? "..." : value}</p>
      <p className="text-xs text-gray-400 mt-2">Live API data</p>
    </Link>
  );
}
