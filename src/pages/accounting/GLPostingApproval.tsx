import {
  BookOpen,
  CheckCircle,
  XCircle,
  Clock,
  User,
  Calendar,
  AlertTriangle,
  History,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

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
import { useActiveOrganizationId } from '@/stores/organizationStore';

import { logger } from "@/lib/logger";
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

interface PendingPosting {
  id: string;
  postingId: string;
  description: string;
  postingDate: string;
  period: string;
  entries: {
    id: string;
    accountCode: string;
    accountName: string;
    debit: number;
    credit: number;
  }[];
  totalDebit: number;
  totalCredit: number;
  createdBy: string;
  createdAt: string;
  priority: 'NORMAL' | 'HIGH' | 'URGENT';
  remarks?: string;
}

interface VoucherLineDto {
  id: string;
  accountCode?: string | null;
  accountName?: string | null;
  debitAmount?: number | string | null;
  creditAmount?: number | string | null;
}

interface VoucherDto {
  id: string;
  voucherNumber?: string | null;
  narration?: string | null;
  voucherTypeName?: string | null;
  voucherDate?: string | null;
  financialYearCode?: string | null;
  lines?: VoucherLineDto[];
  totalDebit?: number | string | null;
  totalCredit?: number | string | null;
  createdBy?: string | null;
  createdAt?: string | null;
}

export default function GLPostingApproval() {
  const { id } = useParams();
  const organizationId = useActiveOrganizationId();
  const [pendingPostings, setPendingPostings] = useState<PendingPosting[]>([]);
  const [selectedPosting, setSelectedPosting] = useState<PendingPosting | null>(null);
  const [approvalRemarks, setApprovalRemarks] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const mapVoucher = useCallback((voucher: VoucherDto): PendingPosting => ({
    id: voucher.id,
    postingId: voucher.voucherNumber || '-',
    description: voucher.narration || voucher.voucherTypeName || 'Voucher posting',
    postingDate: voucher.voucherDate || '-',
    period: voucher.financialYearCode || '-',
    entries: (voucher.lines || []).map((line) => ({
      id: line.id,
      accountCode: line.accountCode || '-',
      accountName: line.accountName || '-',
      debit: Number(line.debitAmount || 0),
      credit: Number(line.creditAmount || 0),
    })),
    totalDebit: Number(voucher.totalDebit || 0),
    totalCredit: Number(voucher.totalCredit || 0),
    createdBy: voucher.createdBy || '-',
    createdAt: voucher.createdAt || '-',
    priority: Number(voucher.totalDebit || 0) >= 5000000 ? 'HIGH' : 'NORMAL',
    remarks: voucher.narration || undefined,
  }), []);

  const selectPosting = useCallback(async (posting: PendingPosting) => {
    try {
      const response = await vouchersApi.get(posting.id);
      setSelectedPosting(mapVoucher(response.data as VoucherDto));
    } catch (error) {
      logger.error('Failed to load posting detail:', error);
      setSelectedPosting(posting);
    }
  }, [mapVoucher]);

  const loadPendingPostings = useCallback(async () => {
    if (!organizationId) return;
    try {
      const response = await vouchersApi.getPendingApproval({
        page_size: 100,
      });
      const postings = ((response.data || []) as VoucherDto[]).map(mapVoucher);
      setPendingPostings(postings);
      if (id) {
        const selected = postings.find((posting) => posting.id === id);
        if (selected) {
          await selectPosting(selected);
        }
      }
    } catch (error) {
      logger.error('Failed to load pending GL postings:', error);
      setPendingPostings([]);
    }
  }, [id, mapVoucher, organizationId, selectPosting]);

  useEffect(() => {
    loadPendingPostings();
  }, [loadPendingPostings]);

  const handleApprove = async () => {
    if (!selectedPosting) return;
    setIsProcessing(true);
    try {
      await vouchersApi.approve(selectedPosting.id, approvalRemarks);
      await vouchersApi.post(selectedPosting.id);
      await loadPendingPostings();
      setSelectedPosting(null);
      setApprovalRemarks('');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!selectedPosting) return;
    setIsProcessing(true);
    try {
      await vouchersApi.reject(selectedPosting.id, approvalRemarks || 'Rejected during approval review');
      await loadPendingPostings();
      setSelectedPosting(null);
      setApprovalRemarks('');
    } finally {
      setIsProcessing(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'HIGH':
        return <Badge variant="destructive">High Priority</Badge>;
      case 'URGENT':
        return <Badge variant="destructive" className="bg-red-600">Urgent</Badge>;
      default:
        return <Badge variant="secondary">Normal</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="GL Posting Approval"
        subtitle="Review and approve pending GL postings"
        breadcrumbs={[
          { label: 'GL Postings', to: '/admin/accounting/gl-postings' },
          { label: 'Approval' },
        ]}
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              Pending Approval
            </div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{pendingPostings.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              High Priority
            </div>
            <div className="text-2xl font-bold mt-1 text-red-600">
              {pendingPostings.filter(p => p.priority === 'HIGH' || p.priority === 'URGENT').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Debit Value</div>
            <div className="text-2xl font-bold mt-1">
              {formatCurrency(pendingPostings.reduce((sum, p) => sum + p.totalDebit, 0))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Oldest Pending</div>
            <div className="text-2xl font-bold mt-1">2 days</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pending List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Pending Postings</CardTitle>
            <CardDescription>{pendingPostings.length} awaiting approval</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pendingPostings.map((posting) => (
                <button
                  type="button"
                  key={posting.id}
                  className={`w-full p-4 border rounded-lg text-left transition-colors ${
                    selectedPosting?.id === posting.id ? 'border-primary bg-muted/50' : 'hover:bg-muted/30'
                  }`}
                  onClick={() => selectPosting(posting)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-mono text-sm">{posting.postingId}</div>
                      <div className="font-medium text-sm mt-1">{posting.description}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        by {posting.createdBy} • {posting.postingDate}
                      </div>
                    </div>
                    {getPriorityBadge(posting.priority)}
                  </div>
                  <div className="mt-2 text-sm font-medium">
                    {formatCurrency(posting.totalDebit)}
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Detail View */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Posting Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedPosting ? (
              <div className="space-y-6">
                {/* Header Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Posting ID</p>
                    <p className="font-mono font-medium">{selectedPosting.postingId}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Posting Date</p>
                    <p className="font-medium">{selectedPosting.postingDate}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Period</p>
                    <p className="font-medium">{selectedPosting.period}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Priority</p>
                    {getPriorityBadge(selectedPosting.priority)}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground mb-1">Description</p>
                  <p className="font-medium">{selectedPosting.description}</p>
                </div>

                {selectedPosting.remarks && (
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground mb-1">Remarks</p>
                    <p className="text-sm">{selectedPosting.remarks}</p>
                  </div>
                )}

                {/* Journal Entries */}
                <div>
                  <h4 className="font-medium mb-3">Journal Entries</h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Account</TableHead>
                        <TableHead className="text-right">Debit</TableHead>
                        <TableHead className="text-right">Credit</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedPosting.entries.map((entry) => (
                        <TableRow key={entry.id}>
                          <TableCell>
                            <div className="font-mono text-sm">{entry.accountCode}</div>
                            <div className="text-sm text-muted-foreground">{entry.accountName}</div>
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {entry.debit > 0 ? formatCurrency(entry.debit) : '-'}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {entry.credit > 0 ? formatCurrency(entry.credit) : '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-muted/50 font-bold">
                        <TableCell>Total</TableCell>
                        <TableCell className="text-right">{formatCurrency(selectedPosting.totalDebit)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(selectedPosting.totalCredit)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  <div className="mt-3 p-3 bg-green-50 rounded-lg flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-800">Entries are balanced</span>
                  </div>
                </div>

                {/* Attachments */}
                {/* Audit Info */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-muted-foreground">Created By</p>
                      <p className="font-medium">{selectedPosting.createdBy}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-muted-foreground">Created At</p>
                      <p className="font-medium">{selectedPosting.createdAt}</p>
                    </div>
                  </div>
                </div>

                {/* Approval Form */}
                <div className="border-t pt-6 space-y-4">
                  <div>
                    <Label>Approval Remarks</Label>
                    <Textarea
                      placeholder="Add remarks for this approval..."
                      value={approvalRemarks}
                      onChange={(e) => setApprovalRemarks(e.target.value)}
                      rows={3}
                      className="mt-2"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={handleApprove}
                      disabled={isProcessing}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Approve & Post
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={handleReject}
                      disabled={isProcessing}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                    <Link to={`/admin/accounting/gl-postings/${selectedPosting.id}`}>
                      <Button variant="outline">
                        <History className="h-4 w-4 mr-2" />
                        View Full Details
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a posting from the list to review</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
