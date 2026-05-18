/**
 * Sanction page extension — "Approved Utilization Breakdown".
 *
 * Renders the dual-column table from the wizard step (Requested + Approved),
 * but here the Approved column is editable (when sanction.status is
 * PENDING_APPROVAL) and the Requested column is read-only.
 *
 * Live-validates SUM(approvedAmount) == sanction.sanctionedAmount.
 * On save, calls applicationUtilizationApi.submitApproved (extended in iifApi).
 *
 * Money handling: keeps `approvedAmount` as a string (Decimal-as-string per
 * CLAUDE.md §6.2). Numbers are only computed for total/diff (math boundary).
 */

import { useMutation } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Loader2, Save } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { ErrorState } from '@/components/common/ErrorState';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useApplicationUtilization } from '@/hooks/lending/useIif';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast, getErrorEnvelope } from '@/lib/errorToast';
import {
  applicationUtilizationApi,
  type ApplicationUtilizationApprovedLine,
} from '@/services/lending/iifApi';

const TOLERANCE = 0.01;

interface SanctionApprovedUtilizationProps {
  applicationId: string;
  /** Already-sanctioned amount the approved sum must equal. */
  sanctionedAmount: number | string;
  /** Read-only when status isn't PENDING_APPROVAL. */
  editable: boolean;
}

interface LineDraft {
  categoryId: string;
  categoryLabel: string;
  requested: string;
  approved: string;
  remarks: string | null;
}

function toNumber(v: string | number | null | undefined): number {
  if (v === null || v === undefined || v === '') return 0;
  const n = typeof v === 'number' ? v : Number(v);
  return Number.isFinite(n) ? n : 0;
}

function formatRupees(n: number): string {
  return n.toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  });
}

export function SanctionApprovedUtilization({
  applicationId,
  sanctionedAmount,
  editable,
}: SanctionApprovedUtilizationProps): JSX.Element {
  const { toast } = useToast();
  const persistedQuery = useApplicationUtilization(applicationId);

  const sanctioned = toNumber(sanctionedAmount);
  const [lines, setLines] = useState<LineDraft[]>([]);

  useEffect(() => {
    const persisted = persistedQuery.data;
    if (!persisted) return;
    setLines(
      persisted.map((l) => ({
        categoryId: l.categoryId,
        categoryLabel: l.categoryLabel,
        requested: l.amount,
        approved: l.approvedAmount ?? '',
        remarks: l.remarks,
      })),
    );
  }, [persistedQuery.data]);

  const totalRequested = useMemo(
    () => lines.reduce((acc, l) => acc + toNumber(l.requested), 0),
    [lines],
  );
  const totalApproved = useMemo(
    () => lines.reduce((acc, l) => acc + toNumber(l.approved), 0),
    [lines],
  );
  const remainder = sanctioned - totalApproved;
  const matches = sanctioned > 0 && Math.abs(remainder) <= TOLERANCE;

  function handleApprovedChange(idx: number, value: string): void {
    setLines((prev) => {
      const next = [...prev];
      const current = next[idx];
      if (!current) return prev;
      const cleaned = value.replace(/[^\d.]/g, '');
      next[idx] = { ...current, approved: cleaned };
      return next;
    });
  }

  const saveMut = useMutation({
    mutationFn: () => {
      const payloadLines: ApplicationUtilizationApprovedLine[] = lines.map((l) => ({
        categoryId: l.categoryId,
        approvedAmount: l.approved === '' ? '0' : l.approved,
        remarks: l.remarks,
      }));
      return applicationUtilizationApi.submitApproved(applicationId, payloadLines);
    },
    onSuccess: () => {
      toast({ title: 'Approved utilization saved' });
      persistedQuery.refetch();
    },
    onError: (err) => {
      const env = getErrorEnvelope(err);
      if (env?.error_code === 'MANDATORY_CHECKLIST_INCOMPLETE') {
        toast({
          variant: 'destructive',
          title: 'Approval blocked',
          description:
            'Mandatory checklist items are still pending. Open the Approval Checklist tab on the application to address them before approving.',
        });
        return;
      }
      showErrorToast(err, toast);
    },
  });

  // --- Render ---------------------------------------------------------------

  if (persistedQuery.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Approved Utilization Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <SkeletonTable rows={5} columns={4} />
        </CardContent>
      </Card>
    );
  }

  if (persistedQuery.isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Approved Utilization Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorState error={persistedQuery.error} onRetry={() => persistedQuery.refetch()} />
        </CardContent>
      </Card>
    );
  }

  if (lines.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Approved Utilization Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>No utilization lines</AlertTitle>
            <AlertDescription>
              The applicant has not split the requested amount across utilization categories. Edit
              the application to fill the fund utilization step first.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Approved Utilization Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="overflow-hidden rounded-lg border bg-background">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead className="w-[200px] text-right">Requested (₹)</TableHead>
                <TableHead className="w-[220px] text-right">Approved (₹)</TableHead>
                <TableHead>Remarks</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {lines.map((line, idx) => (
                <TableRow key={line.categoryId}>
                  <TableCell className="font-medium">{line.categoryLabel}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatRupees(toNumber(line.requested))}
                  </TableCell>
                  <TableCell className="text-right">
                    {editable ? (
                      <Input
                        type="text"
                        inputMode="decimal"
                        value={line.approved}
                        onChange={(e) => handleApprovedChange(idx, e.target.value)}
                        placeholder="0.00"
                        className="text-right tabular-nums"
                        aria-label={`Approved amount for ${line.categoryLabel}`}
                      />
                    ) : (
                      <span className="font-mono tabular-nums">
                        {line.approved ? formatRupees(toNumber(line.approved)) : '—'}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {line.remarks ?? '—'}
                  </TableCell>
                </TableRow>
              ))}
              <TableRow className="border-t-2 bg-muted/30 font-semibold">
                <TableCell>Total</TableCell>
                <TableCell className="text-right tabular-nums">
                  {formatRupees(totalRequested)}
                </TableCell>
                <TableCell
                  className={`text-right tabular-nums ${
                    matches ? 'text-green-700' : 'text-amber-700'
                  }`}
                >
                  {formatRupees(totalApproved)}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <div
          className={`flex flex-wrap items-center justify-between gap-4 rounded-md border p-3 text-sm ${
            matches ? 'border-green-300 bg-green-50' : 'border-amber-300 bg-amber-50'
          }`}
        >
          <div className="space-y-0.5">
            <div className="text-muted-foreground">
              Sanctioned amount:{' '}
              <span className="font-semibold tabular-nums text-foreground">
                {formatRupees(sanctioned)}
              </span>
            </div>
            <div className={matches ? 'text-green-700' : 'text-amber-700'}>
              Approved total:{' '}
              <span className="font-semibold tabular-nums">{formatRupees(totalApproved)}</span>
              {!matches && (
                <span className="ml-2 text-xs">
                  ({remainder > 0 ? '−' : '+'}
                  {formatRupees(Math.abs(remainder))} difference)
                </span>
              )}
            </div>
          </div>
          {matches && (
            <span className="inline-flex items-center gap-1 text-green-700">
              <CheckCircle2 className="h-4 w-4" />
              Totals balance
            </span>
          )}
        </div>

        {editable && (
          <div className="flex justify-end">
            <Button onClick={() => saveMut.mutate()} disabled={!matches || saveMut.isPending}>
              {saveMut.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-2 h-4 w-4" />
              )}
              Save Approved Amounts
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
