/**
 * Fixed Deposit View Page
 */

import {
  CheckCircle,
  XCircle,
  RefreshCw,
  FileText,
  Calendar,
  User,
  CreditCard,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/hooks/useAuth';
import type {
  FixedDeposit,
  FDTransaction,
  FDInterestAccrual,
  FDMaturityProjection,
} from '@/services/fixedDepositService';
import fixedDepositService from '@/services/fixedDepositService';

import { logger } from '@/lib/logger';
import { getErrorMessage } from '@/lib/errorMessage';
const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  DRAFT: 'outline',
  PENDING_APPROVAL: 'secondary',
  ACTIVE: 'default',
  MATURED: 'default',
  PREMATURE_CLOSED: 'secondary',
  RENEWED: 'default',
  CANCELLED: 'destructive',
};

export default function FDView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();

  const [fd, setFD] = useState<FixedDeposit | null>(null);
  const [transactions, setTransactions] = useState<FDTransaction[]>([]);
  const [accruals, setAccruals] = useState<FDInterestAccrual[]>([]);
  const [projection, setProjection] = useState<FDMaturityProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const { user } = useAuth();
  const userId = user?.id ?? '';

  useEffect(() => {
    if (id) {
      loadFD(id);
    }
  }, [id]);

  const loadFD = async (fdId: string) => {
    try {
      setLoading(true);
      const [fdData, txnData, accrualData] = await Promise.all([
        fixedDepositService.getDeposit(fdId),
        fixedDepositService.getTransactions(fdId),
        fixedDepositService.getAccruals(fdId),
      ]);
      setFD(fdData);
      setTransactions(txnData);
      setAccruals(accrualData);

      // Load projection for active FDs
      if (fdData.status === 'ACTIVE') {
        try {
          const proj = await fixedDepositService.getProjection(fdId);
          setProjection(proj);
        } catch (e) {
          logger.error('Failed to load projection', e);
        }
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load fixed deposit',
        variant: 'destructive',
      });
      navigate('/admin/fixed-deposits');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!id) return;
    try {
      setActionLoading(true);
      await fixedDepositService.approveDeposit(id, userId);
      toast({
        title: 'Success',
        description: 'Fixed deposit approved successfully',
      });
      loadFD(id);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to approve FD'),
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async () => {
    if (!id || !fd) return;

    const isMaturity = new Date(fd.maturity_date) <= new Date();
    const closureReason = isMaturity ? 'MATURITY' : 'PREMATURE';

    if (
      !confirm(`Are you sure you want to ${isMaturity ? 'mature' : 'prematurely close'} this FD?`)
    ) {
      return;
    }

    try {
      setActionLoading(true);
      await fixedDepositService.closeDeposit(id, {
        closure_date: new Date().toISOString().split('T')[0],
        closure_reason: closureReason,
        payout_mode: 'BANK_TRANSFER',
      });
      toast({
        title: 'Success',
        description: 'Fixed deposit closed successfully',
      });
      loadFD(id);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to close FD'),
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRenew = async () => {
    if (!id) return;

    if (!confirm('Are you sure you want to renew this FD?')) return;

    try {
      setActionLoading(true);
      const newFD = await fixedDepositService.renewDeposit(id, {
        include_interest: true,
      });
      toast({
        title: 'Success',
        description: `Fixed deposit renewed. New FD: ${newFD.fd_number}`,
      });
      navigate(`/admin/fixed-deposits/${newFD.id}`);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to renew FD'),
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
    }
  };
  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="py-8 text-center">Loading...</div>
      </div>
    );
  }

  if (!fd) {
    return (
      <div className="container mx-auto py-6">
        <div className="py-8 text-center">Fixed deposit not found</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title={fd.fd_number}
        subtitle={fd.product_name || fd.product_code}
        breadcrumbs={[
          { label: 'Fixed Deposits', to: '/admin/fixed-deposits' },
          { label: fd.fd_number },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_COLORS[fd.status]}>{fd.status.replace('_', ' ')}</Badge>
            {fd.status === 'DRAFT' && (
              <Button onClick={handleApprove} disabled={actionLoading}>
                <CheckCircle className="mr-2 h-4 w-4" />
                Approve
              </Button>
            )}
            {fd.status === 'ACTIVE' && (
              <>
                <Button variant="outline" onClick={handleRenew} disabled={actionLoading}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Renew
                </Button>
                <Button variant="destructive" onClick={handleClose} disabled={actionLoading}>
                  <XCircle className="mr-2 h-4 w-4" />
                  Close
                </Button>
              </>
            )}
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Deposit Amount
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatIndianCompactCurrency(fd.deposit_amount)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Interest Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{fd.interest_rate.toFixed(2)}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Maturity Amount
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatIndianCompactCurrency(fd.maturity_amount)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Accrued Interest
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatIndianCompactCurrency(fd.accrued_interest)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="accruals">Interest Accruals</TabsTrigger>
          <TabsTrigger value="projection">Projection</TabsTrigger>
          <TabsTrigger value="nominees">Nominees</TabsTrigger>
        </TabsList>

        <TabsContent value="details" className="space-y-4">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* FD Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  FD Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">FD Number</span>
                  <span className="font-medium">{fd.fd_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Certificate Number</span>
                  <span className="font-medium">{fd.certificate_number || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Product</span>
                  <span className="font-medium">{fd.product_name || fd.product_code}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Customer Category</span>
                  <span className="font-medium">{fd.customer_category}</span>
                </div>
              </CardContent>
            </Card>

            {/* Dates */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Dates
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Deposit Date</span>
                  <span className="font-medium">
                    <DateDisplay date={fd.deposit_date} />
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Value Date</span>
                  <span className="font-medium">
                    <DateDisplay date={fd.value_date} />
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tenure</span>
                  <span className="font-medium">{fd.tenure_days} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Maturity Date</span>
                  <span className="font-medium">
                    <DateDisplay date={fd.maturity_date} />
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Interest Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5" />
                  Interest Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Interest Rate</span>
                  <span className="font-medium">{fd.interest_rate.toFixed(2)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Payout Frequency</span>
                  <span className="font-medium">
                    {fd.interest_payout_frequency.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Compounding</span>
                  <span className="font-medium">{fd.compounding_frequency.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Payout Mode</span>
                  <span className="font-medium">{fd.interest_payout_mode.replace('_', ' ')}</span>
                </div>
              </CardContent>
            </Card>

            {/* Settings */}
            <Card>
              <CardHeader>
                <CardTitle>Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Auto Renew</span>
                  <Badge variant={fd.auto_renew ? 'default' : 'outline'}>
                    {fd.auto_renew ? 'Yes' : 'No'}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Renewal Count</span>
                  <span className="font-medium">{fd.renewal_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Has Loan</span>
                  <Badge variant={fd.has_loan ? 'destructive' : 'outline'}>
                    {fd.has_loan ? 'Yes' : 'No'}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">TDS Deducted</span>
                  <span className="font-medium">
                    {formatIndianCompactCurrency(fd.tds_deducted)}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="transactions">
          <Card>
            <CardHeader>
              <CardTitle>Transaction History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                    <TableHead className="text-right">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="py-8 text-center">
                        No transactions
                      </TableCell>
                    </TableRow>
                  ) : (
                    transactions.map((txn) => (
                      <TableRow key={txn.id}>
                        <TableCell>
                          <DateDisplay date={txn.transaction_date} />
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{txn.transaction_type}</Badge>
                        </TableCell>
                        <TableCell>{txn.description}</TableCell>
                        <TableCell className="text-right text-red-600">
                          {txn.debit_amount > 0
                            ? formatIndianCompactCurrency(txn.debit_amount)
                            : '-'}
                        </TableCell>
                        <TableCell className="text-right text-green-600">
                          {txn.credit_amount > 0
                            ? formatIndianCompactCurrency(txn.credit_amount)
                            : '-'}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatIndianCompactCurrency(txn.balance)}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="accruals">
          <Card>
            <CardHeader>
              <CardTitle>Interest Accruals</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Accrual Date</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead>Days</TableHead>
                    <TableHead className="text-right">Principal</TableHead>
                    <TableHead>Rate</TableHead>
                    <TableHead className="text-right">Interest</TableHead>
                    <TableHead className="text-right">Cumulative</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {accruals.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="py-8 text-center">
                        No accruals recorded
                      </TableCell>
                    </TableRow>
                  ) : (
                    accruals.map((acc) => (
                      <TableRow key={acc.id}>
                        <TableCell>
                          <DateDisplay date={acc.accrual_date} />
                        </TableCell>
                        <TableCell>
                          <DateDisplay date={acc.period_from} /> -{' '}
                          <DateDisplay date={acc.period_to} />
                        </TableCell>
                        <TableCell>{acc.days}</TableCell>
                        <TableCell className="text-right">
                          {formatIndianCompactCurrency(acc.principal_amount)}
                        </TableCell>
                        <TableCell>{acc.interest_rate.toFixed(2)}%</TableCell>
                        <TableCell className="text-right">
                          {formatIndianCompactCurrency(acc.interest_amount)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatIndianCompactCurrency(acc.cumulative_interest)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={acc.is_paid ? 'default' : 'outline'}>
                            {acc.is_paid ? 'Paid' : 'Pending'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="projection">
          {projection ? (
            <Card>
              <CardHeader>
                <CardTitle>Maturity Projection</CardTitle>
                <CardDescription>Estimated values based on current interest rate</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <div className="rounded-lg bg-muted p-4">
                    <p className="text-sm text-muted-foreground">Projected Interest</p>
                    <p className="text-xl font-bold">
                      {formatIndianCompactCurrency(projection.projected_interest)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-muted p-4">
                    <p className="text-sm text-muted-foreground">Maturity Amount</p>
                    <p className="text-xl font-bold text-blue-600">
                      {formatIndianCompactCurrency(projection.projected_maturity_amount)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-muted p-4">
                    <p className="text-sm text-muted-foreground">TDS Estimate</p>
                    <p className="text-xl font-bold text-red-600">
                      {formatIndianCompactCurrency(projection.tds_estimate)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-muted p-4">
                    <p className="text-sm text-muted-foreground">Net Maturity</p>
                    <p className="text-xl font-bold text-green-600">
                      {formatIndianCompactCurrency(projection.net_maturity_amount)}
                    </p>
                  </div>
                </div>

                {projection.schedule.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Period</TableHead>
                        <TableHead>Days</TableHead>
                        <TableHead className="text-right">Principal</TableHead>
                        <TableHead className="text-right">Interest</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {projection.schedule.map((item, idx) => (
                        <TableRow key={idx}>
                          <TableCell>
                            <DateDisplay date={item.period_from} /> -{' '}
                            <DateDisplay date={item.period_to} />
                          </TableCell>
                          <TableCell>{item.days}</TableCell>
                          <TableCell className="text-right">
                            {formatIndianCompactCurrency(item.principal)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatIndianCompactCurrency(item.interest)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Projection available only for active FDs
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="nominees">
          <Card>
            <CardHeader>
              <CardTitle>Nominees</CardTitle>
            </CardHeader>
            <CardContent>
              {fd.nominees.length === 0 ? (
                <p className="py-8 text-center text-muted-foreground">No nominees registered</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Relationship</TableHead>
                      <TableHead>Date of Birth</TableHead>
                      <TableHead className="text-right">Share %</TableHead>
                      <TableHead>Minor</TableHead>
                      <TableHead>Guardian</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fd.nominees.map((nominee) => (
                      <TableRow key={nominee.id}>
                        <TableCell className="font-medium">{nominee.nominee_name}</TableCell>
                        <TableCell>{nominee.relationship}</TableCell>
                        <TableCell>
                          <DateDisplay date={nominee.date_of_birth} />
                        </TableCell>
                        <TableCell className="text-right">{nominee.share_percentage}%</TableCell>
                        <TableCell>
                          <Badge variant={nominee.is_minor ? 'secondary' : 'outline'}>
                            {nominee.is_minor ? 'Yes' : 'No'}
                          </Badge>
                        </TableCell>
                        <TableCell>{nominee.guardian_name || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
