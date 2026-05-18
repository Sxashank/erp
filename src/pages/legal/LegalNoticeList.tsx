/**
 * Legal Notice List Page
 * View and manage legal notices
 */

import {
  FileText,
  Plus,
  Search,
  Loader2,
  Calendar,
  Download,
  Send,
  Truck,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { useState, useEffect } from 'react';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { legalNoticeApi } from '@/services/legalApi';
import type { LegalNotice, NoticeType } from '@/types/legal';

import { logger } from "@/lib/logger";
const noticeTypes: { value: NoticeType; label: string; days: number }[] = [
  { value: 'SECTION_13_2_SARFAESI', label: 'Section 13(2) SARFAESI', days: 60 },
  { value: 'SECTION_13_4_POSSESSION', label: 'Section 13(4) Possession', days: 15 },
  { value: 'AUCTION_NOTICE', label: 'Auction Notice', days: 30 },
  { value: 'SECTION_138_NI_ACT', label: 'Section 138 NI Act', days: 15 },
  { value: 'DRT_NOTICE', label: 'DRT Notice', days: 30 },
  { value: 'DEMAND_NOTICE', label: 'Demand Notice', days: 15 },
  { value: 'LEGAL_NOTICE', label: 'Legal Notice', days: 15 },
];

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700',
  DISPATCHED: 'bg-blue-100 text-blue-700',
  DELIVERED: 'bg-green-100 text-green-700',
  RETURNED: 'bg-red-100 text-red-700',
  RESPONDED: 'bg-purple-100 text-purple-700',
  EXPIRED: 'bg-yellow-100 text-yellow-700',
};

export default function LegalNoticeList() {
  const [loading, setLoading] = useState(true);
  const [notices, setNotices] = useState<LegalNotice[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [activeTab, setActiveTab] = useState('all');
  const [showDispatchDialog, setShowDispatchDialog] = useState(false);
  const [selectedNotice, setSelectedNotice] = useState<LegalNotice | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [dispatchData, setDispatchData] = useState({
    dispatch_date: new Date().toISOString().split('T')[0],
    tracking_number: '',
    delivery_method: 'RPAD',
  });

  useEffect(() => {
    fetchNotices();
  }, [filterType, filterStatus]);

  const fetchNotices = async () => {
    try {
      const response = await legalNoticeApi.getList({
        notice_type: filterType !== 'all' ? filterType : undefined,
        status: filterStatus !== 'all' ? filterStatus : undefined,
      });
      setNotices(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch notices:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleDownloadPdf = async (noticeId: string) => {
    try {
      const response = await legalNoticeApi.downloadPdf(noticeId);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `notice_${noticeId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      logger.error('Failed to download PDF:', error);
    }
  };

  const handleDispatch = async () => {
    if (!selectedNotice) return;

    setSubmitting(true);
    try {
      await legalNoticeApi.recordDispatch(selectedNotice.id, dispatchData);
      setShowDispatchDialog(false);
      fetchNotices();
    } catch (error) {
      logger.error('Failed to record dispatch:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredNotices = notices.filter((n) => {
    const matchesSearch =
      !searchQuery ||
      n.notice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.borrower_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.loan_account_number.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesTab =
      activeTab === 'all' ||
      (activeTab === 'pending' && ['DRAFT', 'DISPATCHED'].includes(n.status)) ||
      (activeTab === 'overdue' &&
        n.status !== 'DELIVERED' &&
        new Date(n.response_due_date) < new Date());

    return matchesSearch && matchesTab;
  });

  const stats = {
    total: notices.length,
    pending: notices.filter((n) => ['DRAFT', 'DISPATCHED'].includes(n.status)).length,
    delivered: notices.filter((n) => n.status === 'DELIVERED').length,
    overdue: notices.filter(
      (n) => n.status !== 'DELIVERED' && new Date(n.response_due_date) < new Date(),
    ).length,
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Legal Notices"
        subtitle="Generate and track legal notices"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Generate Notice
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Notices</p>
                <p className="text-xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-yellow-100 p-2">
                <Clock className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Pending</p>
                <p className="text-xl font-bold">{stats.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <Truck className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Delivered</p>
                <p className="text-xl font-bold">{stats.delivered}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-100 p-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Overdue</p>
                <p className="text-xl font-bold text-red-600">{stats.overdue}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-4 md:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Search by notice number, borrower..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Notice Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {noticeTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="DISPATCHED">Dispatched</SelectItem>
                <SelectItem value="DELIVERED">Delivered</SelectItem>
                <SelectItem value="RETURNED">Returned</SelectItem>
                <SelectItem value="RESPONDED">Responded</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Notices Table */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="all">All Notices</TabsTrigger>
              <TabsTrigger value="pending">Pending</TabsTrigger>
              <TabsTrigger value="overdue">Overdue</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Notice #</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Borrower</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Response Due</TableHead>
                <TableHead>Delivery</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[100px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredNotices.map((notice) => {
                const isOverdue =
                  notice.status !== 'DELIVERED' && new Date(notice.response_due_date) < new Date();
                return (
                  <TableRow key={notice.id}>
                    <TableCell>
                      <p className="font-medium">{notice.notice_number}</p>
                      <p className="text-sm text-gray-500">{notice.loan_account_number}</p>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {noticeTypes.find((t) => t.value === notice.notice_type)?.label ||
                          notice.notice_type}
                      </Badge>
                    </TableCell>
                    <TableCell>{notice.borrower_name}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(notice.amount_demanded)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <DateDisplay date={notice.response_due_date} className={isOverdue ? 'font-medium text-red-600' : ''} />
                      </div>
                      <p className="text-xs text-gray-500">
                        {notice.statutory_period_days} days from notice
                      </p>
                    </TableCell>
                    <TableCell>
                      {notice.tracking_number ? (
                        <div className="text-sm">
                          <p>{notice.tracking_number}</p>
                          <p className="text-gray-500">{notice.delivery_method}</p>
                        </div>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[notice.status]}>{notice.status}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDownloadPdf(notice.id)}
                          title="Download PDF"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        {notice.status === 'DRAFT' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => {
                              setSelectedNotice(notice);
                              setShowDispatchDialog(true);
                            }}
                            title="Record Dispatch"
                          >
                            <Send className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
              {filteredNotices.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-gray-500">
                    <FileText className="mx-auto mb-4 h-12 w-12 opacity-50" />
                    <p>No notices found</p>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Dispatch Dialog */}
      <Dialog open={showDispatchDialog} onOpenChange={setShowDispatchDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Dispatch</DialogTitle>
            <DialogDescription>
              Record dispatch details for notice {selectedNotice?.notice_number}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Dispatch Date</Label>
              <Input
                type="date"
                value={dispatchData.dispatch_date}
                onChange={(e) =>
                  setDispatchData({ ...dispatchData, dispatch_date: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Delivery Method</Label>
              <Select
                value={dispatchData.delivery_method}
                onValueChange={(v) => setDispatchData({ ...dispatchData, delivery_method: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="RPAD">RPAD</SelectItem>
                  <SelectItem value="SPEED_POST">Speed Post</SelectItem>
                  <SelectItem value="COURIER">Courier</SelectItem>
                  <SelectItem value="HAND_DELIVERY">Hand Delivery</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Tracking Number</Label>
              <Input
                value={dispatchData.tracking_number}
                onChange={(e) =>
                  setDispatchData({ ...dispatchData, tracking_number: e.target.value })
                }
                placeholder="Enter tracking/consignment number"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDispatchDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleDispatch} disabled={!dispatchData.tracking_number || submitting}>
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Record Dispatch'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
