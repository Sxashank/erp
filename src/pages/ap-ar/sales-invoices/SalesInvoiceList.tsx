import {
  Plus,
  Search,
  MoreHorizontal,
  Edit,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Eye,
  CheckCircle,
  Send,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { showErrorToast } from '@/lib/errorToast';
import { salesInvoicesApi, organizationsApi, customersApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Organization {
  id: string;
  code: string;
  name: string;
}

interface Customer {
  id: string;
  code: string;
  name: string;
}

interface SalesInvoice {
  id: string;
  invoiceNumber: string;
  invoiceDate: string;
  dueDate: string;
  customerId: string;
  customerName: string | null;
  totalAmount: number;
  balanceAmount: number;
  status: string;
  receiptStatus: string;
  eInvoiceStatus: string | null;
  isPosted: boolean;
}

type SalesInvoiceListParams = Parameters<typeof salesInvoicesApi.list>[0];

const statusLabels: Record<string, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  APPROVED: 'Approved',
  PARTIALLY_RECEIVED: 'Partially Received',
  RECEIVED: 'Received',
  CANCELLED: 'Cancelled',
};

const statusColors: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-800',
  SUBMITTED: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-blue-100 text-blue-800',
  PARTIALLY_RECEIVED: 'bg-orange-100 text-orange-800',
  RECEIVED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

const receiptStatusLabels: Record<string, string> = {
  UNRECEIVED: 'Unreceived',
  PARTIALLY_RECEIVED: 'Partial',
  RECEIVED: 'Received',
};

const receiptStatusColors: Record<string, string> = {
  UNRECEIVED: 'bg-red-100 text-red-800',
  PARTIALLY_RECEIVED: 'bg-orange-100 text-orange-800',
  RECEIVED: 'bg-green-100 text-green-800',
};

const eInvoiceStatusLabels: Record<string, string> = {
  NOT_APPLICABLE: 'N/A',
  PENDING: 'Pending',
  GENERATED: 'Generated',
  CANCELLED: 'Cancelled',
};

const eInvoiceStatusColors: Record<string, string> = {
  NOT_APPLICABLE: 'bg-gray-100 text-gray-600',
  PENDING: 'bg-yellow-100 text-yellow-800',
  GENERATED: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

export function SalesInvoiceList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [invoices, setInvoices] = useState<SalesInvoice[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [receiptStatusFilter, setReceiptStatusFilter] = useState<string>('all');
  const [customerFilter, setCustomerFilter] = useState<string>('all');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [invoiceToDelete, setInvoiceToDelete] = useState<SalesInvoice | null>(null);
  const [invoiceToCancel, setInvoiceToCancel] = useState<SalesInvoice | null>(null);
  const [cancelReason, setCancelReason] = useState('');
  const pageSize = 20;

  const loadOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ page: 1, pageSize: 100 });
      const orgs = response.data.items || [];
      setOrganizations(orgs);
      if (orgs.length > 0) {
        setSelectedOrgId(orgs[0].id);
      }
    } catch (error) {
      logger.error('Failed to load organizations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load organizations',
        variant: 'destructive',
      });
    }
  }, [toast]);

  const loadCustomers = useCallback(async () => {
    if (!selectedOrgId) return;
    try {
      const response = await customersApi.getActive({});
      setCustomers(response.data || []);
    } catch (error) {
      logger.error('Failed to load customers:', error);
    }
  }, [selectedOrgId]);

  const loadInvoices = useCallback(async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    try {
      const params: SalesInvoiceListParams = {
        page,
        page_size: pageSize,
        include_inactive: includeInactive,
      };
      if (searchQuery) {
        params.search = searchQuery;
      }
      if (statusFilter && statusFilter !== 'all') {
        params.status = statusFilter;
      }
      if (receiptStatusFilter && receiptStatusFilter !== 'all') {
        params.receipt_status = receiptStatusFilter;
      }
      if (customerFilter && customerFilter !== 'all') {
        params.customer_id = customerFilter;
      }
      if (fromDate) {
        params.from_date = fromDate;
      }
      if (toDate) {
        params.to_date = toDate;
      }
      const response = await salesInvoicesApi.list(params);
      setInvoices(response.data.items || []);
      setTotal(response.data.total || 0);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      logger.error('Failed to load sales invoices:', error);
      toast({
        title: 'Error',
        description: 'Failed to load sales invoices',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [
    customerFilter,
    fromDate,
    includeInactive,
    page,
    receiptStatusFilter,
    searchQuery,
    selectedOrgId,
    statusFilter,
    toDate,
    toast,
  ]);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      loadCustomers();
      loadInvoices();
    }
  }, [loadCustomers, loadInvoices, selectedOrgId]);

  const handleSubmit = async (invoice: SalesInvoice) => {
    try {
      await salesInvoicesApi.submit(invoice.id);
      toast({
        title: 'Success',
        description: 'Sales invoice submitted for approval',
      });
      loadInvoices();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleApprove = async (invoice: SalesInvoice) => {
    try {
      await salesInvoicesApi.approve(invoice.id);
      toast({
        title: 'Success',
        description: 'Sales invoice approved successfully',
      });
      loadInvoices();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleCancel = async () => {
    if (!invoiceToCancel || !cancelReason) return;
    try {
      await salesInvoicesApi.cancel(invoiceToCancel.id, cancelReason);
      toast({
        title: 'Success',
        description: 'Sales invoice cancelled successfully',
      });
      loadInvoices();
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setCancelDialogOpen(false);
      setInvoiceToCancel(null);
      setCancelReason('');
    }
  };

  const handleDelete = async () => {
    if (!invoiceToDelete) return;
    try {
      await salesInvoicesApi.delete(invoiceToDelete.id);
      toast({
        title: 'Success',
        description: 'Sales invoice deleted successfully',
      });
      loadInvoices();
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setDeleteDialogOpen(false);
      setInvoiceToDelete(null);
    }
  };

  const isOverdue = (dueDate: string, status: string) => {
    if (status === 'RECEIVED' || status === 'CANCELLED') return false;
    return new Date(dueDate) < new Date();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sales Invoices"
        subtitle="Manage customer invoices and sales billing"
        actions={
          <Button onClick={() => navigate('/admin/ap-ar/sales-invoices/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Sales Invoice
          </Button>
        }
      />

      {/* Filters */}
      <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[200px]">
            <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
              <SelectTrigger>
                <SelectValue placeholder="Select organization" />
              </SelectTrigger>
              <SelectContent>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>
                    {org.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="Search by invoice number..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="w-[180px]">
            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setStatusFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="SUBMITTED">Submitted</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="PARTIALLY_RECEIVED">Partially Received</SelectItem>
                <SelectItem value="RECEIVED">Received</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-[180px]">
            <Select
              value={receiptStatusFilter}
              onValueChange={(value) => {
                setReceiptStatusFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Receipt Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Receipt Status</SelectItem>
                <SelectItem value="UNRECEIVED">Unreceived</SelectItem>
                <SelectItem value="PARTIALLY_RECEIVED">Partially Received</SelectItem>
                <SelectItem value="RECEIVED">Received</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-[200px]">
            <Select
              value={customerFilter}
              onValueChange={(value) => {
                setCustomerFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Customers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Customers</SelectItem>
                {customers.map((customer) => (
                  <SelectItem key={customer.id} value={customer.id}>
                    {customer.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setPage(1);
              }}
              className="w-[140px]"
              placeholder="From Date"
            />
            <span className="text-slate-400">to</span>
            <Input
              type="date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setPage(1);
              }}
              className="w-[140px]"
              placeholder="To Date"
            />
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="includeInactive"
              checked={includeInactive}
              onCheckedChange={(checked) => {
                setIncludeInactive(checked === true);
                setPage(1);
              }}
            />
            <label htmlFor="includeInactive" className="text-sm text-slate-600">
              Include inactive
            </label>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-200 bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[120px]">Invoice No.</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead className="w-[100px]">Invoice Date</TableHead>
              <TableHead className="w-[100px]">Due Date</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead className="text-right">Balance</TableHead>
              <TableHead className="w-[100px]">Status</TableHead>
              <TableHead className="w-[80px]">Receipt</TableHead>
              <TableHead className="w-[80px]">E-Invoice</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center py-8">
                  Loading...
                </TableCell>
              </TableRow>
            ) : invoices.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center py-8">
                  No sales invoices found
                </TableCell>
              </TableRow>
            ) : (
              invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell className="font-medium">{invoice.invoiceNumber}</TableCell>
                  <TableCell>{invoice.customerName || '-'}</TableCell>
                  <TableCell><DateDisplay date={invoice.invoiceDate} /></TableCell>
                  <TableCell>
                    <div className={isOverdue(invoice.dueDate, invoice.status) ? 'text-red-600 font-medium' : ''}>
                      <DateDisplay date={invoice.dueDate} />
                      {isOverdue(invoice.dueDate, invoice.status) && (
                        <span className="block text-xs">Overdue</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    <AmountDisplay amount={invoice.totalAmount} />
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    <AmountDisplay amount={invoice.balanceAmount} />
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={statusColors[invoice.status] || 'bg-gray-100'}
                    >
                      {statusLabels[invoice.status] || invoice.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={receiptStatusColors[invoice.receiptStatus] || 'bg-gray-100'}
                    >
                      {receiptStatusLabels[invoice.receiptStatus] || invoice.receiptStatus}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {invoice.eInvoiceStatus && (
                      <Badge
                        variant="secondary"
                        className={eInvoiceStatusColors[invoice.eInvoiceStatus] || 'bg-gray-100'}
                      >
                        {eInvoiceStatusLabels[invoice.eInvoiceStatus] || invoice.eInvoiceStatus}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/ap-ar/sales-invoices/${invoice.id}`)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View
                        </DropdownMenuItem>
                        {invoice.status === 'DRAFT' && (
                          <>
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/ap-ar/sales-invoices/${invoice.id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleSubmit(invoice)}>
                              <Send className="mr-2 h-4 w-4" />
                              Submit
                            </DropdownMenuItem>
                          </>
                        )}
                        {invoice.status === 'SUBMITTED' && (
                          <DropdownMenuItem onClick={() => handleApprove(invoice)}>
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Approve
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        {invoice.status !== 'CANCELLED' && invoice.receiptStatus === 'UNRECEIVED' && (
                          <DropdownMenuItem
                            onClick={() => {
                              setInvoiceToCancel(invoice);
                              setCancelDialogOpen(true);
                            }}
                            className="text-orange-600"
                          >
                            <XCircle className="mr-2 h-4 w-4" />
                            Cancel
                          </DropdownMenuItem>
                        )}
                        {invoice.status === 'DRAFT' && (
                          <DropdownMenuItem
                            onClick={() => {
                              setInvoiceToDelete(invoice);
                              setDeleteDialogOpen(true);
                            }}
                            className="text-red-600"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3">
            <div className="text-sm text-slate-500">
              Showing {(page - 1) * pageSize + 1} to{' '}
              {Math.min(page * pageSize, total)} of {total} invoices
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-slate-600">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Sales Invoice</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete invoice &quot;{invoiceToDelete?.invoiceNumber}&quot;? This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Cancel Confirmation Dialog */}
      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Sales Invoice</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel invoice &quot;{invoiceToCancel?.invoiceNumber}&quot;?
              Please provide a reason for cancellation.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Input
              placeholder="Cancellation reason"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancel}
              disabled={!cancelReason}
              className="bg-orange-600 hover:bg-orange-700"
            >
              Cancel Invoice
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
