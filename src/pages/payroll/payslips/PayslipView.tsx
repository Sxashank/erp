/**
 * Payslip View Page
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Download, Printer } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { AmountDisplay } from '@/components/common/AmountDisplay';
import payrollService, { Payslip, PayslipComponent, PayrollStatutory } from '@/services/payrollService';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

export default function PayslipView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();

  const [payslip, setPayslip] = useState<Payslip | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadPayslip(id);
    }
  }, [id]);

  const loadPayslip = async (payslipId: string) => {
    try {
      setLoading(true);
      const data = await payrollService.getPayslip(payslipId);
      setPayslip(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load payslip',
        variant: 'destructive',
      });
      navigate('/payroll/batches');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading || !payslip) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  const earnings = payslip.components?.filter((c) => c.component_type === 'EARNING') || [];
  const deductions = payslip.components?.filter((c) => c.component_type === 'DEDUCTION') || [];

  return (
    <div className="container mx-auto py-6 space-y-6 max-w-4xl">
      <div className="flex items-center justify-between print:hidden">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Payslip</h1>
            <p className="text-muted-foreground">
              {MONTHS[payslip.payroll_month - 1]} {payslip.payroll_year}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
        </div>
      </div>

      <Card className="print:shadow-none print:border-none">
        <CardHeader className="bg-muted/50">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-xl">PAYSLIP</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                For the period of {MONTHS[payslip.payroll_month - 1]} {payslip.payroll_year}
              </p>
            </div>
            <Badge
              variant={payslip.status === 'PAID' ? 'default' : 'secondary'}
              className="text-sm"
            >
              {payslip.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          {/* Employee Details */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold mb-2">Employee Details</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="text-muted-foreground">Name:</span>{' '}
                  <span className="font-medium">
                    {payslip.employee?.first_name} {payslip.employee?.last_name}
                  </span>
                </p>
                <p>
                  <span className="text-muted-foreground">Employee ID:</span>{' '}
                  {payslip.employee?.employee_code}
                </p>
                <p>
                  <span className="text-muted-foreground">Department:</span>{' '}
                  {payslip.employee?.department?.department_name || '-'}
                </p>
              </div>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Attendance Summary</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="text-muted-foreground">Working Days:</span>{' '}
                  {payslip.working_days}
                </p>
                <p>
                  <span className="text-muted-foreground">Paid Days:</span>{' '}
                  {payslip.paid_days}
                </p>
                <p>
                  <span className="text-muted-foreground">LOP Days:</span>{' '}
                  <span className={payslip.lop_days > 0 ? 'text-destructive' : ''}>
                    {payslip.lop_days}
                  </span>
                </p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Earnings and Deductions */}
          <div className="grid grid-cols-2 gap-6">
            {/* Earnings */}
            <div>
              <h3 className="font-semibold mb-3 text-green-600">Earnings</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Component</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {earnings.map((comp) => (
                    <TableRow key={comp.id}>
                      <TableCell>
                        {comp.component_name}
                        {comp.is_arrear && (
                          <Badge variant="outline" className="ml-2 text-xs">
                            Arrear
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={comp.amount} compact />
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50">
                    <TableCell className="font-semibold">Gross Earnings</TableCell>
                    <TableCell className="text-right font-semibold">
                      <AmountDisplay amount={payslip.gross_earnings} />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            {/* Deductions */}
            <div>
              <h3 className="font-semibold mb-3 text-destructive">Deductions</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Component</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deductions.map((comp) => (
                    <TableRow key={comp.id}>
                      <TableCell>{comp.component_name}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={comp.amount} compact />
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50">
                    <TableCell className="font-semibold">Total Deductions</TableCell>
                    <TableCell className="text-right font-semibold">
                      <AmountDisplay amount={payslip.total_deductions} />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>

          <Separator />

          {/* Statutory Details */}
          {payslip.statutory && payslip.statutory.length > 0 && (
            <>
              <div>
                <h3 className="font-semibold mb-3">Statutory Contributions</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead className="text-right">Wage Base</TableHead>
                      <TableHead className="text-right">Employee</TableHead>
                      <TableHead className="text-right">Employer</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payslip.statutory.map((stat) => (
                      <TableRow key={stat.id}>
                        <TableCell>{stat.statutory_type}</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={stat.wage_base} compact />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={stat.employee_amount} compact />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={stat.employer_amount} compact />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <Separator />
            </>
          )}

          {/* Net Pay */}
          <div className="bg-primary/5 p-4 rounded-lg">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold">Net Payable</h3>
                <p className="text-sm text-muted-foreground">
                  Gross Earnings - Total Deductions
                </p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-primary">
                  <AmountDisplay amount={payslip.net_salary} />
                </p>
              </div>
            </div>
          </div>

          {/* Employer Contribution */}
          {(payslip.employer_pf || payslip.employer_esi) && (
            <div className="text-sm text-muted-foreground">
              <p className="font-medium">Employer Contributions (Not included in Net Pay):</p>
              <div className="flex gap-4 mt-1">
                {payslip.employer_pf && payslip.employer_pf > 0 && (
                  <span>PF: <AmountDisplay amount={payslip.employer_pf} compact /></span>
                )}
                {payslip.employer_esi && payslip.employer_esi > 0 && (
                  <span>ESI: <AmountDisplay amount={payslip.employer_esi} compact /></span>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
