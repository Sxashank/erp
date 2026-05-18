import { zodResolver } from '@hookform/resolvers/zod';
import { Link2, RefreshCw, Save } from 'lucide-react';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';

import { AmountInput } from '@/components/common/AmountInput';
import { DataTable, type Column } from '@/components/common/DataTable';
import { FilterBar } from '@/components/common/FilterBar';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DatePicker } from '@/components/ui/date-picker';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useBorrowings } from '@/hooks/lending/useBorrowings';
import {
  useCreateFundDeployment,
  useFundDeployments,
  useFundDeploymentProfitability,
  useFundDeploymentSummary,
} from '@/hooks/lending/useFundDeployments';
import { useLoanAccounts } from '@/hooks/lending/useLoanAccounts';
import { useToast } from '@/hooks/use-toast';
import {
  fundDeploymentSchema,
  type FundDeploymentFormInput,
  type FundDeploymentInput,
} from '@/schemas/lending/fundDeploymentSchema';
import type { FundDeployment, FundProfitabilityRow } from '@/services/lending/fundDeploymentApi';

const todayIso = new Date().toISOString().slice(0, 10);

export default function SourceOfFundsWorkbench() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const summaryQuery = useFundDeploymentSummary();
  const profitabilityQuery = useFundDeploymentProfitability(25);
  const deploymentsQuery = useFundDeployments({ pageSize: 100 });
  const borrowingsQuery = useBorrowings({ pageSize: 200 });
  const loanAccountsQuery = useLoanAccounts({ status: 'ACTIVE', pageSize: 200 });
  const createDeployment = useCreateFundDeployment();

  const form = useForm<FundDeploymentFormInput, unknown, FundDeploymentInput>({
    resolver: zodResolver(fundDeploymentSchema),
    defaultValues: {
      borrowingId: '',
      loanAccountId: '',
      allocatedAmount: 0,
      allocationDate: todayIso,
      remarks: '',
    },
  });

  const borrowingOptions = borrowingsQuery.data?.items ?? [];
  const loanOptions = loanAccountsQuery.data?.items ?? [];

  const borrowingById = useMemo(
    () => new Map(borrowingOptions.map((item) => [item.id, item])),
    [borrowingOptions],
  );
  const loanById = useMemo(
    () => new Map(loanOptions.map((item) => [item.id, item])),
    [loanOptions],
  );

  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    const items = deploymentsQuery.data?.items ?? [];
    if (!term) return items;
    return items.filter((row) => {
      const borrowing = borrowingById.get(row.borrowingId);
      const loan = loanById.get(row.loanAccountId);
      return [
        row.deploymentReference,
        row.status,
        row.remarks,
        borrowing?.borrowingNumber,
        borrowing?.lenderName,
        loan?.loanAccountNumber,
        loan?.entityName,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(term));
    });
  }, [borrowingById, deploymentsQuery.data?.items, loanById, search]);

  const columns = useMemo<Column<FundDeployment>[]>(
    () => [
      {
        key: 'deploymentReference',
        header: 'Reference',
        sortable: true,
        render: (row) => <span className="font-mono text-sm">{row.deploymentReference}</span>,
      },
      {
        key: 'allocationDate',
        header: 'Date',
        sortable: true,
        render: (row) => <DateDisplay date={row.allocationDate} />,
      },
      {
        key: 'borrowing',
        header: 'Borrowing Source',
        render: (row) => {
          const borrowing = borrowingById.get(row.borrowingId);
          return (
            <div className="space-y-1">
              <p className="font-medium">{borrowing?.lenderName ?? 'Mapped borrowing'}</p>
              <p className="font-mono text-xs text-muted-foreground">
                {borrowing?.borrowingNumber ?? row.borrowingId}
              </p>
            </div>
          );
        },
      },
      {
        key: 'loan',
        header: 'Loan Deployment',
        render: (row) => {
          const loan = loanById.get(row.loanAccountId);
          return (
            <div className="space-y-1">
              <p className="font-medium">{loan?.entityName ?? 'Mapped loan account'}</p>
              <p className="font-mono text-xs text-muted-foreground">
                {loan?.loanAccountNumber ?? row.loanAccountId}
              </p>
            </div>
          );
        },
      },
      {
        key: 'allocatedAmount',
        header: 'Amount',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.allocatedAmount),
        render: (row) => <AmountDisplay amount={row.allocatedAmount} abbreviated />,
      },
      {
        key: 'spreadBps',
        header: 'Spread',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.spreadBps),
        render: (row) => <span className="font-medium">{row.spreadBps} bps</span>,
      },
    ],
    [borrowingById, loanById],
  );

  const profitabilityColumns = useMemo<Column<FundProfitabilityRow>[]>(
    () => [
      {
        key: 'loanAccountNumber',
        header: 'Loan Account',
        sortable: true,
        render: (row) => (
          <div className="space-y-1">
            <p className="font-mono text-sm">{row.loanAccountNumber}</p>
            <p className="text-xs text-muted-foreground">{row.entityName ?? '-'}</p>
          </div>
        ),
      },
      {
        key: 'deployedAmount',
        header: 'Deployed',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.deployedAmount),
        render: (row) => <AmountDisplay amount={row.deployedAmount} abbreviated />,
      },
      {
        key: 'rates',
        header: 'Yield / Cost',
        align: 'right',
        render: (row) => (
          <span className="text-sm">
            <PercentageDisplay value={row.weightedLendingRate} /> /{' '}
            <PercentageDisplay value={row.weightedCostRate} />
          </span>
        ),
      },
      {
        key: 'spreadBps',
        header: 'Spread',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.spreadBps),
        render: (row) => <span className="font-medium">{row.spreadBps} bps</span>,
      },
      {
        key: 'estimatedAnnualNii',
        header: 'Est. Annual NII',
        align: 'right',
        sortable: true,
        sortValue: (row) => Number(row.estimatedAnnualNii),
        render: (row) => <AmountDisplay amount={row.estimatedAnnualNii} abbreviated />,
      },
    ],
    [],
  );

  function handleSubmit(values: FundDeploymentInput) {
    createDeployment.mutate(
      {
        borrowingId: values.borrowingId,
        loanAccountId: values.loanAccountId,
        allocatedAmount: values.allocatedAmount,
        allocationDate: values.allocationDate,
        remarks: values.remarks || undefined,
      },
      {
        onSuccess: (deployment) => {
          toast({
            title: 'Fund deployment mapped',
            description: `${deployment.deploymentReference} created with ${deployment.spreadBps} bps spread`,
          });
          form.reset({
            borrowingId: values.borrowingId,
            loanAccountId: values.loanAccountId,
            allocatedAmount: 0,
            allocationDate: todayIso,
            remarks: '',
          });
        },
        onError: (error) => {
          toast({
            title: 'Deployment mapping failed',
            description:
              error instanceof Error ? error.message : 'Review the mapping and try again',
            variant: 'destructive',
          });
        },
      },
    );
  }

  const summary = summaryQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Source of Funds"
        subtitle="Map borrowing drawdowns to corporate loan deployments and track spread coverage"
        actions={
          <Button
            variant="outline"
            onClick={() => {
              void summaryQuery.refetch();
              void profitabilityQuery.refetch();
              void deploymentsQuery.refetch();
            }}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Deployed Funds</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.deployedAmount ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              {summary?.mappedDeployments ?? 0} mapped deployments
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Unmapped Drawn Funds</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.unmappedDrawnBorrowings ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">Drawdowns pending deployment link</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Weighted Spread</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.weightedSpreadBps ?? '0'} bps</div>
            <p className="text-sm text-muted-foreground">
              Yield <PercentageDisplay value={summary?.weightedLendingRate ?? '0'} /> vs cost{' '}
              <PercentageDisplay value={summary?.weightedCostRate ?? '0'} />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Drawn Borrowings</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={summary?.activeDrawnBorrowings ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">Available for mapping</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Estimated Annual NII</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={profitabilityQuery.data?.summary.estimatedAnnualNii ?? '0'}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="text-sm text-muted-foreground">
              Across {profitabilityQuery.data?.summary.mappedLoans ?? 0} mapped loan assets
            </p>
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Portfolio Profitability</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-3">
              <div>
                <p className="text-xs text-muted-foreground">Annual interest income</p>
                <AmountDisplay
                  amount={profitabilityQuery.data?.summary.estimatedAnnualInterestIncome ?? '0'}
                  abbreviated
                  className="font-semibold"
                />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Annual interest expense</p>
                <AmountDisplay
                  amount={profitabilityQuery.data?.summary.estimatedAnnualInterestExpense ?? '0'}
                  abbreviated
                  className="font-semibold"
                />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Weighted spread</p>
                <p className="font-semibold">
                  {profitabilityQuery.data?.summary.weightedSpreadBps ?? '0'} bps
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <DataTable
        data={profitabilityQuery.data?.rows ?? []}
        columns={profitabilityColumns}
        getRowId={(row) => row.loanAccountId}
        isLoading={profitabilityQuery.isLoading}
        error={profitabilityQuery.isError ? profitabilityQuery.error : undefined}
        onRetry={() => profitabilityQuery.refetch()}
        emptyTitle="No profitability rows"
        emptySubtitle="Create source-of-funds mappings to calculate loan-level spread and NII."
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)}>
          <FormShell
            footer={
              <Button type="submit" disabled={createDeployment.isPending}>
                <Save className="mr-2 h-4 w-4" />
                Create Mapping
              </Button>
            }
          >
            <FormSection
              title="Create Source-of-Funds Mapping"
              description="Select the borrowing source and loan asset receiving the funds."
            >
              <FormField
                control={form.control}
                name="borrowingId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Borrowing source</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value || undefined}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select borrowing facility" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {borrowingOptions.map((item) => (
                          <SelectItem key={item.id} value={item.id}>
                            {item.borrowingNumber} — {item.lenderName ?? 'Lender'} (
                            <AmountDisplay amount={item.drawnAmount} abbreviated /> drawn)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="loanAccountId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loan account</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value || undefined}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select corporate loan account" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {loanOptions.map((item) => (
                          <SelectItem key={item.id} value={item.id}>
                            {item.loanAccountNumber} — {item.entityName ?? 'Borrower'} (
                            <AmountDisplay amount={item.totalDisbursedAmount} abbreviated />{' '}
                            disbursed)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="allocatedAmount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Allocated amount</FormLabel>
                    <FormControl>
                      <AmountInput value={field.value} onChange={field.onChange} />
                    </FormControl>
                    <FormDescription>
                      Amount of drawn borrowing deployed into this loan.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="allocationDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Allocation date</FormLabel>
                    <FormControl>
                      <DatePicker
                        date={field.value ? new Date(`${field.value}T00:00:00`) : undefined}
                        onSelect={(value) =>
                          field.onChange(value ? value.toISOString().slice(0, 10) : '')
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="remarks"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Remarks</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Optional treasury note, deployment basis, or committee reference"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>
          </FormShell>
        </form>
      </Form>

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search deployment, lender, borrower or loan account"
        onClear={() => setSearch('')}
      />

      <DataTable
        data={rows}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={deploymentsQuery.isLoading}
        error={deploymentsQuery.isError ? deploymentsQuery.error : undefined}
        onRetry={() => deploymentsQuery.refetch()}
        emptyTitle="No source-of-funds mappings"
        emptySubtitle="Create the first deployment mapping to connect borrowing drawdowns with loan assets."
        emptyAction={
          <Button variant="outline" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <Link2 className="mr-2 h-4 w-4" />
            Create mapping
          </Button>
        }
      />
    </div>
  );
}
