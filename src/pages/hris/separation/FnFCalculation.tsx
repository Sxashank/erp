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
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { useToast } from '@/hooks/use-toast';
import { formatDate, formatCurrency } from '@/lib/utils';
import { hrisApi } from '@/services/api';

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
    status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'PAID' | 'CANCELLED';
  };
}

interface SeparationSummary {
  employee_id: string;
  employee_code?: string;
  employee_name?: string;
  approved_last_working_date?: string;
  requested_last_working_date?: string;
  actual_last_working_date?: string;
}

interface FnFApiResponse {
  id: string;
  separation_id: string;
  employee_id: string;
  last_working_date: string;
  status: 'DRAFT' | 'CALCULATED' | 'PENDING_APPROVAL' | 'APPROVED' | 'PAID' | 'CANCELLED';
  pending_salary: number | string;
  leave_encashment: number | string;
  leave_encashment_days: number | string;
  gratuity_amount: number | string;
  gratuity_years: number | string;
  gratuity_eligible: boolean;
  bonus_amount: number | string;
  pending_reimbursements: number | string;
  other_earnings: number | string;
  total_earnings: number | string;
  notice_recovery: number | string;
  notice_shortfall_days: number;
  advance_recovery: number | string;
  loan_recovery: number | string;
  asset_recovery: number | string;
  clearance_recovery: number | string;
  other_deductions: number | string;
  tds_amount: number | string;
  total_deductions: number | string;
  net_payable: number | string;
}

const toNumber = (value: number | string | undefined) => Number(value ?? 0);

const toFnFData = (fnf: FnFApiResponse, separation?: SeparationSummary): FnFData => {
  const pendingSalary = toNumber(fnf.pending_salary);
  const leaveEncashment = toNumber(fnf.leave_encashment);
  const gratuityAmount = toNumber(fnf.gratuity_amount);
  const leaveDays = toNumber(fnf.leave_encashment_days);
  const gratuityYears = toNumber(fnf.gratuity_years);
  const tdsAmount = toNumber(fnf.tds_amount);
  const totalEarnings = toNumber(fnf.total_earnings);
  const totalDeductions = toNumber(fnf.total_deductions);

  return {
    separation_id: fnf.separation_id,
    employee: {
      id: fnf.employee_id,
      code: separation?.employee_code || fnf.employee_id,
      name: separation?.employee_name || 'Employee',
      department: '—',
      designation: '—',
      date_of_joining: '',
      last_working_date:
        fnf.last_working_date ||
        separation?.actual_last_working_date ||
        separation?.approved_last_working_date ||
        separation?.requested_last_working_date ||
        '',
      total_service_years: Math.floor(gratuityYears),
      total_service_months: Math.round((gratuityYears % 1) * 12),
    },
    salary_components: {
      basic: 0,
      da: 0,
      hra: 0,
      special_allowance: 0,
      other_allowances: 0,
      gross_salary: pendingSalary,
    },
    earnings: [
      { component: 'Pending salary', description: 'Salary payable until last working date', amount: pendingSalary },
      { component: 'Leave encashment', description: `${leaveDays} days encashed`, amount: leaveEncashment, days: leaveDays },
      { component: 'Gratuity', description: `${gratuityYears} years eligible service`, amount: gratuityAmount },
      { component: 'Bonus', description: 'Pending bonus payable', amount: toNumber(fnf.bonus_amount) },
      { component: 'Reimbursements', description: 'Approved pending reimbursements', amount: toNumber(fnf.pending_reimbursements) },
      { component: 'Other earnings', description: 'Additional earnings captured in FnF', amount: toNumber(fnf.other_earnings) },
    ].filter((item) => item.amount !== 0),
    deductions: [
      { component: 'Notice recovery', description: `${fnf.notice_shortfall_days} day shortfall`, amount: toNumber(fnf.notice_recovery) },
      { component: 'Advance recovery', description: 'Outstanding employee advances', amount: toNumber(fnf.advance_recovery) },
      { component: 'Loan recovery', description: 'Outstanding employee loan balance', amount: toNumber(fnf.loan_recovery) },
      { component: 'Asset recovery', description: 'Asset or clearance recovery', amount: toNumber(fnf.asset_recovery) },
      { component: 'Clearance recovery', description: 'Pending clearance recoveries', amount: toNumber(fnf.clearance_recovery) },
      { component: 'Other deductions', description: 'Additional deductions captured in FnF', amount: toNumber(fnf.other_deductions) },
      { component: 'TDS', description: 'Tax deducted at source on FnF', amount: tdsAmount },
    ].filter((item) => item.amount !== 0),
    gratuity: {
      eligible: fnf.gratuity_eligible,
      service_years: gratuityYears,
      last_drawn_basic_da: 0,
      calculated_amount: gratuityAmount,
      capped_amount: gratuityAmount,
      formula: '(Basic + DA) × 15 / 26 × Years of Service',
    },
    leave_encashment: {
      el_balance: leaveDays,
      daily_rate: leaveDays > 0 ? leaveEncashment / leaveDays : 0,
      amount: leaveEncashment,
    },
    tax_calculation: {
      total_earnings: totalEarnings,
      total_deductions: totalDeductions,
      taxable_amount: Math.max(0, totalEarnings - gratuityAmount - leaveEncashment),
      tds_deducted: tdsAmount,
    },
    summary: {
      total_earnings: totalEarnings,
      total_deductions: totalDeductions,
      net_payable: toNumber(fnf.net_payable),
      status: fnf.status === 'CALCULATED' ? 'PENDING_APPROVAL' : fnf.status,
    },
  };
};

export default function FnFCalculation() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const [fnfData, setFnfData] = useState<FnFData | null>(null);
  const [separation, setSeparation] = useState<SeparationSummary | undefined>();
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);

  const loadFnF = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    try {
      const separationResponse = await hrisApi.getSeparation(id);
      const separationData = separationResponse.data as SeparationSummary;
      setSeparation(separationData);
      const fnfResponse = await hrisApi.getFnF(id);
      setFnfData(toFnFData(fnfResponse.data as FnFApiResponse, separationData));
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } } | null)?.response?.status;
      if (status !== 404) {
        toast({
          title: 'Unable to load FnF settlement',
          description: 'Check HRIS FnF permissions and retry.',
          variant: 'destructive',
        });
      }
      setFnfData(null);
    } finally {
      setIsLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    loadFnF();
  }, [loadFnF]);

  const handleCalculate = async () => {
    if (!id) return;
    setIsCalculating(true);
    try {
      const response = await hrisApi.calculateFnF(id, {
        include_gratuity: true,
        include_leave_encashment: true,
      });
      setFnfData(toFnFData(response.data as FnFApiResponse, separation));
      toast({ title: 'FnF settlement calculated' });
    } catch (error) {
      toast({
        title: 'Unable to calculate FnF',
        description: 'Complete required approvals and clearance steps before calculation.',
        variant: 'destructive',
      });
    } finally {
      setIsCalculating(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const config: Record<
      string,
      { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }
    > = {
      DRAFT: { variant: 'outline', label: 'Draft' },
      PENDING_APPROVAL: { variant: 'secondary', label: 'Pending Approval' },
      APPROVED: { variant: 'default', label: 'Approved' },
      PAID: { variant: 'default', label: 'Paid' },
      CANCELLED: { variant: 'destructive', label: 'Cancelled' },
    };
    const cfg = config[status] || config.DRAFT;
    return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Full & Final Settlement"
          subtitle="Loading settlement calculation"
          breadcrumbs={[{ label: 'Separation', to: '/admin/hris/separation' }, { label: 'FnF' }]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Loading FnF settlement...
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!fnfData) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Full & Final Settlement"
          subtitle={`Settlement calculation for ${separation?.employee_name || 'employee separation'}`}
          breadcrumbs={[{ label: 'Separation', to: '/admin/hris/separation' }, { label: 'FnF' }]}
          actions={
            <Button onClick={handleCalculate} disabled={isCalculating}>
              <Calculator className="mr-2 h-4 w-4" />
              {isCalculating ? 'Calculating...' : 'Calculate FnF'}
            </Button>
          }
        />
        <Card>
          <CardContent className="py-10 text-center">
            <Calculator className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
            <h3 className="text-base font-semibold">No FnF settlement calculated</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Generate the settlement from approved separation, clearance, salary, leave, and recovery data.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Full & Final Settlement"
        subtitle={`Settlement calculation for ${fnfData.employee.name}`}
        breadcrumbs={[{ label: 'Separation', to: '/admin/hris/separation' }, { label: 'FnF' }]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export PDF
            </Button>
            {fnfData.summary.status === 'PENDING_APPROVAL' && (
              <Button>
                <Send className="mr-2 h-4 w-4" />
                Submit for Approval
              </Button>
            )}
          </div>
        }
      />

      {/* Employee Info Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <User className="h-8 w-8 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{fnfData.employee.name}</h2>
                <p className="text-muted-foreground">{fnfData.employee.code}</p>
                <div className="mt-1 flex items-center gap-4 text-sm">
                  <span>{fnfData.employee.department}</span>
                  <span>•</span>
                  <span>{fnfData.employee.designation}</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              {getStatusBadge(fnfData.summary.status)}
              <p className="mt-2 text-sm text-muted-foreground">
                Service: {fnfData.employee.total_service_years} years{' '}
                {fnfData.employee.total_service_months} months
              </p>
            </div>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-4 border-t pt-4 md:grid-cols-4">
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
              <p className="font-medium">
                {formatCurrency(fnfData.salary_components.gross_salary)}
              </p>
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
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card className="border-green-200 bg-green-50">
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

        <Card className="border-red-200 bg-red-50">
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

        <Card className="border-blue-200 bg-blue-50">
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

        <Card className="border-purple-200 bg-purple-50">
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
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Earnings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-700">
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
                <CardTitle className="flex items-center gap-2 text-red-700">
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
              <CardDescription>As per Payment of Gratuity Act, 1972</CardDescription>
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

                  <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                    <div className="rounded-lg bg-muted p-4">
                      <p className="text-sm text-muted-foreground">Service Years</p>
                      <p className="text-2xl font-bold">{fnfData.gratuity.service_years}</p>
                    </div>
                    <div className="rounded-lg bg-muted p-4">
                      <p className="text-sm text-muted-foreground">Last Drawn Basic + DA</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(fnfData.gratuity.last_drawn_basic_da)}
                      </p>
                    </div>
                    <div className="rounded-lg bg-muted p-4">
                      <p className="text-sm text-muted-foreground">Calculated Amount</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(fnfData.gratuity.calculated_amount)}
                      </p>
                    </div>
                    <div className="rounded-lg bg-green-100 p-4">
                      <p className="text-sm text-green-700">Payable Amount</p>
                      <p className="text-2xl font-bold text-green-800">
                        {formatCurrency(fnfData.gratuity.capped_amount)}
                      </p>
                    </div>
                  </div>

                  <div className="rounded-lg bg-blue-50 p-4">
                    <p className="text-sm font-medium text-blue-800">Formula Applied:</p>
                    <p className="mt-1 text-blue-700">{fnfData.gratuity.formula}</p>
                    <p className="mt-2 text-sm text-blue-600">
                      = {formatCurrency(fnfData.gratuity.last_drawn_basic_da)} × 15 / 26 ×{' '}
                      {fnfData.gratuity.service_years}
                    </p>
                    <p className="text-sm text-blue-600">
                      = {formatCurrency(fnfData.gratuity.calculated_amount)}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
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
              <CardDescription>Encashment of earned leave balance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm text-muted-foreground">EL Balance</p>
                  <p className="text-2xl font-bold">{fnfData.leave_encashment.el_balance} days</p>
                </div>
                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm text-muted-foreground">Daily Rate (Basic + DA / 26)</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(fnfData.leave_encashment.daily_rate)}
                  </p>
                </div>
                <div className="rounded-lg bg-green-100 p-4">
                  <p className="text-sm text-green-700">Encashment Amount</p>
                  <p className="text-2xl font-bold text-green-800">
                    {formatCurrency(fnfData.leave_encashment.amount)}
                  </p>
                </div>
              </div>

              <div className="rounded-lg bg-blue-50 p-4">
                <p className="text-sm font-medium text-blue-800">Calculation:</p>
                <p className="mt-1 text-blue-700">
                  {fnfData.leave_encashment.el_balance} days ×{' '}
                  {formatCurrency(fnfData.leave_encashment.daily_rate)} ={' '}
                  {formatCurrency(fnfData.leave_encashment.amount)}
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
              <CardDescription>TDS on Full & Final Settlement</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm text-muted-foreground">Total Earnings</p>
                  <p className="text-xl font-bold">
                    {formatCurrency(fnfData.tax_calculation.total_earnings)}
                  </p>
                </div>
                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm text-muted-foreground">Exemptions</p>
                  <p className="text-xl font-bold">
                    {formatCurrency(
                      fnfData.tax_calculation.total_earnings -
                        fnfData.tax_calculation.taxable_amount,
                    )}
                  </p>
                </div>
                <div className="rounded-lg bg-muted p-4">
                  <p className="text-sm text-muted-foreground">Taxable Amount</p>
                  <p className="text-xl font-bold">
                    {formatCurrency(fnfData.tax_calculation.taxable_amount)}
                  </p>
                </div>
                <div className="rounded-lg bg-red-100 p-4">
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
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm">
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
              <p className="text-sm text-muted-foreground">After all deductions including TDS</p>
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
  const teens = [
    'Ten',
    'Eleven',
    'Twelve',
    'Thirteen',
    'Fourteen',
    'Fifteen',
    'Sixteen',
    'Seventeen',
    'Eighteen',
    'Nineteen',
  ];
  const tens = [
    '',
    '',
    'Twenty',
    'Thirty',
    'Forty',
    'Fifty',
    'Sixty',
    'Seventy',
    'Eighty',
    'Ninety',
  ];

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
