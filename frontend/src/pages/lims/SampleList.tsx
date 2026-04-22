import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { limsApi } from "@/lib/api";

const statusColour: Record<string, string> = {
  received: "bg-gray-100 text-gray-700",
  in_testing: "bg-blue-100 text-blue-700",
  pending_review: "bg-yellow-100 text-yellow-700",
  released: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function SampleList() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("all");

  const { data: samples = [], isLoading } = useQuery({
    queryKey: ["lims-samples", statusFilter],
    queryFn: () =>
      limsApi.listSamples(
        statusFilter === "all" ? { skip: 0, limit: 200 } : { status_filter: statusFilter, skip: 0, limit: 200 }
      ),
  });

  const visibleSamples = useMemo(() => (samples as any[]) ?? [], [samples]);

  return (
    <div className="p-8 space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">LIMS Samples</h1>
        <p className="text-gray-500 text-sm mt-1">
          Track samples by status and drill into test results.
        </p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["all", "pending", "in_progress", "released"].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-3 py-1.5 border rounded text-sm ${
              statusFilter === status ? "bg-brand-600 text-white border-brand-600" : "bg-white"
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Sample Number", "Sample Type", "Status", "Sampled At"].map((h) => (
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
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                  Loading samples...
                </td>
              </tr>
            ) : visibleSamples.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                  No samples found.
                </td>
              </tr>
            ) : (
              visibleSamples.map((sample: any) => (
                <tr
                  key={sample.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/lims/samples/${sample.id}`)}
                >
                  <td className="px-4 py-3 font-mono text-brand-700">{sample.sample_number}</td>
                  <td className="px-4 py-3 text-gray-700">{sample.sample_type}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        statusColour[sample.status] ?? "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {String(sample.status).replaceAll("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {sample.sampled_at ? new Date(sample.sampled_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

