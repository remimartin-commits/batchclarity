import { useCallback, useMemo, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { qmsApi, usersApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card as UiCard, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2 } from "lucide-react";

const STATUS_STYLES: Record<string, string> = {
  open: "bg-gray-100 text-gray-600",
  investigation: "bg-yellow-100 text-yellow-800",
  action_plan_approved: "bg-blue-100 text-blue-800",
  in_progress: "bg-purple-100 text-purple-800",
  effectiveness_check: "bg-orange-100 text-orange-800",
  closed: "bg-green-100 text-green-700",
};

const NEXT_MEANING_BY_STATUS: Record<string, string | undefined> = {
  open: "investigation",
  investigation: "action_plan_approved",
  action_plan_approved: "in_progress",
  in_progress: "effectiveness_check",
  effectiveness_check: "closed",
};

const RISK_STYLES: Record<string, string> = {
  low: "text-green-700 bg-green-50",
  medium: "text-yellow-700 bg-yellow-50",
  high: "text-orange-700 bg-orange-50",
  critical: "text-red-700 bg-red-50",
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export default function CAPADetail() {
  const { toast } = useToast();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isSignOpen, setIsSignOpen] = useState(false);
  const [downloadingAttachmentId, setDownloadingAttachmentId] = useState<string | null>(null);
  const { data: auditTrail = [] } = useQuery({
    queryKey: ["qms-capa-audit", id],
    queryFn: () => qmsApi.listCapaAuditTrail(id!),
    enabled: Boolean(id),
  });
  const { data: attachments = [], isLoading: attachmentsLoading } = useQuery({
    queryKey: ["qms-capa-attachments", id],
    queryFn: () => qmsApi.listCapaAttachments(id!),
    enabled: Boolean(id),
  });

  const { data: capa, isLoading } = useQuery({
    queryKey: ["qms-capa-detail", id],
    queryFn: () => qmsApi.getCapa(id!),
    enabled: Boolean(id),
  });

  // Fetch users list once (stale for 5 min) to resolve owner UUID → full name
  const { data: users = [] } = useQuery({
    queryKey: ["users-list"],
    queryFn: usersApi.listUsers,
    staleTime: 300_000,
  });

  const ownerUser = users.find((u: { id: string }) => u.id === capa?.owner_id);
  const ownerLabel = ownerUser
    ? `${ownerUser.full_name} (${ownerUser.username})`
    : capa?.owner_id ?? "—";

  const uploaderLabel = useCallback(
    (uid: string) => {
      const u = users.find((x: { id: string }) => x.id === uid);
      return u ? `${u.full_name} (${u.username})` : uid;
    },
    [users]
  );

  const attachmentColumns = useMemo<ColumnDef<Record<string, unknown>>[]>(
    () => [
      { accessorKey: "file_name", header: "File name" },
      {
        id: "size",
        header: "Size",
        cell: ({ row }) => formatBytes(Number(row.original.file_size_bytes ?? 0)),
      },
      {
        id: "by",
        header: "Uploaded by",
        cell: ({ row }) => uploaderLabel(String(row.original.uploaded_by_id ?? "")),
      },
      {
        accessorKey: "uploaded_at",
        header: "Uploaded at",
        cell: ({ row }) =>
          row.original.uploaded_at
            ? new Date(String(row.original.uploaded_at)).toLocaleString()
            : "—",
      },
      {
        id: "dl",
        header: "Download",
        cell: ({ row }) => {
          const attId = String(row.original.id);
          const busy = downloadingAttachmentId === attId;
          return (
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={busy}
              aria-busy={busy}
              onClick={async () => {
                if (!id) return;
                setDownloadingAttachmentId(attId);
                try {
                  await qmsApi.downloadCapaAttachmentFile(id, attId, String(row.original.file_name));
                } catch (e: unknown) {
                  const err = e as { message?: string };
                  toast({
                    title: "Download failed",
                    description: err?.message ?? "Could not download attachment.",
                    variant: "destructive",
                  });
                } finally {
                  setDownloadingAttachmentId((cur) => (cur === attId ? null : cur));
                }
              }}
            >
              {busy ? (
                <>
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" aria-hidden />
                  Downloading
                </>
              ) : (
                "Download"
              )}
            </Button>
          );
        },
      },
    ],
    [id, uploaderLabel, downloadingAttachmentId, toast]
  );

  const attachmentTable = useReactTable({
    data: attachments as Record<string, unknown>[],
    columns: attachmentColumns,
    getCoreRowModel: getCoreRowModel(),
  });

  const signMutation = useMutation({
    mutationFn: (payload: { username: string; password: string; meaning: string; comments: string }) =>
      qmsApi.signCapa(id!, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["qms-capa-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["qms-capas"] });
      setIsSignOpen(false);
      toast({ title: "Signature recorded", description: "CAPA transition signed and recorded." });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast({ title: "Signature failed", description: typeof detail === "string" ? detail : "CAPA signature failed.", variant: "destructive" });
    },
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center gap-3 text-gray-400">
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        Loading CAPA detail…
      </div>
    );
  }

  if (!capa) {
    return <div className="p-8 text-gray-500">CAPA not found.</div>;
  }

  const isClosed = ["closed", "completed", "cancelled"].includes(capa.current_status);
  const transitionMeaning = NEXT_MEANING_BY_STATUS[capa.current_status] ?? "closed";

  return (
    <div className="p-8 max-w-5xl space-y-5">
      {/* Back nav */}
      <button
        onClick={() => navigate("/qms/capas")}
        className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to CAPA dashboard
      </button>

      {/* Header card */}
      <UiCard className="p-6 flex items-start justify-between gap-4">
        <div className="space-y-2 min-w-0">
          <p className="font-mono text-brand-700 font-semibold text-sm">{capa.capa_number}</p>
          <h1 className="text-2xl font-bold text-gray-900">{capa.title}</h1>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-gray-500">
              {capa.capa_type
                .split("_")
                .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(" ")}
            </span>
            <span className="text-gray-300">•</span>
            <span className="text-gray-500">{capa.department}</span>
            <span className="text-gray-300">•</span>
            <Badge className={STATUS_STYLES[capa.current_status] ?? "bg-gray-100 text-gray-600"}>
              {String(capa.current_status).replaceAll("_", " ")}
            </Badge>
            <Badge className={RISK_STYLES[capa.risk_level] ?? ""}>
              {capa.risk_level} risk
            </Badge>
          </div>
          <p className="text-xs text-gray-400">
            Created {new Date(capa.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
            {capa.actual_completion_date && (
              <> · Closed {new Date(capa.actual_completion_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</>
            )}
          </p>
        </div>
        {!isClosed ? (
          <Button
            onClick={() => setIsSignOpen(true)}
            className="whitespace-nowrap flex-shrink-0"
          >
            {transitionMeaning === "closed"
              ? "Close CAPA"
              : `Move to ${transitionMeaning.replaceAll("_", " ")}`}
          </Button>
        ) : (
          <span className="inline-flex items-center gap-1.5 bg-green-50 text-green-700 text-sm font-medium px-3 py-1.5 rounded-lg border border-green-200 flex-shrink-0">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            Closed
          </span>
        )}
      </UiCard>

      {/* Meta grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <FieldCard title="Owner">{ownerLabel}</FieldCard>
        <FieldCard title="Source">
          {capa.source
            .split("_")
            .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(" ")}
        </FieldCard>
        <FieldCard title="Department">{capa.department}</FieldCard>
        <FieldCard title="GMP Classification">{String(capa.gmp_classification || "—").toUpperCase()}</FieldCard>
        <FieldCard title="Product/Material Affected">{capa.product_material_affected || "—"}</FieldCard>
        <FieldCard title="Batch/Lot Number">{capa.batch_lot_number || "—"}</FieldCard>
        <FieldCard title="Identified Date">
          {new Date(capa.identified_date).toLocaleDateString("en-GB", {
            day: "numeric", month: "short", year: "numeric",
          })}
        </FieldCard>
        <FieldCard title="Target Completion Date">
          {capa.target_completion_date
            ? new Date(capa.target_completion_date).toLocaleDateString("en-GB", {
                day: "numeric", month: "short", year: "numeric",
              })
            : "—"}
        </FieldCard>
        <FieldCard title="Actual Completion Date">
          {capa.actual_completion_date
            ? new Date(capa.actual_completion_date).toLocaleDateString("en-GB", {
                day: "numeric", month: "short", year: "numeric",
              })
            : "—"}
        </FieldCard>
      </div>

      {/* Impact flags */}
      <UiCard>
        <CardHeader>
          <CardTitle className="text-xs uppercase tracking-wide text-gray-500 font-semibold">Impact Assessment</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Badge variant={capa.product_impact ? "destructive" : "secondary"}>Product Impact: {capa.product_impact ? "Yes" : "No"}</Badge>
          <Badge variant={capa.patient_safety_impact ? "destructive" : "secondary"}>Patient Safety Impact: {capa.patient_safety_impact ? "Yes" : "No"}</Badge>
          <Badge variant={capa.regulatory_reportable ? "destructive" : "secondary"}>Regulatory Reportable: {capa.regulatory_reportable ? "Yes" : "No"}</Badge>
        </CardContent>
      </UiCard>

      {/* Description fields */}
      <FieldCard title="Problem Description">{capa.problem_description}</FieldCard>

      <FieldCard title="Immediate Actions">
        {capa.immediate_actions?.trim() ? capa.immediate_actions : "—"}
      </FieldCard>

      <FieldCard title="Root Cause">
        {capa.root_cause?.trim() ? (
          <>
            {capa.root_cause}
            {capa.root_cause_method && (
              <span className="ml-2 text-xs text-gray-400">
                (method: {capa.root_cause_method})
              </span>
            )}
          </>
        ) : "—"}
      </FieldCard>

      <FieldCard title="Root Cause Category">
        {capa.root_cause_category
          ? String(capa.root_cause_category)
              .split("_")
              .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
              .join(" ")
          : "—"}
      </FieldCard>

      <FieldCard title="Regulatory Reporting Justification">
        {capa.regulatory_reporting_justification?.trim() ? capa.regulatory_reporting_justification : "—"}
      </FieldCard>

      {/* Effectiveness */}
      {(capa.effectiveness_criteria || capa.effectiveness_result) && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <FieldCard title="Effectiveness Criteria">
            {capa.effectiveness_criteria ?? "—"}
          </FieldCard>
          <FieldCard title="Effectiveness Result">
            {capa.effectiveness_result ?? "—"}
          </FieldCard>
          <FieldCard title="Effectiveness Check Date">
            {capa.effectiveness_check_date
              ? new Date(capa.effectiveness_check_date).toLocaleDateString("en-GB")
              : "—"}
          </FieldCard>
          <FieldCard title="Effectiveness Method">
            {capa.effectiveness_check_method ?? "—"}
          </FieldCard>
          <FieldCard title="Effectiveness Evidence">
            {capa.effectiveness_evidence_note ?? "—"}
          </FieldCard>
        </div>
      )}

      {/* Action Plan */}
      <FieldCard title={`Action Plan (${capa.actions?.length ?? 0})`}>
        {!capa.actions?.length ? (
          <p className="text-sm text-gray-400 italic">No action items defined yet.</p>
        ) : (
          <div className="space-y-2 mt-1">
            {capa.actions.map((action: any) => (
              <div
                key={action.id}
                className="border border-gray-100 rounded-lg px-3 py-2.5 text-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-gray-800">
                    {action.sequence_number}. {action.description}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded whitespace-nowrap">
                    {action.status}
                  </span>
                </div>
                {action.due_date && (
                  <p className="text-xs text-gray-400 mt-1">
                    Due: {new Date(action.due_date).toLocaleDateString("en-GB")}
                  </p>
                )}
                {action.completion_evidence && (
                  <p className="text-xs text-gray-500 mt-1">
                    Evidence: {action.completion_evidence}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </FieldCard>

      {/* Attachments — TanStack Table (GMP evidence) */}
      <UiCard>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs uppercase tracking-wide text-gray-500 font-semibold">
            Attachments ({attachments.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {attachmentsLoading ? (
            <p className="text-sm text-gray-400 flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              Loading attachments…
            </p>
          ) : !attachments.length ? (
            <p className="text-sm text-gray-400 italic">No attachments for this CAPA.</p>
          ) : (
            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                  {attachmentTable.getHeaderGroups().map((hg) => (
                    <TableRow key={hg.id}>
                      {hg.headers.map((header) => (
                        <TableHead key={header.id}>
                          {header.isPlaceholder
                            ? null
                            : flexRender(header.column.columnDef.header, header.getContext())}
                        </TableHead>
                      ))}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {attachmentTable.getRowModel().rows.map((row) => (
                    <TableRow key={row.id}>
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </UiCard>

      <FieldCard title={`Audit Trail (${auditTrail.length})`}>
        {!auditTrail.length ? (
          <p className="text-sm text-gray-400 italic">No audit events found.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role at Time</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Old Value</TableHead>
                  <TableHead>New Value</TableHead>
                  <TableHead>UTC Timestamp</TableHead>
                  <TableHead>IP</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {auditTrail.map((event: any, idx: number) => (
                  <TableRow key={idx}>
                    <TableCell>{event.user_full_name || "—"}</TableCell>
                    <TableCell>{event.role_at_time || "—"}</TableCell>
                    <TableCell>{event.action || "—"}</TableCell>
                    <TableCell className="break-all">{event.old_value ? JSON.stringify(event.old_value) : "—"}</TableCell>
                    <TableCell className="break-all">{event.new_value ? JSON.stringify(event.new_value) : "—"}</TableCell>
                    <TableCell>{event.timestamp_utc ? new Date(event.timestamp_utc).toISOString() : "—"}</TableCell>
                    <TableCell>{event.ip_address || "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </FieldCard>

      {/* E-Signature modal */}
      <ESignatureModal
        isOpen={isSignOpen}
        isLoading={signMutation.isPending}
        title="Close CAPA"
        description="Apply your electronic signature to permanently close this CAPA. The actual completion date will be recorded and the record locked."
        meaning={transitionMeaning}
        onClose={() => setIsSignOpen(false)}
        onConfirm={async ({ username, password, meaning, comments }) => {
          await signMutation.mutateAsync({ username, password, meaning, comments });
        }}
      />
    </div>
  );
}

function FieldCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <UiCard>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs uppercase tracking-wide text-gray-500 font-semibold">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-gray-800 leading-relaxed">{children}</CardContent>
    </UiCard>
  );
}
