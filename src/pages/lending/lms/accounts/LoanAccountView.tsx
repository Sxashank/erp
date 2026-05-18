import { FileText, Receipt } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { DPDBadge } from '@/components/lending/common/DPDBadge';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLoanAccount } from '@/hooks/lending/useLoanAccount';

export default function LoanAccountView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: account, isLoading, isError, error, refetch } = useLoanAccount(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Loan Account" subtitle="Loading..." />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !account) {
    return (
      <div className="space-y-6">
        <PageHeader title="Loan Account" />
        <ErrorState title="Could not load loan account" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={account.loanAccountNumber}
        subtitle={`${account.entityName ?? account.entityLegalName ?? 'Entity'} · ${account.productName ?? 'Product'}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Accounts', to: '/admin/lending/accounts' },
          { label: account.loanAccountNumber },
        ]}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate(`/admin/lending/accounts/${id}/statement`)}
            >
              <FileText className="mr-2 h-4 w-4" />
              Statement
            </Button>
            <Button onClick={() => navigate(`/admin/lending/receipts/new?accountId=${id}`)}>
              <Receipt className="mr-2 h-4 w-4" />
              Record Receipt
            </Button>
          </div>
        }
      />

      {/* Status + key metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <StatusBadge status={account.status} type="loan" />
            <p className="mt-2 text-xs text-muted-foreground">
              Opened: <DateDisplay date={account.accountOpenDate} />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Outstanding
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={account.totalOutstanding}
              abbreviated
              className="text-2xl font-bold"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              of <AmountDisplay amount={account.sanctionedAmount} abbreviated /> sanctioned
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">DPD</CardTitle>
          </CardHeader>
          <CardContent>
            <DPDBadge dpd={account.daysPastDue} />
            <p className="mt-2 text-xs text-muted-foreground">
              {account.assetClassification}
              {account.npaDate && (
                <>
                  {' '}
                  · NPA on <DateDisplay date={account.npaDate} />
                </>
              )}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Interest Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <PercentageDisplay value={account.currentInterestRate} /> p.a.
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{account.interestType}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabbed details */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
          <TabsTrigger value="disbursements">Disbursements</TabsTrigger>
          <TabsTrigger value="receipts">Receipts</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Loan Terms</CardTitle>
              <CardDescription>Sanctioned terms and interest configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Sanctioned Amount</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={account.sanctionedAmount} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Tenure</dt>
                  <dd className="font-medium">{account.tenureMonths} months</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Moratorium</dt>
                  <dd className="font-medium">{account.moratoriumMonths} months</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Repayment Frequency</dt>
                  <dd className="font-medium">{account.repaymentFrequency}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Repayment Mode</dt>
                  <dd className="font-medium">{account.repaymentMode}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Day-Count</dt>
                  <dd className="font-medium">{account.dayCountConvention}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Current Rate</dt>
                  <dd className="font-medium">
                    <PercentageDisplay value={account.currentInterestRate} /> p.a.
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Penal Rate</dt>
                  <dd className="font-medium">
                    <PercentageDisplay value={account.penalInterestRate} /> p.a.
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Base Rate</dt>
                  <dd className="font-medium">
                    {account.currentBaseRate ? (
                      <>
                        <PercentageDisplay value={account.currentBaseRate} /> + {account.spreadBps}{' '}
                        bps
                      </>
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">First Disbursement</dt>
                  <dd className="font-medium">
                    {account.firstDisbursementDate ? (
                      <DateDisplay date={account.firstDisbursementDate} />
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Repayment Start</dt>
                  <dd className="font-medium">
                    {account.repaymentStartDate ? (
                      <DateDisplay date={account.repaymentStartDate} />
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Maturity</dt>
                  <dd className="font-medium">
                    {account.maturityDate ? <DateDisplay date={account.maturityDate} /> : '—'}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">EMI Amount</dt>
                  <dd className="font-medium">
                    {account.currentEmiAmount ? (
                      <AmountDisplay amount={account.currentEmiAmount} />
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Last Rate Reset</dt>
                  <dd className="font-medium">
                    {account.lastRateResetDate ? (
                      <DateDisplay date={account.lastRateResetDate} />
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Next Rate Reset</dt>
                  <dd className="font-medium">
                    {account.nextRateResetDate ? (
                      <DateDisplay date={account.nextRateResetDate} />
                    ) : (
                      '—'
                    )}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Outstanding Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                <div>
                  <dt className="text-muted-foreground">Principal</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={account.principalOutstanding} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Interest</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={account.interestOutstanding} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Penal Interest</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={account.penalInterestOutstanding} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Charges</dt>
                  <dd className="font-medium">
                    <AmountDisplay amount={account.chargesOutstanding} />
                  </dd>
                </div>
              </dl>
              <div className="mt-4 flex items-center justify-between border-t pt-4">
                <span className="text-sm font-medium">Total Outstanding</span>
                <AmountDisplay amount={account.totalOutstanding} className="text-lg font-bold" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Borrower</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                <div>
                  <dt className="text-muted-foreground">Legal Name</dt>
                  <dd className="font-medium">{account.entityLegalName ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Entity Code</dt>
                  <dd className="font-mono text-xs">{account.entityCode ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">PAN</dt>
                  <dd className="font-mono text-xs">{account.entityPan ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Product</dt>
                  <dd className="font-medium">
                    {account.productName ?? '—'}
                    {account.productCode && (
                      <span className="ml-1 text-xs text-muted-foreground">
                        ({account.productCode})
                      </span>
                    )}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="schedule" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Repayment Schedule</CardTitle>
              <CardDescription>Installment-wise principal + interest plan</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Schedule view not embedded yet"
                subtitle="Repayment schedule for this loan lives at /lending/loan-accounts/{id}/schedule. The embedded view will follow."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="disbursements" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Disbursements</CardTitle>
              <CardDescription>Tranches against this loan</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Per-account disbursements coming soon"
                subtitle="Filter the Disbursements list by this loan account for now."
                action={
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/admin/lending/disbursements?loan_account_id=${id}`)}
                  >
                    Open Disbursements
                  </Button>
                }
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="receipts" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Receipts</CardTitle>
              <CardDescription>Payments received against this loan</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Per-account receipts coming soon"
                subtitle="Filter the Receipts list by this loan account for now."
                action={
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/admin/lending/receipts?loan_account_id=${id}`)}
                  >
                    Open Receipts
                  </Button>
                }
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
