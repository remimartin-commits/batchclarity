import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { limsApi, api } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

// ── Types ────────────────────────────────────────────────────────────────────

interface TestResult {
  id: string;
  test_name: string;
  method: string;
  specification: string;
  result?: string;
  unit?: string;
  pass_fail?: "pass" | "fail" | "pending";
  oos_investigation_id?: string;
  reviewed_by?: string;
  reviewed_at?: string;
}

interface Sample {
  id: string;
  sample_number: string;
  sample_type: "raw_material" | "in_process" | "finished_product" | "environmental" | "water";
  product_name?: string;
  batch_number?: string;
  collected_by: string;
  collected_at: string;
  received_at?: string;
  storage_condition?: string;
  status: "registered" | "in_testing" | "completed" | "disposed";
  results: TestResult[];
  created_at: string;
  updated_at: string;
}

interface AuditEntry {
  id: string;
  action: string;
  performed_by: string;
  performed_at: string;
  details?: string;
}

// ── Colour maps ──────────────────────────────────────────────────────────────

const STATUS_COLOUR: Record<string, string> = {
  registered: "bg-gray-100 text-gray-700",
  in_testing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  disposed: "bg-gray-200 text-gray-500",
};

const SAMPLE_TYPE_LABEL: Record<string, string> = {
  raw_material: "Raw Material",
  in_process: "In-Process",
  finished_product: "Finished Product",
  environmental: "Environmental",
  water: "Water",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (iso?: string) => (iso ? new Date(iso).toLocaleDateString() : "—");
const fmtFull = (iso?: string) => (iso ? new Date(iso).toLocaleString() : "—");

// ── Component ────────────────────────────────────────────────────────────────

export default function SampleDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const [auditExpanded, setAuditExpanded] = useState(false);
  const [reviewModal, setReviewModal] = useState<TestResult | null>(null);
  const [reviewPassword, setReviewPassword] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [coaLoading, setCoaLoading] = useState(false);

  const { data: sample, isLoading } = useQuery<Sample>({
    queryKey: ["sample", id],
    queryFn: () => limsApi.getSample(id!),
    enabled: !!id,
  });

  const { data: auditLog = [] } = useQuery<AuditEntry[]>({
    queryKey: ["audit", "sample", id],
    queryFn: () =>
      api
        .get("/audit-log", {
          params: { entity_type: "sample", entity_id: id, limit: 5 },
        })
        .then((r) => r.data),
    enabled: !!id && auditExpanded,
  });

  const reviewMutation = useMutation({
    mutationFn: () =>
      limsApi.reviewResult(id!, reviewModal!.id, { password: reviewPassword }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sample", id] });
      setReviewModal(null);
      setReviewPassword("");
      setReviewError("");
    },
    onError: (err: any) =>
      setReviewError(err.response?.data?.detail ?? "Review failed."),
  });

  const handleCoA = async () => {
    setCoaLoading(true);
    try {
      const res = await api.get(`/lims/samples/${id}/coa`, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `CoA_${sample?.sample_number ?? id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } finally {
      setCoaLoading(false);
    }
  };

  if (isLoading) return <LoadingSpinner />;
  if (!sample)
    return <NotFound message="Sample not found." onBack={() => navigate("/lims/samples")} />;

  const allResultsIn =
    sample.results?.length > 0 &&
    sample.results.every((r) => r.pass_fail === "pass" || r.pass_fail === "fail");
  const allPass = sample.results?.every((r) => r.pass_fail === "pass");
  const hasAnyFail = sample.results?.some((r) => r.pass_fail === "fail");
  const canGenerateCoA = allPass && sample.status === "completed";
  const canReviewResults = user?.permissions.includes("lims.review_results");

  const passCount = sample.results?.filter((r) => r.pass_fail === "pass").length ?? 0;
  const failCount = sample.results?.filter((r) => r.pass_fail === "fail").length ?? 0;
  const pendingCount = sample.results?.filter((r) => !r.pass_fail || r.pass_fail === "pending").length ?? 0;

  return (
    <div className="p-8 max-w-5xl">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: "Home", href: "/" },
          { label: "LIMS", href: "/lims/samples" },
          { label: "Samples", href: "/lims/samples" },
          { label: sample.sample_number },
        ]}
      />

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <span className="font-mono text-brand-600 font-semibold text-lg">
              {sample.sample_number}
            </span>
            <StatusBadge status={sample.status} colourMap={STATUS_COLOUR} />
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-gray-100 text-gray-600">
              {SAMPLE_TYPE_LABEL[sample.sample_type]}
            </span>
            {hasAnyFail && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-red-100 text-red-700">
                OOS Result(s)
              </span>
            )}
          </div>
          <h1 className="text-xl font-bold text-gray-900">
            {sample.product_name ?? "Sample"}
            {sample.batch_number && (
              <span className="text-gray-400 font-normal ml-2 text-base">
                Batch: {sample.batch_number}
              </span>
            )}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Collected by {sample.collected_by} &middot; {fmtFull(sample.collected_at)}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {canGenerateCoA && (
            <button
              onClick={handleCoA}
              disabled={coaLoading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {coaLoading ? "Generating..." : "Generate CoA"}
            </button>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard label="Total Tests" value={String(sample.results?.length ?? 0)} />
          <SummaryCard label="Passed" value={String(passCount)} highlight={passCount > 0 ? "ok" : undefined} />
          <SummaryCard label="Failed" value={String(failCount)} highlight={failCount > 0 ? "error" : undefined} />
          <SummaryCard label="Pending" value={String(pendingCount)} highlight={pendingCount > 0 ? "warn" : undefined} />
        </div>

        {/* Sample Info */}
        <Section title="Sample Information">
          <div className="grid grid-cols-3 gap-x-8 gap-y-4">
            <FieldRow label="Sample Type" value={SAMPLE_TYPE_LABEL[sample.sample_type]} />
            <FieldRow label="Product Name" value={sample.product_name ?? "—"} />
            <FieldRow label="Batch Number" value={sample.batch_number ?? "—"} />
            <FieldRow label="Collected By" value={sample.collected_by} />
            <FieldRow label="Collected At" value={fmtFull(sample.collected_at)} />
            <FieldRow label="Received At" value={sample.received_at ? fmtFull(sample.received_at) : "—"} />
            <FieldRow label="Storage Condition" value={sample.storage_condition ?? "—"} />
            <FieldRow label="Status" value={sample.status.replace(/_/g, " ")} />
          </div>
        </Section>

        {/* Test Results */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              Test Results
            </h3>
            {allResultsIn && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${allPass ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                {allPass ? "All Tests Passed" : `${failCount} Test${failCount > 1 ? "s" : ""} Failed (OOS)`}
              </span>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {["Test Name", "Method", "Specification", "Result", "Unit", "Pass/Fail", "Reviewed By", "OOS", ""].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {!sample.results?.length ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-6 text-center text-gray-400">
                      No test results recorded yet.
                    </td>
                  </tr>
                ) : (
                  sample.results.map((result) => (
                    <tr
                      key={result.id}
                      className={`hover:bg-gray-50 ${result.pass_fail === "fail" ? "bg-red-50" : ""}`}
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">{result.test_name}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs font-mono">{result.method}</td>
                      <td className="px-4 py-3 text-gray-600 text-xs">{result.specification}</td>
                      <td className="px-4 py-3 font-semibold text-gray-900">{result.result ?? "—"}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{result.unit ?? "—"}</td>
                      <td className="px-4 py-3">
                        {result.pass_fail && result.pass_fail !== "pending" ? (
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                              result.pass_fail === "pass"
                                ? "bg-green-100 text-green-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {result.pass_fail.toUpperCase()}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-300">Pending</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {result.reviewed_by ? (
                          <span title={result.reviewed_at ? fmtFull(result.reviewed_at) : undefined}>
                            {result.reviewed_by}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {result.pass_fail === "fail" && result.oos_investigation_id ? (
                          <Link
                            to={`/qms/deviations/${result.oos_investigation_id}`}
                            className="text-xs text-orange-600 hover:underline font-medium inline-flex items-center gap-1"
                          >
                            View OOS
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </Link>
                        ) : result.pass_fail === "fail" ? (
                          <span className="text-xs text-red-400">No investigation</span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {canReviewResults && result.result && !result.reviewed_by && (
                          <button
                            onClick={() => {
                              setReviewModal(result);
                              setReviewPassword("");
                              setReviewError("");
                            }}
                            className="text-xs text-brand-600 hover:underline font-medium"
                          >
                            Review
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* OOS callout */}
          {hasAnyFail && (
            <div className="mx-6 mb-4 mt-2 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="text-sm font-semibold text-red-800">Out-of-Specification (OOS) Results Detected</p>
                <p className="text-xs text-red-600 mt-0.5">
                  An OOS investigation should be initiated for failed test results. Link each failed result to a Deviation or CAPA record.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Audit Log */}
        <AuditLogSection
          expanded={auditExpanded}
          onToggle={() => setAuditExpanded((v) => !v)}
          entries={auditLog}
        />
      </div>

      {/* Result Review Modal */}
      {reviewModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Review Test Result</h3>
            <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm space-y-1">
              <p>
                <span className="text-gray-400 text-xs uppercase tracking-wide">Test: </span>
                <span className="font-medium text-gray-800">{reviewModal.test_name}</span>
              </p>
              <p>
                <span className="text-gray-400 text-xs uppercase tracking-wide">Result: </span>
                <span className="font-semibold text-gray-900">
                  {reviewModal.result} {reviewModal.unit}
                </span>
              </p>
              <p>
                <span className="text-gray-400 text-xs uppercase tracking-wide">Specification: </span>
                <span className="text-gray-700">{reviewModal.specification}</span>
              </p>
              <p>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    reviewModal.pass_fail === "pass"
                      ? "bg-green-100 text-green-700"
                      : reviewModal.pass_fail === "fail"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {(reviewModal.pass_fail ?? "pending").toUpperCase()}
                </span>
              </p>
            </div>
            {reviewError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {reviewError}
              </div>
            )}
            <p className="text-xs text-gray-400 mb-3">
              21 CFR Part 11 — password re-entry required to sign off this review.
            </p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Your password</label>
              <input
                type="password"
                value={reviewPassword}
                onChange={(e) => setReviewPassword(e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
                placeholder="Re-enter your password to sign"
                autoComplete="current-password"
              />
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setReviewModal(null);
                  setReviewError("");
                }}
                className="flex-1 border border-gray-200 text-gray-700 font-medium py-2 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => reviewMutation.mutate()}
                disabled={!reviewPassword || reviewMutation.isPending}
                className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-2 rounded-lg text-sm transition-colors"
              >
                {reviewMutation.isPending ? "Signing..." : "Confirm Review"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────

function SummaryCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "ok" | "warn" | "error";
}) {
  const cls =
    highlight === "error"
      ? "text-red-600"
      : highlight === "warn"
      ? "text-orange-600"
      : highlight === "ok"
      ? "text-green-600"
      : "text-gray-900";
  return (
    <div className="bg-white rounded-xl shadow-sm p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${cls}`}>{value}</p>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="p-8 flex items-center justify-center text-gray-400">
      <svg className="w-6 h-6 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      Loading...
    </div>
  );
}

function NotFound({ message, onBack }: { message: string; onBack: () => void }) {
  return (
    <div className="p-8 text-gray-400">
      <p>{message}</p>
      <button onClick={onBack} className="mt-2 text-sm text-brand-600 hover:underline">Go back</button>
    </div>
  );
}

function Breadcrumb({ items }: { items: { label: string; href?: string }[] }) {
  return (
    <nav className="flex items-center gap-1 text-sm text-gray-400 mb-6">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          )}
          {item.href && i < items.length - 1 ? (
            <Link to={item.href} className="hover:text-gray-700 transition-colors">{item.label}</Link>
          ) : (
            <span className={i === items.length - 1 ? "text-gray-700 font-medium" : ""}>{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

function StatusBadge({ status, colourMap }: { status: string; colourMap: Record<string, string> }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colourMap[status] ?? "bg-gray-100 text-gray-700"}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">{title}</h3>
      {children}
    </div>
  );
}

function FieldRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm text-gray-800">{value || "—"}</p>
    </div>
  );
}

interface AuditEntry {
  id: string;
  action: string;
  performed_by: string;
  performed_at: string;
  details?: string;
}

function AuditLogSection({ expanded, onToggle, entries }: { expanded: boolean; onToggle: () => void; entries: AuditEntry[] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <button onClick={onToggle} className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-gray-50 transition-colors">
        <span className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Audit Trail (last 5)</span>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && (
        <div className="px-6 pb-4 border-t border-gray-50">
          {entries.length === 0 ? (
            <p className="text-sm text-gray-400 py-4">No audit entries found.</p>
          ) : (
            <div className="space-y-3 pt-3">
              {entries.map((entry) => (
                <div key={entry.id} className="flex gap-4 text-sm">
                  <div className="w-1 rounded-full bg-brand-200 flex-shrink-0 my-0.5" />
                  <div>
                    <p className="font-medium text-gray-800">{entry.action}</p>
                    <p className="text-gray-400 text-xs">{entry.performed_by} &middot; {new Date(entry.performed_at).toLocaleString()}</p>
                    {entry.details && <p className="text-gray-500 text-xs mt-0.5">{entry.details}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
