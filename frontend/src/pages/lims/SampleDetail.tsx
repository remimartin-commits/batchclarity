import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { limsApi } from "@/lib/api";
import { toast } from "@/stores/toastStore";

export default function SampleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [form, setForm] = useState({
    test_name: "",
    observed_value: "",
    spec_limit: "",
    is_oos: false,
  });

  const { data: sample, isLoading: loadingSample } = useQuery({
    queryKey: ["lims-sample", id],
    queryFn: () => limsApi.getSample(id!),
    enabled: Boolean(id),
  });

  const { data: results = [], isLoading: loadingResults } = useQuery({
    queryKey: ["lims-sample-results", id],
    queryFn: () => limsApi.listResults(id!),
    enabled: Boolean(id),
  });

  const addResultMutation = useMutation({
    mutationFn: () =>
      limsApi.addResult(id!, {
        test_method_id: form.test_name || "manual-test",
        result_value: form.observed_value,
        spec_limit: form.spec_limit,
        tested_at: new Date().toISOString(),
        is_oos: form.is_oos,
      }),
    onSuccess: async () => {
      toast.success("Result recorded.");
      setShowRecordModal(false);
      setForm({ test_name: "", observed_value: "", spec_limit: "", is_oos: false });
      await queryClient.invalidateQueries({ queryKey: ["lims-sample-results", id] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Failed to record result.");
    },
  });

  if (loadingSample) return <div className="p-8 text-gray-500">Loading sample...</div>;
  if (!sample) return <div className="p-8 text-gray-500">Sample not found.</div>;

  return (
    <div className="p-8 space-y-5">
      <button
        className="text-sm text-gray-500 hover:text-gray-800"
        onClick={() => navigate("/lims/samples")}
      >
        ← Back to sample list
      </button>

      <div className="bg-white rounded-xl shadow-sm p-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{sample.sample_number}</h1>
          <p className="text-sm text-gray-500 mt-1">
            Type: {sample.sample_type} • Status: {sample.status}
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
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Test Results
          </h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {["Test", "Observed Value", "Status", "Deviation Link"].map((h) => (
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
            {loadingResults ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                  Loading results...
                </td>
              </tr>
            ) : (results as any[]).length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                  No results recorded yet.
                </td>
              </tr>
            ) : (
              (results as any[]).map((result: any) => (
                <tr key={result.id} className={result.is_oos ? "bg-red-50" : ""}>
                  <td className="px-4 py-3 text-gray-700">{result.test_method_id}</td>
                  <td className="px-4 py-3 text-gray-700">{result.result_value}</td>
                  <td className="px-4 py-3">
                    {result.is_oos ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
                        OOS
                      </span>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
                        Normal
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {result.is_oos ? (
                      <Link
                        to={`/qms/deviations?source=lims&result_id=${result.id}`}
                        className="text-xs text-brand-600 hover:text-brand-700 font-medium"
                      >
                        View Deviation
                      </Link>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showRecordModal && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-3">
            <h3 className="text-lg font-semibold text-gray-900">Record Result</h3>
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              placeholder="test_name"
              value={form.test_name}
              onChange={(e) => setForm((f) => ({ ...f, test_name: e.target.value }))}
            />
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              placeholder="observed_value"
              value={form.observed_value}
              onChange={(e) => setForm((f) => ({ ...f, observed_value: e.target.value }))}
            />
            <input
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-full"
              placeholder="spec_limit"
              value={form.spec_limit}
              onChange={(e) => setForm((f) => ({ ...f, spec_limit: e.target.value }))}
            />
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.is_oos}
                onChange={(e) => setForm((f) => ({ ...f, is_oos: e.target.checked }))}
              />
              is_oos
            </label>
            {form.is_oos && (
              <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                This will auto-create a QMS Deviation.
              </p>
            )}
            <div className="flex gap-3 pt-1">
              <button
                className="flex-1 border border-gray-300 rounded-lg py-2 text-sm"
                onClick={() => setShowRecordModal(false)}
              >
                Cancel
              </button>
              <button
                className="flex-1 bg-brand-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
                disabled={addResultMutation.isPending || !form.test_name || !form.observed_value}
                onClick={() => addResultMutation.mutate()}
              >
                {addResultMutation.isPending ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

