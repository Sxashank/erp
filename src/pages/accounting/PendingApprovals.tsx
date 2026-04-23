import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Filter,
  AlertTriangle,
  FileText,
  Banknote,
  Receipt,
  ShoppingCart,
  Users,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency, formatDate } from '@/lib/utils';

// Mock data
const pendingItems = [
  {
    id: '1',
    reference_number: 'SMFC/DISB/2025/00145',
    module: 'LENDING',
    transaction_type: 'DISBURSEMENT',
    description: 'Loan Disbursement - Metro Logistics',
    entity: 'Metro Logistics Pvt Ltd',
    amount: 10000000,
    requested_by: 'John Smith',
    requested_date: '2025-01-14',
    current_level: 2,
    total_levels: 3,
    urgency: 'HIGH',
    days_pending: 2,
  },
  {
    id: '2',
    reference_number: 'SMFC/DISB/2025/00146',
    module: 'LENDING',
    transaction_type: 'DISBURSEMENT',
    description: 'Loan Disbursement - Eastern Trading',
    entity: 'Eastern Trading Company',
    amount: 15000000,
    requested_by: 'Sarah Wilson',
    requested_date: '2025-01-15',
    current_level: 1,
    total_levels: 3,
    urgency: 'NORMAL',
    days_pending: 1,
  },
  {
    id: '3',
    reference_number: 'PO/2025/00089',
    module: 'PROCUREMENT',
    transaction_type: 'PURCHASE_ORDER',
    description: 'IT Equipment Purchase',
    entity: 'Tech Solutions Inc',
    amount: 450000,
    requested_by: 'Mike Johnson',
    requested_date: '2025-01-13',
    current_level: 1,
    total_levels: 2,
    urgency: 'NORMAL',
    days_pending: 3,
  },
  {
    id: '4',
    reference_number: 'JV/2025/00234',
    module: 'ACCOUNTING',
    transaction_type: 'JOURNAL_VOUCHER',
    description: 'Monthly Accrual Entry',
    entity: null,
    amount: 2500000,
    requested_by: 'Finance Team',
    requested_date: '2025-01-14',
    current_level: 1,
    total_levels: 1,
    urgency: 'LOW',
    days_pending: 2,
  },
  {
    id: '5',
    reference_number: 'PAY/2025/00567',
    module: 'AP_AR',
    transaction_type: 'VENDOR_PAYMENT',
    description: 'Vendor Payment - ABC Suppliers',
    entity: 'ABC Suppliers Pvt Ltd',
    amount: 350000,
    requested_by: 'Accounts Payable',
    requested_date: '2025-01-12',
    current_level: 1,
    total_levels: 1,
    urgency: 'HIGH',
    days_pending: 4,
  },
];

const getModuleIcon = (module: string) => {
  switch (module) {
    case 'LENDING':
      return <Banknote className="h-4 w-4" />;
    case 'PROCUREMENT':
      return <ShoppingCart className="h-4 w-4" />;
    case 'ACCOUNTING':
      return <FileText className="h-4 w-4" />;
    case 'AP_AR':
      return <Receipt className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
};

const getUrgencyBadge = (urgency: string) => {
  switch (urgency) {
    case 'HIGH':
      return <Badge variant="destructive">High Priority</Badge>;
    case 'NORMAL':
      return <Badge variant="secondary">Normal</Badge>;
    case 'LOW':
      return <Badge variant="outline">Low</Badge>;
    default:
      return <Badge variant="outline">{urgency}</Badge>;
  }
};

export default function PendingApprovals() {
  const navigate = useNavigate();
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [moduleFilter, setModuleFilter] = useState('all');
  const [urgencyFilter, setUrgencyFilter] = useState('all');
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<typeof pendingItems[0] | null>(null);
  const [remarks, setRemarks] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedItems(filteredItems.map((i) => i.id));
    } else {
      setSelectedItems([]);
    }
  };

  const handleSelectItem = (id: string, checked: boolean) => {
    if (checked) {
      setSelectedItems([...selectedItems, id]);
    } else {
      setSelectedItems(selectedItems.filter((item) => item !== id));
    }
  };

  const openApproveDialog = (item: typeof pendingItems[0] | null = null) => {
    setCurrentItem(item);
    setRemarks('');
    setIsApproveDialogOpen(true);
  };

  const openRejectDialog = (item: typeof pendingItems[0]) => {
    setCurrentItem(item);
    setRemarks('');
    setIsRejectDialogOpen(true);
  };

  const handleApprove = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsLoading(false);
    setIsApproveDialogOpen(false);
    setSelectedItems([]);
  };

  const handleReject = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsLoading(false);
    setIsRejectDialogOpen(false);
  };

  const filteredItems = pendingItems.filter((item) => {
    const matchesModule = moduleFilter === 'all' || item.module === moduleFilter;
    const matchesUrgency = urgencyFilter === 'all' || item.urgency === urgencyFilter;
    return matchesModule && matchesUrgency;
  });

  const moduleCount = {
    LENDING: pendingItems.filter((i) => i.module === 'LENDING').length,
    PROCUREMENT: pendingItems.filter((i) => i.module === 'PROCUREMENT').length,
    ACCOUNTING: pendingItems.filter((i) => i.module === 'ACCOUNTING').length,
    AP_AR: pendingItems.filter((i) => i.module === 'AP_AR').length,
  };

  const totalAmount = filteredItems.reduce((sum, i) => sum + i.amount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pending Approvals"
        subtitle="Review and approve pending transactions"
        actions={
          selectedItems.length > 0 ? (
            <Button onClick={() => openApproveDialog(null)} disabled={isLoading}>
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve Selected ({selectedItems.length})
            </Button>
          ) : undefined
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{pendingItems.length}</div>
            <p className="text-xs text-muted-foreground">{formatCurrency(totalAmount)}</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50" onClick={() => setModuleFilter('LENDING')}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Banknote className="h-4 w-4" />
              Lending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{moduleCount.LENDING}</div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50" onClick={() => setModuleFilter('PROCUREMENT')}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <ShoppingCart className="h-4 w-4" />
              Procurement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{moduleCount.PROCUREMENT}</div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:bg-muted/50" onClick={() => setModuleFilter('ACCOUNTING')}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
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
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Receipt className="h-4 w-4" />
              AP/AR
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{moduleCount.AP_AR}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 flex-wrap items-center">
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

      {/* Pending Items Table */}
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
                    onCheckedChange={handleSelectAll}
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
                <TableRow
                  key={item.id}
                  className={item.urgency === 'HIGH' ? 'bg-red-50' : ''}
                >
                  <TableCell>
                    <Checkbox
                      checked={selectedItems.includes(item.id)}
                      onCheckedChange={(checked) =>
                        handleSelectItem(item.id, checked as boolean)
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <div className="font-mono text-sm">{item.reference_number}</div>
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
                    <div className="text-sm">{item.requested_by}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatDate(item.requested_date)}
                    </div>
                    {item.days_pending > 2 && (
                      <Badge variant="outline" className="text-orange-600 mt-1">
                        {item.days_pending} days ago
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: item.total_levels }).map((_, i) => (
                        <div
                          key={i}
                          className={`w-2 h-2 rounded-full ${
                            i < item.current_level ? 'bg-green-500' : 'bg-gray-300'
                          }`}
                        />
                      ))}
                      <span className="text-xs ml-2">
                        {item.current_level}/{item.total_levels}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{getUrgencyBadge(item.urgency)}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/admin/${item.module.toLowerCase()}/${item.id}`)}
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
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No pending approvals</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Approve Dialog */}
      <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Approve Transaction</DialogTitle>
            <DialogDescription>
              {currentItem
                ? `Approve ${currentItem.reference_number}?`
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
              <label className="text-sm font-medium">Remarks (Optional)</label>
              <Textarea
                placeholder="Add any remarks for the approval"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsApproveDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApprove} disabled={isLoading}>
              <CheckCircle className="h-4 w-4 mr-2" />
              {isLoading ? 'Approving...' : 'Approve'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reject Transaction</DialogTitle>
            <DialogDescription>
              {currentItem && `Reject ${currentItem.reference_number}?`}
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
              <label className="text-sm font-medium">Reason for Rejection *</label>
              <Textarea
                placeholder="Provide reason for rejection"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                required
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRejectDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={isLoading || !remarks.trim()}
            >
              <XCircle className="h-4 w-4 mr-2" />
              {isLoading ? 'Rejecting...' : 'Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
