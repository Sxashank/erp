import {
  Banknote,
  CheckCircle,
  Eye,
  FileText,
  Receipt,
  ShoppingCart,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency, formatDate } from '@/lib/utils';
import { vouchersApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

import { logger } from "@/lib/logger";
interface PendingApprovalItem {
  id: string;
  referenceNumber: string;
  module: 'ACCOUNTING';
  transactionType: string;
  description: string;
  entity?: string | null;
  amount: number;
  requestedBy: string;
  requestedDate: string;
  currentLevel: number;
  totalLevels: number;
  urgency: 'LOW' | 'NORMAL' | 'HIGH';
  daysPending: number;
}

interface PendingVoucherDto {
  id: string;
  createdAt?: string | null;
  voucherDate?: string | null;
  voucherNumber?: string | null;
  voucherTypeName?: string | null;
  voucherClass?: string | null;
  narration?: string | null;
  partyName?: string | null;
  totalDebit?: number | string | null;
  totalAmount?: number | string | null;
  createdBy?: string | null;
}

const getModuleIcon = (module: string) => {
  switch (module) {
    case 'LENDING':
      return <Banknote className="h-4 w-4" />;
    case 'PROCUREMENT':
      return <ShoppingCart className="h-4 w-4" />;
    case 'AP_AR':
      return <Receipt className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
};

const getUrgencyBadge = (urgency: PendingApprovalItem['urgency']) => {
  switch (urgency) {
    case 'HIGH':
      return <Badge variant="destructive">High Priority</Badge>;
    case 'LOW':
      return <Badge variant="outline">Low</Badge>;
    default:
      return <Badge variant="secondary">Normal</Badge>;
  }
};

const getDaysPending = (requestedDate: string) => {
  const requested = new Date(requestedDate);
  if (Number.isNaN(requested.getTime())) return 0;
  return Math.max(
    0,
    Math.floor((Date.now() - requested.getTime()) / (1000 * 60 * 60 * 24)),
  );
};

const getUrgency = (daysPending: number): PendingApprovalItem['urgency'] => {
  if (daysPending >= 3) return 'HIGH';
  if (daysPending <= 1) return 'LOW';
  return 'NORMAL';
};

export default function PendingApprovals() {
  const navigate = useNavigate();
  const organizationId = useActiveOrganizationId();
  const [items, setItems] = useState<PendingApprovalItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [moduleFilter, setModuleFilter] = useState('all');
  const [urgencyFilter, setUrgencyFilter] = useState('all');
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<PendingApprovalItem | null>(null);
  const [remarks, setRemarks] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const loadPendingItems = useCallback(async () => {
    if (!organizationId) return;
    setIsLoading(true);
    try {
      const response = await vouchersApi.getPendingApproval({
        page_size: 100,
      });
      const pending = (response.data.items || []) as PendingVoucherDto[];
      setItems(
        pending.map((voucher) => {
          const requestedDate = voucher.createdAt || voucher.voucherDate || '';
          const daysPending = getDaysPending(requestedDate);
          return {
            id: voucher.id,
            referenceNumber: voucher.voucherNumber || voucher.id,
            module: 'ACCOUNTING',
            transactionType: voucher.voucherTypeName || voucher.voucherClass || 'Voucher',
            description: voucher.narration || voucher.voucherTypeName || 'Voucher approval',
            entity: voucher.partyName || null,
            amount: Number(voucher.totalDebit || voucher.totalAmount || 0),
            requestedBy: voucher.createdBy || 'System',
            requestedDate,
            currentLevel: 1,
            totalLevels: 1,
            urgency: getUrgency(daysPending),
            daysPending,
          };
        }),
      );
    } catch (error) {
      logger.error('Failed to load pending approvals:', error);
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    loadPendingItems();
  }, [loadPendingItems]);

  const filteredItems = useMemo(
    () =>
      items.filter((item) => {
        const matchesModule = moduleFilter === 'all' || item.module === moduleFilter;
        const matchesUrgency = urgencyFilter === 'all' || item.urgency === urgencyFilter;
        return matchesModule && matchesUrgency;
      }),
    [items, moduleFilter, urgencyFilter],
  );

  const handleSelectAll = (checked: boolean) => {
    setSelectedItems(checked ? filteredItems.map((item) => item.id) : []);
  };

  const handleSelectItem = (id: string, checked: boolean) => {
    setSelectedItems((prev) => (checked ? [...prev, id] : prev.filter((item) => item !== id)));
  };

  const openApproveDialog = (item: PendingApprovalItem | null = null) => {
    setCurrentItem(item);
    setRemarks('');
    setIsApproveDialogOpen(true);
  };

  const openRejectDialog = (item: PendingApprovalItem) => {
    setCurrentItem(item);
    setRemarks('');
    setIsRejectDialogOpen(true);
  };

  const handleApprove = async () => {
    const ids = currentItem ? [currentItem.id] : selectedItems;
    setIsLoading(true);
    try {
      await Promise.all(
        ids.map(async (id) => {
          await vouchersApi.approve(id, remarks);
          await vouchersApi.post(id);
        }),
      );
      setIsApproveDialogOpen(false);
      setSelectedItems([]);
      setCurrentItem(null);
      await loadPendingItems();
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    if (!currentItem) return;
    setIsLoading(true);
    try {
      await vouchersApi.reject(currentItem.id, remarks || 'Rejected during approval review');
      setIsRejectDialogOpen(false);
      setCurrentItem(null);
      await loadPendingItems();
    } finally {
      setIsLoading(false);
    }
  };

  const moduleCount = {
    LENDING: 0,
    PROCUREMENT: 0,
    ACCOUNTING: items.length,
    AP_AR: 0,
  };

  const totalAmount = filteredItems.reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pending Approvals"
        subtitle="Review and approve pending transactions"
        actions={
          selectedItems.length > 0 ? (
            <Button onClick={() => openApproveDialog(null)} disabled={isLoading}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Approve Selected ({selectedItems.length})
            </Button>
          ) : undefined
        }
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{items.length}</div>
            <p className="text-xs text-muted-foreground">{formatCurrency(totalAmount)}</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50" onClick={() => setModuleFilter('LENDING')}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Banknote className="h-4 w-4" />
              Lending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{moduleCount.LENDING}</div>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:bg-muted/50"
          onClick={() => setModuleFilter('PROCUREMENT')}
        >
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <ShoppingCart className="h-4 w-4" />
              Procurement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{moduleCount.PROCUREMENT}</div>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:bg-muted/50"
          onClick={() => setModuleFilter('ACCOUNTING')}
        >
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <FileText className="h-4 w-4" />
              Accounting
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{moduleCount.ACCOUNTING}</div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50" onClick={() => setModuleFilter('AP_AR')}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Receipt className="h-4 w-4" />
              AP/AR
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{moduleCount.AP_AR}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <Select value={moduleFilter} onValueChange={setModuleFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Module" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Modules</SelectItem>
                <SelectItem value="LENDING">Lending</SelectItem>
                <SelectItem value="PROCUREMENT">Procurement</SelectItem>
                <SelectItem value="ACCOUNTING">Accounting</SelectItem>
                <SelectItem value="AP_AR">AP/AR</SelectItem>
              </SelectContent>
            </Select>
            <Select value={urgencyFilter} onValueChange={setUrgencyFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Urgency" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priority</SelectItem>
                <SelectItem value="HIGH">High Priority</SelectItem>
                <SelectItem value="NORMAL">Normal</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
              </SelectContent>
            </Select>
            {(moduleFilter !== 'all' || urgencyFilter !== 'all') && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setModuleFilter('all');
                  setUrgencyFilter('all');
                }}
              >
                Clear Filters
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pending Items</CardTitle>
          <CardDescription>{filteredItems.length} items pending your approval</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={
                      selectedItems.length === filteredItems.length && filteredItems.length > 0
                    }
                    onCheckedChange={(checked) => handleSelectAll(Boolean(checked))}
                  />
                </TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Module</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Requested</TableHead>
                <TableHead>Level</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((item) => (
                <TableRow key={item.id} className={item.urgency === 'HIGH' ? 'bg-red-50' : ''}>
                  <TableCell>
                    <Checkbox
                      checked={selectedItems.includes(item.id)}
                      onCheckedChange={(checked) => handleSelectItem(item.id, Boolean(checked))}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="font-mono text-sm">{item.referenceNumber}</div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getModuleIcon(item.module)}
                      <Badge variant="outline">{item.module.replace(/_/g, '/')}</Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{item.description}</div>
                    {item.entity && (
                      <div className="text-xs text-muted-foreground">{item.entity}</div>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-bold">
                    {formatCurrency(item.amount)}
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{item.requestedBy}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatDate(item.requestedDate)}
                    </div>
                    {item.daysPending > 2 && (
                      <Badge variant="outline" className="mt-1 text-orange-600">
                        {item.daysPending} days ago
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: item.totalLevels }).map((_, index) => (
                        <div
                          key={index}
                          className={`h-2 w-2 rounded-full ${
                            index < item.currentLevel ? 'bg-green-500' : 'bg-gray-300'
                          }`}
                        />
                      ))}
                      <span className="ml-2 text-xs">
                        {item.currentLevel}/{item.totalLevels}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{getUrgencyBadge(item.urgency)}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/admin/accounting/gl-postings/approval')}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-green-600"
                        onClick={() => openApproveDialog(item)}
                      >
                        <CheckCircle className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600"
                        onClick={() => openRejectDialog(item)}
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {filteredItems.length === 0 && (
            <EmptyState
              className="mt-4"
              icon={CheckCircle}
              title={isLoading ? 'Loading pending approvals' : 'No pending approvals'}
              subtitle="Pending accounting vouchers will appear here after they are submitted for approval."
            />
          )}
        </CardContent>
      </Card>

      <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Approve Transaction</DialogTitle>
            <DialogDescription>
              {currentItem
                ? `Approve ${currentItem.referenceNumber}?`
                : `Approve ${selectedItems.length} selected items?`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {currentItem && (
              <div>
                <p className="text-sm text-muted-foreground">Amount</p>
                <p className="text-2xl font-bold">{formatCurrency(currentItem.amount)}</p>
              </div>
            )}
            <div>
              <label htmlFor="approval-remarks" className="text-sm font-medium">Remarks (Optional)</label>
              <Textarea
                id="approval-remarks"
                placeholder="Add any remarks for the approval"
                value={remarks}
                onChange={(event) => setRemarks(event.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsApproveDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApprove} disabled={isLoading}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reject Transaction</DialogTitle>
            <DialogDescription>
              {currentItem ? `Reject ${currentItem.referenceNumber}?` : 'Reject transaction?'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {currentItem && (
              <div>
                <p className="text-sm text-muted-foreground">Amount</p>
                <p className="text-2xl font-bold">{formatCurrency(currentItem.amount)}</p>
              </div>
            )}
            <div>
              <label htmlFor="rejection-reason" className="text-sm font-medium">Rejection Reason</label>
              <Textarea
                id="rejection-reason"
                placeholder="Enter reason for rejection"
                value={remarks}
                onChange={(event) => setRemarks(event.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRejectDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleReject} disabled={isLoading}>
              <XCircle className="mr-2 h-4 w-4" />
              Reject
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
