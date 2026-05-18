import { Check, CheckCircle, Edit, Loader2, Printer, Send, X, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { vouchersApi } from '@/services/api';
import type { Voucher } from '@/types';
import { VOUCHER_STATUSES } from '@/types';

import { logger } from "@/lib/logger";
export function VoucherView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [voucher, setVoucher] = useState<Voucher | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (id) {
      fetchVoucher(id);
    }
  }, [id]);

  const fetchVoucher = async (voucherId: string) => {
    try {
      setLoading(true);
      const response = await vouchersApi.get(voucherId);
      setVoucher(response.data);
    } catch (error) {
      logger.error('Failed to fetch voucher:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!id || !confirm('Are you sure you want to submit this voucher for approval?')) return;
    try {
      setActionLoading(true);
      await vouchersApi.submit(id);
      fetchVoucher(id);
    } catch (error) {
      logger.error('Failed to submit voucher:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!id || !confirm('Are you sure you want to approve this voucher?')) return;
    try {
      setActionLoading(true);
      await vouchersApi.approve(id);
      fetchVoucher(id);
    } catch (error) {
      logger.error('Failed to approve voucher:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!id) return;
    const reason = prompt('Please enter rejection reason:');
    if (!reason) return;
    try {
      setActionLoading(true);
      await vouchersApi.reject(id, reason);
      fetchVoucher(id);
    } catch (error) {
      logger.error('Failed to reject voucher:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePost = async () => {
    if (!id || !confirm('Are you sure you want to post this voucher to the ledger?')) return;
    try {
      setActionLoading(true);
      await vouchersApi.post(id);
      fetchVoucher(id);
    } catch (error) {
      logger.error('Failed to post voucher:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!id) return;
    const reason = prompt('Please enter cancellation reason:');
    if (!reason) return;
    try {
      setActionLoading(true);
      await vouchersApi.cancel(id, reason);
      fetchVoucher(id);
    } catch (error) {
      logger.error('Failed to cancel voucher:', error);
    } finally {
      setActionLoading(false);
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

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const formatDateTime = (dateString: string | undefined) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (!voucher) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-slate-500">Voucher not found</p>
        <Button variant="link" onClick={() => navigate('/admin/finance/vouchers')}>
          Go back to voucher list
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={voucher.voucher_number}
        subtitle={`${voucher.voucher_type_name} | ${formatDate(voucher.voucher_date)}`}
        breadcrumbs={[
          { label: 'Vouchers', to: '/admin/finance/vouchers' },
          { label: voucher.voucher_number },
        ]}
        actions={
          <div className="flex items-center gap-2">
            {getStatusBadge(voucher.status)}
            <Button variant="outline" size="sm">
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>

            {voucher.status === 'DRAFT' && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/admin/finance/vouchers/${id}/edit`)}
                >
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </Button>
                <Button size="sm" onClick={handleSubmit} disabled={actionLoading}>
                  <Send className="mr-2 h-4 w-4" />
                  Submit for Approval
                </Button>
              </>
            )}

            {voucher.status === 'PENDING_APPROVAL' && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReject}
                  disabled={actionLoading}
                  className="border-red-200 text-red-600 hover:bg-red-50"
                >
                  <XCircle className="mr-2 h-4 w-4" />
                  Reject
                </Button>
                <Button
                  size="sm"
                  onClick={handleApprove}
                  disabled={actionLoading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Approve
                </Button>
              </>
            )}

            {voucher.status === 'APPROVED' && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancel}
                  disabled={actionLoading}
                  className="border-red-200 text-red-600 hover:bg-red-50"
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handlePost}
                  disabled={actionLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Check className="mr-2 h-4 w-4" />
                  Post to Ledger
                </Button>
              </>
            )}

            {voucher.status === 'POSTED' && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                disabled={actionLoading}
                className="border-red-200 text-red-600 hover:bg-red-50"
              >
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Voucher Details</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-500">Voucher Number</p>
                <p className="font-medium">{voucher.voucher_number}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Voucher Date</p>
                <p className="font-medium"><DateDisplay date={voucher.voucher_date} /></p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Voucher Type</p>
                <p className="font-medium">{voucher.voucher_type_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Financial Year</p>
                <p className="font-medium">{voucher.financial_year_code}</p>
              </div>
              {voucher.reference_number && (
                <div>
                  <p className="text-sm text-slate-500">Reference Number</p>
                  <p className="font-medium">{voucher.reference_number}</p>
                </div>
              )}
              {voucher.unit_name && (
                <div>
                  <p className="text-sm text-slate-500">Unit</p>
                  <p className="font-medium">{voucher.unit_name}</p>
                </div>
              )}
            </div>
            {voucher.narration && (
              <div>
                <p className="text-sm text-slate-500">Narration</p>
                <p className="font-medium">{voucher.narration}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Status & Timeline</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-500">Status</p>
                <div className="mt-1">{getStatusBadge(voucher.status)}</div>
              </div>
              <div>
                <p className="text-sm text-slate-500">Created At</p>
                <p className="font-medium">{formatDateTime(voucher.created_at)}</p>
              </div>
              {voucher.submitted_at && (
                <div>
                  <p className="text-sm text-slate-500">Submitted At</p>
                  <p className="font-medium">{formatDateTime(voucher.submitted_at)}</p>
                </div>
              )}
              {voucher.approved_at && (
                <div>
                  <p className="text-sm text-slate-500">Approved At</p>
                  <p className="font-medium">{formatDateTime(voucher.approved_at)}</p>
                </div>
              )}
              {voucher.posted_at && (
                <div>
                  <p className="text-sm text-slate-500">Posted At</p>
                  <p className="font-medium">{formatDateTime(voucher.posted_at)}</p>
                </div>
              )}
              {voucher.cancelled_at && (
                <div>
                  <p className="text-sm text-slate-500">Cancelled At</p>
                  <p className="font-medium">{formatDateTime(voucher.cancelled_at)}</p>
                </div>
              )}
            </div>
            {voucher.rejection_reason && (
              <div>
                <p className="text-sm text-slate-500">Rejection Reason</p>
                <p className="font-medium text-red-600">{voucher.rejection_reason}</p>
              </div>
            )}
            {voucher.cancellation_reason && (
              <div>
                <p className="text-sm text-slate-500">Cancellation Reason</p>
                <p className="font-medium text-red-600">{voucher.cancellation_reason}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Voucher Lines</CardTitle>
          <CardDescription>Debit and credit entries</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>S.No</TableHead>
                <TableHead>Account Code</TableHead>
                <TableHead>Account Name</TableHead>
                <TableHead className="text-right">Debit</TableHead>
                <TableHead className="text-right">Credit</TableHead>
                <TableHead>Narration</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {voucher.lines?.map((line, index) => (
                <TableRow key={line.id || index}>
                  <TableCell>{index + 1}</TableCell>
                  <TableCell className="font-medium">{line.account_code}</TableCell>
                  <TableCell>{line.account_name}</TableCell>
                  <TableCell className="text-right">
                    {line.debit_amount > 0 ? formatAmount(line.debit_amount) : '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    {line.credit_amount > 0 ? formatAmount(line.credit_amount) : '-'}
                  </TableCell>
                  <TableCell>{line.narration || '-'}</TableCell>
                </TableRow>
              ))}
              <TableRow className="bg-slate-50 font-medium">
                <TableCell colSpan={3} className="text-right">
                  Total
                </TableCell>
                <TableCell className="text-right">{formatAmount(voucher.total_debit)}</TableCell>
                <TableCell className="text-right">{formatAmount(voucher.total_credit)}</TableCell>
                <TableCell></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
