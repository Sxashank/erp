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
import { purchaseBillsApi, organizationsApi, vendorsApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Organization {
  id: string;
  code: string;
  name: string;
}

interface Vendor {
  id: string;
  code: string;
  name: string;
}

interface PurchaseBill {
  id: string;
  bill_number: string;
  vendor_invoice_number: string | null;
  bill_date: string;
  due_date: string;
  vendor_id: string;
  vendor_name: string | null;
  total_amount: number;
  balance_amount: number;
  status: string;
  payment_status: string;
  is_posted: boolean;
}

type PurchaseBillListParams = Parameters<typeof purchaseBillsApi.list>[0];

const statusLabels: Record<string, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  APPROVED: 'Approved',
  PARTIALLY_PAID: 'Partially Paid',
  PAID: 'Paid',
  CANCELLED: 'Cancelled',
};

const statusColors: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-800',
  SUBMITTED: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-blue-100 text-blue-800',
  PARTIALLY_PAID: 'bg-orange-100 text-orange-800',
  PAID: 'bg-green-100 text-green-800',
  CANCELLED: 'bg-red-100 text-red-800',
};

const paymentStatusLabels: Record<string, string> = {
  UNPAID: 'Unpaid',
  PARTIALLY_PAID: 'Partial',
  PAID: 'Paid',
};

const paymentStatusColors: Record<string, string> = {
  UNPAID: 'bg-red-100 text-red-800',
  PARTIALLY_PAID: 'bg-orange-100 text-orange-800',
  PAID: 'bg-green-100 text-green-800',
};

export function PurchaseBillList() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [bills, setBills] = useState<PurchaseBill[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [paymentStatusFilter, setPaymentStatusFilter] = useState<string>('all');
  const [vendorFilter, setVendorFilter] = useState<string>('all');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [billToDelete, setBillToDelete] = useState<PurchaseBill | null>(null);
  const [billToCancel, setBillToCancel] = useState<PurchaseBill | null>(null);
  const [cancelReason, setCancelReason] = useState('');
  const pageSize = 20;

  const loadOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ page: 1, page_size: 100 });
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

  const loadVendors = useCallback(async () => {
    if (!selectedOrgId) return;
    try {
      const response = await vendorsApi.getActive({ organization_id: selectedOrgId });
      setVendors(response.data || []);
    } catch (error) {
      logger.error('Failed to load vendors:', error);
    }
  }, [selectedOrgId]);

  const loadBills = useCallback(async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    try {
      const params: PurchaseBillListParams = {
        organization_id: selectedOrgId,
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
      if (paymentStatusFilter && paymentStatusFilter !== 'all') {
        params.payment_status = paymentStatusFilter;
      }
      if (vendorFilter && vendorFilter !== 'all') {
        params.vendor_id = vendorFilter;
      }
      if (fromDate) {
        params.from_date = fromDate;
      }
      if (toDate) {
        params.to_date = toDate;
      }
      const response = await purchaseBillsApi.list(params);
      setBills(response.data.items || []);
      setTotal(response.data.total || 0);
      setTotalPages(response.data.pages || 1);
    } catch (error) {
      logger.error('Failed to load purchase bills:', error);
      toast({
        title: 'Error',
        description: 'Failed to load purchase bills',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [
    fromDate,
    includeInactive,
    page,
    paymentStatusFilter,
    searchQuery,
    selectedOrgId,
    statusFilter,
    toDate,
    toast,
    vendorFilter,
  ]);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      loadVendors();
      loadBills();
    }
  }, [loadBills, loadVendors, selectedOrgId]);

  const handleSubmit = async (bill: PurchaseBill) => {
    try {
      await purchaseBillsApi.submit(bill.id);
      toast({
        title: 'Success',
        description: 'Purchase bill submitted for approval',
      });
      loadBills();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleApprove = async (bill: PurchaseBill) => {
    try {
      await purchaseBillsApi.approve(bill.id);
      toast({
        title: 'Success',
        description: 'Purchase bill approved successfully',
      });
      loadBills();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleCancel = async () => {
    if (!billToCancel || !cancelReason) return;
    try {
      await purchaseBillsApi.cancel(billToCancel.id, cancelReason);
      toast({
        title: 'Success',
        description: 'Purchase bill cancelled successfully',
      });
      loadBills();
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setCancelDialogOpen(false);
      setBillToCancel(null);
      setCancelReason('');
    }
  };

  const handleDelete = async () => {
    if (!billToDelete) return;
    try {
      await purchaseBillsApi.delete(billToDelete.id);
      toast({
        title: 'Success',
        description: 'Purchase bill deleted successfully',
      });
      loadBills();
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setDeleteDialogOpen(false);
      setBillToDelete(null);
    }
  };

  const isOverdue = (dueDate: string, status: string) => {
    if (status === 'PAID' || status === 'CANCELLED') return false;
    return new Date(dueDate) < new Date();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Purchase Bills"
        subtitle="Manage vendor invoices and purchase bills"
        actions={
          <Button onClick={() => navigate('/admin/ap-ar/purchase-bills/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Purchase Bill
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
                placeholder="Search by bill number, invoice number..."
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
                <SelectItem value="PARTIALLY_PAID">Partially Paid</SelectItem>
                <SelectItem value="PAID">Paid</SelectItem>
                <SelectItem value="CANCELLED">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-[180px]">
            <Select
              value={paymentStatusFilter}
              onValueChange={(value) => {
                setPaymentStatusFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Payment Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Payment Status</SelectItem>
                <SelectItem value="UNPAID">Unpaid</SelectItem>
                <SelectItem value="PARTIALLY_PAID">Partially Paid</SelectItem>
                <SelectItem value="PAID">Paid</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-[200px]">
            <Select
              value={vendorFilter}
              onValueChange={(value) => {
                setVendorFilter(value);
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Vendors" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Vendors</SelectItem>
                {vendors.map((vendor) => (
                  <SelectItem key={vendor.id} value={vendor.id}>
                    {vendor.name}
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
              <TableHead className="w-[120px]">Bill No.</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead>Vendor Invoice</TableHead>
              <TableHead className="w-[100px]">Bill Date</TableHead>
              <TableHead className="w-[100px]">Due Date</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead className="text-right">Balance</TableHead>
              <TableHead className="w-[100px]">Status</TableHead>
              <TableHead className="w-[80px]">Payment</TableHead>
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
            ) : bills.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center py-8">
                  No purchase bills found
                </TableCell>
              </TableRow>
            ) : (
              bills.map((bill) => (
                <TableRow key={bill.id}>
                  <TableCell className="font-medium">{bill.bill_number}</TableCell>
                  <TableCell>{bill.vendor_name || '-'}</TableCell>
                  <TableCell className="font-mono text-sm">
                    {bill.vendor_invoice_number || '-'}
                  </TableCell>
                  <TableCell><DateDisplay date={bill.bill_date} /></TableCell>
                  <TableCell>
                    <div className={isOverdue(bill.due_date, bill.status) ? 'text-red-600 font-medium' : ''}>
                      <DateDisplay date={bill.due_date} />
                      {isOverdue(bill.due_date, bill.status) && (
                        <span className="block text-xs">Overdue</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    <AmountDisplay amount={bill.total_amount} />
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    <AmountDisplay amount={bill.balance_amount} />
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={statusColors[bill.status] || 'bg-gray-100'}
                    >
                      {statusLabels[bill.status] || bill.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={paymentStatusColors[bill.payment_status] || 'bg-gray-100'}
                    >
                      {paymentStatusLabels[bill.payment_status] || bill.payment_status}
                    </Badge>
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
                          onClick={() => navigate(`/admin/ap-ar/purchase-bills/${bill.id}`)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View
                        </DropdownMenuItem>
                        {bill.status === 'DRAFT' && (
                          <>
                            <DropdownMenuItem
                              onClick={() => navigate(`/admin/ap-ar/purchase-bills/${bill.id}/edit`)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleSubmit(bill)}>
                              <Send className="mr-2 h-4 w-4" />
                              Submit
                            </DropdownMenuItem>
                          </>
                        )}
                        {bill.status === 'SUBMITTED' && (
                          <DropdownMenuItem onClick={() => handleApprove(bill)}>
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Approve
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        {bill.status !== 'CANCELLED' && bill.payment_status === 'UNPAID' && (
                          <DropdownMenuItem
                            onClick={() => {
                              setBillToCancel(bill);
                              setCancelDialogOpen(true);
                            }}
                            className="text-orange-600"
                          >
                            <XCircle className="mr-2 h-4 w-4" />
                            Cancel
                          </DropdownMenuItem>
                        )}
                        {bill.status === 'DRAFT' && (
                          <DropdownMenuItem
                            onClick={() => {
                              setBillToDelete(bill);
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
              {Math.min(page * pageSize, total)} of {total} bills
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
            <AlertDialogTitle>Delete Purchase Bill</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete bill &quot;{billToDelete?.bill_number}&quot;? This action
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
            <AlertDialogTitle>Cancel Purchase Bill</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel bill &quot;{billToCancel?.bill_number}&quot;?
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
              Cancel Bill
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
