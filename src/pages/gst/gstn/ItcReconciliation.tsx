import { format, subMonths } from 'date-fns';
import {
  AlertCircle,
  AlertTriangle,
  Check,
  CheckCircle,
  Download,
  Filter,
  Loader2,
  RefreshCw,
  Scale,
  XCircle,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { ItcMismatchTypeBadge, ItcResolutionStatusBadge } from '@/components/gst/GstnStatusBadge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  getApiErrorMessage,
  useFetchGstr2b,
  useItcMismatches,
  useResolveItcMismatch,
  useRunItcReconciliation,
  type ItcMismatch,
} from '@/hooks/tax/useGstn';
import { useGSTRegistrations } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

interface ReconciliationSummary {
  totalBookValue: number;
  totalGstr2bValue: number;
  matchedCount: number;
  matchedValue: number;
  missingIn2bCount: number;
  missingIn2bValue: number;
  missingInBooksCount: number;
  missingInBooksValue: number;
  amountMismatchCount: number;
  amountMismatchVariance: number;
}

function formatReturnPeriod(period: string) {
  if (!period || period.length !== 6) {
    return period;
  }

  const month = Number.parseInt(period.substring(0, 2), 10);
  const year = period.substring(2, 6);
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${monthNames[month - 1]} ${year}`;
}

function getInitialReturnPeriod() {
  return format(subMonths(new Date(), 1), 'MMyyyy');
}

export function ItcReconciliation() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const activeOrganizationId = useActiveOrganizationId();
  const [gstin, setGstin] = useState(searchParams.get('gstin') || '');
  const [returnPeriod, setReturnPeriod] = useState(getInitialReturnPeriod());
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filteredType, setFilteredType] = useState('all');
  const [filteredStatus, setFilteredStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMismatch, setSelectedMismatch] = useState<ItcMismatch | null>(null);
  const [showResolveDialog, setShowResolveDialog] = useState(false);
  const [resolutionStatus, setResolutionStatus] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [activeTab, setActiveTab] = useState('summary');

  const registrationsQuery = useGSTRegistrations({
    includeInactive: false,
    pageSize: 100,
  });
  const registrations = registrationsQuery.data?.items;

  useEffect(() => {
    if (!gstin && registrations && registrations.length > 0) {
      setGstin(registrations[0].gstin);
    }
  }, [gstin, registrations]);

  const mismatchesQuery = useItcMismatches({
    gstin: gstin || undefined,
    returnPeriod,
    mismatchType: filteredType === 'all' ? undefined : filteredType,
    resolutionStatus: filteredStatus === 'all' ? undefined : filteredStatus,
    page: 1,
    pageSize: 100,
  });
  const fetchGstr2b = useFetchGstr2b(gstin || undefined, returnPeriod);
  const runReconciliation = useRunItcReconciliation(gstin || undefined, returnPeriod);
  const resolveMismatch = useResolveItcMismatch();

  const mismatches = mismatchesQuery.data?.items;
  const selectedRegistration = registrations?.find((registration) => registration.gstin === gstin);

  const filteredMismatches = useMemo(
    () =>
      (mismatches ?? []).filter((mismatch) => {
        if (!searchTerm) {
          return true;
        }

        const normalizedSearch = searchTerm.toLowerCase();
        return (
          mismatch.supplierGstin.toLowerCase().includes(normalizedSearch) ||
          mismatch.supplierName.toLowerCase().includes(normalizedSearch) ||
          mismatch.invoiceNumber.toLowerCase().includes(normalizedSearch)
        );
      }),
    [mismatches, searchTerm],
  );

  const summary = useMemo<ReconciliationSummary | null>(() => {
    if (!mismatches || mismatches.length === 0) {
      return null;
    }

    return mismatches.reduce<ReconciliationSummary>(
      (accumulator, mismatch) => {
        accumulator.totalBookValue += mismatch.bookTaxableValue;
        accumulator.totalGstr2bValue += mismatch.gstr2bTaxableValue;

        switch (mismatch.mismatchType) {
          case 'MATCHED':
            accumulator.matchedCount += 1;
            accumulator.matchedValue += mismatch.bookTaxableValue;
            break;
          case 'MISSING_IN_2B':
            accumulator.missingIn2bCount += 1;
            accumulator.missingIn2bValue += mismatch.bookTaxableValue;
            break;
          case 'MISSING_IN_BOOKS':
            accumulator.missingInBooksCount += 1;
            accumulator.missingInBooksValue += mismatch.gstr2bTaxableValue;
            break;
          case 'AMOUNT_MISMATCH':
            accumulator.amountMismatchCount += 1;
            accumulator.amountMismatchVariance += Math.abs(mismatch.varianceAmount);
            break;
          default:
            break;
        }

        return accumulator;
      },
      {
        totalBookValue: 0,
        totalGstr2bValue: 0,
        matchedCount: 0,
        matchedValue: 0,
        missingIn2bCount: 0,
        missingIn2bValue: 0,
        missingInBooksCount: 0,
        missingInBooksValue: 0,
        amountMismatchCount: 0,
        amountMismatchVariance: 0,
      },
    );
  }, [mismatches]);

  const pendingCount = (mismatches ?? []).filter(
    (mismatch) => mismatch.resolutionStatus === 'PENDING',
  ).length;

  const mismatchColumns = useMemo<Column<ItcMismatch>[]>(
    () => [
      {
        key: 'supplier',
        header: 'Supplier',
        render: (mismatch) => (
          <div>
            <p className="font-medium">{mismatch.supplierName}</p>
            <p className="font-mono text-sm text-muted-foreground">{mismatch.supplierGstin}</p>
          </div>
        ),
      },
      {
        key: 'invoice',
        header: 'Invoice',
        render: (mismatch) => (
          <div>
            <p className="font-medium">{mismatch.invoiceNumber}</p>
            <DateDisplay date={mismatch.invoiceDate} className="text-sm text-muted-foreground" />
          </div>
        ),
      },
      {
        key: 'bookTaxableValue',
        header: 'Book Value',
        align: 'right',
        sortable: true,
        render: (mismatch) => <AmountDisplay amount={mismatch.bookTaxableValue} />,
      },
      {
        key: 'gstr2bTaxableValue',
        header: 'GSTR-2B Value',
        align: 'right',
        sortable: true,
        render: (mismatch) => <AmountDisplay amount={mismatch.gstr2bTaxableValue} />,
      },
      {
        key: 'varianceAmount',
        header: 'Variance',
        align: 'right',
        sortable: true,
        render: (mismatch) => (
          <span
            className={
              mismatch.varianceAmount > 0
                ? 'text-red-600'
                : mismatch.varianceAmount < 0
                  ? 'text-amber-600'
                  : ''
            }
          >
            <AmountDisplay amount={mismatch.varianceAmount} />
          </span>
        ),
      },
      {
        key: 'mismatchType',
        header: 'Type',
        render: (mismatch) => <ItcMismatchTypeBadge status={mismatch.mismatchType} />,
      },
      {
        key: 'resolutionStatus',
        header: 'Status',
        render: (mismatch) => <ItcResolutionStatusBadge status={mismatch.resolutionStatus} />,
      },
      {
        key: 'actions',
        header: 'Action',
        align: 'right',
        render: (mismatch) => (
          <Button
            variant="ghost"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              setSelectedMismatch(mismatch);
              setResolutionStatus(mismatch.resolutionStatus);
              setResolutionNotes(mismatch.resolutionNotes || '');
              setShowResolveDialog(true);
            }}
          >
            Resolve
          </Button>
        ),
      },
    ],
    [],
  );

  async function handleFetch2B() {
    setError('');
    setSuccess('');
    try {
      await fetchGstr2b.mutateAsync();
      setSuccess('GSTR-2B data fetched successfully.');
      await mismatchesQuery.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to fetch GSTR-2B.'));
    }
  }

  async function handleReconcile() {
    setError('');
    setSuccess('');
    try {
      await runReconciliation.mutateAsync();
      setSuccess('Reconciliation completed successfully.');
      await mismatchesQuery.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to run reconciliation.'));
    }
  }

  async function handleResolve() {
    if (!selectedMismatch || !resolutionStatus) {
      return;
    }

    try {
      await resolveMismatch.mutateAsync({
        mismatchId: selectedMismatch.id,
        input: {
          resolutionStatus,
          resolutionNotes: resolutionNotes || undefined,
        },
      });
      setSuccess('Mismatch resolution saved successfully.');
      setShowResolveDialog(false);
      setSelectedMismatch(null);
      setResolutionStatus('');
      setResolutionNotes('');
      await mismatchesQuery.refetch();
    } catch (mutationError) {
      setError(getApiErrorMessage(mutationError, 'Failed to save mismatch resolution.'));
    }
  }

  if (registrationsQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="ITC Reconciliation"
          subtitle="Match purchase records with GSTR-2B"
          breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'ITC Reconciliation' }]}
        />
        <div className="flex h-40 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (!registrations || registrations.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="ITC Reconciliation"
          subtitle="Match purchase records with GSTR-2B"
          breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'ITC Reconciliation' }]}
        />
        <EmptyState
          title="No GST registrations"
          subtitle="Add a GST registration before reconciling ITC."
          action={
            <Button onClick={() => navigate('/admin/gst/registrations')}>
              Manage GST Registrations
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="ITC Reconciliation"
        subtitle="Match purchase records with GSTR-2B"
        breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'ITC Reconciliation' }]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleFetch2B} disabled={fetchGstr2b.isPending || !gstin} data-testid="itc-fetch-gstr2b">
              {fetchGstr2b.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Fetching...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Fetch GSTR-2B
                </>
              )}
            </Button>
            <Button onClick={handleReconcile} disabled={runReconciliation.isPending || !gstin} data-testid="itc-run-reconciliation">
              {runReconciliation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Reconciling...
                </>
              ) : (
                <>
                  <Scale className="mr-2 h-4 w-4" />
                  Run Reconciliation
                </>
              )}
            </Button>
          </div>
        }
      />

      <FilterBar
        onClear={() => {
          setError('');
          setSuccess('');
        }}
      >
        <div className="min-w-[320px]">
          <Label htmlFor="itc-gstin">GSTIN</Label>
          <Select value={gstin} onValueChange={setGstin}>
            <SelectTrigger id="itc-gstin" className="mt-1">
              <SelectValue placeholder="Select GSTIN" />
            </SelectTrigger>
            <SelectContent>
              {registrations.map((registration) => (
                <SelectItem key={registration.id} value={registration.gstin}>
                  {registration.gstin} · {registration.tradeName || registration.legalName}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-48">
          <Label htmlFor="itc-period">Return Period</Label>
          <Input
            id="itc-period"
            type="month"
            value={`${returnPeriod.substring(2, 6)}-${returnPeriod.substring(0, 2)}`}
            onChange={(event) => {
              const [year, month] = event.target.value.split('-');
              if (year && month) {
                setReturnPeriod(`${month}${year}`);
              }
            }}
            className="mt-1"
          />
        </div>
        <Button
          variant="outline"
          onClick={() => mismatchesQuery.refetch()}
          disabled={!gstin || mismatchesQuery.isFetching}
          className="self-end"
        >
          {mismatchesQuery.isFetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>
      </FilterBar>

      {error ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {success ? (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      ) : null}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="mismatches">
            Mismatches
            {pendingCount > 0 ? (
              <Badge className="ml-2 bg-red-100 text-red-700">{pendingCount}</Badge>
            ) : null}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="space-y-4">
          {summary ? (
            <>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm font-medium">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Matched
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">{summary.matchedCount}</div>
                    <p className="text-sm text-muted-foreground">
                      <AmountDisplay amount={summary.matchedValue} />
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm font-medium">
                      <XCircle className="h-4 w-4 text-red-500" />
                      Missing in GSTR-2B
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-600">{summary.missingIn2bCount}</div>
                    <p className="text-sm text-muted-foreground">
                      <AmountDisplay amount={summary.missingIn2bValue} />
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm font-medium">
                      <AlertTriangle className="h-4 w-4 text-amber-500" />
                      Missing in Books
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-amber-600">{summary.missingInBooksCount}</div>
                    <p className="text-sm text-muted-foreground">
                      <AmountDisplay amount={summary.missingInBooksValue} />
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-sm font-medium">
                      <AlertCircle className="h-4 w-4 text-purple-500" />
                      Amount Mismatch
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-purple-600">{summary.amountMismatchCount}</div>
                    <p className="text-sm text-muted-foreground">
                      Variance <AmountDisplay amount={summary.amountMismatchVariance} />
                    </p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Reconciliation Summary for {formatReturnPeriod(returnPeriod)}</CardTitle>
                  <CardDescription>
                    {selectedRegistration
                      ? `${selectedRegistration.tradeName || selectedRegistration.legalName} · ${gstin}`
                      : 'Book vs GSTR-2B comparison'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">Books</p>
                      <p className="text-xl font-semibold">
                        <AmountDisplay amount={summary.totalBookValue} />
                      </p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">GSTR-2B</p>
                      <p className="text-xl font-semibold">
                        <AmountDisplay amount={summary.totalGstr2bValue} />
                      </p>
                    </div>
                    <div className="rounded-lg border p-4">
                      <p className="text-sm text-muted-foreground">Difference</p>
                      <p className="text-xl font-semibold">
                        <AmountDisplay amount={summary.totalBookValue - summary.totalGstr2bValue} />
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <EmptyState
              title="No reconciliation data"
              subtitle="Fetch GSTR-2B and run reconciliation to compare GST input credits with your books."
              action={
                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleFetch2B} disabled={fetchGstr2b.isPending || !gstin}>
                    <Download className="mr-2 h-4 w-4" />
                    Fetch GSTR-2B
                  </Button>
                  <Button onClick={handleReconcile} disabled={runReconciliation.isPending || !gstin}>
                    <Scale className="mr-2 h-4 w-4" />
                    Run Reconciliation
                  </Button>
                </div>
              }
            />
          )}
        </TabsContent>

        <TabsContent value="mismatches" className="space-y-4">
          <FilterBar
            search={searchTerm}
            onSearchChange={setSearchTerm}
            searchPlaceholder="Search by GSTIN, supplier, or invoice"
            onClear={() => {
              setSearchTerm('');
              setFilteredType('all');
              setFilteredStatus('all');
            }}
          >
            <div className="w-48">
              <Select value={filteredType} onValueChange={setFilteredType}>
                <SelectTrigger>
                  <SelectValue placeholder="Mismatch Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="MATCHED">Matched</SelectItem>
                  <SelectItem value="MISSING_IN_2B">Missing in GSTR-2B</SelectItem>
                  <SelectItem value="MISSING_IN_BOOKS">Missing in Books</SelectItem>
                  <SelectItem value="AMOUNT_MISMATCH">Amount Mismatch</SelectItem>
                  <SelectItem value="GSTIN_MISMATCH">GSTIN Mismatch</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-48">
              <Select value={filteredStatus} onValueChange={setFilteredStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="Resolution Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="ACCEPTED">Accepted</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
                  <SelectItem value="FOLLOW_UP">Follow Up</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" onClick={() => mismatchesQuery.refetch()}>
              <Filter className="h-4 w-4" />
            </Button>
          </FilterBar>

          <Card>
            <CardHeader>
              <CardTitle>ITC Mismatches</CardTitle>
              <CardDescription>
                {filteredMismatches.length} records found for {formatReturnPeriod(returnPeriod)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {filteredMismatches.length === 0 ? (
                <EmptyState
                  title="No mismatches found"
                  subtitle="Either the books are fully reconciled or the current filters returned no results."
                />
              ) : (
                <DataTable
                  data={filteredMismatches}
                  columns={mismatchColumns}
                  getRowId={(mismatch) => mismatch.id}
                  isLoading={mismatchesQuery.isLoading}
                  error={mismatchesQuery.error}
                  onRetry={() => mismatchesQuery.refetch()}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={showResolveDialog} onOpenChange={setShowResolveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resolve Mismatch</DialogTitle>
            <DialogDescription>
              Update the resolution status and notes for this ITC mismatch.
            </DialogDescription>
          </DialogHeader>
          {selectedMismatch ? (
            <div className="space-y-4 py-4">
              <div className="space-y-2 rounded-lg bg-slate-50 p-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Supplier</span>
                  <span className="font-medium">{selectedMismatch.supplierName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Invoice</span>
                  <span className="font-medium">{selectedMismatch.invoiceNumber}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Variance</span>
                  <span className="font-medium">
                    <AmountDisplay amount={selectedMismatch.varianceAmount} />
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Resolution Status</Label>
                <Select value={resolutionStatus} onValueChange={setResolutionStatus}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PENDING">Pending</SelectItem>
                    <SelectItem value="ACCEPTED">Accepted (claim ITC)</SelectItem>
                    <SelectItem value="REJECTED">Rejected (do not claim)</SelectItem>
                    <SelectItem value="UNDER_REVIEW">Under Review</SelectItem>
                    <SelectItem value="FOLLOW_UP">Follow Up with Supplier</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={resolutionNotes}
                  onChange={(event) => setResolutionNotes(event.target.value)}
                  placeholder="Add notes about the resolution"
                  rows={3}
                />
              </div>
            </div>
          ) : null}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResolveDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleResolve} disabled={resolveMismatch.isPending || !resolutionStatus}>
              {resolveMismatch.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Save Resolution
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ItcReconciliation;
