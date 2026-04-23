import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Check,
  CheckCircle,
  Edit,
  Eye,
  FileText,
  MoreHorizontal,
  Plus,
  Send,
  Trash2,
  X,
  XCircle,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { vouchersApi, organizationsApi } from '@/services/api';
import type { Voucher, Organization, PaginatedResponse } from '@/types';
import { VOUCHER_STATUSES } from '@/types';

export function VoucherList() {
  const navigate = useNavigate();
  const [vouchers, setVouchers] = useState<Voucher[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, total: 0, totalPages: 0 });
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchVouchers();
    }
  }, [selectedOrgId, selectedStatus, activeTab]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchVouchers = async (page = 1) => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const params: any = {
        organization_id: selectedOrgId,
        page,
        page_size: 20,
        include_inactive: true,
      };

      if (activeTab === 'pending') {
        params.status = 'PENDING_APPROVAL';
      } else if (selectedStatus && selectedStatus !== 'all') {
        params.status = selectedStatus;
      }

      const response = await vouchersApi.list(params);
      const data: PaginatedResponse<Voucher> = response.data;
      setVouchers(data.items);
      setPagination({ page: data.page, total: data.total, totalPages: data.total_pages });
    } catch (error) {
      console.error('Failed to fetch vouchers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this voucher?')) return;
    try {
      await vouchersApi.delete(id);
      fetchVouchers(pagination.page);
    } catch (error) {
      console.error('Failed to delete voucher:', error);
    }
  };

  const handleSubmit = async (id: string) => {
    if (!confirm('Are you sure you want to submit this voucher for approval?')) return;
    try {
      await vouchersApi.submit(id);
      fetchVouchers(pagination.page);
    } catch (error) {
      console.error('Failed to submit voucher:', error);
    }
  };

  const handleApprove = async (id: string) => {
    if (!confirm('Are you sure you want to approve this voucher?')) return;
    try {
      await vouchersApi.approve(id);
      fetchVouchers(pagination.page);
    } catch (error) {
      console.error('Failed to approve voucher:', error);
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt('Please enter rejection reason:');
    if (!reason) return;
    try {
      await vouchersApi.reject(id, reason);
      fetchVouchers(pagination.page);
    } catch (error) {
      console.error('Failed to reject voucher:', error);
    }
  };

  const handlePost = async (id: string) => {
    if (!confirm('Are you sure you want to post this voucher to the ledger?')) return;
    try {
      await vouchersApi.post(id);
      fetchVouchers(pagination.page);
    } catch (error) {
      console.error('Failed to post voucher:', error);
    }
  };

  const handleCancel = async (id: string) => {
    const reason = prompt('Please enter cancellation reason:');
    if (!reason) return;
    try {
      await vouchersApi.cancel(id, reason);
      fetchVouchers(pagination.page);
    } catch (error) {
      console.error('Failed to cancel voucher:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = VOUCHER_STATUSES.find((s) => s.value === status);
    return statusConfig ? (
      <Badge className={`${statusConfig.color} hover:${statusConfig.color}`}>
        {statusConfig.label}
      </Badge>
    ) : (
      <Badge>{status}</Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const renderVoucherTable = () => (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Voucher No.</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Narration</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[70px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {vouchers.map((voucher) => (
            <TableRow key={voucher.id}>
              <TableCell className="font-medium">{voucher.voucher_number}</TableCell>
              <TableCell>{formatDate(voucher.voucher_date)}</TableCell>
              <TableCell>
                <Badge variant="outline">{voucher.voucher_type_name || voucher.voucher_type_code}</Badge>
              </TableCell>
              <TableCell className="max-w-[200px] truncate">
                {voucher.narration || '-'}
              </TableCell>
              <TableCell className="text-right">{formatAmount(voucher.total_debit)}</TableCell>
              <TableCell>{getStatusBadge(voucher.status)}</TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={() => navigate(`/admin/finance/vouchers/${voucher.id}`)}
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      View
                    </DropdownMenuItem>

                    {voucher.status === 'DRAFT' && (
                      <>
                        <DropdownMenuItem
                          onClick={() => navigate(`/admin/finance/vouchers/${voucher.id}/edit`)}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleSubmit(voucher.id)}>
                          <Send className="mr-2 h-4 w-4" />
                          Submit for Approval
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDelete(voucher.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </>
                    )}

                    {voucher.status === 'PENDING_APPROVAL' && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleApprove(voucher.id)}
                          className="text-green-600"
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Approve
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => handleReject(voucher.id)}
                          className="text-red-600"
                        >
                          <XCircle className="mr-2 h-4 w-4" />
                          Reject
                        </DropdownMenuItem>
                      </>
                    )}

                    {voucher.status === 'APPROVED' && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handlePost(voucher.id)}
                          className="text-blue-600"
                        >
                          <Check className="mr-2 h-4 w-4" />
                          Post to Ledger
                        </DropdownMenuItem>
                      </>
                    )}

                    {(voucher.status === 'POSTED' || voucher.status === 'APPROVED') && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleCancel(voucher.id)}
                          className="text-red-600"
                        >
                          <X className="mr-2 h-4 w-4" />
                          Cancel
                        </DropdownMenuItem>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {pagination.totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-slate-500">
            Showing {vouchers.length} of {pagination.total} vouchers
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page <= 1}
              onClick={() => fetchVouchers(pagination.page - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page >= pagination.totalPages}
              onClick={() => fetchVouchers(pagination.page + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vouchers"
        subtitle="Create and manage accounting vouchers"
        actions={
          <Button onClick={() => navigate('/admin/finance/vouchers/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Create Voucher
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>All Vouchers</CardTitle>
            <div className="flex items-center gap-4">
              {activeTab === 'all' && (
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="All Statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    {VOUCHER_STATUSES.map((status) => (
                      <SelectItem key={status.value} value={status.value}>
                        {status.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[250px]">
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
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="all">All Vouchers</TabsTrigger>
              <TabsTrigger value="pending">Pending Approval</TabsTrigger>
            </TabsList>
            <TabsContent value="all">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-sm text-slate-500">Loading...</p>
                </div>
              ) : vouchers.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <FileText className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No vouchers found</p>
                  <Button variant="link" onClick={() => navigate('/admin/finance/vouchers/new')}>
                    Create your first voucher
                  </Button>
                </div>
              ) : (
                renderVoucherTable()
              )}
            </TabsContent>
            <TabsContent value="pending">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-sm text-slate-500">Loading...</p>
                </div>
              ) : vouchers.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <CheckCircle className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No vouchers pending approval</p>
                </div>
              ) : (
                renderVoucherTable()
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
