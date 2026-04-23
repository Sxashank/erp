import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Banknote,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  Clock,
  Filter,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import { formatCurrency, formatDate } from '@/lib/utils';

// Mock data
const pendingDisbursements = [
  {
    id: '1',
    disbursement_number: 'SMFC/LA/2025/00146/D001',
    loan_account: 'SMFC/LA/2025/00146',
    entity: 'Metro Logistics Pvt Ltd',
    product: 'Term Loan',
    requested_amount: 10000000,
    sanctioned_amount: 25000000,
    already_disbursed: 0,
    scheduled_date: '2025-01-16',
    created_date: '2025-01-14',
    created_by: 'John Smith',
    beneficiary_name: 'Metro Logistics Pvt Ltd',
    beneficiary_account: '5555666677',
    beneficiary_ifsc: 'SBIN0009999',
    beneficiary_bank: 'State Bank of India',
    disbursement_mode: 'RTGS',
    status: 'PENDING_APPROVAL',
    purpose: 'Working capital requirement',
    conditions_verified: true,
    documents_complete: true,
    security_coverage: 125,
  },
  {
    id: '2',
    disbursement_number: 'SMFC/LA/2025/00147/D001',
    loan_account: 'SMFC/LA/2025/00147',
    entity: 'Eastern Trading Company',
    product: 'Working Capital',
    requested_amount: 15000000,
    sanctioned_amount: 30000000,
    already_disbursed: 5000000,
    scheduled_date: '2025-01-17',
    created_date: '2025-01-15',
    created_by: 'Sarah Wilson',
    beneficiary_name: 'Eastern Trading Pvt Ltd',
    beneficiary_account: '9876543210',
    beneficiary_ifsc: 'HDFC0001234',
    beneficiary_bank: 'HDFC Bank',
    disbursement_mode: 'NEFT',
    status: 'VERIFIED',
    purpose: 'Machinery purchase',
    conditions_verified: true,
    documents_complete: true,
    security_coverage: 110,
  },
  {
    id: '3',
    disbursement_number: 'SMFC/LA/2025/00150/D001',
    loan_account: 'SMFC/LA/2025/00150',
    entity: 'Southern Exports',
    product: 'Export Finance',
    requested_amount: 8000000,
    sanctioned_amount: 20000000,
    already_disbursed: 10000000,
    scheduled_date: '2025-01-18',
    created_date: '2025-01-15',
    created_by: 'Mike Johnson',
    beneficiary_name: 'Southern Exports Ltd',
    beneficiary_account: '1122334455',
    beneficiary_ifsc: 'ICIC0005678',
    beneficiary_bank: 'ICICI Bank',
    disbursement_mode: 'RTGS',
    status: 'PENDING_APPROVAL',
    purpose: 'Export order financing',
    conditions_verified: false,
    documents_complete: true,
    security_coverage: 95,
  },
];

export default function DisbursementApproval() {
  const navigate = useNavigate();
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<typeof pendingDisbursements[0] | null>(null);
  const [approvedAmount, setApprovedAmount] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [remarks, setRemarks] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedItems(pendingDisbursements.map((d) => d.id));
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

  const openApproveDialog = (item: typeof pendingDisbursements[0]) => {
    setCurrentItem(item);
    setApprovedAmount(item.requested_amount.toString());
    setRemarks('');
    setIsApproveDialogOpen(true);
  };

  const openRejectDialog = (item: typeof pendingDisbursements[0]) => {
    setCurrentItem(item);
    setRejectionReason('');
    setRemarks('');
    setIsRejectDialogOpen(true);
  };

  const handleApprove = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsLoading(false);
    setIsApproveDialogOpen(false);
    // Would refresh the list in real implementation
  };

  const handleReject = async () => {
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsLoading(false);
    setIsRejectDialogOpen(false);
    // Would refresh the list in real implementation
  };

  const handleBulkApprove = async () => {
    if (selectedItems.length === 0) return;
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);
    setSelectedItems([]);
  };

  const totalPendingAmount = pendingDisbursements.reduce((sum, d) => sum + d.requested_amount, 0);
  const selectedAmount = pendingDisbursements
    .filter((d) => selectedItems.includes(d.id))
    .reduce((sum, d) => sum + d.requested_amount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disbursement Approval"
        subtitle="Review and approve pending disbursement requests"
        actions={
          selectedItems.length > 0 ? (
            <Button onClick={handleBulkApprove} disabled={isLoading}>
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve Selected ({selectedItems.length})
            </Button>
          ) : undefined
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Approvals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{pendingDisbursements.length}</div>
            <p className="text-xs text-muted-foreground">
              Total: {formatCurrency(totalPendingAmount)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Selected for Approval
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{selectedItems.length}</div>
            <p className="text-xs text-muted-foreground">
              Amount: {formatCurrency(selectedAmount)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Requiring Attention
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-500">
              {pendingDisbursements.filter((d) => !d.conditions_verified || d.security_coverage < 100).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Incomplete conditions or low coverage
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Pending Disbursements Table */}
      <Card>
        <CardHeader>
          <CardTitle>Pending Disbursement Requests</CardTitle>
          <CardDescription>Review each request before approval</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={selectedItems.length === pendingDisbursements.length}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>Request Details</TableHead>
                <TableHead>Entity / Product</TableHead>
                <TableHead className="text-right">Requested</TableHead>
                <TableHead className="text-right">Sanctioned</TableHead>
                <TableHead>Beneficiary</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Checks</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pendingDisbursements.map((disbursement) => (
                <TableRow key={disbursement.id}>
                  <TableCell>
                    <Checkbox
                      checked={selectedItems.includes(disbursement.id)}
                      onCheckedChange={(checked) =>
                        handleSelectItem(disbursement.id, checked as boolean)
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <div className="font-mono text-sm">{disbursement.disbursement_number}</div>
                    <div className="text-xs text-muted-foreground">
                      Created: {formatDate(disbursement.created_date)} by {disbursement.created_by}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{disbursement.entity}</div>
                    <div className="text-xs text-muted-foreground">{disbursement.product}</div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="font-bold">{formatCurrency(disbursement.requested_amount)}</div>
                    <div className="text-xs text-muted-foreground">
                      {disbursement.disbursement_mode}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div>{formatCurrency(disbursement.sanctioned_amount)}</div>
                    <div className="text-xs text-muted-foreground">
                      Disbursed: {formatCurrency(disbursement.already_disbursed)}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{disbursement.beneficiary_name}</div>
                    <div className="text-xs text-muted-foreground font-mono">
                      {disbursement.beneficiary_account}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {disbursement.beneficiary_bank}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={disbursement.status === 'VERIFIED' ? 'default' : 'outline'}
                      className="flex items-center gap-1 w-fit"
                    >
                      {disbursement.status === 'VERIFIED' ? (
                        <CheckCircle className="h-3 w-3" />
                      ) : (
                        <Clock className="h-3 w-3" />
                      )}
                      {disbursement.status === 'VERIFIED' ? 'Verified' : 'Pending'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1">
                        {disbursement.conditions_verified ? (
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-3 w-3 text-orange-500" />
                        )}
                        <span className="text-xs">Conditions</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {disbursement.documents_complete ? (
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-3 w-3 text-orange-500" />
                        )}
                        <span className="text-xs">Documents</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {disbursement.security_coverage >= 100 ? (
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        ) : (
                          <AlertTriangle className="h-3 w-3 text-orange-500" />
                        )}
                        <span className="text-xs">Coverage: {disbursement.security_coverage}%</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/lending/disbursements/${disbursement.id}`)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-green-600"
                        onClick={() => openApproveDialog(disbursement)}
                      >
                        <CheckCircle className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600"
                        onClick={() => openRejectDialog(disbursement)}
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {pendingDisbursements.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No pending disbursements for approval</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Approve Dialog */}
      <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Approve Disbursement</DialogTitle>
            <DialogDescription>
              {currentItem?.disbursement_number} - {currentItem?.entity}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Requested Amount</label>
              <p className="text-2xl font-bold">
                {formatCurrency(currentItem?.requested_amount || 0)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Approved Amount</label>
              <Input
                type="number"
                value={approvedAmount}
                onChange={(e) => setApprovedAmount(e.target.value)}
                max={currentItem?.requested_amount}
              />
              <p className="text-xs text-muted-foreground mt-1">
                You can approve a lower amount if needed
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Remarks</label>
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
            <DialogTitle>Reject Disbursement</DialogTitle>
            <DialogDescription>
              {currentItem?.disbursement_number} - {currentItem?.entity}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Requested Amount</label>
              <p className="text-2xl font-bold">
                {formatCurrency(currentItem?.requested_amount || 0)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Rejection Reason *</label>
              <Select value={rejectionReason} onValueChange={setRejectionReason}>
                <SelectTrigger>
                  <SelectValue placeholder="Select reason" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DOCUMENTATION_INCOMPLETE">Documentation Incomplete</SelectItem>
                  <SelectItem value="CONDITIONS_NOT_MET">Conditions Not Met</SelectItem>
                  <SelectItem value="SECURITY_INSUFFICIENT">Security Insufficient</SelectItem>
                  <SelectItem value="LIMIT_EXCEEDED">Limit Exceeded</SelectItem>
                  <SelectItem value="ACCOUNT_IRREGULAR">Account Irregular</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Remarks</label>
              <Textarea
                placeholder="Provide detailed reason for rejection"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
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
              disabled={isLoading || !rejectionReason}
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
