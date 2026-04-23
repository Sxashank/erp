import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Edit,
  Trash2,
  Check,
  X,
  Send,
  CreditCard,
  Banknote,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { paymentsApi, organizationsApi, vendorsApi, customersApi } from '@/services/api';

interface Payment {
  id: string;
  payment_number: string;
  payment_date: string;
  payment_type: string;
  party_type: string;
  party_name: string | null;
  payment_mode: string;
  amount: number;
  net_amount: number;
  status: string;
  cheque_status: string | null;
  is_posted: boolean;
  created_at: string;
}

const PAYMENT_TYPES = [
  { value: 'VENDOR_PAYMENT', label: 'Vendor Payment' },
  { value: 'CUSTOMER_RECEIPT', label: 'Customer Receipt' },
  { value: 'ADVANCE_PAYMENT', label: 'Advance Payment' },
  { value: 'ADVANCE_RECEIPT', label: 'Advance Receipt' },
  { value: 'REFUND_PAYMENT', label: 'Refund Payment' },
  { value: 'REFUND_RECEIPT', label: 'Refund Receipt' },
];

const PAYMENT_MODES = [
  { value: 'CASH', label: 'Cash' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'NEFT', label: 'NEFT' },
  { value: 'RTGS', label: 'RTGS' },
  { value: 'IMPS', label: 'IMPS' },
  { value: 'UPI', label: 'UPI' },
  { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
];

export function PaymentList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();

  const [payments, setPayments] = useState<Payment[]>([]);
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [vendors, setVendors] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Filters
  const [selectedOrg, setSelectedOrg] = useState(searchParams.get('org') || '');
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'all');
  const [paymentTypeFilter, setPaymentTypeFilter] = useState(searchParams.get('payment_type') || 'all');
  const [partyTypeFilter, setPartyTypeFilter] = useState(searchParams.get('party_type') || 'all');
  const [vendorFilter, setVendorFilter] = useState(searchParams.get('vendor_id') || 'all');
  const [customerFilter, setCustomerFilter] = useState(searchParams.get('customer_id') || 'all');
  const [fromDate, setFromDate] = useState(searchParams.get('from_date') || '');
  const [toDate, setToDate] = useState(searchParams.get('to_date') || '');

  // Dialogs
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [cancellationReason, setCancellationReason] = useState('');

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrg) {
      loadPayments();
      loadVendors();
      loadCustomers();
    }
  }, [selectedOrg, search, statusFilter, paymentTypeFilter, partyTypeFilter, vendorFilter, customerFilter, fromDate, toDate]);

  const loadOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ include_inactive: false });
      setOrganizations(response.data.items || []);
      if (!selectedOrg && response.data.items?.length > 0) {
        setSelectedOrg(response.data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to load organizations:', error);
    }
  };

  const loadVendors = async () => {
    if (!selectedOrg) return;
    try {
      const response = await vendorsApi.getActive({ organization_id: selectedOrg });
      setVendors(response.data || []);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    }
  };

  const loadCustomers = async () => {
    if (!selectedOrg) return;
    try {
      const response = await customersApi.getActive({ organization_id: selectedOrg });
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Failed to load customers:', error);
    }
  };

  const loadPayments = async () => {
    if (!selectedOrg) return;
    setLoading(true);
    try {
      const params: any = {
        organization_id: selectedOrg,
        limit: 100,
      };
      if (search) params.search = search;
      if (statusFilter !== 'all') params.status = statusFilter;
      if (paymentTypeFilter !== 'all') params.payment_type = paymentTypeFilter;
      if (partyTypeFilter !== 'all') params.party_type = partyTypeFilter;
      if (vendorFilter !== 'all') params.vendor_id = vendorFilter;
      if (customerFilter !== 'all') params.customer_id = customerFilter;
      if (fromDate) params.from_date = fromDate;
      if (toDate) params.to_date = toDate;

      const response = await paymentsApi.list(params);
      setPayments(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load payments:', error);
      toast({
        title: 'Error',
        description: 'Failed to load payments',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (payment: Payment) => {
    try {
      await paymentsApi.submit(payment.id);
      toast({ title: 'Success', description: 'Payment submitted for approval' });
      loadPayments();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to submit payment',
        variant: 'destructive',
      });
    }
  };

  const handleApprove = async (payment: Payment) => {
    try {
      await paymentsApi.approve(payment.id);
      toast({ title: 'Success', description: 'Payment approved and posted' });
      loadPayments();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to approve payment',
        variant: 'destructive',
      });
    }
  };

  const handleCancel = async () => {
    if (!selectedPayment || !cancellationReason.trim()) return;
    try {
      await paymentsApi.cancel(selectedPayment.id, cancellationReason);
      toast({ title: 'Success', description: 'Payment cancelled' });
      setCancelDialogOpen(false);
      setCancellationReason('');
      setSelectedPayment(null);
      loadPayments();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to cancel payment',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async () => {
    if (!selectedPayment) return;
    try {
      await paymentsApi.delete(selectedPayment.id);
      toast({ title: 'Success', description: 'Payment deleted' });
      setDeleteDialogOpen(false);
      setSelectedPayment(null);
      loadPayments();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete payment',
        variant: 'destructive',
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      POSTED: 'bg-green-100 text-green-800',
      CANCELLED: 'bg-red-100 text-red-800',
    };
    return <Badge className={styles[status] || 'bg-gray-100'}>{status}</Badge>;
  };

  const getPaymentTypeLabel = (type: string) => {
    return PAYMENT_TYPES.find(t => t.value === type)?.label || type;
  };

  const getPaymentModeLabel = (mode: string) => {
    return PAYMENT_MODES.find(m => m.value === mode)?.label || mode;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payments & Receipts"
        subtitle="Manage vendor payments and customer receipts"
        actions={
          <div className="flex gap-2">
            <Button asChild variant="outline">
              <Link to="/admin/ap-ar/payments/new?type=CUSTOMER_RECEIPT">
                <Banknote className="mr-2 h-4 w-4" />
                New Receipt
              </Link>
            </Button>
            <Button asChild>
              <Link to="/admin/ap-ar/payments/new?type=VENDOR_PAYMENT">
                <Plus className="mr-2 h-4 w-4" />
                New Payment
              </Link>
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-1 gap-2">
              <Select value={selectedOrg} onValueChange={setSelectedOrg}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select Organization" />
                </SelectTrigger>
                <SelectContent>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search payments..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <Tabs value={statusFilter} onValueChange={setStatusFilter}>
              <TabsList>
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="DRAFT">Draft</TabsTrigger>
                <TabsTrigger value="SUBMITTED">Pending</TabsTrigger>
                <TabsTrigger value="POSTED">Posted</TabsTrigger>
                <TabsTrigger value="CANCELLED">Cancelled</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>

        <CardContent className="pb-3">
          <div className="flex flex-wrap gap-2 mb-4">
            <Select value={paymentTypeFilter} onValueChange={setPaymentTypeFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Payment Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {PAYMENT_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={partyTypeFilter} onValueChange={setPartyTypeFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Party Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Parties</SelectItem>
                <SelectItem value="VENDOR">Vendors</SelectItem>
                <SelectItem value="CUSTOMER">Customers</SelectItem>
              </SelectContent>
            </Select>

            {partyTypeFilter !== 'CUSTOMER' && (
              <Select value={vendorFilter} onValueChange={setVendorFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select Vendor" />
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
            )}

            {partyTypeFilter !== 'VENDOR' && (
              <Select value={customerFilter} onValueChange={setCustomerFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select Customer" />
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
            )}

            <Input
              type="date"
              placeholder="From Date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="w-[150px]"
            />
            <Input
              type="date"
              placeholder="To Date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="w-[150px]"
            />
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Number</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Party</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[80px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      Loading...
                    </TableCell>
                  </TableRow>
                ) : payments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
                      No payments found
                    </TableCell>
                  </TableRow>
                ) : (
                  payments.map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell className="font-medium">
                        <Link
                          to={`/admin/ap-ar/payments/${payment.id}`}
                          className="text-blue-600 hover:underline"
                        >
                          {payment.payment_number}
                        </Link>
                      </TableCell>
                      <TableCell>
                        {format(new Date(payment.payment_date), 'dd MMM yyyy')}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {getPaymentTypeLabel(payment.payment_type)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span>{payment.party_name || '-'}</span>
                          <span className="text-xs text-muted-foreground">
                            {payment.party_type}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{getPaymentModeLabel(payment.payment_mode)}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(payment.net_amount)}
                      </TableCell>
                      <TableCell>{getStatusBadge(payment.status)}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                              <Link to={`/admin/ap-ar/payments/${payment.id}`}>
                                <Eye className="mr-2 h-4 w-4" />
                                View
                              </Link>
                            </DropdownMenuItem>
                            {payment.status === 'DRAFT' && (
                              <>
                                <DropdownMenuItem asChild>
                                  <Link to={`/admin/ap-ar/payments/${payment.id}/edit`}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    Edit
                                  </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleSubmit(payment)}>
                                  <Send className="mr-2 h-4 w-4" />
                                  Submit
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-red-600"
                                  onClick={() => {
                                    setSelectedPayment(payment);
                                    setDeleteDialogOpen(true);
                                  }}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </>
                            )}
                            {payment.status === 'SUBMITTED' && (
                              <>
                                <DropdownMenuItem onClick={() => handleApprove(payment)}>
                                  <Check className="mr-2 h-4 w-4" />
                                  Approve
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  className="text-red-600"
                                  onClick={() => {
                                    setSelectedPayment(payment);
                                    setCancelDialogOpen(true);
                                  }}
                                >
                                  <X className="mr-2 h-4 w-4" />
                                  Cancel
                                </DropdownMenuItem>
                              </>
                            )}
                            {payment.status === 'POSTED' && (
                              <DropdownMenuItem
                                className="text-red-600"
                                onClick={() => {
                                  setSelectedPayment(payment);
                                  setCancelDialogOpen(true);
                                }}
                              >
                                <X className="mr-2 h-4 w-4" />
                                Cancel
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
          </div>

          <div className="flex items-center justify-between mt-4">
            <p className="text-sm text-muted-foreground">
              Showing {payments.length} of {total} payments
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Payment</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete payment {selectedPayment?.payment_number}?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Cancel Dialog */}
      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Payment</AlertDialogTitle>
            <AlertDialogDescription>
              Please provide a reason for cancelling payment {selectedPayment?.payment_number}.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Label htmlFor="reason">Cancellation Reason</Label>
            <Textarea
              id="reason"
              value={cancellationReason}
              onChange={(e) => setCancellationReason(e.target.value)}
              placeholder="Enter reason for cancellation..."
              className="mt-2"
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setCancellationReason('')}>
              Back
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancel}
              disabled={!cancellationReason.trim()}
              className="bg-red-600"
            >
              Cancel Payment
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
