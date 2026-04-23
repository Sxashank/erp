import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit, FileText, Printer, Plus, CheckCircle } from 'lucide-react';
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
import { AuditTimeline } from '@/components/lending/common/AuditTimeline';

// Mock sanction data
const mockSanction = {
  id: '1',
  sanctionNumber: 'SMFC/SAN/2025/00001',
  applicationNumber: 'SMFC/TL/DEL/2025/A00001',
  status: 'ACCEPTED',
  entity: {
    id: '1',
    entityCode: 'ENT/2025/00001',
    legalName: 'ABC Industries Private Limited',
    pan: 'AABCA1234A',
    entityType: 'CORPORATE',
  },
  product: {
    id: '1',
    productCode: 'TL-CORP-001',
    productName: 'Corporate Term Loan',
    category: 'TERM_LOAN',
  },
  sanctionedAmount: 250000000,
  disbursedAmount: 50000000,
  interestType: 'FLOATING',
  baseRate: 'SMFC_BR',
  currentBaseRate: 10.5,
  spreadBps: 200,
  effectiveRate: 12.5,
  tenureMonths: 60,
  moratoriumMonths: 6,
  repaymentFrequency: 'MONTHLY',
  repaymentMode: 'EMI',
  processingFee: 2500000,
  processingFeePaid: true,
  sanctionDate: '2025-01-10',
  validUntil: '2025-04-10',
  acceptedOn: '2025-01-12',
  approvedBy: 'Credit Committee',
  conditions: {
    preDisbursement: [
      { condition: 'Creation of mortgage on primary security', status: 'COMPLETED', completedOn: '2025-01-15' },
      { condition: 'Submission of insurance policy for assets', status: 'COMPLETED', completedOn: '2025-01-16' },
      { condition: 'Equity infusion of 20% before first disbursement', status: 'PENDING', completedOn: null },
      { condition: 'Board resolution for availing the loan', status: 'COMPLETED', completedOn: '2025-01-12' },
    ],
    postDisbursement: [
      { condition: 'Submission of utilization certificate within 30 days', status: 'PENDING', completedOn: null },
      { condition: 'Quarterly progress reports on project', status: 'PENDING', completedOn: null },
      { condition: 'Annual audited financials', status: 'PENDING', completedOn: null },
    ],
  },
  securities: [
    {
      securityType: 'PRIMARY',
      nature: 'PROPERTY',
      description: 'Industrial land and building at Plot 45, Industrial Area, Phase II, Gurgaon',
      value: 400000000,
      margin: 25,
      chargeCreated: true,
      chargeId: 'CHG001234',
    },
    {
      securityType: 'COLLATERAL',
      nature: 'FIXED_DEPOSIT',
      description: 'FD with SBI, Gurgaon branch',
      value: 50000000,
      margin: 10,
      chargeCreated: true,
      chargeId: 'LIEN00567',
    },
  ],
  covenants: [
    {
      covenantType: 'FINANCIAL',
      description: 'Minimum DSCR to be maintained',
      frequency: 'YEARLY',
      threshold: '1.5x',
    },
    {
      covenantType: 'FINANCIAL',
      description: 'Maximum Debt-Equity ratio',
      frequency: 'YEARLY',
      threshold: '2:1',
    },
    {
      covenantType: 'REPORTING',
      description: 'Submission of stock statements',
      frequency: 'MONTHLY',
      threshold: null,
    },
    {
      covenantType: 'NEGATIVE',
      description: 'No dividend distribution without prior approval',
      frequency: 'ONE_TIME',
      threshold: null,
    },
  ],
  disbursements: [
    {
      id: 'D001',
      tranche: 1,
      amount: 50000000,
      date: '2025-01-20',
      status: 'COMPLETED',
      milestone: 'Land acquisition',
    },
  ],
  auditTrail: [
    { id: 's1', action: 'Sanction Created', user_name: 'Sanction Team', timestamp: '2025-01-10T14:30:00', description: 'Sanction created after CC approval' },
    { id: 's2', action: 'Sanction Letter Generated', user_name: 'System', timestamp: '2025-01-10T14:35:00', description: 'Sanction letter generated' },
    { id: 's3', action: 'Sanction Accepted', user_name: 'ABC Industries', timestamp: '2025-01-12T11:00:00', description: 'Borrower accepted sanction terms' },
    { id: 's4', action: 'Processing Fee Received', user_name: 'Operations', timestamp: '2025-01-12T15:30:00', description: 'Processing fee of ₹25L received' },
    { id: 's5', action: 'Security Created', user_name: 'Legal Team', timestamp: '2025-01-15T10:00:00', description: 'Mortgage created on property' },
    { id: 's6', action: 'Disbursement Completed', user_name: 'Treasury', timestamp: '2025-01-20T12:00:00', description: 'First tranche of ₹5 Cr disbursed' },
  ],
};

export default function SanctionView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const sanction = mockSanction;

  const completedPreConditions = sanction.conditions.preDisbursement.filter(
    (c) => c.status === 'COMPLETED'
  ).length;
  const totalPreConditions = sanction.conditions.preDisbursement.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/sanctions')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">Loan Sanction</h1>
            <StatusBadge status={sanction.status} type="sanction" />
          </div>
          <p className="text-muted-foreground font-mono">{sanction.sanctionNumber}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate(`/admin/lending/sanctions/${id}/letter`)}>
            <FileText className="mr-2 h-4 w-4" />
            Sanction Letter
          </Button>
          {sanction.status === 'ACCEPTED' && (
            <Button
              onClick={() => navigate(`/admin/lending/disbursements/new?sanctionId=${id}`)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Disbursement
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={sanction.sanctionedAmount} abbreviated className="text-2xl font-bold" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Disbursed</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={sanction.disbursedAmount} abbreviated className="text-2xl font-bold" />
            <p className="text-xs text-muted-foreground">
              <PercentageDisplay
                value={(sanction.disbursedAmount / sanction.sanctionedAmount) * 100}
              />{' '}
              utilized
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Interest Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <PercentageDisplay value={sanction.effectiveRate} />
            </div>
            <p className="text-xs text-muted-foreground">
              {sanction.baseRate} + {sanction.spreadBps} bps
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tenure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sanction.tenureMonths} Months</div>
            <p className="text-xs text-muted-foreground">
              {sanction.moratoriumMonths} months moratorium
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Conditions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {completedPreConditions}/{totalPreConditions}
            </div>
            <p className="text-xs text-muted-foreground">Pre-disbursement completed</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Sanction Details</TabsTrigger>
          <TabsTrigger value="conditions">Conditions</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="covenants">Covenants</TabsTrigger>
          <TabsTrigger value="disbursements">Disbursements</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-6 mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Entity Information</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Entity Name</dt>
                    <dd className="font-medium">{sanction.entity.legalName}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Entity Code</dt>
                    <dd className="font-mono">{sanction.entity.entityCode}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">PAN</dt>
                    <dd className="font-mono">{sanction.entity.pan}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Entity Type</dt>
                    <dd>{sanction.entity.entityType}</dd>
                  </div>
                </dl>
                <Button
                  variant="link"
                  className="p-0 mt-4"
                  onClick={() => navigate(`/admin/lending/entities/${sanction.entity.id}`)}
                >
                  View Full Profile →
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Sanction Information</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Sanction Number</dt>
                    <dd className="font-mono">{sanction.sanctionNumber}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Application Number</dt>
                    <dd className="font-mono">{sanction.applicationNumber}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Product</dt>
                    <dd>{sanction.product.productName}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Approved By</dt>
                    <dd>{sanction.approvedBy}</dd>
                  </div>
                </dl>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Loan Terms</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-3">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Sanctioned Amount</dt>
                  <dd>
                    <AmountDisplay amount={sanction.sanctionedAmount} showFull />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Interest Type</dt>
                  <dd>
                    <Badge variant="outline">{sanction.interestType}</Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Effective Rate</dt>
                  <dd>
                    <PercentageDisplay value={sanction.effectiveRate} /> p.a.
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Tenure</dt>
                  <dd>{sanction.tenureMonths} Months</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Moratorium</dt>
                  <dd>{sanction.moratoriumMonths} Months</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Repayment Mode</dt>
                  <dd>{sanction.repaymentMode}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Repayment Frequency</dt>
                  <dd>{sanction.repaymentFrequency}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Processing Fee</dt>
                  <dd>
                    <AmountDisplay amount={sanction.processingFee} />
                    {sanction.processingFeePaid && (
                      <Badge variant="default" className="ml-2 bg-green-100 text-green-700">
                        Paid
                      </Badge>
                    )}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Important Dates</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-4">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Sanction Date</dt>
                  <dd>
                    <DateDisplay date={sanction.sanctionDate} />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Valid Until</dt>
                  <dd>
                    <DateDisplay date={sanction.validUntil} />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Accepted On</dt>
                  <dd>
                    <DateDisplay date={sanction.acceptedOn} />
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Conditions Tab */}
        <TabsContent value="conditions" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Pre-Disbursement Conditions</CardTitle>
              <CardDescription>
                {completedPreConditions} of {totalPreConditions} conditions completed
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">#</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Completed On</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sanction.conditions.preDisbursement.map((cond, index) => (
                    <TableRow key={index}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>{cond.condition}</TableCell>
                      <TableCell>
                        <Badge
                          variant={cond.status === 'COMPLETED' ? 'default' : 'secondary'}
                          className={
                            cond.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
                          {cond.status === 'COMPLETED' && <CheckCircle className="h-3 w-3 mr-1" />}
                          {cond.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {cond.completedOn ? <DateDisplay date={cond.completedOn} /> : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Post-Disbursement Conditions</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">#</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Completed On</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sanction.conditions.postDisbursement.map((cond, index) => (
                    <TableRow key={index}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>{cond.condition}</TableCell>
                      <TableCell>
                        <Badge
                          variant={cond.status === 'COMPLETED' ? 'default' : 'secondary'}
                          className={
                            cond.status === 'COMPLETED' ? 'bg-green-100 text-green-700' : ''
                          }
                        >
                          {cond.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {cond.completedOn ? <DateDisplay date={cond.completedOn} /> : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Security/Collateral Details</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Nature</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                    <TableHead className="text-right">Margin</TableHead>
                    <TableHead className="text-right">Net Value</TableHead>
                    <TableHead>Charge Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sanction.securities.map((security, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Badge
                          variant={security.securityType === 'PRIMARY' ? 'default' : 'secondary'}
                        >
                          {security.securityType}
                        </Badge>
                      </TableCell>
                      <TableCell>{security.nature}</TableCell>
                      <TableCell className="max-w-[300px]">{security.description}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={security.value} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <PercentageDisplay value={security.margin} />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay
                          amount={security.value * (1 - security.margin / 100)}
                          abbreviated
                        />
                      </TableCell>
                      <TableCell>
                        {security.chargeCreated ? (
                          <Badge variant="default" className="bg-green-100 text-green-700">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Created
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Pending</Badge>
                        )}
                        {security.chargeId && (
                          <div className="text-xs text-muted-foreground mt-1">
                            {security.chargeId}
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="font-medium bg-muted/50">
                    <TableCell colSpan={3}>Total Security Coverage</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay
                        amount={sanction.securities.reduce((sum, s) => sum + s.value, 0)}
                        abbreviated
                      />
                    </TableCell>
                    <TableCell></TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay
                        amount={sanction.securities.reduce(
                          (sum, s) => sum + s.value * (1 - s.margin / 100),
                          0
                        )}
                        abbreviated
                      />
                    </TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Covenants Tab */}
        <TabsContent value="covenants" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Financial & Other Covenants</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Monitoring Frequency</TableHead>
                    <TableHead>Threshold</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sanction.covenants.map((covenant, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Badge variant="outline">{covenant.covenantType}</Badge>
                      </TableCell>
                      <TableCell>{covenant.description}</TableCell>
                      <TableCell>{covenant.frequency}</TableCell>
                      <TableCell>{covenant.threshold || '-'}</TableCell>
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
                <AmountDisplay amount={sanction.disbursedAmount} abbreviated /> of{' '}
                <AmountDisplay amount={sanction.sanctionedAmount} abbreviated /> disbursed (
                <PercentageDisplay
                  value={(sanction.disbursedAmount / sanction.sanctionedAmount) * 100}
                />
                )
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sanction.disbursements.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No disbursements yet
                </div>
              ) : (
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
                    {sanction.disbursements.map((disb, index) => (
                      <TableRow key={index}>
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
                          <Badge
                            variant="default"
                            className="bg-green-100 text-green-700"
                          >
                            {disb.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="font-medium bg-muted/50">
                      <TableCell colSpan={2}>Remaining to Disburse</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay
                          amount={sanction.sanctionedAmount - sanction.disbursedAmount}
                          abbreviated
                        />
                      </TableCell>
                      <TableCell colSpan={3}></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              )}

              {sanction.status === 'ACCEPTED' &&
                sanction.disbursedAmount < sanction.sanctionedAmount && (
                  <Button
                    className="mt-4"
                    onClick={() =>
                      navigate(`/admin/lending/disbursements/new?sanctionId=${sanction.id}`)
                    }
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Request Disbursement
                  </Button>
                )}
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
              <AuditTimeline entries={sanction.auditTrail} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
