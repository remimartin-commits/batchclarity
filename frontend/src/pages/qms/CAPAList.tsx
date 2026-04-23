import { useMemo, useState } from "react";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { qmsApi, usersApi } from "@/lib/api";
import { mockCreateCAPA, mockGetCAPAs } from "@/lib/mock-api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const capaSchema = z
  .object({
    title: z.string().min(5),
    capa_type: z.enum(["corrective", "preventive", "corrective_and_preventive"]),
    source: z.enum([
      "deviation",
      "audit_finding",
      "customer_complaint",
      "oos",
      "oot",
      "self_inspection",
      "risk_assessment",
      "supplier_issue",
      "other",
    ]),
    product_material_affected: z.string().min(1),
    batch_lot_number: z.string().optional(),
    gmp_classification: z.enum(["critical", "major", "minor", "observation"]),
    risk_level: z.enum(["low", "medium", "high", "critical"]),
    product_impact: z.boolean(),
    patient_safety_impact: z.boolean(),
    regulatory_reportable: z.boolean(),
    regulatory_reporting_justification: z.string().optional(),
    root_cause_category: z.enum([
      "human_error",
      "equipment",
      "process",
      "material",
      "environment",
      "documentation",
      "software_it",
      "unknown",
    ]),
    root_cause: z.string().min(1),
    problem_description: z.string().min(20),
    immediate_actions: z.string().optional(),
    department: z.string().min(1),
    identified_date: z.string(),
    target_completion_date: z.string().optional(),
    effectiveness_check_date: z.string().optional(),
    effectiveness_check_method: z.string().optional(),
    effectiveness_result: z.enum(["pass", "fail"]).optional(),
    effectiveness_evidence_note: z.string().optional(),
  })
  .refine(
    (v) => !v.regulatory_reportable || (v.regulatory_reporting_justification ?? "").trim().length >= 5,
    { message: "Justification is required when regulatory reporting is required.", path: ["regulatory_reporting_justification"] }
  );

type CapaCreatePayload = z.infer<typeof capaSchema> & { actions: [] };
type CapaRow = any;

const statusStyles: Record<string, string> = {
  open: "bg-gray-100 text-gray-700 border border-gray-200",
  investigation: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  action_plan_approved: "bg-blue-100 text-blue-800 border border-blue-200",
  in_progress: "bg-purple-100 text-purple-800 border border-purple-200",
  effectiveness_check: "bg-orange-100 text-orange-800 border border-orange-200",
  closed: "bg-green-100 text-green-700 border border-green-200",
};

export default function CAPAList() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [sorting, setSorting] = useState<SortingState>([]);
  const useMock = Boolean(import.meta.env.VITE_USE_MOCK);

  const form = useForm<CapaCreatePayload>({
    resolver: zodResolver(capaSchema),
    defaultValues: {
      title: "",
      capa_type: "corrective_and_preventive",
      source: "deviation",
      product_material_affected: "",
      batch_lot_number: "",
      gmp_classification: "major",
      risk_level: "medium",
      product_impact: false,
      patient_safety_impact: false,
      regulatory_reportable: false,
      regulatory_reporting_justification: "",
      root_cause_category: "unknown",
      root_cause: "",
      problem_description: "",
      immediate_actions: "",
      department: "Quality",
      identified_date: new Date().toISOString(),
      target_completion_date: "",
      effectiveness_check_date: "",
      effectiveness_check_method: "",
      effectiveness_result: undefined,
      effectiveness_evidence_note: "",
      actions: [],
    },
  });

  const { data: capas = [], isLoading } = useQuery({
    queryKey: ["qms-capas", statusFilter],
    queryFn: async () => {
      if (useMock) {
        const result = await mockGetCAPAs();
        return result.items.map((c) => ({
          ...c,
          current_status: String(c.status).toLowerCase(),
          target_completion_date: c.target_date,
          owner_id: c.owner_id,
          gmp_classification: String(c.gmp_classification).toLowerCase(),
        }));
      }
      return qmsApi.listCapas({
        ...(statusFilter ? { status_filter: statusFilter } : {}),
        skip: 0,
        limit: 100,
      });
    },
  });

  const { data: users = [] } = useQuery({
    queryKey: ["users-list"],
    queryFn: usersApi.listUsers,
    staleTime: 300_000,
  });

  const resolveOwner = (ownerId: string) => {
    const u = users.find((x: { id: string; full_name?: string }) => x.id === ownerId);
    return u?.full_name ?? `${ownerId.slice(0, 8)}…`;
  };

  const createMutation = useMutation({
    mutationFn: async (payload: CapaCreatePayload) => {
      if (useMock) return mockCreateCAPA(payload);
      return qmsApi.createCapa(payload);
    },
    onSuccess: async (created, variables) => {
      if (!useMock) {
        const hasEffectivenessFields =
          Boolean(variables.effectiveness_check_date) ||
          Boolean(variables.effectiveness_check_method) ||
          Boolean(variables.effectiveness_result) ||
          Boolean(variables.effectiveness_evidence_note);
        if (hasEffectivenessFields) {
          await qmsApi.updateCapa(created.id, {
            effectiveness_check_date: variables.effectiveness_check_date || undefined,
            effectiveness_check_method: variables.effectiveness_check_method || undefined,
            effectiveness_result: variables.effectiveness_result || undefined,
            effectiveness_evidence_note: variables.effectiveness_evidence_note || undefined,
          });
        }
      }
      queryClient.invalidateQueries({ queryKey: ["qms-capas"] });
      setCreateOpen(false);
      toast({ title: "CAPA created", description: `CAPA ${created.capa_number} created.` });
      navigate(`/qms/capas/${created.id}`);
      form.reset();
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast({ title: "Create failed", description: typeof detail === "string" ? detail : "Failed to create CAPA.", variant: "destructive" });
    },
  });

  const visibleCapas = useMemo(() => capas ?? [], [capas]);

  const columns = useMemo<ColumnDef<CapaRow>[]>(
    () => [
      {
        accessorKey: "capa_number",
        header: "CAPA #",
        cell: ({ row }) => <span className="font-mono text-brand-700">{row.original.capa_number}</span>,
      },
      { accessorKey: "title", header: "Title" },
      {
        accessorKey: "current_status",
        header: "Status",
        cell: ({ row }) => (
          <Badge className={statusStyles[row.original.current_status] ?? statusStyles.open}>
            {String(row.original.current_status).replaceAll("_", " ")}
          </Badge>
        ),
      },
      {
        accessorKey: "gmp_classification",
        header: "Classification",
        cell: ({ row }) => String(row.original.gmp_classification ?? "—").toUpperCase(),
      },
      {
        accessorKey: "target_completion_date",
        header: "Due Date",
        cell: ({ row }) =>
          row.original.target_completion_date
            ? new Date(row.original.target_completion_date).toLocaleDateString()
            : "-",
      },
      {
        id: "owner",
        header: "Assigned To",
        cell: ({ row }) => (row.original.owner_id ? resolveOwner(row.original.owner_id) : "-"),
      },
    ],
    [users]
  );

  const table = useReactTable({
    data: visibleCapas,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const onSubmit = form.handleSubmit((values) => {
    createMutation.mutate({
      ...values,
      target_completion_date: values.target_completion_date || undefined,
      immediate_actions: values.immediate_actions || undefined,
      actions: [],
    });
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CAPA Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Track corrective and preventive actions with full GMP controls.</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>Create CAPA</Button>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filter</CardTitle>
        </CardHeader>
        <CardContent>
          <Label htmlFor="status-filter">Status</Label>
          <Select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="mt-1 max-w-xs"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="investigation">Investigation</option>
          <option value="action_plan_approved">Action plan approved</option>
          <option value="in_progress">In progress</option>
          <option value="effectiveness_check">Effectiveness check</option>
          <option value="closed">Closed</option>
          </Select>
        </CardContent>
      </Card>

      {isLoading ? (
        <Card><CardContent className="py-8 text-sm text-gray-500">Loading CAPAs...</CardContent></Card>
      ) : visibleCapas.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-gray-500">
            {statusFilter ? `No "${statusFilter.replaceAll("_", " ")}" CAPAs.` : "No CAPAs yet."}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">CAPA List</CardTitle>
            <CardDescription>Sortable by status, classification, and due date.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead
                        key={header.id}
                        onClick={header.column.getToggleSortingHandler()}
                        className="cursor-pointer"
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id} onClick={() => navigate(`/qms/capas/${row.original.id}`)} className="cursor-pointer">
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create CAPA</DialogTitle>
            <DialogDescription>RHF + Zod validated CAPA creation flow.</DialogDescription>
          </DialogHeader>
          <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <Label>Title</Label>
              <Input placeholder="Title" {...form.register("title")} />
            </div>
            <div className="col-span-2">
              <Label>CAPA Type</Label>
              <Select {...form.register("capa_type")}>
                  <option value="corrective">Corrective</option>
                  <option value="preventive">Preventive</option>
                  <option value="corrective_and_preventive">Corrective and Preventive</option>
              </Select>
            </div>
            <div className="col-span-2">
              <Label>Source</Label>
              <Select {...form.register("source")}>
                  <option value="deviation">Deviation</option>
                  <option value="audit_finding">Audit Finding</option>
                  <option value="customer_complaint">Customer Complaint</option>
                  <option value="oos">OOS</option>
                  <option value="oot">OOT</option>
                  <option value="self_inspection">Self-Inspection</option>
                  <option value="risk_assessment">Risk Assessment</option>
                  <option value="supplier_issue">Supplier Issue</option>
                  <option value="other">Other</option>
              </Select>
            </div>
            <div>
              <Label>Product/Material Affected</Label>
              <Input {...form.register("product_material_affected")} />
            </div>
            <div>
              <Label>Batch/Lot Number</Label>
              <Input {...form.register("batch_lot_number")} />
            </div>
            <div>
              <Label>GMP Classification</Label>
              <Select {...form.register("gmp_classification")}>
                <option value="critical">Critical</option>
                <option value="major">Major</option>
                <option value="minor">Minor</option>
                <option value="observation">Observation</option>
              </Select>
            </div>
            <div>
              <Label>Department</Label>
              <Input {...form.register("department")} />
            </div>
            <div>
              <Label>Risk Level</Label>
              <Select {...form.register("risk_level")}>
                <option value="low">Low risk</option>
                <option value="medium">Medium risk</option>
                <option value="high">High risk</option>
                <option value="critical">Critical risk</option>
              </Select>
            </div>
            <div className="col-span-2 flex items-center gap-2">
              <Checkbox
                checked={form.watch("regulatory_reportable")}
                onChange={(e) => form.setValue("regulatory_reportable", e.target.checked)}
              />
              <Label>Regulatory Reportable</Label>
            </div>
            {form.watch("regulatory_reportable") && (
              <div className="col-span-2">
                <Label>Regulatory Reporting Justification</Label>
                <Textarea rows={2} {...form.register("regulatory_reporting_justification")} />
              </div>
            )}
            <div className="col-span-2">
              <Label>Root Cause Category</Label>
              <Select {...form.register("root_cause_category")}>
                <option value="human_error">Human Error</option>
                <option value="equipment">Equipment</option>
                <option value="process">Process</option>
                <option value="material">Material</option>
                <option value="environment">Environment</option>
                <option value="documentation">Documentation</option>
                <option value="software_it">Software-IT</option>
                <option value="unknown">Unknown</option>
              </Select>
            </div>
            <div className="col-span-2">
              <Label>Root Cause Description</Label>
              <Textarea rows={2} {...form.register("root_cause")} />
            </div>
            <div className="col-span-2">
              <Label>Problem Description</Label>
              <Textarea rows={3} {...form.register("problem_description")} />
            </div>
            <div className="col-span-2">
              <Label>Immediate Actions</Label>
              <Textarea rows={2} {...form.register("immediate_actions")} />
            </div>
            <div>
              <Label>Effectiveness Check Date</Label>
              <Input type="date" {...form.register("effectiveness_check_date")} />
            </div>
            <div>
              <Label>Effectiveness Check Method</Label>
              <Input {...form.register("effectiveness_check_method")} />
            </div>
            <div>
              <Label>Effectiveness Result</Label>
              <Select {...form.register("effectiveness_result")}>
                <option value="">Select</option>
                <option value="pass">PASS</option>
                <option value="fail">FAIL</option>
              </Select>
            </div>
            <div>
              <Label>Target Completion Date</Label>
              <Input type="date" {...form.register("target_completion_date")} />
            </div>
            <div className="col-span-2">
              <Label>Effectiveness Evidence Note</Label>
              <Textarea rows={2} {...form.register("effectiveness_evidence_note")} />
            </div>
            {(form.formState.errors.title || form.formState.errors.problem_description || form.formState.errors.regulatory_reporting_justification) && (
              <p className="col-span-2 text-sm text-red-600">
                {form.formState.errors.title?.message ||
                  form.formState.errors.problem_description?.message ||
                  form.formState.errors.regulatory_reporting_justification?.message}
              </p>
            )}
            <DialogFooter className="col-span-2">
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create CAPA"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
