/**
 * Credit Bureau Pull Detail View
 * Displays full credit report with score, accounts, enquiries, and analysis
 */

import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Building2,
  CreditCard,
  Calendar,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  AlertCircle,
  FileWarning,
  Wallet,
  Banknote,
  IndianRupee,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';

// Score Band Colors
const scoreBandColors: Record<string, { bg: string; text: string; ring: string }> = {
  EXCELLENT: { bg: 'bg-green-500', text: 'text-green-700', ring: 'ring-green-500' },
  GOOD: { bg: 'bg-emerald-500', text: 'text-emerald-700', ring: 'ring-emerald-500' },
  FAIR: { bg: 'bg-amber-500', text: 'text-amber-700', ring: 'ring-amber-500' },
  POOR: { bg: 'bg-orange-500', text: 'text-orange-700', ring: 'ring-orange-500' },
  VERY_POOR: { bg: 'bg-red-500', text: 'text-red-700', ring: 'ring-red-500' },
};

// Credit Score Gauge Component
const CreditScoreGauge = ({ score, band }: { score: number; band: string }) => {
  const percentage = Math.min(Math.max(((score - 300) / 600) * 100, 0), 100);
  const colors = scoreBandColors[band] || scoreBandColors.FAIR;

  return (
    <div className="flex flex-col items-center">
      {/* Semi-circular gauge */}
      <div className="relative w-48 h-24 overflow-hidden">
        <div className="absolute inset-0 rounded-t-full border-8 border-gray-200" />
        <div
          className={`absolute inset-0 rounded-t-full border-8 ${colors.bg} border-transparent`}
          style={{
            clipPath: `polygon(0 100%, 0 0, ${percentage}% 0, ${percentage}% 100%)`,
            borderColor: 'currentColor',
          }}
        />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
          <div className="text-4xl font-bold">{score}</div>
          <Badge className={`${colors.bg} text-white mt-1`}>{band.replace('_', ' ')}</Badge>
        </div>
      </div>
      {/* Scale markers */}
      <div className="flex justify-between w-48 mt-2 text-xs text-muted-foreground">
        <span>300</span>
        <span>500</span>
        <span>700</span>
        <span>900</span>
      </div>
    </div>
  );
};

// Risk Indicator Component
const RiskIndicator = ({ level, label }: { level: 'low' | 'medium' | 'high' | 'critical'; label: string }) => {
  const colors = {
    low: 'bg-green-100 text-green-700 border-green-300',
    medium: 'bg-amber-100 text-amber-700 border-amber-300',
    high: 'bg-orange-100 text-orange-700 border-orange-300',
    critical: 'bg-red-100 text-red-700 border-red-300',
  };

  const icons = {
    low: <CheckCircle className="h-4 w-4" />,
    medium: <AlertCircle className="h-4 w-4" />,
    high: <AlertTriangle className="h-4 w-4" />,
    critical: <XCircle className="h-4 w-4" />,
  };

  return (
    <Badge variant="outline" className={`${colors[level]} flex items-center gap-1`}>
      {icons[level]}
      {label}
    </Badge>
  );
};

// Mock credit pull data
const mockCreditPull = {
  id: '1',
  bureau: 'CIBIL',
  pullType: 'SOFT',
  status: 'SUCCESS',
  customerName: 'Rahul Sharma',
  panNumber: 'ABCDE1234F',
  dateOfBirth: '1985-03-15',
  mobileNumber: '9876543210',
  entityName: 'ABC Industries Pvt Ltd',
  loanApplicationNumber: 'APP-2025-0001',
  creditScore: 782,
  scoreBand: 'EXCELLENT',
  scoreVersion: 'CIBIL_V2',
  scoreDate: '2025-01-10',

  // Summary
  totalAccounts: 8,
  activeAccounts: 5,
  closedAccounts: 3,
  totalSanctioned: 5000000,
  totalOutstanding: 2500000,
  totalOverdue: 0,
  maxDpdLast12m: 0,
  maxDpdLast24m: 15,
  enquiriesLast30d: 1,
  enquiriesLast12m: 4,

  // References
  requestReference: 'REQ-2025-001',
  bureauReference: 'CIB-RPT-001',
  pulledAt: '2025-01-10T14:30:00',
  expiresAt: '2025-02-10T14:30:00',
  isValid: true,

  // Accounts
  accounts: [
    {
      id: '1',
      accountNumberMasked: 'XXXX1234',
      institutionName: 'HDFC Bank Ltd',
      accountType: 'HOME_LOAN',
      accountStatus: 'ACTIVE',
      ownership: 'INDIVIDUAL',
      sanctionedAmount: 3500000,
      currentBalance: 2100000,
      overdueAmount: 0,
      emiAmount: 32000,
      openedDate: '2020-06-15',
      maxDpd: 0,
      isSecured: true,
      tenureMonths: 180,
      remainingTenure: 126,
    },
    {
      id: '2',
      accountNumberMasked: 'XXXX5678',
      institutionName: 'ICICI Bank Ltd',
      accountType: 'CREDIT_CARD',
      accountStatus: 'ACTIVE',
      ownership: 'INDIVIDUAL',
      creditLimit: 300000,
      currentBalance: 45000,
      overdueAmount: 0,
      openedDate: '2018-03-20',
      maxDpd: 0,
      isSecured: false,
    },
    {
      id: '3',
      accountNumberMasked: 'XXXX9012',
      institutionName: 'Axis Bank Ltd',
      accountType: 'PERSONAL_LOAN',
      accountStatus: 'CLOSED',
      ownership: 'INDIVIDUAL',
      sanctionedAmount: 500000,
      currentBalance: 0,
      overdueAmount: 0,
      openedDate: '2019-01-10',
      closedDate: '2023-01-10',
      maxDpd: 15,
      isSecured: false,
      tenureMonths: 48,
    },
    {
      id: '4',
      accountNumberMasked: 'XXXX3456',
      institutionName: 'SBI Cards',
      accountType: 'CREDIT_CARD',
      accountStatus: 'ACTIVE',
      ownership: 'INDIVIDUAL',
      creditLimit: 200000,
      currentBalance: 35000,
      overdueAmount: 0,
      openedDate: '2019-08-05',
      maxDpd: 0,
      isSecured: false,
    },
    {
      id: '5',
      accountNumberMasked: 'XXXX7890',
      institutionName: 'Bajaj Finance',
      accountType: 'AUTO_LOAN',
      accountStatus: 'ACTIVE',
      ownership: 'INDIVIDUAL',
      sanctionedAmount: 800000,
      currentBalance: 320000,
      overdueAmount: 0,
      emiAmount: 18500,
      openedDate: '2022-04-20',
      maxDpd: 0,
      isSecured: true,
      tenureMonths: 60,
      remainingTenure: 28,
    },
  ],

  // Enquiries
  enquiries: [
    {
      id: '1',
      enquiryDate: '2025-01-05',
      institutionName: 'XYZ Finance Ltd',
      enquiryPurpose: 'PERSONAL_LOAN',
      enquiryAmount: 500000,
    },
    {
      id: '2',
      enquiryDate: '2024-11-15',
      institutionName: 'HDFC Bank Ltd',
      enquiryPurpose: 'CREDIT_CARD',
      enquiryAmount: null,
    },
    {
      id: '3',
      enquiryDate: '2024-09-20',
      institutionName: 'ICICI Bank Ltd',
      enquiryPurpose: 'HOME_LOAN',
      enquiryAmount: 4000000,
    },
    {
      id: '4',
      enquiryDate: '2024-05-10',
      institutionName: 'Axis Bank Ltd',
      enquiryPurpose: 'AUTO_LOAN',
      enquiryAmount: 900000,
    },
  ],

  // Risk factors
  riskFactors: [] as { factor: string; severity: string; description: string }[],
};

// Account type colors
const accountTypeColors: Record<string, string> = {
  HOME_LOAN: 'bg-blue-100 text-blue-700',
  AUTO_LOAN: 'bg-purple-100 text-purple-700',
  PERSONAL_LOAN: 'bg-amber-100 text-amber-700',
  CREDIT_CARD: 'bg-green-100 text-green-700',
  BUSINESS_LOAN: 'bg-orange-100 text-orange-700',
  GOLD_LOAN: 'bg-yellow-100 text-yellow-700',
  EDUCATION_LOAN: 'bg-indigo-100 text-indigo-700',
  OTHER: 'bg-gray-100 text-gray-700',
};

// Account status colors
const accountStatusColors: Record<string, string> = {
  ACTIVE: 'bg-green-100 text-green-700',
  CLOSED: 'bg-gray-100 text-gray-700',
  SETTLED: 'bg-blue-100 text-blue-700',
  WRITTEN_OFF: 'bg-red-100 text-red-700',
  SUIT_FILED: 'bg-red-200 text-red-800',
};

export default function CreditPullView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const pull = mockCreditPull;

  // Calculate utilization
  const creditCardLimit = pull.accounts
    .filter((a) => a.accountType === 'CREDIT_CARD' && a.creditLimit)
    .reduce((sum, a) => sum + (a.creditLimit || 0), 0);
  const creditCardBalance = pull.accounts
    .filter((a) => a.accountType === 'CREDIT_CARD')
    .reduce((sum, a) => sum + (a.currentBalance || 0), 0);
  const utilization = creditCardLimit > 0 ? (creditCardBalance / creditCardLimit) * 100 : 0;

  // Calculate total EMI
  const totalEmi = pull.accounts
    .filter((a) => a.accountStatus === 'ACTIVE' && a.emiAmount)
    .reduce((sum, a) => sum + (a.emiAmount || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/lending/credit')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Credit Report</h1>
            <p className="text-muted-foreground">
              {pull.bureau} Report for {pull.customerName}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
          {!pull.isValid && (
            <Button>
              <RefreshCw className="mr-2 h-4 w-4" />
              Pull New Report
            </Button>
          )}
        </div>
      </div>

      {/* Status Banner */}
      <Card className={pull.isValid ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'}>
        <CardContent className="py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {pull.isValid ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-amber-600" />
              )}
              <div>
                <span className={pull.isValid ? 'text-green-700' : 'text-amber-700'}>
                  {pull.isValid ? 'Valid Report' : 'Report Expired'}
                </span>
                <span className="text-muted-foreground ml-2">
                  Pulled on <DateDisplay date={pull.pulledAt} format="long" />
                </span>
              </div>
            </div>
            <div className="text-sm text-muted-foreground">
              Ref: <span className="font-mono">{pull.requestReference}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Score & Summary */}
        <div className="lg:col-span-1 space-y-6">
          {/* Credit Score Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Credit Score</span>
                <Badge variant="outline">{pull.bureau}</Badge>
              </CardTitle>
              <CardDescription>
                {pull.scoreVersion} as of <DateDisplay date={pull.scoreDate} format="short" />
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center pb-6">
              <CreditScoreGauge score={pull.creditScore} band={pull.scoreBand} />
            </CardContent>
          </Card>

          {/* Customer Info */}
          <Card>
            <CardHeader>
              <CardTitle>Customer Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Name</span>
                <span className="font-medium">{pull.customerName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">PAN</span>
                <span className="font-mono">{pull.panNumber}</span>
              </div>
              {pull.dateOfBirth && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Date of Birth</span>
                  <DateDisplay date={pull.dateOfBirth} format="short" />
                </div>
              )}
              {pull.entityName && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Entity</span>
                  <span>{pull.entityName}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Risk Factors */}
          {pull.riskFactors.length > 0 && (
            <Card className="border-red-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-700">
                  <FileWarning className="h-5 w-5" />
                  Risk Factors
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {pull.riskFactors.map((risk, index) => (
                  <div key={index} className="flex items-start gap-2 text-sm">
                    <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
                    <div>
                      <div className="font-medium">{risk.factor}</div>
                      <div className="text-muted-foreground">{risk.description}</div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {pull.riskFactors.length === 0 && (
            <Card className="border-green-200">
              <CardContent className="py-6 text-center">
                <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <div className="font-medium text-green-700">No Risk Factors</div>
                <div className="text-sm text-muted-foreground">
                  Credit profile looks healthy
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column - Details */}
        <div className="lg:col-span-2">
          <Card>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <CardHeader>
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="accounts">Accounts ({pull.totalAccounts})</TabsTrigger>
                  <TabsTrigger value="enquiries">Enquiries ({pull.enquiries.length})</TabsTrigger>
                </TabsList>
              </CardHeader>
              <CardContent>
                {/* Overview Tab */}
                <TabsContent value="overview" className="mt-0">
                  <div className="grid gap-6 md:grid-cols-2">
                    {/* Account Summary */}
                    <div className="space-y-4">
                      <h3 className="font-semibold flex items-center gap-2">
                        <CreditCard className="h-4 w-4" />
                        Account Summary
                      </h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-3 bg-muted rounded-lg">
                          <div className="text-2xl font-bold">{pull.totalAccounts}</div>
                          <div className="text-xs text-muted-foreground">Total</div>
                        </div>
                        <div className="text-center p-3 bg-green-50 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">{pull.activeAccounts}</div>
                          <div className="text-xs text-muted-foreground">Active</div>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-gray-600">{pull.closedAccounts}</div>
                          <div className="text-xs text-muted-foreground">Closed</div>
                        </div>
                      </div>
                    </div>

                    {/* Financial Summary */}
                    <div className="space-y-4">
                      <h3 className="font-semibold flex items-center gap-2">
                        <IndianRupee className="h-4 w-4" />
                        Financial Summary
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Total Sanctioned</span>
                          <AmountDisplay amount={pull.totalSanctioned} className="font-medium" />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Outstanding</span>
                          <AmountDisplay amount={pull.totalOutstanding} className="font-medium" />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Total EMI</span>
                          <AmountDisplay amount={totalEmi} className="font-medium" />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Overdue</span>
                          <AmountDisplay
                            amount={pull.totalOverdue}
                            className={pull.totalOverdue > 0 ? 'font-medium text-red-600' : 'font-medium text-green-600'}
                          />
                        </div>
                      </div>
                    </div>

                    {/* DPD Summary */}
                    <div className="space-y-4">
                      <h3 className="font-semibold flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        Payment Behavior (DPD)
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Max DPD (12 months)</span>
                          <Badge variant={pull.maxDpdLast12m === 0 ? 'default' : 'destructive'}>
                            {pull.maxDpdLast12m} days
                          </Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Max DPD (24 months)</span>
                          <Badge variant={pull.maxDpdLast24m <= 30 ? 'secondary' : 'destructive'}>
                            {pull.maxDpdLast24m} days
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* Enquiry Summary */}
                    <div className="space-y-4">
                      <h3 className="font-semibold flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Credit Enquiries
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Last 30 days</span>
                          <Badge variant={pull.enquiriesLast30d >= 3 ? 'destructive' : 'secondary'}>
                            {pull.enquiriesLast30d}
                          </Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Last 12 months</span>
                          <Badge variant={pull.enquiriesLast12m >= 6 ? 'destructive' : 'secondary'}>
                            {pull.enquiriesLast12m}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* Credit Card Utilization */}
                    <div className="md:col-span-2 space-y-4">
                      <h3 className="font-semibold flex items-center gap-2">
                        <Wallet className="h-4 w-4" />
                        Credit Card Utilization
                      </h3>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>
                            <AmountDisplay amount={creditCardBalance} /> of{' '}
                            <AmountDisplay amount={creditCardLimit} />
                          </span>
                          <span className={utilization > 70 ? 'text-red-600' : 'text-green-600'}>
                            {utilization.toFixed(1)}%
                          </span>
                        </div>
                        <Progress
                          value={utilization}
                          className={utilization > 70 ? 'bg-red-100' : 'bg-green-100'}
                        />
                        <div className="text-xs text-muted-foreground">
                          {utilization <= 30
                            ? 'Excellent - Low utilization'
                            : utilization <= 50
                            ? 'Good - Moderate utilization'
                            : utilization <= 70
                            ? 'Fair - Consider reducing'
                            : 'High utilization - May affect score'}
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                {/* Accounts Tab */}
                <TabsContent value="accounts" className="mt-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Account</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Limit/Sanctioned</TableHead>
                        <TableHead className="text-right">Outstanding</TableHead>
                        <TableHead>DPD</TableHead>
                        <TableHead>Opened</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pull.accounts.map((account) => (
                        <TableRow key={account.id}>
                          <TableCell>
                            <div className="space-y-1">
                              <div className="font-medium">{account.institutionName}</div>
                              <div className="text-xs text-muted-foreground font-mono">
                                {account.accountNumberMasked}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="secondary"
                              className={accountTypeColors[account.accountType] || 'bg-gray-100'}
                            >
                              {account.accountType.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={accountStatusColors[account.accountStatus]}
                            >
                              {account.accountStatus}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay
                              amount={account.creditLimit || account.sanctionedAmount || 0}
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={account.currentBalance || 0} />
                          </TableCell>
                          <TableCell>
                            {account.maxDpd === 0 ? (
                              <Badge variant="outline" className="bg-green-50 text-green-700">
                                0
                              </Badge>
                            ) : account.maxDpd && account.maxDpd <= 30 ? (
                              <Badge variant="outline" className="bg-amber-50 text-amber-700">
                                {account.maxDpd}
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="bg-red-50 text-red-700">
                                {account.maxDpd}
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <DateDisplay date={account.openedDate} format="short" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>

                {/* Enquiries Tab */}
                <TabsContent value="enquiries" className="mt-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Institution</TableHead>
                        <TableHead>Purpose</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pull.enquiries.map((enquiry) => (
                        <TableRow key={enquiry.id}>
                          <TableCell>
                            <DateDisplay date={enquiry.enquiryDate} format="short" />
                          </TableCell>
                          <TableCell className="font-medium">{enquiry.institutionName}</TableCell>
                          <TableCell>
                            <Badge variant="secondary">
                              {enquiry.enquiryPurpose?.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            {enquiry.enquiryAmount ? (
                              <AmountDisplay amount={enquiry.enquiryAmount} />
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>
              </CardContent>
            </Tabs>
          </Card>
        </div>
      </div>
    </div>
  );
}
