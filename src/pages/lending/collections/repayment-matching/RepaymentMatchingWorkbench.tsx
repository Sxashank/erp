import { RefreshCw, SearchCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DataTable, type Column } from '@/components/common/DataTable';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useCreateMatchedReceipt,
  useRepaymentMatchCandidates,
} from '@/hooks/lending/useRepaymentMatching';
import { useToast } from '@/hooks/use-toast';
import type {
  RepaymentMatchCandidate,
  RepaymentMatchingFilters,
} from '@/services/lending/repaymentMatchingApi';

const confidenceOptions = [
  { label: 'All candidates', value: '0' },
  { label: 'Reviewable only', value: '50' },
  { label: 'High confidence', value: '80' },
];

export default function RepaymentMatchingWorkbench() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [minConfidence, setMinConfidence] = useState('0');

  const filters = useMemo<RepaymentMatchingFilters>(
    () => ({ minConfidence, limit: 100 }),
    [minConfidence],
  );
  const { data, isLoading, isError, error, refetch, isFetching } =
    useRepaymentMatchCandidates(filters);
  const createMatchedReceipt = useCreateMatchedReceipt();

  const candidates = useMemo(() => {
    const rows = data?.candidates ?? [];
    const term = search.trim().toLowerCase();
    if (!term) return rows;
    return rows.filter((row) =>
      [
        row.referenceNumber,
        row.utrNumber,
        row.description,
        row.loanAccountNumber,
        row.entityName,
        row.suggestedAction,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term)),
    );
  }, [data?.candidates, search]);

  const columns = useMemo<Column<RepaymentMatchCandidate>[]>(
    () => [
      {
        key: 'transactionDate',
        header: 'Txn Date',
        sortable: true,
        render: (row) => <DateDisplay date={row.transactionDate} />,
      },
      {
        key: 'reference',
        header: 'Reference / UTR',
        render: (row) => (
          <div className="space-y-1">
            <p className="font-mono text-sm">{row.utrNumber ?? row.referenceNumber ?? '-'}</p>
            <p className="max-w-[260px] truncate text-xs text-muted-foreground">
              {row.description ?? '-'}
            </p>
          </div>
        ),
      },
      {
        key: 'creditAmount',
        header: 'Credit',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.creditAmount),
        render: (row) => <AmountDisplay amount={row.creditAmount} abbreviated />,
      },
      {
        key: 'borrower',
        header: 'Suggested Loan',
        render: (row) => (
          <div className="space-y-1">
            <p className="font-medium">{row.entityName ?? 'Unidentified borrower'}</p>
            <p className="font-mono text-xs text-muted-foreground">
              {row.loanAccountNumber ?? 'No loan match'}
            </p>
          </div>
        ),
      },
      {
        key: 'due',
        header: 'Demand',
        align: 'right',
        render: (row) => (
          <div className="space-y-1">
            <AmountDisplay amount={row.dueAmount} abbreviated />
            <p className="text-xs text-muted-foreground">
              Due <DateDisplay date={row.dueDate} />
            </p>
          </div>
        ),
      },
      {
        key: 'confidence',
        header: 'Confidence',
        align: 'center',
        sortable: true,
        sortValue: (row) => Number(row.confidence),
        render: (row) => <PercentageDisplay value={row.confidence} decimals={0} />,
      },
      {
        key: 'action',
        header: 'Suggested Action',
        render: (row) => (
          <div className="space-y-2">
            <StatusBadge type="product" status={row.suggestedAction} size="sm" />
            <p className="max-w-[220px] text-xs text-muted-foreground">
              {row.matchBasis.length ? row.matchBasis.join(', ') : 'Manual review required'}
            </p>
          </div>
        ),
      },
      {
        key: 'open',
        header: '',
        align: 'right',
        render: (row) => (
          <Button
            variant="outline"
            size="sm"
            disabled={createMatchedReceipt.isPending}
            onClick={(event) => {
              event.stopPropagation();
              if (!row.suggestedLoanAccountId) {
                navigate('/admin/lending/receipts/create');
                return;
              }
              createMatchedReceipt.mutate(
                {
                  statementId: row.statementId,
                  body: {
                    loanAccountId: row.suggestedLoanAccountId,
                    autoAllocate: true,
                  },
                },
                {
                  onSuccess: (receipt) => {
                    toast({
                      title: 'Receipt created',
                      description: `${receipt.receiptNumber} linked as ${receipt.matchType.toLowerCase()} match (${Number(receipt.matchConfidence).toFixed(0)}% confidence)`,
                    });
                  },
                  onError: (mutationError) => {
                    toast({
                      title: 'Receipt creation failed',
                      description:
                        mutationError instanceof Error
                          ? mutationError.message
                          : 'Review the candidate and try again',
                      variant: 'destructive',
                    });
                  },
                },
              );
            }}
          >
            {row.suggestedLoanAccountId ? 'Create receipt' : 'Record receipt'}
          </Button>
        ),
      },
    ],
    [createMatchedReceipt, navigate, toast],
  );

  const summary = data?.summary;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Future Repayment Matching"
        subtitle="Optional future automation for imported bank credits; current operations use manual receipt entry and allocation"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => refetch()} disabled={isFetching}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Future Unmatched Credits</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.unmatchedCreditCount ?? 0}</div>
            <AmountDisplay amount={summary?.unmatchedCreditAmount ?? '0'} abbreviated />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Future Match Candidates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.highConfidenceCount ?? 0}</div>
            <p className="text-sm text-muted-foreground">Confidence ≥ 80%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Review Required</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.reviewRequiredCount ?? 0}</div>
            <p className="text-sm text-muted-foreground">Low confidence or no match</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Visible Candidates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{candidates.length}</div>
            <p className="text-sm text-muted-foreground">After current filters</p>
          </CardContent>
        </Card>
      </div>

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search reference, UTR, borrower, loan account"
        onClear={() => {
          setSearch('');
          setMinConfidence('0');
        }}
      >
        <Select value={minConfidence} onValueChange={setMinConfidence}>
          <SelectTrigger className="w-[190px]">
            <SelectValue placeholder="Confidence" />
          </SelectTrigger>
          <SelectContent>
            {confidenceOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FilterBar>

      <DataTable
        data={candidates}
        columns={columns}
        getRowId={(row) => row.statementId}
        isLoading={isLoading}
        error={isError ? error : undefined}
        onRetry={() => refetch()}
        emptyTitle="Future automation not enabled"
        emptySubtitle="This future automation screen is hidden from current manual operations."
        emptyAction={
          <Button onClick={() => navigate('/admin/lending/collection-cockpit')}>
            <SearchCheck className="mr-2 h-4 w-4" />
            Open collection cockpit
          </Button>
        }
      />
    </div>
  );
}
