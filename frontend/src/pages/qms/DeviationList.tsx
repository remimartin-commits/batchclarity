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
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { qmsApi } from "@/lib/api";
import { mockGetDeviations } from "@/lib/mock-api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const deviationSchema = z
  .object({
    title: z.string().min(5),
    deviation_type: z.enum(["process", "equipment", "environmental", "material", "documentation", "personnel", "laboratory", "other"]),
    gmp_impact_classification: z.enum(["critical", "major", "minor"]),
    potential_patient_impact: z.boolean(),
    potential_patient_impact_justification: z.string().optional(),
    batches_affected_csv: z.string().optional(),
    product_affected: z.string().min(1),
    description: z.string().min(20),
    detected_during: z.string().min(3),
    immediate_containment_actions: z.string().min(10),
    root_cause_category: z.enum(["human_error", "equipment", "process", "material", "environment", "documentation", "software_it", "unknown"]),
    root_cause: z.string().optional(),
    requires_capa: z.boolean(),
    regulatory_notification_required: z.boolean(),
    regulatory_authority_name: z.string().optional(),
    regulatory_notification_deadline: z.string().optional(),
  })
  .refine(
    (v) => !v.potential_patient_impact || (v.potential_patient_impact_justification ?? "").trim().length >= 5,
    { message: "Justification is required when potential patient impact is Yes.", path: ["potential_patient_impact_justification"] }
  )
  .refine(
    (v) => !v.regulatory_notification_required || (v.regulatory_authority_name ?? "").trim().length >= 2,
    { message: "Regulatory authority is required when notification is required.", path: ["regulatory_authority_name"] }
  )
  .refine(
    (v) => !v.regulatory_notification_required || Boolean(v.regulatory_notification_deadline),
    { message: "Regulatory deadline is required when notification is required.", path: ["regulatory_notification_deadline"] }
  );

type DeviationCreatePayload = z.infer<typeof deviationSchema>;
type DeviationRow = any;

const statusStyles: Record<string, string> = {
  open: "bg-gray-100 text-gray-700 border border-gray-200",
  under_investigation: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  pending_approval: "bg-blue-100 text-blue-800 border border-blue-200",
  closed: "bg-green-100 text-green-700 border border-green-200",
};

export default function DeviationList() {
  const { toast } = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [sorting, setSorting] = useState<SortingState>([]);
  const useMock = Boolean(import.meta.env.VITE_USE_MOCK);

  const form = useForm<DeviationCreatePayload>({
    resolver: zodResolver(deviationSchema),
    defaultValues: {
      title: "",
      deviation_type: "process",
      gmp_impact_classification: "major",
      potential_patient_impact: false,
      potential_patient_impact_justification: "",
      batches_affected_csv: "",
      product_affected: "",
      description: "",
      detected_during: "manufacturing",
      immediate_containment_actions: "",
      root_cause_category: "unknown",
      root_cause: "",
      requires_capa: false,
      regulatory_notification_required: false,
      regulatory_authority_name: "",
      regulatory_notification_deadline: "",
    },
  });

  const { data: deviations = [], isLoading } = useQuery({
    queryKey: ["deviations"],
    queryFn: async () => {
      if (useMock) {
        const result = await mockGetDeviations();
        return result.items.map((d) => ({
          ...d,
          current_status: String(d.status).toLowerCase(),
          created_at: d.created_at,
          description: d.description,
          gmp_impact_classification: String(d.gmp_impact_classification).toLowerCase(),
        }));
      }
      return qmsApi.listDeviations({ skip: 0, limit: 200 });
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload: any) => qmsApi.createDeviation(payload),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["deviations"] });
      setCreateOpen(false);
      toast({ title: "Deviation created", description: `Deviation ${created.deviation_number} created.` });
      navigate(`/qms/deviations/${created.id}`);
      form.reset();
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast({ title: "Create failed", description: typeof detail === "string" ? detail : "Failed to create deviation.", variant: "destructive" });
    },
  });

  const rows = useMemo(() => deviations ?? [], [deviations]);
  const columns = useMemo<ColumnDef<DeviationRow>[]>(
    () => [
      { accessorKey: "deviation_number", header: "Deviation #", cell: ({ row }) => <span className="font-mono">{row.original.deviation_number}</span> },
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
        accessorKey: "gmp_impact_classification",
        header: "GMP Impact",
        cell: ({ row }) => String(row.original.gmp_impact_classification ?? "—").toUpperCase(),
      },
      {
        accessorKey: "created_at",
        header: "Created",
        cell: ({ row }) => (row.original.created_at ? new Date(row.original.created_at).toLocaleString() : "—"),
      },
    ],
    []
  );

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const onSubmit = form.handleSubmit((values) => {
    createMutation.mutate({
      title: values.title,
      deviation_type: values.deviation_type,
      gmp_impact_classification: values.gmp_impact_classification,
      potential_patient_impact: values.potential_patient_impact,
      potential_patient_impact_justification: values.potential_patient_impact_justification || undefined,
      batches_affected: (values.batches_affected_csv || "").split(",").map((x) => x.trim()).filter(Boolean),
      product_affected: values.product_affected,
      description: values.description,
      detected_during: values.detected_during,
      detection_date: new Date().toISOString(),
      risk_level: values.gmp_impact_classification === "critical" ? "critical" : "high",
      immediate_containment_actions: values.immediate_containment_actions,
      immediate_action: values.immediate_containment_actions,
      root_cause_category: values.root_cause_category,
      root_cause: values.root_cause || undefined,
      requires_capa: values.requires_capa,
      regulatory_notification_required: values.regulatory_notification_required,
      regulatory_authority_name: values.regulatory_authority_name || undefined,
      regulatory_notification_deadline: values.regulatory_notification_deadline
        ? new Date(values.regulatory_notification_deadline).toISOString()
        : undefined,
    });
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Deviations</h1>
          <p className="text-sm text-gray-500 mt-1">Track GMP deviations with CAPA linkage controls.</p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>New Deviation</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Deviation List</CardTitle>
          <CardDescription>Sortable by status and GMP impact classification.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id} onClick={header.column.getToggleSortingHandler()} className="cursor-pointer">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={5} className="py-8 text-center text-gray-500">Loading deviations...</TableCell></TableRow>
              ) : table.getRowModel().rows.length === 0 ? (
                <TableRow><TableCell colSpan={5} className="py-8 text-center text-gray-500">No deviations found.</TableCell></TableRow>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id} onClick={() => navigate(`/qms/deviations/${row.original.id}`)} className="cursor-pointer">
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Deviation</DialogTitle>
            <DialogDescription>RHF + Zod validated deviation creation.</DialogDescription>
          </DialogHeader>
          <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3">
            <div className="col-span-2"><Label>Title</Label><Input {...form.register("title")} /></div>

            <div>
              <Label>Deviation Type</Label>
              <Controller
                control={form.control}
                name="deviation_type"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="process">Process</SelectItem>
                      <SelectItem value="equipment">Equipment</SelectItem>
                      <SelectItem value="environmental">Environmental</SelectItem>
                      <SelectItem value="material">Material</SelectItem>
                      <SelectItem value="documentation">Documentation</SelectItem>
                      <SelectItem value="personnel">Personnel</SelectItem>
                      <SelectItem value="laboratory">Laboratory</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div>
              <Label>GMP Impact</Label>
              <Controller
                control={form.control}
                name="gmp_impact_classification"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="major">Major</SelectItem>
                      <SelectItem value="minor">Minor</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div><Label>Product affected</Label><Input {...form.register("product_affected")} /></div>
            <div><Label>Batches affected (comma-separated)</Label><Input {...form.register("batches_affected_csv")} /></div>

            <div className="col-span-2 flex items-center gap-2">
              <Controller
                control={form.control}
                name="potential_patient_impact"
                render={({ field }) => (
                  <Checkbox checked={field.value} onCheckedChange={(checked) => field.onChange(Boolean(checked))} />
                )}
              />
              <Label>Potential patient impact</Label>
            </div>

            {form.watch("potential_patient_impact") && (
              <div className="col-span-2">
                <Label>Patient impact justification</Label>
                <Textarea rows={2} {...form.register("potential_patient_impact_justification")} />
              </div>
            )}

            <div className="col-span-2"><Label>Description</Label><Textarea rows={3} {...form.register("description")} /></div>
            <div className="col-span-2"><Label>Detected During</Label><Input {...form.register("detected_during")} /></div>
            <div className="col-span-2"><Label>Immediate containment actions</Label><Textarea rows={2} {...form.register("immediate_containment_actions")} /></div>

            <div>
              <Label>Root Cause Category</Label>
              <Controller
                control={form.control}
                name="root_cause_category"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="human_error">Human Error</SelectItem>
                      <SelectItem value="equipment">Equipment</SelectItem>
                      <SelectItem value="process">Process</SelectItem>
                      <SelectItem value="material">Material</SelectItem>
                      <SelectItem value="environment">Environment</SelectItem>
                      <SelectItem value="documentation">Documentation</SelectItem>
                      <SelectItem value="software_it">Software-IT</SelectItem>
                      <SelectItem value="unknown">Unknown</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
            <div><Label>Root Cause</Label><Input {...form.register("root_cause")} /></div>

            <div className="col-span-2 flex items-center gap-2">
              <Controller
                control={form.control}
                name="requires_capa"
                render={({ field }) => (
                  <Checkbox checked={field.value} onCheckedChange={(checked) => field.onChange(Boolean(checked))} />
                )}
              />
              <Label>Requires CAPA linkage</Label>
            </div>

            <div className="col-span-2 flex items-center gap-2">
              <Controller
                control={form.control}
                name="regulatory_notification_required"
                render={({ field }) => (
                  <Checkbox checked={field.value} onCheckedChange={(checked) => field.onChange(Boolean(checked))} />
                )}
              />
              <Label>Regulatory notification required</Label>
            </div>

            {form.watch("regulatory_notification_required") && (
              <>
                <div><Label>Regulatory authority</Label><Input {...form.register("regulatory_authority_name")} /></div>
                <div><Label>Regulatory deadline</Label><Input type="datetime-local" {...form.register("regulatory_notification_deadline")} /></div>
              </>
            )}

            {Object.values(form.formState.errors).length > 0 && (
              <p className="col-span-2 text-sm text-red-600">Please resolve validation errors before creating the deviation.</p>
            )}

            <DialogFooter className="col-span-2">
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create Deviation"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
