import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, FileText, Receipt, RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { DPDBadge } from '@/components/lending/common/DPDBadge';
import { AuditTimeline } from '@/components/lending/common/AuditTimeline';

// Mock data
const mockLoanAccount = {
  id: '1',
  loanAccountNumber: 'SMFC/TL/DEL/2025/L00001',
  sanctionNumber: 'SMFC/SAN/2025/00001',
  status: 'ACTIVE',
  entity: {
    id: '1',
    entityCode: 'ENT/2025/00001',
    legalName: 'ABC Industries Private Limited',
    pan: 'AABCA1234A',
  },
  product: {
    id: '1',
    productCode: 'TL-CORP-001',
    productName: 'Corporate Term Loan',
    category: 'TERM_LOAN',
  },
  sanctionedAmount: 250000000,
  disbursedAmount: 50000000,
  principalOutstanding: 48500000,
  interestOutstanding: 520000,
  penalOutstanding: 0,
  otherCharges: 0,
  totalOutstanding: 49020000,
  interestType: 'FLOATING',
  baseRate: 'SMFC_BR',
  currentBaseRate: 10.5,
  spreadBps: 200,
  effectiveRate: 12.5,
  dayCountConvention: 'ACT_365',
  tenureMonths: 60,
  moratoriumMonths: 6,
  repaymentFrequency: 'MONTHLY',
  repaymentMode: 'EMI',
  disbursementDate: '2025-01-20',
  repaymentStartDate: '2025-08-15',
  maturityDate: '2030-01-20',
  dpd: 0,
  assetClassification: 'STANDARD',
  provisionRate: 0.4,
  provisionAmount: 196080,
  lastRateResetDate: '2025-01-20',
  nextRateResetDate: '2025-04-20',
  schedule: [
    { installment: 1, dueDate: '2025-08-15', principal: 645000, interest: 510417, total: 1155417, status: 'UPCOMING' },
    { installment: 2, dueDate: '2025-09-15', principal: 651708, interest: 503709, total: 1155417, status: 'UPCOMING' },
    { installment: 3, dueDate: '2025-10-15', principal: 658486, interest: 496931, total: 1155417, status: 'UPCOMING' },
    { installment: 4, dueDate: '2025-11-15', principal: 665335, interest: 490082, total: 1155417, status: 'UPCOMING' },
    { installment: 5, dueDate: '2025-12-15', principal: 672255, interest: 483162, total: 1155417, status: 'UPCOMING' },
  ],
  disbursements: [
    { id: 'D001', tranche: 1, amount: 50000000, date: '2025-01-20', milestone: 'Land acquisition', status: 'COMPLETED' },
  ],
  receipts: [
    { id: 'R001', receiptNumber: 'RCP/2025/00001', amount: 2500000, date: '2025-01-12', mode: 'NEFT', type: 'PROCESSING_FEE' },
  ],
  rateResets: [
    { effectiveDate: '2025-01-20', baseRate: 10.5, spread: 200, effectiveRate: 12.5, reason: 'Initial Rate' },
  ],
  auditTrail: [
    { id: 'l1', action: 'Loan Account Created', user_name: 'System', timestamp: '2025-01-20T10:00:00', description: 'Account created from sanction' },
    { id: 'l2', action: 'Disbursement - Tranche 1', user_name: 'Treasury', timestamp: '2025-01-20T12:00:00', description: '₹5 Cr disbursed' },
    { id: 'l3', action: 'Processing Fee Received', user_name: 'Operations', timestamp: '2025-01-12T15:30:00', description: '₹25L received' },
  ],
};

export default function LoanAccountView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const account = mockLoanAccount;

  const utilizationPercent = (account.disbursedAmount / account.sanctionedAmount) * 100;
  const remainingToDisburse = account.sanctionedAmount - account.disbursedAmount;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/accounts')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">Loan Account</h1>
            <StatusBadge status={account.status} type="loanAccount" />
            <StatusBadge status={account.assetClassification} type="classification" />
          </div>
          <p className="text-muted-foreground font-mono">{account.loanAccountNumber}</p>
        </div>
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
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Outstanding
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={account.totalOutstanding} abbreviated className="text-2xl font-bold" />
            <div className="text-xs text-muted-foreground mt-1">
              Principal: <AmountDisplay amount={account.principalOutstanding} abbreviated />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Disbursed / Sanctioned
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <AmountDisplay amount={account.disbursedAmount} abbreviated />
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              of <AmountDisplay amount={account.sanctionedAmount} abbreviated /> (
              <PercentageDisplay value={utilizationPercent} />)
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
            <div className="text-2xl font-bold">
              <PercentageDisplay value={account.effectiveRate} /> p.a.
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {account.baseRate} + {account.spreadBps} bps
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">DPD</CardTitle>
          </CardHeader>
          <CardContent>
            <DPDBadge dpd={account.dpd} size="lg" />
            <div className="text-xs text-muted-foreground mt-1">Days Past Due</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Maturity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold">
              <DateDisplay date={account.maturityDate} />
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {account.tenureMonths} months tenure
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="summary">
        <TabsList>
          <TabsTrigger value="summary">Account Summary</TabsTrigger>
          <TabsTrigger value="schedule">Repayment Schedule</TabsTrigger>
          <TabsTrigger value="disbursements">Disbursements</TabsTrigger>
          <TabsTrigger value="receipts">Receipts</TabsTrigger>
          <TabsTrigger value="rateHistory">Rate History</TabsTrigger>
          <TabsTrigger value="history">Activity</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-6 mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Entity Information</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Entity Name</dt>
                    <dd className="font-medium">{account.entity.legalName}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Entity Code</dt>
                    <dd className="font-mono">{account.entity.entityCode}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">PAN</dt>
                    <dd className="font-mono">{account.entity.pan}</dd>
                  </div>
                </dl>
                <Button
                  variant="link"
                  className="p-0 mt-4"
                  onClick={() => navigate(`/admin/lending/entities/${account.entity.id}`)}
                >
                  View Entity Profile →
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Account Information</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Account Number</dt>
                    <dd className="font-mono">{account.loanAccountNumber}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Sanction Reference</dt>
                    <dd className="font-mono">{account.sanctionNumber}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Product</dt>
                    <dd>{account.product.productName}</dd>
                  </div>
                </dl>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Outstanding Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Principal Outstanding</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.principalOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Interest Outstanding</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.interestOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Penal Interest</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.penalOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Other Charges</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.otherCharges} showFull />
                    </TableCell>
                  </TableRow>
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell>Total Outstanding</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={account.totalOutstanding} showFull />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Loan Terms</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-4">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Interest Type</dt>
                  <dd>
                    <Badge variant="outline">{account.interestType}</Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Base Rate</dt>
                  <dd>
                    {account.baseRate} @ <PercentageDisplay value={account.currentBaseRate} />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Spread</dt>
                  <dd>{account.spreadBps} bps</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Day Count</dt>
                  <dd>{account.dayCountConvention}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Repayment Mode</dt>
                  <dd>{account.repaymentMode}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Repayment Frequency</dt>
                  <dd>{account.repaymentFrequency}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Next Rate Reset</dt>
                  <dd>
                    <DateDisplay date={account.nextRateResetDate} />
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Classification & Provisioning</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-4">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">DPD</dt>
                  <dd>
                    <DPDBadge dpd={account.dpd} />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Classification</dt>
                  <dd>
                    <StatusBadge status={account.assetClassification} type="classification" />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Provision Rate</dt>
                  <dd>
                    <PercentageDisplay value={account.provisionRate} />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Provision Amount</dt>
                  <dd>
                    <AmountDisplay amount={account.provisionAmount} />
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schedule Tab */}
        <TabsContent value="schedule" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Repayment Schedule</CardTitle>
              <CardDescription>
                {account.repaymentMode} repayment @ {account.repaymentFrequency.toLowerCase()}{' '}
                frequency
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">#</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead className="text-right">Principal</TableHead>
                    <TableHead className="text-right">Interest</TableHead>
                    <TableHead className="text-right">Total EMI</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {account.schedule.map((row) => (
                    <TableRow key={row.installment}>
                      <TableCell>{row.installment}</TableCell>
                      <TableCell>
                        <DateDisplay date={row.dueDate} />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={row.principal} />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={row.interest} />
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        <AmountDisplay amount={row.total} />
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={row.status === 'PAID' ? 'default' : 'secondary'}
                          className={row.status === 'PAID' ? 'bg-green-100 text-green-700' : ''}
                        >
                          {row.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Disbursements Tab */}
        <TabsContent value="disbursements" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Disbursement History</CardTitle>
              <CardDescription>
                <AmountDisplay amount={account.disbursedAmount} abbreviated /> of{' '}
                <AmountDisplay amount={account.sanctionedAmount} abbreviated /> disbursed
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tranche</TableHead>
                    <TableHead>Disbursement ID</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Milestone</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {account.disbursements.map((disb) => (
                    <TableRow key={disb.id}>
                      <TableCell>{disb.tranche}</TableCell>
                      <TableCell className="font-mono">{disb.id}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={disb.amount} abbreviated />
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={disb.date} />
                      </TableCell>
                      <TableCell>{disb.milestone}</TableCell>
                      <TableCell>
                        <Badge variant="default" className="bg-green-100 text-green-700">
                          {disb.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                  {remainingToDisburse > 0 && (
                    <TableRow className="bg-muted/50">
                      <TableCell colSpan={2} className="font-medium">
                        Remaining to Disburse
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        <AmountDisplay amount={remainingToDisburse} abbreviated />
                      </TableCell>
                      <TableCell colSpan={3}></TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Receipts Tab */}
        <TabsContent value="receipts" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Receipt History</CardTitle>
                  <CardDescription>All payments received against this account</CardDescription>
                </div>
                <Button onClick={() => navigate(`/admin/lending/receipts/new?accountId=${id}`)}>
                  <Receipt className="mr-2 h-4 w-4" />
                  Record Receipt
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Receipt Number</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Mode</TableHead>
                    <TableHead>Type</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {account.receipts.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                        No receipts recorded yet
                      </TableCell>
                    </TableRow>
                  ) : (
                    account.receipts.map((receipt) => (
                      <TableRow key={receipt.id}>
                        <TableCell className="font-mono">{receipt.receiptNumber}</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={receipt.amount} />
                        </TableCell>
                        <TableCell>
                          <DateDisplay date={receipt.date} />
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{receipt.mode}</Badge>
                        </TableCell>
                        <TableCell>{receipt.type.replace('_', ' ')}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rate History Tab */}
        <TabsContent value="rateHistory" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Interest Rate History</CardTitle>
              <CardDescription>Rate resets and changes over time</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Effective Date</TableHead>
                    <TableHead className="text-right">Base Rate</TableHead>
                    <TableHead className="text-right">Spread (bps)</TableHead>
                    <TableHead className="text-right">Effective Rate</TableHead>
                    <TableHead>Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {account.rateResets.map((reset, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <DateDisplay date={reset.effectiveDate} />
                      </TableCell>
                      <TableCell className="text-right">
                        <PercentageDisplay value={reset.baseRate} />
                      </TableCell>
                      <TableCell className="text-right">{reset.spread}</TableCell>
                      <TableCell className="text-right font-medium">
                        <PercentageDisplay value={reset.effectiveRate} />
                      </TableCell>
                      <TableCell>{reset.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Activity Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <AuditTimeline entries={account.auditTrail} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
