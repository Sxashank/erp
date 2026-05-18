/**
 * Wizard Step — Fund Utilization (IIF).
 *
 * Splits the application's requested amount across the active IIF scheme's
 * fund-utilization categories. The sum of line amounts must equal
 * `requestedAmount` (from the previous wizard step) to advance, unless a
 * `treasury:write`-permissioned user toggles the override.
 *
 * Wire shape: persisted via PUT /lending/iif/applications/:id/utilization on
 * step completion (handled by the wizard's onSubmit; this step writes its
 * lines into wizard data under the `fund-utilization` key).
 *
 * Money fields are Decimal-as-string per CLAUDE.md §6.2 — we keep
 * `amount: string` in the row state and only call `Number(x)` at the math
 * boundary (total + remainder helpers).
 */

import { AlertTriangle, Eraser, ShieldCheck, Split } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { ErrorState } from '@/components/common/ErrorState';
import { SkeletonTable } from '@/components/common/SkeletonTable';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useApplicationUtilization,
  useSubventionSchemes,
  useUtilizationCategories,
} from '@/hooks/lending/useIif';
import { usePermission } from '@/hooks/usePermission';

const STEP_ID = 'fund-utilization';
const TOLERANCE = 0.01;

export interface UtilizationLineDraft {
  categoryId: string;
  categoryLabel: string;
  amount: string;
  /**
   * Lender-side approved amount per category. Populated at sanction stage;
   * the wizard renders it read-only (display only). Editable on the
   * Sanction page's "Approved Utilization" section.
   */
  approvedAmount?: string | null;
  remarks: string | null;
}

interface StepData {
  lines?: UtilizationLineDraft[];
  override?: boolean;
}

interface LoanDetailsData {
  requestedAmount?: number;
}

interface Props {
  applicationId?: string;
}

function safeNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === '') return 0;
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : 0;
}

function formatRupees(n: number): string {
  return n.toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  });
}

export default function StepFundUtilization({ applicationId }: Props): JSX.Element {
  const wizard = useWizard();
  const stepData = (wizard.data[STEP_ID] || {}) as StepData;
  const loanDetails = (wizard.data['loan-details'] || {}) as LoanDetailsData;
  const requestedAmount = safeNumber(loanDetails.requestedAmount);

  const canOverride = usePermission('TREASURY_WRITE');

  // Active IIF scheme — first ACTIVE one wins. We only need its id for the
  // categories query.
  const schemesQuery = useSubventionSchemes({ isActive: true });
  const activeScheme = useMemo(
    () => schemesQuery.data?.items?.find((s) => s.isActive) ?? null,
    [schemesQuery.data],
  );

  const categoriesQuery = useUtilizationCategories(
    activeScheme ? { schemeId: activeScheme.id, isActive: true } : undefined,
  );

  // If this is an edit (applicationId is known), preload any persisted
  // utilization lines from the backend.
  const persistedQuery = useApplicationUtilization(applicationId);

  const [lines, setLines] = useState<UtilizationLineDraft[]>(stepData.lines ?? []);
  const [override, setOverride] = useState<boolean>(Boolean(stepData.override));

  // Seed rows from categories (fresh wizard) or persisted lines (edit).
  useEffect(() => {
    // If we already have lines from step data (user navigated back), keep them.
    if ((stepData.lines ?? []).length > 0) return;

    // Persisted lines win when present.
    const persisted = persistedQuery.data;
    if (persisted && persisted.length > 0) {
      setLines(
        persisted.map((l) => ({
          categoryId: l.categoryId,
          categoryLabel: l.categoryLabel,
          amount: l.amount,
          approvedAmount: l.approvedAmount ?? null,
          remarks: l.remarks,
        })),
      );
      return;
    }

    // Otherwise seed from active scheme categories.
    const cats = categoriesQuery.data?.items;
    if (cats && cats.length > 0) {
      const sorted = [...cats].sort((a, b) => a.sortOrder - b.sortOrder);
      setLines(
        sorted.map((c) => ({
          categoryId: c.id,
          categoryLabel: c.label,
          amount: '',
          approvedAmount: null,
          remarks: null,
        })),
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persistedQuery.data, categoriesQuery.data]);

  // Push lines into wizard state whenever they change.
  useEffect(() => {
    wizard.updateStepData(STEP_ID, { lines, override });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lines, override]);

  // Compute totals (math boundary — convert string → number here only).
  const totalEntered = useMemo(
    () => lines.reduce((acc, l) => acc + safeNumber(l.amount), 0),
    [lines],
  );

  const totalApproved = useMemo(
    () => lines.reduce((acc, l) => acc + safeNumber(l.approvedAmount ?? null), 0),
    [lines],
  );

  const hasAnyApproved = useMemo(
    () => lines.some((l) => l.approvedAmount != null && l.approvedAmount !== ''),
    [lines],
  );

  const remainder = requestedAmount - totalEntered;
  const matchesRequested = requestedAmount > 0 && Math.abs(remainder) <= TOLERANCE;

  // Validation — sum must match unless override is set.
  useEffect(() => {
    const hasAllCategories = lines.length > 0;
    const allRowsHaveAmount = lines.every((l) => l.amount !== '' && safeNumber(l.amount) >= 0);
    const isValid = hasAllCategories && allRowsHaveAmount && (matchesRequested || override);
    wizard.setValidation(STEP_ID, isValid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lines, matchesRequested, override]);

  const handleAmountChange = (idx: number, value: string) => {
    setLines((prev) => {
      const next = [...prev];
      // Allow blank, allow numeric. Reject obvious garbage but be lenient —
      // zod-level validation happens at submit boundary.
      const cleaned = value.replace(/[^\d.]/g, '');
      next[idx] = { ...next[idx], amount: cleaned };
      return next;
    });
  };

  const handleRemarksChange = (idx: number, value: string) => {
    setLines((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], remarks: value || null };
      return next;
    });
  };

  const handleDistributeRemainder = () => {
    if (lines.length === 0 || requestedAmount <= 0) return;
    // Distribute requestedAmount equally; round each line to 2dp, push
    // any rounding residue into the last row.
    const equalShare = Math.floor((requestedAmount / lines.length) * 100) / 100;
    setLines((prev) => {
      const distributed = prev.map((l, i) => ({
        ...l,
        amount:
          i === prev.length - 1
            ? // last row absorbs rounding
              (requestedAmount - equalShare * (prev.length - 1)).toFixed(2)
            : equalShare.toFixed(2),
      }));
      return distributed;
    });
  };

  const handleClearAll = () => {
    setLines((prev) => prev.map((l) => ({ ...l, amount: '', remarks: null })));
  };

  // --- render --------------------------------------------------------------

  const isLoading =
    schemesQuery.isLoading ||
    categoriesQuery.isLoading ||
    (Boolean(applicationId) && persistedQuery.isLoading);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Fund Utilization</h3>
          <p className="text-sm text-muted-foreground">
            Splitting the requested loan amount across utilization categories.
          </p>
        </div>
        <SkeletonTable rows={5} columns={3} />
      </div>
    );
  }

  if (schemesQuery.isError) {
    return <ErrorState error={schemesQuery.error} onRetry={schemesQuery.refetch} />;
  }
  if (categoriesQuery.isError) {
    return <ErrorState error={categoriesQuery.error} onRetry={categoriesQuery.refetch} />;
  }

  if (!activeScheme || lines.length === 0) {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Fund Utilization</h3>
        </div>
        <Alert variant="default">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>No active subvention scheme</AlertTitle>
          <AlertDescription>
            Configure at least one active subvention scheme with utilization categories before
            applicants can split their loan amount.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Fund Utilization</h3>
        <p className="text-sm text-muted-foreground">
          Allocate the requested loan amount across the {activeScheme.schemeCode} scheme's
          utilization categories. The total must match the requested amount entered in the previous
          step.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleDistributeRemainder}
          disabled={requestedAmount <= 0}
        >
          <Split className="mr-2 h-4 w-4" />
          Distribute equally
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={handleClearAll}>
          <Eraser className="mr-2 h-4 w-4" />
          Clear all
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border bg-background">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Category</TableHead>
              <TableHead className="w-[200px] text-right">Requested (₹)</TableHead>
              <TableHead className="w-[200px] text-right">Approved (₹)</TableHead>
              <TableHead>Remarks</TableHead>
              <TableHead className="w-[120px] text-right">Δ Share</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lines.map((line, idx) => {
              const numericAmount = safeNumber(line.amount);
              const share = requestedAmount > 0 ? (numericAmount / requestedAmount) * 100 : 0;
              const approvedDisplay = safeNumber(line.approvedAmount ?? null);
              const approvedIsSet = line.approvedAmount != null && line.approvedAmount !== '';
              return (
                <TableRow key={line.categoryId}>
                  <TableCell className="font-medium">{line.categoryLabel}</TableCell>
                  <TableCell className="text-right">
                    <Input
                      type="text"
                      inputMode="decimal"
                      value={line.amount}
                      onChange={(e) => handleAmountChange(idx, e.target.value)}
                      placeholder="0.00"
                      className="text-right tabular-nums"
                      aria-label={`Requested amount for ${line.categoryLabel}`}
                    />
                  </TableCell>
                  <TableCell className="text-right text-sm tabular-nums text-muted-foreground">
                    {approvedIsSet ? (
                      <span className="font-mono">{formatRupees(approvedDisplay)}</span>
                    ) : (
                      <span className="text-muted-foreground/60">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Input
                      value={line.remarks ?? ''}
                      onChange={(e) => handleRemarksChange(idx, e.target.value)}
                      placeholder="Optional"
                      aria-label={`Remarks for ${line.categoryLabel}`}
                    />
                  </TableCell>
                  <TableCell className="text-right text-sm tabular-nums text-muted-foreground">
                    {share.toFixed(2)}%
                  </TableCell>
                </TableRow>
              );
            })}
            <TableRow className="border-t-2 bg-muted/30 font-semibold">
              <TableCell>Total</TableCell>
              <TableCell
                className={`text-right tabular-nums ${matchesRequested ? 'text-green-700' : ''}`}
              >
                {formatRupees(totalEntered)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {hasAnyApproved ? (
                  <span className="font-mono">{formatRupees(totalApproved)}</span>
                ) : (
                  <span className="text-muted-foreground/60">—</span>
                )}
              </TableCell>
              <TableCell />
              <TableCell />
            </TableRow>
          </TableBody>
        </Table>
      </div>

      <div
        className={`flex flex-wrap items-center justify-between gap-4 rounded-md border p-4 ${
          matchesRequested ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'
        }`}
      >
        <div className="space-y-1 text-sm">
          <div className="text-muted-foreground">
            Requested amount:{' '}
            <span className="font-medium tabular-nums text-foreground">
              {formatRupees(requestedAmount)}
            </span>
          </div>
          <div className={matchesRequested ? 'text-green-700' : 'text-red-700'}>
            Total entered:{' '}
            <span className="font-semibold tabular-nums">{formatRupees(totalEntered)}</span>
            {!matchesRequested && requestedAmount > 0 && (
              <span className="ml-2 text-xs">
                ({remainder > 0 ? '−' : '+'}
                {formatRupees(Math.abs(remainder))} difference)
              </span>
            )}
          </div>
        </div>
        {!matchesRequested && (
          <div className="flex items-center gap-3">
            {canOverride && (
              <div className="flex items-center gap-2">
                <Switch
                  id="utilization-override"
                  checked={override}
                  onCheckedChange={setOverride}
                />
                <Label htmlFor="utilization-override" className="flex items-center gap-1 text-sm">
                  <ShieldCheck className="h-4 w-4" />
                  Override mismatch
                </Label>
              </div>
            )}
          </div>
        )}
      </div>

      {!matchesRequested && !override && requestedAmount > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Totals do not match</AlertTitle>
          <AlertDescription>
            The sum of utilization amounts must equal the requested loan amount (
            {formatRupees(requestedAmount)}) before you can advance.
            {canOverride && ' You can toggle Override mismatch above to bypass.'}
          </AlertDescription>
        </Alert>
      )}

      {override && (
        <Alert>
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>Override active</AlertTitle>
          <AlertDescription>
            Allocations will be saved with a mismatch note. This is logged for audit.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
