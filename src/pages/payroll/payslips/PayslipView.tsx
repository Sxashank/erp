/**
 * Payslip View Page
 */

import { Download, Printer } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import type { Payslip } from '@/services/payrollService';
import payrollService, { PayslipComponent, PayrollStatutory } from '@/services/payrollService';

const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
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
      navigate('/admin/payroll/batches');
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
        <div className="py-8 text-center">Loading...</div>
      </div>
    );
  }

  const earnings = payslip.components?.filter((c) => c.component_type === 'EARNING') || [];
  const deductions = payslip.components?.filter((c) => c.component_type === 'DEDUCTION') || [];

  return (
    <div className="container mx-auto max-w-4xl space-y-6 py-6">
      <div className="print:hidden">
        <PageHeader
          title="Payslip"
          subtitle={`${MONTHS[payslip.payroll_month - 1]} ${payslip.payroll_year}`}
          breadcrumbs={[
            { label: 'Payslips', to: '/admin/payroll/payslips' },
            { label: `${MONTHS[payslip.payroll_month - 1]} ${payslip.payroll_year}` },
          ]}
          actions={
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
          }
        />
      </div>

      <Card className="print:border-none print:shadow-none">
        <CardHeader className="bg-muted/50">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">PAYSLIP</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
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
              <h3 className="mb-2 font-semibold">Employee Details</h3>
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
              <h3 className="mb-2 font-semibold">Attendance Summary</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="text-muted-foreground">Working Days:</span>{' '}
                  {payslip.working_days}
                </p>
                <p>
                  <span className="text-muted-foreground">Paid Days:</span> {payslip.paid_days}
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
              <h3 className="mb-3 font-semibold text-green-600">Earnings</h3>
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
              <h3 className="mb-3 font-semibold text-destructive">Deductions</h3>
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
                <h3 className="mb-3 font-semibold">Statutory Contributions</h3>
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
          <div className="rounded-lg bg-primary/5 p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Net Payable</h3>
                <p className="text-sm text-muted-foreground">Gross Earnings - Total Deductions</p>
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
              <div className="mt-1 flex gap-4">
                {payslip.employer_pf && payslip.employer_pf > 0 && (
                  <span>
                    PF: <AmountDisplay amount={payslip.employer_pf} compact />
                  </span>
                )}
                {payslip.employer_esi && payslip.employer_esi > 0 && (
                  <span>
                    ESI: <AmountDisplay amount={payslip.employer_esi} compact />
                  </span>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
