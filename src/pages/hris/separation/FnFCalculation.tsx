import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Calculator,
  Download,
  Send,
  CheckCircle,
  AlertTriangle,
  IndianRupee,
  Calendar,
  User,
  FileText,
  Printer,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatDate, formatCurrency } from '@/lib/utils';

interface FnFData {
  separation_id: string;
  employee: {
    id: string;
    code: string;
    name: string;
    department: string;
    designation: string;
    date_of_joining: string;
    last_working_date: string;
    total_service_years: number;
    total_service_months: number;
  };
  salary_components: {
    basic: number;
    da: number;
    hra: number;
    special_allowance: number;
    other_allowances: number;
    gross_salary: number;
  };
  earnings: {
    component: string;
    description: string;
    amount: number;
    days?: number;
  }[];
  deductions: {
    component: string;
    description: string;
    amount: number;
  }[];
  gratuity: {
    eligible: boolean;
    service_years: number;
    last_drawn_basic_da: number;
    calculated_amount: number;
    capped_amount: number;
    formula: string;
  };
  leave_encashment: {
    el_balance: number;
    daily_rate: number;
    amount: number;
  };
  tax_calculation: {
    total_earnings: number;
    total_deductions: number;
    taxable_amount: number;
    tds_deducted: number;
  };
  summary: {
    total_earnings: number;
    total_deductions: number;
    net_payable: number;
    status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'PAID';
  };
}

// Mock F&F data
const mockFnFData: FnFData = {
  separation_id: 'sep-001',
  employee: {
    id: 'emp-001',
    code: 'EMP001',
    name: 'Rahul Sharma',
    department: 'Engineering',
    designation: 'Senior Developer',
    date_of_joining: '2018-03-15',
    last_working_date: '2024-12-31',
    total_service_years: 6,
    total_service_months: 9,
  },
  salary_components: {
    basic: 50000,
    da: 10000,
    hra: 25000,
    special_allowance: 15000,
    other_allowances: 5000,
    gross_salary: 105000,
  },
  earnings: [
    { component: 'Salary (Pro-rata)', description: '15 days of December 2024', amount: 52500, days: 15 },
    { component: 'Leave Encashment', description: 'EL Balance: 24 days', amount: 48000, days: 24 },
    { component: 'Gratuity', description: '6 years 9 months service', amount: 346154 },
    { component: 'Bonus (Pro-rata)', description: 'FY 2024-25 (9 months)', amount: 37500 },
    { component: 'Notice Period Buyout', description: 'Company paid', amount: 0 },
    { component: 'Reimbursements', description: 'Pending claims', amount: 12500 },
  ],
  deductions: [
    { component: 'PF Recovery', description: 'Employee contribution', amount: 9000 },
    { component: 'Professional Tax', description: 'December 2024', amount: 200 },
    { component: 'Loan Recovery', description: 'Outstanding balance', amount: 50000 },
    { component: 'Notice Period Shortfall', description: 'Not applicable', amount: 0 },
    { component: 'Asset Recovery', description: 'Laptop not returned', amount: 0 },
    { component: 'TDS', description: 'Tax on F&F', amount: 45000 },
  ],
  gratuity: {
    eligible: true,
    service_years: 6,
    last_drawn_basic_da: 60000,
    calculated_amount: 346154,
    capped_amount: 346154,
    formula: '(Basic + DA) × 15 / 26 × Years of Service',
  },
  leave_encashment: {
    el_balance: 24,
    daily_rate: 2000,
    amount: 48000,
  },
  tax_calculation: {
    total_earnings: 496654,
    total_deductions: 104200,
    taxable_amount: 392454,
    tds_deducted: 45000,
  },
  summary: {
    total_earnings: 496654,
    total_deductions: 104200,
    net_payable: 392454,
    status: 'PENDING_APPROVAL',
  },
};

export default function FnFCalculation() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [fnfData] = useState<FnFData>(mockFnFData);

  const getStatusBadge = (status: string) => {
    const config: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }> = {
      DRAFT: { variant: 'outline', label: 'Draft' },
      PENDING_APPROVAL: { variant: 'secondary', label: 'Pending Approval' },
      APPROVED: { variant: 'default', label: 'Approved' },
      PAID: { variant: 'default', label: 'Paid' },
    };
    const cfg = config[status] || config.DRAFT;
    return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/hris/separation')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Full & Final Settlement</h1>
            <p className="text-muted-foreground">
              Settlement calculation for {fnfData.employee.name}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </Button>
          {fnfData.summary.status === 'PENDING_APPROVAL' && (
            <Button>
              <Send className="h-4 w-4 mr-2" />
              Submit for Approval
            </Button>
          )}
        </div>
      </div>

      {/* Employee Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{fnfData.employee.name}</h2>
                <p className="text-muted-foreground">{fnfData.employee.code}</p>
                <div className="flex items-center gap-4 mt-1 text-sm">
                  <span>{fnfData.employee.department}</span>
                  <span>•</span>
                  <span>{fnfData.employee.designation}</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              {getStatusBadge(fnfData.summary.status)}
              <p className="text-sm text-muted-foreground mt-2">
                Service: {fnfData.employee.total_service_years} years {fnfData.employee.total_service_months} months
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-4 border-t">
            <div>
              <p className="text-xs text-muted-foreground">Date of Joining</p>
              <p className="font-medium">{formatDate(fnfData.employee.date_of_joining)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Last Working Date</p>
              <p className="font-medium">{formatDate(fnfData.employee.last_working_date)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Gross Salary</p>
              <p className="font-medium">{formatCurrency(fnfData.salary_components.gross_salary)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Basic + DA</p>
              <p className="font-medium">
                {formatCurrency(fnfData.salary_components.basic + fnfData.salary_components.da)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700">Total Earnings</p>
                <p className="text-2xl font-bold text-green-800">
                  {formatCurrency(fnfData.summary.total_earnings)}
                </p>
              </div>
              <IndianRupee className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-700">Total Deductions</p>
                <p className="text-2xl font-bold text-red-800">
                  {formatCurrency(fnfData.summary.total_deductions)}
                </p>
              </div>
              <IndianRupee className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-700">TDS Deducted</p>
                <p className="text-2xl font-bold text-blue-800">
                  {formatCurrency(fnfData.tax_calculation.tds_deducted)}
                </p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-700">Net Payable</p>
                <p className="text-2xl font-bold text-purple-800">
                  {formatCurrency(fnfData.summary.net_payable)}
                </p>
              </div>
              <Calculator className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Breakdown */}
      <Tabs defaultValue="breakdown" className="space-y-4">
        <TabsList>
          <TabsTrigger value="breakdown">Earnings & Deductions</TabsTrigger>
          <TabsTrigger value="gratuity">Gratuity Calculation</TabsTrigger>
          <TabsTrigger value="leave">Leave Encashment</TabsTrigger>
          <TabsTrigger value="tax">Tax Calculation</TabsTrigger>
        </TabsList>

        <TabsContent value="breakdown" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Earnings */}
            <Card>
              <CardHeader>
                <CardTitle className="text-green-700 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Earnings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Component</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fnfData.earnings.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-medium">{item.component}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {item.description}
                        </TableCell>
                        <TableCell className="text-right text-green-700">
                          {formatCurrency(item.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="bg-green-50">
                      <TableCell colSpan={2} className="font-bold">
                        Total Earnings
                      </TableCell>
                      <TableCell className="text-right font-bold text-green-700">
                        {formatCurrency(fnfData.summary.total_earnings)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Deductions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-red-700 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  Deductions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Component</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fnfData.deductions.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-medium">{item.component}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {item.description}
                        </TableCell>
                        <TableCell className="text-right text-red-700">
                          {formatCurrency(item.amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow className="bg-red-50">
                      <TableCell colSpan={2} className="font-bold">
                        Total Deductions
                      </TableCell>
                      <TableCell className="text-right font-bold text-red-700">
                        {formatCurrency(fnfData.summary.total_deductions)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="gratuity">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Gratuity Calculation
              </CardTitle>
              <CardDescription>
                As per Payment of Gratuity Act, 1972
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {fnfData.gratuity.eligible ? (
                <>
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertTitle>Eligible for Gratuity</AlertTitle>
                    <AlertDescription>
                      Employee has completed more than 5 years of continuous service.
                    </AlertDescription>
                  </Alert>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Service Years</p>
                      <p className="text-2xl font-bold">{fnfData.gratuity.service_years}</p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Last Drawn Basic + DA</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(fnfData.gratuity.last_drawn_basic_da)}
                      </p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">Calculated Amount</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(fnfData.gratuity.calculated_amount)}
                      </p>
                    </div>
                    <div className="p-4 bg-green-100 rounded-lg">
                      <p className="text-sm text-green-700">Payable Amount</p>
                      <p className="text-2xl font-bold text-green-800">
                        {formatCurrency(fnfData.gratuity.capped_amount)}
                      </p>
                    </div>
                  </div>

                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-800">Formula Applied:</p>
                    <p className="text-blue-700 mt-1">{fnfData.gratuity.formula}</p>
                    <p className="text-sm text-blue-600 mt-2">
                      = {formatCurrency(fnfData.gratuity.last_drawn_basic_da)} × 15 / 26 × {fnfData.gratuity.service_years}
                    </p>
                    <p className="text-sm text-blue-600">
                      = {formatCurrency(fnfData.gratuity.calculated_amount)}
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Note: Maximum gratuity payable is capped at ₹20,00,000 as per the Act
                    </p>
                  </div>
                </>
              ) : (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Not Eligible for Gratuity</AlertTitle>
                  <AlertDescription>
                    Employee has not completed 5 years of continuous service.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="leave">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Leave Encashment
              </CardTitle>
              <CardDescription>
                Encashment of earned leave balance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">EL Balance</p>
                  <p className="text-2xl font-bold">{fnfData.leave_encashment.el_balance} days</p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">Daily Rate (Basic + DA / 26)</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(fnfData.leave_encashment.daily_rate)}
                  </p>
                </div>
                <div className="p-4 bg-green-100 rounded-lg">
                  <p className="text-sm text-green-700">Encashment Amount</p>
                  <p className="text-2xl font-bold text-green-800">
                    {formatCurrency(fnfData.leave_encashment.amount)}
                  </p>
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-800">Calculation:</p>
                <p className="text-blue-700 mt-1">
                  {fnfData.leave_encashment.el_balance} days × {formatCurrency(fnfData.leave_encashment.daily_rate)} = {formatCurrency(fnfData.leave_encashment.amount)}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tax">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Tax Calculation
              </CardTitle>
              <CardDescription>
                TDS on Full & Final Settlement
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">Total Earnings</p>
                  <p className="text-xl font-bold">
                    {formatCurrency(fnfData.tax_calculation.total_earnings)}
                  </p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">Exemptions</p>
                  <p className="text-xl font-bold">
                    {formatCurrency(fnfData.tax_calculation.total_earnings - fnfData.tax_calculation.taxable_amount)}
                  </p>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">Taxable Amount</p>
                  <p className="text-xl font-bold">
                    {formatCurrency(fnfData.tax_calculation.taxable_amount)}
                  </p>
                </div>
                <div className="p-4 bg-red-100 rounded-lg">
                  <p className="text-sm text-red-700">TDS Deducted</p>
                  <p className="text-xl font-bold text-red-800">
                    {formatCurrency(fnfData.tax_calculation.tds_deducted)}
                  </p>
                </div>
              </div>

              <Alert>
                <FileText className="h-4 w-4" />
                <AlertTitle>Tax Treatment Notes</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
                    <li>Gratuity up to ₹20 lakh is exempt under Section 10(10)</li>
                    <li>Leave encashment up to ₹25 lakh is exempt under Section 10(10AA)</li>
                    <li>Pro-rata salary is fully taxable</li>
                    <li>TDS calculated based on average tax rate for the financial year</li>
                  </ul>
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Final Summary */}
      <Card className="border-2 border-primary">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold">Net Payable Amount</h3>
              <p className="text-sm text-muted-foreground">
                After all deductions including TDS
              </p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-primary">
                {formatCurrency(fnfData.summary.net_payable)}
              </p>
              <p className="text-sm text-muted-foreground">
                (Rupees {numberToWords(fnfData.summary.net_payable)} Only)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper function to convert number to words (simplified)
function numberToWords(num: number): string {
  const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
  const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];

  if (num === 0) return 'Zero';

  const lakhs = Math.floor(num / 100000);
  const thousands = Math.floor((num % 100000) / 1000);
  const hundreds = Math.floor((num % 1000) / 100);
  const remainder = num % 100;

  let result = '';

  if (lakhs > 0) {
    result += (lakhs < 10 ? ones[lakhs] : '') + ' Lakh ';
  }
  if (thousands > 0) {
    if (thousands < 10) result += ones[thousands] + ' Thousand ';
    else if (thousands < 20) result += teens[thousands - 10] + ' Thousand ';
    else result += tens[Math.floor(thousands / 10)] + ' ' + ones[thousands % 10] + ' Thousand ';
  }
  if (hundreds > 0) {
    result += ones[hundreds] + ' Hundred ';
  }
  if (remainder > 0) {
    if (remainder < 10) result += ones[remainder];
    else if (remainder < 20) result += teens[remainder - 10];
    else result += tens[Math.floor(remainder / 10)] + ' ' + ones[remainder % 10];
  }

  return result.trim();
}
