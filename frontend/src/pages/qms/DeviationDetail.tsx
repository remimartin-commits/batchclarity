import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { qmsApi } from "@/lib/api";
import ESignatureModal from "@/components/shared/ESignatureModal";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type TransitionMeaning = "under_investigation" | "pending_approval" | "closed";

export default function DeviationDetail() {
  const { toast } = useToast();
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [pendingMeaning, setPendingMeaning] = useState<TransitionMeaning | null>(null);
  const [noCapaConfirmed, setNoCapaConfirmed] = useState(false);
  const [noCapaJustification, setNoCapaJustification] = useState("");

  const { data: deviation, isLoading } = useQuery({
    queryKey: ["qms-deviation", id],
    queryFn: () => qmsApi.getDeviation(id),
    enabled: Boolean(id),
  });
  const { data: auditTrail = [] } = useQuery({
    queryKey: ["qms-deviation-audit", id],
    queryFn: () => qmsApi.listDeviationAuditTrail(id),
    enabled: Boolean(id),
  });

  const transitionMutation = useMutation({
    mutationFn: async (payload: {
      username: string;
      password: string;
      meaning: TransitionMeaning;
      comments: string;
    }) => {
      return qmsApi.signDeviation(id, {
        username: payload.username,
        password: payload.password,
        meaning: payload.meaning,
        comments: payload.comments,
        no_capa_needed_confirmed: payload.meaning === "closed" ? noCapaConfirmed : undefined,
        no_capa_needed_justification:
          payload.meaning === "closed" ? noCapaJustification : undefined,
      });
    },
    onSuccess: async () => {
      toast({ title: "Deviation transition completed" });
      setPendingMeaning(null);
      setNoCapaConfirmed(false);
      setNoCapaJustification("");
      await queryClient.invalidateQueries({ queryKey: ["qms-deviation", id] });
      await queryClient.invalidateQueries({ queryKey: ["qms-deviation-audit", id] });
      await queryClient.invalidateQueries({ queryKey: ["deviations"] });
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail;
      toast({
        title: "Transition failed",
        description: typeof detail === "string" ? detail : "Transition failed.",
        variant: "destructive",
      });
    },
  });

  const nextMeaning = useMemo(() => {
    const status = deviation?.current_status;
    if (status === "open") return "under_investigation" as TransitionMeaning;
    if (status === "under_investigation") return "pending_approval" as TransitionMeaning;
    if (status === "pending_approval") return "closed" as TransitionMeaning;
    return null;
  }, [deviation?.current_status]);

  const limsOriginHint = useMemo(() => {
    const description: string = deviation?.description ?? "";
    return description.includes("Sample ID:") || description.includes("Result ID:");
  }, [deviation?.description]);

  if (isLoading) return <div className="p-8 text-gray-500">Loading deviation...</div>;
  if (!deviation) return <div className="p-8 text-gray-500">Deviation not found.</div>;

  const isMajorOrCritical = ["major", "critical"].includes(String(deviation.gmp_impact_classification || "").toLowerCase());

  return (
    <div className="p-8 max-w-5xl space-y-5">
      <div className="text-sm text-gray-500">
        <Link to="/qms/deviations" className="text-brand-600 hover:underline">
          Deviations
        </Link>{" "}
        / {deviation.deviation_number}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-2xl">{deviation.title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex flex-wrap gap-2">
            <Badge>{String(deviation.current_status).replaceAll("_", " ")}</Badge>
            <Badge variant="secondary">{String(deviation.deviation_type).replaceAll("_", " ")}</Badge>
            <Badge variant="secondary">{String(deviation.gmp_impact_classification).toUpperCase()}</Badge>
            {deviation.potential_patient_impact && <Badge variant="destructive">Potential Patient Impact</Badge>}
          </div>
          <p className="text-sm text-gray-500">
            {deviation.deviation_number} • Created {deviation.created_at ? new Date(deviation.created_at).toLocaleString() : "—"}
          </p>
          <p className="text-sm text-gray-700 whitespace-pre-wrap">{deviation.description}</p>
          <p className="text-sm text-gray-700">Product affected: {deviation.product_affected || "—"}</p>
          <p className="text-sm text-gray-700">Batches affected: {deviation.batches_affected?.length ? deviation.batches_affected.join(", ") : "—"}</p>
          <p className="text-sm text-gray-700">Immediate containment: {deviation.immediate_containment_actions || "—"}</p>
          <p className="text-sm text-gray-700">
            Root cause: {deviation.root_cause ? `${deviation.root_cause_category || "unknown"} - ${deviation.root_cause}` : "—"}
          </p>
          <p className="text-sm text-gray-700">Linked CAPA: {deviation.linked_capa_id || "None"}</p>
        </CardContent>
      </Card>

      {limsOriginHint && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
          Originating OOS investigation detected from LIMS-linked description.
          <Link
            to="/lims/samples"
            className="ml-1 text-brand-600 hover:text-brand-700 font-medium"
          >
            Open LIMS samples
          </Link>
        </div>
      )}

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">State Transition</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Button disabled={!nextMeaning} onClick={() => nextMeaning && setPendingMeaning(nextMeaning)}>
            {nextMeaning ? `Move to ${nextMeaning.replaceAll("_", " ")}` : "No transition available"}
          </Button>
          {deviation.potential_patient_impact && (
            <p className="text-sm text-amber-700">Closure requires QA Director signature because potential patient impact is set.</p>
          )}
          {isMajorOrCritical && !deviation.linked_capa_id && (
            <p className="text-sm text-amber-700">
              Major/Critical deviations require linked CAPA before closure, or explicit no-CAPA confirmation with written justification.
            </p>
          )}
        {nextMeaning === "closed" && !deviation.linked_capa_id && (
          <div className="space-y-2 border border-amber-200 bg-amber-50 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <Checkbox checked={noCapaConfirmed} onCheckedChange={(checked) => setNoCapaConfirmed(Boolean(checked))} />
              <Label>Confirm no CAPA is needed for closure</Label>
            </div>
            <Textarea
              rows={2}
              placeholder="Mandatory justification for closing without CAPA"
              value={noCapaJustification}
              onChange={(e) => setNoCapaJustification(e.target.value)}
            />
          </div>
        )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Audit Trail</CardTitle></CardHeader>
        <CardContent>
        {!auditTrail.length ? (
          <p className="text-sm text-gray-400">No audit events found.</p>
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
        </CardContent>
      </Card>

      <Button variant="outline" onClick={() => navigate("/qms/deviations")}>Back to deviations</Button>

      <ESignatureModal
        isOpen={Boolean(pendingMeaning)}
        isLoading={transitionMutation.isPending}
        title="Deviation State Transition"
        description={
          pendingMeaning
            ? `Apply signature and transition deviation to '${pendingMeaning}'.`
            : undefined
        }
        meaning={pendingMeaning || undefined}
        onClose={() => setPendingMeaning(null)}
        onConfirm={async ({ username, password, meaning, comments }) => {
          if (!pendingMeaning) return;
          await transitionMutation.mutateAsync({
            username,
            password,
            meaning: meaning as TransitionMeaning,
            comments,
          });
        }}
      />
    </div>
  );
}

