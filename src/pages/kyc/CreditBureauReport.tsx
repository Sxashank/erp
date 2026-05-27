import {
  Download,
  Printer,
  CreditCard,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Building,
  User,
  FileText,
  Search,
} from 'lucide-react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';

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

// Mock credit report data
const reportData = {
  reportId: 'RPT2025011500001',
  bureau: 'CIBIL',
  pullDate: '2025-01-15 14:30:00',
  validUntil: '2025-02-14',

  customer: {
    name: 'Rajesh Kumar',
    customerId: 'CUST001',
    pan: 'ABCDE1234F',
    dob: '1985-03-15',
    gender: 'Male',
    mobile: '9876543210',
    email: 'rajesh.kumar@email.com',
    address: '123, MG Road, Bangalore - 560001',
  },

  score: {
    value: 782,
    range: { min: 300, max: 900 },
    rating: 'GOOD',
    factors: [
      { factor: 'Payment History', impact: 'POSITIVE', description: 'Consistent on-time payments' },
      {
        factor: 'Credit Utilization',
        impact: 'POSITIVE',
        description: 'Low utilization ratio (28%)',
      },
      {
        factor: 'Credit Age',
        impact: 'NEUTRAL',
        description: 'Average age of accounts: 4.2 years',
      },
      { factor: 'Credit Mix', impact: 'POSITIVE', description: 'Good mix of credit types' },
      {
        factor: 'Recent Enquiries',
        impact: 'NEGATIVE',
        description: '3 enquiries in last 6 months',
      },
    ],
  },

  summary: {
    totalAccounts: 5,
    activeAccounts: 3,
    closedAccounts: 2,
    overdueAccounts: 0,
    totalCreditLimit: 850000,
    totalOutstanding: 238000,
    utilizationPercent: 28,
    oldestAccount: '2018-05-20',
    newestAccount: '2024-08-15',
  },

  accounts: [
    {
      id: '1',
      lender: 'HDFC Bank',
      accountType: 'Credit Card',
      accountNumber: '****4521',
      sanctionedAmount: 200000,
      currentBalance: 45000,
      status: 'ACTIVE',
      openDate: '2020-03-15',
      closeDate: null,
      lastPaymentDate: '2025-01-10',
      dpd: 0,
      paymentHistory: 'XXXXXXXXX000',
    },
    {
      id: '2',
      lender: 'SBI',
      accountType: 'Personal Loan',
      accountNumber: '****7892',
      sanctionedAmount: 300000,
      currentBalance: 125000,
      status: 'ACTIVE',
      openDate: '2023-06-20',
      closeDate: null,
      lastPaymentDate: '2025-01-05',
      dpd: 0,
      paymentHistory: 'XXXXXX000000',
    },
    {
      id: '3',
      lender: 'ICICI Bank',
      accountType: 'Credit Card',
      accountNumber: '****3456',
      sanctionedAmount: 350000,
      currentBalance: 68000,
      status: 'ACTIVE',
      openDate: '2018-05-20',
      closeDate: null,
      lastPaymentDate: '2025-01-08',
      dpd: 0,
      paymentHistory: 'XXXXXXXXXXXX',
    },
    {
      id: '4',
      lender: 'Axis Bank',
      accountType: 'Auto Loan',
      accountNumber: '****9012',
      sanctionedAmount: 500000,
      currentBalance: 0,
      status: 'CLOSED',
      openDate: '2019-08-10',
      closeDate: '2024-02-10',
      lastPaymentDate: '2024-02-10',
      dpd: 0,
      paymentHistory: 'XXXXXXXXXXXX',
    },
    {
      id: '5',
      lender: 'Bajaj Finance',
      accountType: 'Consumer Durable',
      accountNumber: '****5678',
      sanctionedAmount: 50000,
      currentBalance: 0,
      status: 'CLOSED',
      openDate: '2022-11-05',
      closeDate: '2023-11-05',
      lastPaymentDate: '2023-11-05',
      dpd: 0,
      paymentHistory: 'XXXXXXXX0000',
    },
  ],

  enquiries: [
    { date: '2025-01-15', lender: 'XYZ Finance', type: 'Personal Loan', amount: 500000 },
    { date: '2024-12-20', lender: 'ABC Bank', type: 'Credit Card', amount: 200000 },
    { date: '2024-10-15', lender: 'PQR NBFC', type: 'Business Loan', amount: 1000000 },
  ],

  addresses: [
    {
      type: 'Current',
      address: '123, MG Road, Bangalore - 560001',
      reportedBy: 'HDFC Bank',
      reportedOn: '2024-06-15',
    },
    {
      type: 'Previous',
      address: '456, JP Nagar, Bangalore - 560078',
      reportedBy: 'SBI',
      reportedOn: '2023-06-20',
    },
  ],

  employments: [
    {
      employer: 'Tech Solutions Pvt Ltd',
      designation: 'Senior Engineer',
      income: 150000,
      reportedBy: 'HDFC Bank',
      reportedOn: '2024-03-15',
    },
  ],
};
export default function CreditBureauReport() {
  const { reportId } = useParams();
  const [activeTab, setActiveTab] = useState('summary');

  const getScoreColor = (score: number) => {
    if (score >= 750) return 'text-green-600';
    if (score >= 650) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 750) return 'bg-green-100';
    if (score >= 650) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getRatingBadge = (rating: string) => {
    switch (rating) {
      case 'EXCELLENT':
        return <Badge className="bg-green-100 text-green-800">Excellent</Badge>;
      case 'GOOD':
        return <Badge className="bg-blue-100 text-blue-800">Good</Badge>;
      case 'FAIR':
        return <Badge className="bg-yellow-100 text-yellow-800">Fair</Badge>;
      case 'POOR':
        return <Badge className="bg-red-100 text-red-800">Poor</Badge>;
      default:
        return <Badge variant="outline">{rating}</Badge>;
    }
  };

  const getAccountStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Active
          </Badge>
        );
      case 'CLOSED':
        return <Badge variant="secondary">Closed</Badge>;
      case 'WRITTEN_OFF':
        return <Badge variant="destructive">Written Off</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'POSITIVE':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'NEGATIVE':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Credit Report"
        subtitle={`Report ID: ${reportData.reportId} | ${reportData.bureau} | Generated: ${reportData.pullDate}`}
        breadcrumbs={[
          { label: 'Credit Bureau', to: '/admin/kyc/credit-bureau' },
          { label: reportData.reportId },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
          </div>
        }
      />

      {/* Score Header */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <Card className={`lg:col-span-1 ${getScoreBg(reportData.score.value)}`}>
          <CardContent className="pt-6 text-center">
            <div className={`text-6xl font-bold ${getScoreColor(reportData.score.value)}`}>
              {reportData.score.value}
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Credit Score ({reportData.score.range.min}-{reportData.score.range.max})
            </p>
            <div className="mt-2">{getRatingBadge(reportData.score.rating)}</div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Customer Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
              <div>
                <p className="text-muted-foreground">Name</p>
                <p className="font-medium">{reportData.customer.name}</p>
              </div>
              <div>
                <p className="text-muted-foreground">PAN</p>
                <p className="font-mono">{reportData.customer.pan}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Date of Birth</p>
                <p>{reportData.customer.dob}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Mobile</p>
                <p>{reportData.customer.mobile}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="accounts">Accounts ({reportData.accounts.length})</TabsTrigger>
          <TabsTrigger value="enquiries">Enquiries ({reportData.enquiries.length})</TabsTrigger>
          <TabsTrigger value="factors">Score Factors</TabsTrigger>
          <TabsTrigger value="personal">Personal Info</TabsTrigger>
        </TabsList>

        <TabsContent value="summary" className="mt-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Building className="h-4 w-4" />
                  Total Accounts
                </div>
                <div className="mt-1 text-2xl font-bold">{reportData.summary.totalAccounts}</div>
                <p className="text-xs text-muted-foreground">
                  {reportData.summary.activeAccounts} active, {reportData.summary.closedAccounts}{' '}
                  closed
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CreditCard className="h-4 w-4" />
                  Total Credit Limit
                </div>
                <div className="mt-1 text-2xl font-bold">
                  {formatIndianCompactCurrency(reportData.summary.totalCreditLimit)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <FileText className="h-4 w-4" />
                  Current Outstanding
                </div>
                <div className="mt-1 text-2xl font-bold">
                  {formatIndianCompactCurrency(reportData.summary.totalOutstanding)}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <TrendingUp className="h-4 w-4" />
                  Credit Utilization
                </div>
                <div
                  className={`mt-1 text-2xl font-bold ${reportData.summary.utilizationPercent < 30 ? 'text-green-600' : reportData.summary.utilizationPercent < 50 ? 'text-yellow-600' : 'text-red-600'}`}
                >
                  {reportData.summary.utilizationPercent}%
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Account Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
                <div className="rounded-lg bg-green-50 p-4 text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {reportData.summary.activeAccounts}
                  </div>
                  <p className="text-sm text-muted-foreground">Active Accounts</p>
                </div>
                <div className="rounded-lg bg-gray-50 p-4 text-center">
                  <div className="text-3xl font-bold text-gray-600">
                    {reportData.summary.closedAccounts}
                  </div>
                  <p className="text-sm text-muted-foreground">Closed Accounts</p>
                </div>
                <div className="rounded-lg bg-red-50 p-4 text-center">
                  <div className="text-3xl font-bold text-red-600">
                    {reportData.summary.overdueAccounts}
                  </div>
                  <p className="text-sm text-muted-foreground">Overdue Accounts</p>
                </div>
                <div className="rounded-lg bg-blue-50 p-4 text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {reportData.enquiries.length}
                  </div>
                  <p className="text-sm text-muted-foreground">Recent Enquiries</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="accounts" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Credit Accounts</CardTitle>
              <CardDescription>All credit accounts reported to the bureau</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Lender</TableHead>
                    <TableHead>Account Type</TableHead>
                    <TableHead>Account No.</TableHead>
                    <TableHead className="text-right">Sanctioned</TableHead>
                    <TableHead className="text-right">Outstanding</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Open Date</TableHead>
                    <TableHead>DPD</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportData.accounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell className="font-medium">{account.lender}</TableCell>
                      <TableCell>{account.accountType}</TableCell>
                      <TableCell className="font-mono">{account.accountNumber}</TableCell>
                      <TableCell className="text-right">
                        {formatIndianCompactCurrency(account.sanctionedAmount)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatIndianCompactCurrency(account.currentBalance)}
                      </TableCell>
                      <TableCell>{getAccountStatusBadge(account.status)}</TableCell>
                      <TableCell>{account.openDate}</TableCell>
                      <TableCell>
                        <Badge variant={account.dpd === 0 ? 'default' : 'destructive'}>
                          {account.dpd}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="enquiries" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Credit Enquiries
              </CardTitle>
              <CardDescription>Recent credit enquiries made by lenders</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Lender</TableHead>
                    <TableHead>Enquiry Type</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportData.enquiries.map((enquiry, index) => (
                    <TableRow key={index}>
                      <TableCell>{enquiry.date}</TableCell>
                      <TableCell className="font-medium">{enquiry.lender}</TableCell>
                      <TableCell>{enquiry.type}</TableCell>
                      <TableCell className="text-right">
                        {formatIndianCompactCurrency(enquiry.amount)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {reportData.enquiries.length > 3 && (
                <div className="mt-4 rounded-lg bg-yellow-50 p-4">
                  <div className="flex items-center gap-2 text-yellow-800">
                    <AlertTriangle className="h-5 w-5" />
                    <span className="font-medium">High Enquiry Activity</span>
                  </div>
                  <p className="mt-1 text-sm text-yellow-700">
                    Multiple credit enquiries in a short period may negatively impact the credit
                    score.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="factors" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Score Factors</CardTitle>
              <CardDescription>Factors affecting the credit score</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {reportData.score.factors.map((factor, index) => (
                  <div key={index} className="flex items-start gap-4 rounded-lg border p-4">
                    <div className="mt-1">{getImpactIcon(factor.impact)}</div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">{factor.factor}</h4>
                        <Badge
                          variant={
                            factor.impact === 'POSITIVE'
                              ? 'default'
                              : factor.impact === 'NEGATIVE'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {factor.impact}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{factor.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="personal" className="mt-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Addresses</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {reportData.addresses.map((addr, index) => (
                    <div key={index} className="rounded-lg border p-3">
                      <div className="mb-2 flex items-center justify-between">
                        <Badge variant="outline">{addr.type}</Badge>
                        <span className="text-xs text-muted-foreground">
                          Reported: {addr.reportedOn}
                        </span>
                      </div>
                      <p className="text-sm">{addr.address}</p>
                      <p className="mt-1 text-xs text-muted-foreground">By: {addr.reportedBy}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Employment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {reportData.employments.map((emp, index) => (
                    <div key={index} className="rounded-lg border p-3">
                      <h4 className="font-medium">{emp.employer}</h4>
                      <p className="text-sm text-muted-foreground">{emp.designation}</p>
                      <p className="mt-2 text-sm">
                        Monthly Income:{' '}
                        <span className="font-medium">
                          {formatIndianCompactCurrency(emp.income)}
                        </span>
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Reported by {emp.reportedBy} on {emp.reportedOn}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
