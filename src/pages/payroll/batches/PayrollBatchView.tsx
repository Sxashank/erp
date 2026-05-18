/**
 * Payroll Batch View Page
 */

import { Play, CheckCircle, Banknote, FileText, Users, Download, Send } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import type { PayrollBatch, Payslip } from '@/services/payrollService';
import payrollService from '@/services/payrollService';

import { logger } from "@/lib/logger";
import { getErrorMessage } from "@/lib/errorMessage";
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
  const [confirmAction, setConfirmAction] = useState<'process' | 'approve' | 'paid' | null>(null);
  const [paymentReference, setPaymentReference] = useState('');
  const [glDialogOpen, setGlDialogOpen] = useState(false);
  const [glForm, setGlForm] = useState({
    salary_expense_account_id: '',
    net_salary_payable_account_id: '',
    pf_payable_account_id: '',
    esi_payable_account_id: '',
    pt_payable_account_id: '',
    tds_payable_account_id: '',
    other_deductions_payable_account_id: '',
    employer_contribution_expense_account_id: '',
  });

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
      navigate('/admin/payroll/batches');
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
      logger.error('Failed to load payslips:', error);
    }
  };

  const handleProcess = async () => {
    if (!id) return;

    try {
      setProcessing(true);
      await payrollService.processBatch(id);
      toast({
        title: 'Success',
        description: 'Payroll processing completed',
      });
      loadBatch(id);
      loadPayslips(id);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to process batch'),
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleApprove = async () => {
    if (!id) return;

    try {
      setProcessing(true);
      await payrollService.approveBatch(id);
      toast({
        title: 'Success',
        description: 'Batch approved successfully',
      });
      loadBatch(id);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to approve batch'),
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleMarkPaid = async () => {
    if (!id) return;
    const reference = paymentReference.trim();
    if (!reference) {
      toast({
        title: 'Payment reference required',
        description: 'Enter the NEFT batch or bank upload reference before marking payroll paid',
        variant: 'destructive',
      });
      return;
    }

    try {
      setProcessing(true);
      await payrollService.markBatchPaid(id, reference);
      toast({
        title: 'Success',
        description: 'Batch marked as paid',
      });
      loadBatch(id);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to mark as paid'),
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleConfirmedAction = async () => {
    const action = confirmAction;
    setConfirmAction(null);
    if (action === 'process') await handleProcess();
    if (action === 'approve') await handleApprove();
    if (action === 'paid') await handleMarkPaid();
  };

  const handleExportBankFile = async () => {
    if (!id) return;
    try {
      const file = await payrollService.exportBankFile(id);
      const blob = new Blob([file.file_content], { type: 'text/csv;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = file.file_name;
      link.click();
      window.URL.revokeObjectURL(url);
      toast({
        title: 'Bank file generated',
        description: `${file.record_count} records exported for salary upload`,
      });
    } catch (error: unknown) {
      toast({
        title: 'Export failed',
        description: getErrorMessage(error, 'Failed to generate bank file'),
        variant: 'destructive',
      });
    }
  };

  const handlePostGL = async () => {
    if (!id) return;
    try {
      setProcessing(true);
      const result = await payrollService.postBatchToGL(id, {
        ...glForm,
        pf_payable_account_id: glForm.pf_payable_account_id || undefined,
        esi_payable_account_id: glForm.esi_payable_account_id || undefined,
        pt_payable_account_id: glForm.pt_payable_account_id || undefined,
        tds_payable_account_id: glForm.tds_payable_account_id || undefined,
        other_deductions_payable_account_id: glForm.other_deductions_payable_account_id || undefined,
        employer_contribution_expense_account_id:
          glForm.employer_contribution_expense_account_id || undefined,
      });
      setGlDialogOpen(false);
      toast({
        title: 'GL posted',
        description: `Voucher ${result.voucher_number || result.source_reference} created`,
      });
    } catch (error: unknown) {
      toast({
        title: 'GL posting failed',
        description: getErrorMessage(error, 'Failed to post payroll to GL'),
        variant: 'destructive',
      });
    } finally {
      setProcessing(false);
    }
  };

  if (loading || !batch) {
    return (
      <div className="container mx-auto py-6">
        <div className="py-8 text-center">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title={batch.batch_reference}
        subtitle={`${MONTHS[batch.payroll_month - 1]} ${batch.payroll_year}`}
        breadcrumbs={[
          { label: 'Payroll Batches', to: '/admin/payroll/batches' },
          { label: batch.batch_reference },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_COLORS[batch.status] || 'outline'}>{batch.status}</Badge>
            {batch.status === 'DRAFT' && (
              <Button onClick={() => setConfirmAction('process')} disabled={processing}>
                <Play className="mr-2 h-4 w-4" />
                {processing ? 'Processing...' : 'Process Payroll'}
              </Button>
            )}
            {batch.status === 'PROCESSED' && (
              <Button onClick={() => setConfirmAction('approve')} disabled={processing}>
                <CheckCircle className="mr-2 h-4 w-4" />
                {processing ? 'Approving...' : 'Approve Batch'}
              </Button>
            )}
            {['APPROVED', 'PAID'].includes(batch.status) && (
              <Button variant="outline" onClick={handleExportBankFile} disabled={processing}>
                <Download className="mr-2 h-4 w-4" />
                Bank File
              </Button>
            )}
            {['APPROVED', 'PAID'].includes(batch.status) && (
              <Button variant="outline" onClick={() => setGlDialogOpen(true)} disabled={processing}>
                <Send className="mr-2 h-4 w-4" />
                Post GL
              </Button>
            )}
            {batch.status === 'APPROVED' && (
              <Button onClick={() => setConfirmAction('paid')} disabled={processing}>
                <Banknote className="mr-2 h-4 w-4" />
                {processing ? 'Processing...' : 'Mark as Paid'}
              </Button>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Employees
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Users className="mr-2 h-4 w-4 text-muted-foreground" />
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
            <CardTitle className="text-sm font-medium text-muted-foreground">Net Payable</CardTitle>
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
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Payslips</CardTitle>
              <CardDescription>Individual employee payslips for this batch</CardDescription>
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
                  <TableCell colSpan={10} className="py-8 text-center">
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
                    <TableCell>{payslip.employee?.department?.department_name || '-'}</TableCell>
                    <TableCell className="text-right">{payslip.working_days}</TableCell>
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
                        onClick={() => navigate(`/admin/payroll/payslips/${payslip.id}`)}
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

      <Dialog open={confirmAction !== null} onOpenChange={(open) => !open && setConfirmAction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {confirmAction === 'process' && 'Process payroll batch'}
              {confirmAction === 'approve' && 'Approve payroll batch'}
              {confirmAction === 'paid' && 'Mark payroll as paid'}
            </DialogTitle>
            <DialogDescription>
              This action updates the batch lifecycle and is recorded for payroll audit.
            </DialogDescription>
          </DialogHeader>
          {confirmAction === 'paid' && (
            <div className="space-y-2">
              <Label htmlFor="payment-reference">Payment reference</Label>
              <Input
                id="payment-reference"
                value={paymentReference}
                onChange={(event) => setPaymentReference(event.target.value)}
                placeholder="NEFT batch / bank upload reference"
              />
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmAction(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmedAction}
              disabled={processing || (confirmAction === 'paid' && !paymentReference.trim())}
            >
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={glDialogOpen} onOpenChange={setGlDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Post Payroll to GL</DialogTitle>
            <DialogDescription>
              Enter finance account IDs for the balanced payroll voucher.
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {[
              ['salary_expense_account_id', 'Salary expense account'],
              ['net_salary_payable_account_id', 'Net salary payable account'],
              ['pf_payable_account_id', 'PF payable account'],
              ['esi_payable_account_id', 'ESI payable account'],
              ['pt_payable_account_id', 'PT payable account'],
              ['tds_payable_account_id', 'TDS payable account'],
              ['other_deductions_payable_account_id', 'Other deductions payable account'],
              ['employer_contribution_expense_account_id', 'Employer contribution expense account'],
            ].map(([field, label]) => (
              <div key={field} className="space-y-2">
                <Label htmlFor={field}>{label}</Label>
                <Input
                  id={field}
                  value={glForm[field as keyof typeof glForm]}
                  onChange={(event) =>
                    setGlForm((current) => ({ ...current, [field]: event.target.value }))
                  }
                  placeholder="Account UUID"
                />
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setGlDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handlePostGL}
              disabled={
                processing || !glForm.salary_expense_account_id || !glForm.net_salary_payable_account_id
              }
            >
              Post GL
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
