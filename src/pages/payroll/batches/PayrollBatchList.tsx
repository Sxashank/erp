/**
 * Payroll Batch List Page
 */

import { Plus, Eye, Play, CheckCircle, Banknote, Search } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { PayrollConfirmDialog } from '@/components/payroll/PayrollConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type { PayrollBatch } from '@/services/payrollService';
import payrollService from '@/services/payrollService';
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

const ALL_STATUSES = '__all__';

type BatchAction = 'process' | 'approve' | 'paid';

const ACTION_COPY: Record<BatchAction, { title: string; description: string; confirmLabel: string }> = {
  process: {
    title: 'Process payroll batch?',
    description: 'This recalculates payroll for eligible employees using locked attendance and active salary setup.',
    confirmLabel: 'Process Payroll',
  },
  approve: {
    title: 'Approve payroll batch?',
    description: 'Approved payroll becomes available for bank payout export and GL posting.',
    confirmLabel: 'Approve Batch',
  },
  paid: {
    title: 'Mark payroll batch as paid?',
    description: 'This marks generated payslips as paid. Confirm only after salary payout is complete.',
    confirmLabel: 'Mark Paid',
  },
};

export default function PayrollBatchList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [batches, setBatches] = useState<PayrollBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [yearFilter, setYearFilter] = useState<string>(new Date().getFullYear().toString());
  const [statusFilter, setStatusFilter] = useState<string>(ALL_STATUSES);
  const [total, setTotal] = useState(0);
  const [confirmAction, setConfirmAction] = useState<{ batchId: string; action: BatchAction } | null>(null);
  const [actionBusy, setActionBusy] = useState(false);

  const organizationId = useRequiredActiveOrganizationId();

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  useEffect(() => {
    loadBatches();
  }, [yearFilter, statusFilter]);

  const loadBatches = async () => {
    try {
      setLoading(true);
      const response = await payrollService.listBatches({
        year: yearFilter ? parseInt(yearFilter) : undefined,
        status: statusFilter === ALL_STATUSES ? undefined : statusFilter,
      });
      setBatches(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load payroll batches',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const executeBatchAction = async () => {
    if (!confirmAction) return;
    try {
      setActionBusy(true);
      if (confirmAction.action === 'process') {
        await payrollService.processBatch(confirmAction.batchId);
        toast({
          title: 'Success',
          description: 'Payroll processing completed',
        });
      }
      if (confirmAction.action === 'approve') {
        await payrollService.approveBatch(confirmAction.batchId);
        toast({
          title: 'Success',
          description: 'Batch approved successfully',
        });
      }
      if (confirmAction.action === 'paid') {
        await payrollService.markBatchPaid(confirmAction.batchId);
        toast({
          title: 'Success',
          description: 'Batch marked as paid',
        });
      }
      setConfirmAction(null);
      await loadBatches();
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Payroll batch action failed'),
        variant: 'destructive',
      });
    } finally {
      setActionBusy(false);
    }
  };

  const filteredBatches = batches.filter((batch) =>
    batch.batchReference.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Payroll Batches"
        subtitle="Process and manage monthly payroll runs"
        actions={
          <Button onClick={() => navigate('/admin/payroll/batches/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Batch
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col justify-between gap-4 md:flex-row">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground" />
              <Input
                placeholder="Search batches..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Select value={yearFilter} onValueChange={setYearFilter}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Year" />
                </SelectTrigger>
                <SelectContent>
                  {years.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_STATUSES}>All Status</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="PROCESSING">Processing</SelectItem>
                  <SelectItem value="PROCESSED">Processed</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="PAID">Paid</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Reference</TableHead>
                <TableHead>Period</TableHead>
                <TableHead className="text-right">Employees</TableHead>
                <TableHead className="text-right">Gross</TableHead>
                <TableHead className="text-right">Deductions</TableHead>
                <TableHead className="text-right">Net Pay</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredBatches.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center">
                    No batches found
                  </TableCell>
                </TableRow>
              ) : (
                filteredBatches.map((batch) => (
                  <TableRow key={batch.id}>
                    <TableCell className="font-mono">{batch.batchReference}</TableCell>
                    <TableCell>
                      {MONTHS[batch.payrollMonth - 1]} {batch.payrollYear}
                    </TableCell>
                    <TableCell className="text-right">{batch.totalEmployees}</TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={batch.totalGross} />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={batch.totalDeductions} />
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      <AmountDisplay amount={batch.totalNet} />
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_COLORS[batch.status] || 'outline'}>
                        {batch.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/admin/payroll/batches/${batch.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {batch.status === 'DRAFT' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setConfirmAction({ batchId: batch.id, action: 'process' })}
                            title="Process Payroll"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                        {batch.status === 'PROCESSED' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setConfirmAction({ batchId: batch.id, action: 'approve' })}
                            title="Approve"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
                        {batch.status === 'APPROVED' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setConfirmAction({ batchId: batch.id, action: 'paid' })}
                            title="Mark as Paid"
                          >
                            <Banknote className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <PayrollConfirmDialog
        open={Boolean(confirmAction)}
        title={confirmAction ? ACTION_COPY[confirmAction.action].title : ''}
        description={confirmAction ? ACTION_COPY[confirmAction.action].description : ''}
        confirmLabel={confirmAction ? ACTION_COPY[confirmAction.action].confirmLabel : 'Confirm'}
        busy={actionBusy}
        onOpenChange={(open) => {
          if (!open && !actionBusy) setConfirmAction(null);
        }}
        onConfirm={executeBatchAction}
      />
    </div>
  );
}
