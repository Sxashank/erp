import { Edit, CheckCircle, XCircle, Clock, Download, Printer, User, FileText } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { vouchersApi } from '@/services/api';

import { logger } from '@/lib/logger';
interface PostingDetail {
  id: string;
  postingId: string;
  description: string;
  postingDate: string;
  period: string;
  reference?: string | null;
  narration?: string | null;
  status: string;
  createdBy: string;
  createdAt: string;
  approvedBy?: string | null;
  approvedAt?: string | null;
  postedAt?: string | null;
  entries: {
    id: string;
    accountCode: string;
    accountName: string;
    description?: string | null;
    costCenter?: string | null;
    debit: number;
    credit: number;
  }[];
  history: { action: string; by: string; at: string; remarks?: string | null }[];
}

interface VoucherLineDto {
  id: string;
  accountCode?: string | null;
  accountName?: string | null;
  narration?: string | null;
  costCenterId?: string | null;
  debitAmount?: number | string | null;
  creditAmount?: number | string | null;
}

interface VoucherDetailDto {
  id: string;
  voucherNumber?: string | null;
  narration?: string | null;
  voucherTypeName?: string | null;
  voucherDate?: string | null;
  financialYearCode?: string | null;
  referenceNumber?: string | null;
  status?: string | null;
  createdBy?: string | null;
  createdAt?: string | null;
  updatedBy?: string | null;
  updatedAt?: string | null;
  approvedAt?: string | null;
  postedAt?: string | null;
  lines?: VoucherLineDto[];
}

export default function GLPostingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [approvalRemarks, setApprovalRemarks] = useState('');
  const [postingDetail, setPostingDetail] = useState<PostingDetail | null>(null);
  const [loading, setLoading] = useState(false);

  const mapVoucher = (voucher: VoucherDetailDto): PostingDetail => ({
    id: voucher.id,
    postingId: voucher.voucherNumber || '-',
    description: voucher.narration || voucher.voucherTypeName || 'Voucher posting',
    postingDate: voucher.voucherDate || '-',
    period: voucher.financialYearCode || '-',
    reference: voucher.referenceNumber || null,
    narration: voucher.narration || null,
    status: voucher.status || 'DRAFT',
    createdBy: voucher.createdBy || '-',
    createdAt: voucher.createdAt || '-',
    approvedBy: voucher.approvedAt ? 'Approver' : null,
    approvedAt: voucher.approvedAt || null,
    postedAt: voucher.postedAt || null,
    entries: (voucher.lines || []).map((line) => ({
      id: line.id,
      accountCode: line.accountCode || '-',
      accountName: line.accountName || '-',
      description: line.narration || null,
      costCenter: line.costCenterId || '-',
      debit: Number(line.debitAmount || 0),
      credit: Number(line.creditAmount || 0),
    })),
    history: [
      {
        action: voucher.status || 'DRAFT',
        by: voucher.updatedBy || voucher.createdBy || '-',
        at: voucher.updatedAt || voucher.createdAt || '-',
      },
    ],
  });

  useEffect(() => {
    const loadPosting = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const response = await vouchersApi.get(id);
        setPostingDetail(mapVoucher(response.data as VoucherDetailDto));
      } catch (error) {
        logger.error('Failed to load GL posting detail:', error);
        setPostingDetail(null);
      } finally {
        setLoading(false);
      }
    };

    loadPosting();
  }, [id]);

  const totalDebit = postingDetail?.entries.reduce((sum, e) => sum + e.debit, 0) || 0;
  const totalCredit = postingDetail?.entries.reduce((sum, e) => sum + e.credit, 0) || 0;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'POSTED':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <CheckCircle className="mr-1 h-3 w-3" />
            Posted
          </Badge>
        );
      case 'PENDING_APPROVAL':
        return (
          <Badge variant="secondary">
            <Clock className="mr-1 h-3 w-3" />
            Pending Approval
          </Badge>
        );
      case 'DRAFT':
        return (
          <Badge variant="outline">
            <Edit className="mr-1 h-3 w-3" />
            Draft
          </Badge>
        );
      case 'REJECTED':
        return (
          <Badge variant="destructive">
            <XCircle className="mr-1 h-3 w-3" />
            Rejected
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleApprove = async () => {
    if (!postingDetail) return;
    await vouchersApi.approve(postingDetail.id, approvalRemarks);
    await vouchersApi.post(postingDetail.id);
    navigate('/admin/accounting/gl-postings');
  };

  const handleReject = async () => {
    if (!postingDetail) return;
    await vouchersApi.reject(
      postingDetail.id,
      approvalRemarks || 'Rejected during approval review',
    );
    navigate('/admin/accounting/gl-postings');
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6 text-muted-foreground">Loading GL posting...</div>
    );
  }

  if (!postingDetail) {
    return (
      <div className="container mx-auto py-6 text-muted-foreground">GL posting not found.</div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title={postingDetail.postingId}
        subtitle={postingDetail.description}
        breadcrumbs={[
          { label: 'GL Postings', to: '/admin/accounting/gl-postings' },
          { label: postingDetail.postingId },
        ]}
        actions={
          <div className="flex items-center gap-2">
            {getStatusBadge(postingDetail.status)}
            <Button variant="outline" size="sm">
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="space-y-6 lg:col-span-2">
          {/* Posting Details */}
          <Card>
            <CardHeader>
              <CardTitle>Posting Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                <div>
                  <p className="text-muted-foreground">Posting ID</p>
                  <p className="font-mono font-medium">{postingDetail.postingId}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Posting Date</p>
                  <p className="font-medium">{postingDetail.postingDate}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Accounting Period</p>
                  <p className="font-medium">{postingDetail.period}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Reference</p>
                  <p className="font-medium">{postingDetail.reference || 'N/A'}</p>
                </div>
              </div>
              {postingDetail.narration && (
                <div className="mt-4 rounded-lg bg-muted p-3">
                  <p className="mb-1 text-sm text-muted-foreground">Narration</p>
                  <p className="text-sm">{postingDetail.narration}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Journal Entries */}
          <Card>
            <CardHeader>
              <CardTitle>Journal Entries</CardTitle>
              <CardDescription>{postingDetail.entries.length} line items</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Cost Center</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {postingDetail.entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>
                        <div>
                          <div className="font-mono text-sm">{entry.accountCode}</div>
                          <div className="text-sm text-muted-foreground">{entry.accountName}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{entry.description}</TableCell>
                      <TableCell className="text-sm">{entry.costCenter}</TableCell>
                      <TableCell className="text-right font-medium">
                        {entry.debit > 0 ? formatIndianCompactCurrency(entry.debit) : '-'}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {entry.credit > 0 ? formatIndianCompactCurrency(entry.credit) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell colSpan={3} className="text-right">
                      Total
                    </TableCell>
                    <TableCell className="text-right">
                      {formatIndianCompactCurrency(totalDebit)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatIndianCompactCurrency(totalCredit)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              <div className="mt-4 flex items-center justify-between rounded-lg bg-green-50 p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-800">Entries are balanced</span>
                </div>
                <span className="text-green-700">{formatIndianCompactCurrency(totalDebit)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Approval Actions (if pending) */}
          {postingDetail.status === 'PENDING_APPROVAL' && (
            <Card>
              <CardHeader>
                <CardTitle>Approval Action</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Remarks</Label>
                  <Textarea
                    placeholder="Add approval remarks..."
                    value={approvalRemarks}
                    onChange={(e) => setApprovalRemarks(e.target.value)}
                    rows={3}
                  />
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleApprove} className="bg-green-600 hover:bg-green-700">
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Approve & Post
                  </Button>
                  <Button variant="destructive" onClick={handleReject}>
                    <XCircle className="mr-2 h-4 w-4" />
                    Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Total Debit</span>
                <span className="text-lg font-bold">{formatIndianCompactCurrency(totalDebit)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Total Credit</span>
                <span className="text-lg font-bold">
                  {formatIndianCompactCurrency(totalCredit)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Line Items</span>
                <span className="font-bold">{postingDetail.entries.length}</span>
              </div>
            </CardContent>
          </Card>

          {/* Audit Information */}
          <Card>
            <CardHeader>
              <CardTitle>Audit Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-muted-foreground">Created By</p>
                  <p className="font-medium">{postingDetail.createdBy}</p>
                  <p className="text-xs text-muted-foreground">{postingDetail.createdAt}</p>
                </div>
              </div>
              {postingDetail.approvedBy && (
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <div>
                    <p className="text-muted-foreground">Approved By</p>
                    <p className="font-medium">{postingDetail.approvedBy}</p>
                    <p className="text-xs text-muted-foreground">{postingDetail.approvedAt}</p>
                  </div>
                </div>
              )}
              {postingDetail.postedAt && (
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-500" />
                  <div>
                    <p className="text-muted-foreground">Posted At</p>
                    <p className="text-xs text-muted-foreground">{postingDetail.postedAt}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* History */}
          <Card>
            <CardHeader>
              <CardTitle>Activity History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {postingDetail.history.map((entry, index) => (
                  <div key={index} className="flex gap-3 text-sm">
                    <div className="flex flex-col items-center">
                      <div
                        className={`h-2 w-2 rounded-full ${index === 0 ? 'bg-green-500' : 'bg-gray-300'}`}
                      />
                      {index < postingDetail.history.length - 1 && (
                        <div className="h-full w-px bg-gray-200" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <p className="font-medium">{entry.action}</p>
                      <p className="text-muted-foreground">by {entry.by}</p>
                      <p className="text-xs text-muted-foreground">{entry.at}</p>
                      {entry.remarks && (
                        <p className="mt-1 rounded bg-muted p-2 text-xs">{entry.remarks}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
