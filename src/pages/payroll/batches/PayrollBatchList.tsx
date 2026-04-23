/**
 * Payroll Batch List Page
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, Play, CheckCircle, Banknote, Search } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { AmountDisplay } from '@/components/common/AmountDisplay';
import payrollService, { PayrollBatch } from '@/services/payrollService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  DRAFT: 'outline',
  PROCESSING: 'secondary',
  PROCESSED: 'default',
  APPROVED: 'default',
  PAID: 'default',
  CANCELLED: 'destructive',
};

export default function PayrollBatchList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [batches, setBatches] = useState<PayrollBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [yearFilter, setYearFilter] = useState<string>(new Date().getFullYear().toString());
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [total, setTotal] = useState(0);

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
        organization_id: organizationId,
        year: yearFilter ? parseInt(yearFilter) : undefined,
        status: statusFilter || undefined,
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

  const handleProcess = async (id: string) => {
    if (!confirm('Start processing payroll for this batch?')) return;

    try {
      await payrollService.processBatch(id);
      toast({
        title: 'Success',
        description: 'Payroll processing started',
      });
      loadBatches();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to process batch',
        variant: 'destructive',
      });
    }
  };

  const handleApprove = async (id: string) => {
    if (!confirm('Approve this payroll batch?')) return;

    try {
      await payrollService.approveBatch(id);
      toast({
        title: 'Success',
        description: 'Batch approved successfully',
      });
      loadBatches();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to approve batch',
        variant: 'destructive',
      });
    }
  };

  const handleMarkPaid = async (id: string) => {
    if (!confirm('Mark this batch as paid?')) return;

    try {
      await payrollService.markBatchPaid(id);
      toast({
        title: 'Success',
        description: 'Batch marked as paid',
      });
      loadBatches();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to mark as paid',
        variant: 'destructive',
      });
    }
  };

  const filteredBatches = batches.filter((batch) =>
    batch.batch_reference.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Payroll Batches"
        subtitle="Process and manage monthly payroll runs"
        actions={
          <Button onClick={() => navigate('/payroll/batches/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Batch
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row gap-4 justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
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
                  <SelectItem value="">All Status</SelectItem>
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
                  <TableCell colSpan={8} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredBatches.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    No batches found
                  </TableCell>
                </TableRow>
              ) : (
                filteredBatches.map((batch) => (
                  <TableRow key={batch.id}>
                    <TableCell className="font-mono">
                      {batch.batch_reference}
                    </TableCell>
                    <TableCell>
                      {MONTHS[batch.payroll_month - 1]} {batch.payroll_year}
                    </TableCell>
                    <TableCell className="text-right">
                      {batch.total_employees}
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={batch.total_gross} />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={batch.total_deductions} />
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      <AmountDisplay amount={batch.total_net} />
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
                          onClick={() => navigate(`/payroll/batches/${batch.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        {batch.status === 'DRAFT' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleProcess(batch.id)}
                            title="Process Payroll"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                        {batch.status === 'PROCESSED' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleApprove(batch.id)}
                            title="Approve"
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
                        {batch.status === 'APPROVED' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleMarkPaid(batch.id)}
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
    </div>
  );
}
