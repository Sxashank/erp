/**
 * Payroll Batch View Page
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  CheckCircle,
  Banknote,
  FileText,
  Users,
  DollarSign,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { AmountDisplay } from '@/components/common/AmountDisplay';
import payrollService, { PayrollBatch, Payslip } from '@/services/payrollService';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  DRAFT: 'outline',
  PROCESSING: 'secondary',
  PROCESSED: 'default',
  APPROVED: 'default',
  PAID: 'default',
  CANCELLED: 'destructive',
};

export default function PayrollBatchView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();

  const [batch, setBatch] = useState<PayrollBatch | null>(null);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (id) {
      loadBatch(id);
      loadPayslips(id);
    }
  }, [id]);

  const loadBatch = async (batchId: string) => {
    try {
      setLoading(true);
      const data = await payrollService.getBatch(batchId);
      setBatch(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load batch details',
        variant: 'destructive',
      });
      navigate('/payroll/batches');
    } finally {
      setLoading(false);
    }
  };

  const loadPayslips = async (batchId: string) => {
    try {
      const response = await payrollService.listPayslips({
        batch_id: batchId,
        limit: 200,
      });
      setPayslips(response.items);
    } catch (error) {
      console.error('Failed to load payslips:', error);
    }
  };

  const handleProcess = async () => {
    if (!id || !confirm('Start processing payroll for this batch?')) return;

    try {
      setProcessing(true);
      await payrollService.processBatch(id);
      toast({
        title: 'Success',
        description: 'Payroll processing completed',
      });
      loadBatch(id);
      loadPayslips(id);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to process batch',
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleApprove = async () => {
    if (!id || !confirm('Approve this payroll batch?')) return;

    try {
      setProcessing(true);
      await payrollService.approveBatch(id);
      toast({
        title: 'Success',
        description: 'Batch approved successfully',
      });
      loadBatch(id);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to approve batch',
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleMarkPaid = async () => {
    if (!id || !confirm('Mark this batch as paid?')) return;

    try {
      setProcessing(true);
      await payrollService.markBatchPaid(id);
      toast({
        title: 'Success',
        description: 'Batch marked as paid',
      });
      loadBatch(id);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to mark as paid',
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  if (loading || !batch) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/payroll/batches')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">{batch.batch_reference}</h1>
              <Badge variant={STATUS_COLORS[batch.status] || 'outline'}>
                {batch.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {MONTHS[batch.payroll_month - 1]} {batch.payroll_year}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {batch.status === 'DRAFT' && (
            <Button onClick={handleProcess} disabled={processing}>
              <Play className="mr-2 h-4 w-4" />
              {processing ? 'Processing...' : 'Process Payroll'}
            </Button>
          )}
          {batch.status === 'PROCESSED' && (
            <Button onClick={handleApprove} disabled={processing}>
              <CheckCircle className="mr-2 h-4 w-4" />
              {processing ? 'Approving...' : 'Approve Batch'}
            </Button>
          )}
          {batch.status === 'APPROVED' && (
            <Button onClick={handleMarkPaid} disabled={processing}>
              <Banknote className="mr-2 h-4 w-4" />
              {processing ? 'Processing...' : 'Mark as Paid'}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Employees
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-2 text-muted-foreground" />
              <span className="text-2xl font-bold">{batch.total_employees}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Gross Salary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              <AmountDisplay amount={batch.total_gross} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Deductions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              <AmountDisplay amount={batch.total_deductions} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Net Payable
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              <AmountDisplay amount={batch.total_net} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Payslips</CardTitle>
              <CardDescription>
                Individual employee payslips for this batch
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employee</TableHead>
                <TableHead>Department</TableHead>
                <TableHead className="text-right">Working Days</TableHead>
                <TableHead className="text-right">Paid Days</TableHead>
                <TableHead className="text-right">LOP</TableHead>
                <TableHead className="text-right">Gross</TableHead>
                <TableHead className="text-right">Deductions</TableHead>
                <TableHead className="text-right">Net Pay</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {payslips.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8">
                    {batch.status === 'DRAFT'
                      ? 'No payslips generated yet. Click "Process Payroll" to generate.'
                      : 'No payslips found'}
                  </TableCell>
                </TableRow>
              ) : (
                payslips.map((payslip) => (
                  <TableRow key={payslip.id}>
                    <TableCell>
                      <div>
                        <span className="font-medium">
                          {payslip.employee?.first_name} {payslip.employee?.last_name}
                        </span>
                        <br />
                        <span className="text-sm text-muted-foreground">
                          {payslip.employee?.employee_code}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {payslip.employee?.department?.department_name || '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {payslip.working_days}
                    </TableCell>
                    <TableCell className="text-right">{payslip.paid_days}</TableCell>
                    <TableCell className="text-right">
                      {payslip.lop_days > 0 ? (
                        <span className="text-destructive">{payslip.lop_days}</span>
                      ) : (
                        payslip.lop_days
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={payslip.gross_earnings} compact />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={payslip.total_deductions} compact />
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      <AmountDisplay amount={payslip.net_salary} compact />
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={STATUS_COLORS[payslip.status] || 'outline'}
                        className="text-xs"
                      >
                        {payslip.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/payroll/payslips/${payslip.id}`)}
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {batch.remarks && (
        <Card>
          <CardHeader>
            <CardTitle>Remarks</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{batch.remarks}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
