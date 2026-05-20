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

  const earnings = payslip.components?.filter((c) => c.componentType === 'EARNING') || [];
  const deductions = payslip.components?.filter((c) => c.componentType === 'DEDUCTION') || [];

  return (
    <div className="container mx-auto max-w-4xl space-y-6 py-6">
      <div className="print:hidden">
        <PageHeader
          title="Payslip"
          subtitle={`${MONTHS[payslip.payrollMonth - 1]} ${payslip.payrollYear}`}
          breadcrumbs={[
            { label: 'Payslips', to: '/admin/payroll/payslips' },
            { label: `${MONTHS[payslip.payrollMonth - 1]} ${payslip.payrollYear}` },
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
                For the period of {MONTHS[payslip.payrollMonth - 1]} {payslip.payrollYear}
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
                    {payslip.employee?.firstName} {payslip.employee?.lastName}
                  </span>
                </p>
                <p>
                  <span className="text-muted-foreground">Employee ID:</span>{' '}
                  {payslip.employee?.employeeCode}
                </p>
                <p>
                  <span className="text-muted-foreground">Department:</span>{' '}
                  {payslip.employee?.department?.departmentName || '-'}
                </p>
              </div>
            </div>
            <div>
              <h3 className="mb-2 font-semibold">Attendance Summary</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="text-muted-foreground">Working Days:</span>{' '}
                  {payslip.workingDays}
                </p>
                <p>
                  <span className="text-muted-foreground">Paid Days:</span> {payslip.paidDays}
                </p>
                <p>
                  <span className="text-muted-foreground">LOP Days:</span>{' '}
                  <span className={payslip.lopDays > 0 ? 'text-destructive' : ''}>
                    {payslip.lopDays}
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
                        {comp.componentName}
                        {comp.isArrear && (
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
                      <AmountDisplay amount={payslip.grossEarnings} />
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
                      <TableCell>{comp.componentName}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={comp.amount} compact />
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50">
                    <TableCell className="font-semibold">Total Deductions</TableCell>
                    <TableCell className="text-right font-semibold">
                      <AmountDisplay amount={payslip.totalDeductions} />
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
                        <TableCell>{stat.statutoryType}</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={stat.wageBase} compact />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={stat.employeeAmount} compact />
                        </TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay amount={stat.employerAmount} compact />
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
                  <AmountDisplay amount={payslip.netSalary} />
                </p>
              </div>
            </div>
          </div>

          {/* Employer Contribution */}
          {(payslip.employerPf || payslip.employerEsi) && (
            <div className="text-sm text-muted-foreground">
              <p className="font-medium">Employer Contributions (Not included in Net Pay):</p>
              <div className="mt-1 flex gap-4">
                {payslip.employerPf && payslip.employerPf > 0 && (
                  <span>
                    PF: <AmountDisplay amount={payslip.employerPf} compact />
                  </span>
                )}
                {payslip.employerEsi && payslip.employerEsi > 0 && (
                  <span>
                    ESI: <AmountDisplay amount={payslip.employerEsi} compact />
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
