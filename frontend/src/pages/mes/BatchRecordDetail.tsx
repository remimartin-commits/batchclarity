import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { mesApi, api } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

// ── Types ────────────────────────────────────────────────────────────────────

interface BatchStep {
  id: string;
  step_number: number;
  step_name: string;
  instruction: string;
  critical_parameter?: string;
  target_value?: string;
  actual_value?: string;
  unit?: string;
  performed_by?: string;
  performed_at?: string;
  pass_fail?: "pass" | "fail" | null;
  status: "pending" | "in_progress" | "completed" | "skipped";
}

interface MaterialUsed {
  id: string;
  material_name: string;
  material_code?: string;
  lot_number: string;
  quantity_dispensed: number;
  unit: string;
  dispensed_by?: string;
  dispensed_at?: string;
}

interface BatchRecord {
  id: string;
  batch_number: string;
  product_name: string;
  product_code: string;
  master_batch_record_ref?: string;
  planned_quantity: number;
  actual_yield?: number;
  yield_unit: string;
  manufacturing_date: string;
  expiry_date?: string;
  status: string;
  steps: BatchStep[];
  materials: MaterialUsed[];
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
  draft: "bg-gray-100 text-gray-700",
  in_progress: "bg-blue-100 text-blue-700",
  pending_release: "bg-yellow-100 text-yellow-800",
  released: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  void: "bg-red-100 text-red-700",
};

const STEP_STATUS_COLOUR: Record<string, string> = {
  pending: "bg-gray-100 text-gray-500",
  in_progress: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  skipped: "bg-orange-100 text-orange-700",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (iso?: string) => (iso ? new Date(iso).toLocaleDateString() : "—");
const fmtFull = (iso?: string) => (iso ? new Date(iso).toLocaleString() : "—");

const yieldPct = (planned: number, actual?: number) => {
  if (!actual || planned === 0) return null;
  return ((actual / planned) * 100).toFixed(1);
};

// ── Component ────────────────────────────────────────────────────────────────

export default function BatchRecordDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const [auditExpanded, setAuditExpanded] = useState(false);
  const [signModal, setSignModal] = useState(false);
  const [sigPassword, setSigPassword] = useState("");
  const [sigComments, setSigComments] = useState("");
  const [sigError, setSigError] = useState("");

  // Step execution modal
  const [stepModal, setStepModal] = useState<BatchStep | null>(null);
  const [stepActual, setStepActual] = useState("");
  const [stepPassFail, setStepPassFail] = useState<"pass" | "fail">("pass");

  const { data: batch, isLoading } = useQuery<BatchRecord>({
    queryKey: ["batch-record", id],
    queryFn: () => mesApi.getBatchRecord(id!),
    enabled: !!id,
  });

  const { data: auditLog = [] } = useQuery<AuditEntry[]>({
    queryKey: ["audit", "batch-record", id],
    queryFn: () =>
      api
        .get("/audit-log", {
          params: { entity_type: "batch_record", entity_id: id, limit: 5 },
        })
        .then((r) => r.data),
    enabled: !!id && auditExpanded,
  });

  const executeStepMutation = useMutation({
    mutationFn: () =>
      mesApi.executeStep(id!, stepModal!.id, {
        actual_value: stepActual,
        pass_fail: stepPassFail,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-record", id] });
      setStepModal(null);
      setStepActual("");
    },
  });

  const releaseMutation = useMutation({
    mutationFn: () =>
      mesApi.releaseBatchRecord(id!, {
        password: sigPassword,
        meaning: "approved",
        comments: sigComments,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-record", id] });
      setSignModal(false);
      setSigPassword("");
      setSigError("");
    },
    onError: (err: any) =>
      setSigError(err.response?.data?.detail ?? "Release signature failed."),
  });

  if (isLoading) return <LoadingSpinner />;
  if (!batch)
    return (
      <NotFound
        message="Batch record not found."
        onBack={() => navigate("/mes/batch-records")}
      />
    );

  const pct = yieldPct(batch.planned_quantity, batch.actual_yield);
  const canRelease =
    batch.status === "pending_release" && user?.permissions.includes("mes.release_batch");
  const canExecuteSteps = batch.status === "in_progress";

  const completedSteps = batch.steps?.filter((s) => s.status === "completed").length ?? 0;
  const totalSteps = batch.steps?.length ?? 0;
  const failedSteps = batch.steps?.filter((s) => s.pass_fail === "fail").length ?? 0;

  return (
    <div className="p-8 max-w-6xl">
      {/* Breadcrumb */}
      <Breadcrumb
        items={[
          { label: "Home", href: "/" },
          { label: "MES", href: "/mes/batch-records" },
          { label: "Batch Records", href: "/mes/batch-records" },
          { label: batch.batch_number },
        ]}
      />

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1 flex-wrap">
            <span className="font-mono text-brand-600 font-semibold text-lg">
              {batch.batch_number}
            </span>
            <StatusBadge status={batch.status} colourMap={STATUS_COLOUR} />
            {failedSteps > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-red-100 text-red-700">
                {failedSteps} step{failedSteps > 1 ? "s" : ""} failed
              </span>
            )}
          </div>
          <h1 className="text-xl font-bold text-gray-900">
            {batch.product_name}
            <span className="text-gray-400 font-normal ml-2 text-base">({batch.product_code})</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Manufacturing date: {fmt(batch.manufacturing_date)} &middot; Expires:{" "}
            {batch.expiry_date ? fmt(batch.expiry_date) : "—"}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {canRelease && (
            <button
              onClick={() => setSignModal(true)}
              className="bg-green-600 hover:bg-green-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Release Batch
            </button>
          )}
        </div>
      </div>

      <div className="space-y-6">
        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard
            label="Planned Quantity"
            value={`${batch.planned_quantity} ${batch.yield_unit}`}
          />
          <SummaryCard
            label="Actual Yield"
            value={
              batch.actual_yield
                ? `${batch.actual_yield} ${batch.yield_unit}`
                : "—"
            }
          />
          <SummaryCard
            label="Yield %"
            value={pct ? `${pct}%` : "—"}
            highlight={pct ? (parseFloat(pct) < 90 ? "warn" : "ok") : undefined}
          />
          <SummaryCard
            label="Steps"
            value={`${completedSteps} / ${totalSteps}`}
            highlight={failedSteps > 0 ? "error" : undefined}
          />
        </div>

        {/* Overview */}
        <Section title="Batch Overview">
          <div className="grid grid-cols-3 gap-x-8 gap-y-4">
            <FieldRow label="Product Code" value={batch.product_code} />
            <FieldRow label="Manufacturing Date" value={fmt(batch.manufacturing_date)} />
            <FieldRow label="Expiry Date" value={batch.expiry_date ? fmt(batch.expiry_date) : "—"} />
            <FieldRow
              label="Master Batch Record"
              value={batch.master_batch_record_ref ?? "—"}
            />
            <FieldRow label="Last Updated" value={fmtFull(batch.updated_at)} />
          </div>
        </Section>

        {/* Critical: Batch Steps */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              Batch Steps
            </h3>
            <span className="text-xs text-gray-400">
              {completedSteps}/{totalSteps} complete
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {[
                    "#",
                    "Step Name",
                    "Critical Parameter",
                    "Target",
                    "Actual",
                    "Unit",
                    "Pass/Fail",
                    "Performed By",
                    "Performed At",
                    "Status",
                    "",
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {!batch.steps?.length ? (
                  <tr>
                    <td colSpan={11} className="px-4 py-6 text-center text-gray-400">
                      No steps defined.
                    </td>
                  </tr>
                ) : (
                  batch.steps.map((step) => (
                    <tr
                      key={step.id}
                      className={`hover:bg-gray-50 ${step.pass_fail === "fail" ? "bg-red-50" : ""}`}
                    >
                      <td className="px-3 py-2.5 font-mono text-gray-500 text-xs">
                        {step.step_number}
                      </td>
                      <td className="px-3 py-2.5 font-medium text-gray-900 max-w-[160px]">
                        <span className="block truncate" title={step.step_name}>
                          {step.step_name}
                        </span>
                        <span
                          className="block text-xs text-gray-400 truncate font-normal"
                          title={step.instruction}
                        >
                          {step.instruction}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-gray-600 text-xs">
                        {step.critical_parameter || "—"}
                      </td>
                      <td className="px-3 py-2.5 text-gray-600">{step.target_value || "—"}</td>
                      <td className="px-3 py-2.5 font-medium text-gray-900">
                        {step.actual_value || "—"}
                      </td>
                      <td className="px-3 py-2.5 text-gray-500 text-xs">{step.unit || "—"}</td>
                      <td className="px-3 py-2.5">
                        {step.pass_fail ? (
                          <span
                            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                              step.pass_fail === "pass"
                                ? "bg-green-100 text-green-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {step.pass_fail.toUpperCase()}
                          </span>
                        ) : (
                          <span className="text-gray-300 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-gray-500 text-xs">
                        {step.performed_by || "—"}
                      </td>
                      <td className="px-3 py-2.5 text-gray-500 text-xs whitespace-nowrap">
                        {step.performed_at ? fmtFull(step.performed_at) : "—"}
                      </td>
                      <td className="px-3 py-2.5">
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium ${STEP_STATUS_COLOUR[step.status]}`}
                        >
                          {step.status}
                        </span>
                      </td>
                      <td className="px-3 py-2.5">
                        {canExecuteSteps && step.status !== "completed" && step.status !== "skipped" && (
                          <button
                            onClick={() => {
                              setStepModal(step);
                              setStepActual(step.actual_value ?? "");
                              setStepPassFail("pass");
                            }}
                            className="text-xs text-brand-600 hover:underline font-medium"
                          >
                            Record
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Materials Used */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
              Materials Used ({batch.materials?.length ?? 0})
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {["Material Name", "Code", "Lot Number", "Qty Dispensed", "Unit", "Dispensed By", "Dispensed At"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {!batch.materials?.length ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-6 text-center text-gray-400">
                      No materials recorded.
                    </td>
                  </tr>
                ) : (
                  batch.materials.map((m) => (
                    <tr key={m.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-medium text-gray-900">{m.material_name}</td>
                      <td className="px-4 py-2.5 font-mono text-gray-500 text-xs">{m.material_code || "—"}</td>
                      <td className="px-4 py-2.5 font-mono text-gray-700">{m.lot_number}</td>
                      <td className="px-4 py-2.5 text-gray-900">{m.quantity_dispensed}</td>
                      <td className="px-4 py-2.5 text-gray-500">{m.unit}</td>
                      <td className="px-4 py-2.5 text-gray-500">{m.dispensed_by || "—"}</td>
                      <td className="px-4 py-2.5 text-gray-500 text-xs">{m.dispensed_at ? fmtFull(m.dispensed_at) : "—"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Audit Log */}
        <AuditLogSection
          expanded={auditExpanded}
          onToggle={() => setAuditExpanded((v) => !v)}
          entries={auditLog}
        />
      </div>

      {/* Step Recording Modal */}
      {stepModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold text-gray-900 mb-1">
              Record Step {stepModal.step_number}: {stepModal.step_name}
            </h3>
            {stepModal.instruction && (
              <p className="text-sm text-gray-500 mb-4 bg-gray-50 rounded-lg p-3">
                {stepModal.instruction}
              </p>
            )}
            <div className="space-y-4">
              {stepModal.critical_parameter && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800">
                  <span className="font-semibold">Critical parameter:</span>{" "}
                  {stepModal.critical_parameter} — target: {stepModal.target_value ?? "N/A"}{" "}
                  {stepModal.unit}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Actual Value {stepModal.unit ? `(${stepModal.unit})` : ""}
                </label>
                <input
                  type="text"
                  value={stepActual}
                  onChange={(e) => setStepActual(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Result</label>
                <div className="flex gap-3">
                  {(["pass", "fail"] as const).map((v) => (
                    <button
                      key={v}
                      onClick={() => setStepPassFail(v)}
                      className={`flex-1 py-2 rounded-lg text-sm font-semibold border-2 transition-colors ${
                        stepPassFail === v
                          ? v === "pass"
                            ? "border-green-500 bg-green-50 text-green-700"
                            : "border-red-500 bg-red-50 text-red-700"
                          : "border-gray-200 text-gray-500 hover:bg-gray-50"
                      }`}
                    >
                      {v.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setStepModal(null)}
                className="flex-1 border border-gray-200 text-gray-700 font-medium py-2 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => executeStepMutation.mutate()}
                disabled={executeStepMutation.isPending}
                className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-2 rounded-lg text-sm transition-colors"
              >
                {executeStepMutation.isPending ? "Saving..." : "Record Step"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Release Signature Modal */}
      {signModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold text-gray-900 mb-1">Batch Release Signature</h3>
            <p className="text-xs text-gray-400 mb-1">
              Batch: <span className="font-mono font-semibold">{batch.batch_number}</span>
            </p>
            <p className="text-xs text-gray-400 mb-4">21 CFR Part 11 — password re-entry required</p>
            {sigError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {sigError}
              </div>
            )}
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800">
                Signature meaning: <span className="font-semibold">Approved for Release</span>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Your password</label>
                <input
                  type="password"
                  value={sigPassword}
                  onChange={(e) => setSigPassword(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
                  placeholder="Re-enter your password to sign"
                  autoComplete="current-password"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Release comments (optional)
                </label>
                <textarea
                  value={sigComments}
                  onChange={(e) => setSigComments(e.target.value)}
                  rows={2}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 resize-none"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setSignModal(false);
                  setSigError("");
                }}
                className="flex-1 border border-gray-200 text-gray-700 font-medium py-2 rounded-lg text-sm hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => releaseMutation.mutate()}
                disabled={!sigPassword || releaseMutation.isPending}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold py-2 rounded-lg text-sm transition-colors"
              >
                {releaseMutation.isPending ? "Releasing..." : "Release Batch"}
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
      <p className={`text-xl font-bold ${cls}`}>{value}</p>
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
