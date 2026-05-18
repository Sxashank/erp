import { AlertTriangle, CheckCircle, Clock, Eye, XCircle } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import { Textarea } from '@/components/ui/textarea';
import {
  useApproveDisbursement,
  useDisbursements,
  useRejectDisbursement,
  useVerifyDisbursementConditions,
} from '@/hooks/lending/useDisbursements';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { DisbursementListItem } from '@/services/lending/disbursementApi';

export default function DisbursementApproval() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data, isLoading } = useDisbursements({ status: 'PENDING', pageSize: 100 });
  const verifyMutation = useVerifyDisbursementConditions();
  const approveMutation = useApproveDisbursement();
  const rejectMutation = useRejectDisbursement();
  const pendingDisbursements = data?.items ?? [];
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [currentItem, setCurrentItem] = useState<DisbursementListItem | null>(null);
  const [approvedAmount, setApprovedAmount] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [remarks, setRemarks] = useState('');
  const [isBulkApproving, setIsBulkApproving] = useState(false);

  const handleSelectAll = (checked: boolean) => {
    setSelectedItems(checked ? pendingDisbursements.map((d) => d.id) : []);
  };

  const handleSelectItem = (id: string, checked: boolean) => {
    setSelectedItems((items) =>
      checked ? [...items, id] : items.filter((item) => item !== id),
    );
  };

  const openApproveDialog = (item: DisbursementListItem) => {
    setCurrentItem(item);
    setApprovedAmount(item.requestedAmount);
    setRemarks('');
    setIsApproveDialogOpen(true);
  };

  const openRejectDialog = (item: DisbursementListItem) => {
    setCurrentItem(item);
    setRejectionReason('');
    setRemarks('');
    setIsRejectDialogOpen(true);
  };

  const verifyAndApprove = async (item: DisbursementListItem, amount?: string, note?: string) => {
    await verifyMutation.mutateAsync({
      disbursementId: item.id,
      verificationNotes: note || 'Manual pre-disbursement conditions verified during approval',
    });
    return approveMutation.mutateAsync({
      disbursementId: item.id,
      ...(amount ? { approvedAmount: amount } : {}),
      ...(note ? { remarks: note } : {}),
    });
  };

  const handleApprove = async () => {
    if (!currentItem) return;
    try {
      const result = await verifyAndApprove(currentItem, approvedAmount, remarks);
      toast({
        title: 'Disbursement approved',
        description: `${currentItem.disbursementReference} is now ${result.status.toLowerCase()}.`,
      });
      setIsApproveDialogOpen(false);
      setSelectedItems((items) => items.filter((id) => id !== currentItem.id));
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  const handleReject = async () => {
    if (!currentItem) return;
    try {
      const reasonText = remarks ? `${rejectionReason}: ${remarks}` : rejectionReason;
      await rejectMutation.mutateAsync({
        disbursementId: currentItem.id,
        rejectionReason: reasonText,
      });
      toast({
        title: 'Disbursement rejected',
        description: `${currentItem.disbursementReference} has been rejected.`,
      });
      setIsRejectDialogOpen(false);
      setSelectedItems((items) => items.filter((id) => id !== currentItem.id));
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  const handleBulkApprove = async () => {
    if (selectedItems.length === 0) return;
    setIsBulkApproving(true);
    let approved = 0;
    let failed = 0;
    let lastError: unknown = null;

    for (const id of selectedItems) {
      const item = pendingDisbursements.find((d) => d.id === id);
      if (!item) continue;
      try {
        await verifyAndApprove(item);
        approved += 1;
      } catch (err) {
        failed += 1;
        lastError = err;
      }
    }

    setIsBulkApproving(false);
    if (failed === 0) {
      toast({
        title: 'Bulk approval complete',
        description: `${approved} disbursement${approved === 1 ? '' : 's'} approved.`,
      });
      setSelectedItems([]);
    } else if (approved === 0 && lastError) {
      showErrorToast(lastError, toast);
    } else {
      toast({
        title: 'Bulk approval partially complete',
        description: `${approved} approved, ${failed} failed. Review the failed items.`,
        variant: 'destructive',
      });
    }
  };

  const totalPendingAmount = pendingDisbursements.reduce(
    (sum, d) => sum + Number(d.requestedAmount),
    0,
  );
  const selectedAmount = pendingDisbursements
    .filter((d) => selectedItems.includes(d.id))
    .reduce((sum, d) => sum + Number(d.requestedAmount), 0);
  const isMutating =
    approveMutation.isPending || verifyMutation.isPending || rejectMutation.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Disbursement Approval"
        subtitle="Verify manual pre-disbursement conditions and approve pending requests"
        actions={
          selectedItems.length > 0 ? (
            <Button onClick={handleBulkApprove} disabled={isBulkApproving || isMutating}>
              <CheckCircle className="mr-2 h-4 w-4" />
              {isBulkApproving
                ? `Approving ${selectedItems.length}...`
                : `Approve Selected (${selectedItems.length})`}
            </Button>
          ) : undefined
        }
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
              Manual Verification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-500">{selectedItems.length}</div>
            <p className="text-xs text-muted-foreground">Verified before approval is posted</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pending Disbursement Requests</CardTitle>
          <CardDescription>
            Approval performs manual condition verification first, then records approval.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Checkbox
                    checked={
                      pendingDisbursements.length > 0 &&
                      selectedItems.length === pendingDisbursements.length
                    }
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>Request</TableHead>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Requested</TableHead>
                <TableHead>Beneficiary</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
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
                    <div className="font-mono text-sm">{disbursement.disbursementReference}</div>
                    <div className="text-xs text-muted-foreground">
                      Requested: {formatDate(disbursement.requestDate)}
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {disbursement.loanAccountNumber ?? '—'}
                  </TableCell>
                  <TableCell>{disbursement.entityName ?? '—'}</TableCell>
                  <TableCell className="text-right font-bold">
                    {formatCurrency(Number(disbursement.requestedAmount))}
                  </TableCell>
                  <TableCell>{disbursement.beneficiaryName}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="flex w-fit items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Pending
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/admin/lending/disbursements/${disbursement.id}`)}
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

          {isLoading && (
            <div className="py-12 text-center text-muted-foreground">
              <Clock className="mx-auto mb-4 h-12 w-12 opacity-50" />
              <p>Loading pending disbursements...</p>
            </div>
          )}

          {!isLoading && pendingDisbursements.length === 0 && (
            <div className="py-12 text-center text-muted-foreground">
              <CheckCircle className="mx-auto mb-4 h-12 w-12 opacity-50" />
              <p>No pending disbursements for approval</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Approve Disbursement</DialogTitle>
            <DialogDescription>
              {currentItem?.disbursementReference} - {currentItem?.entityName ?? 'Borrower'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Requested Amount</label>
              <p className="text-2xl font-bold">
                {formatCurrency(Number(currentItem?.requestedAmount ?? 0))}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Approved Amount</label>
              <Input
                type="number"
                value={approvedAmount}
                onChange={(event) => setApprovedAmount(event.target.value)}
                max={currentItem?.requestedAmount}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Manual condition verification is recorded before approval.
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Remarks</label>
              <Textarea
                placeholder="Add approval or condition-verification remarks"
                value={remarks}
                onChange={(event) => setRemarks(event.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsApproveDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApprove} disabled={isMutating}>
              <CheckCircle className="mr-2 h-4 w-4" />
              {isMutating ? 'Approving...' : 'Verify & Approve'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Reject Disbursement</DialogTitle>
            <DialogDescription>
              {currentItem?.disbursementReference} - {currentItem?.entityName ?? 'Borrower'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Requested Amount</label>
              <p className="text-2xl font-bold">
                {formatCurrency(Number(currentItem?.requestedAmount ?? 0))}
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
                onChange={(event) => setRemarks(event.target.value)}
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
              disabled={rejectMutation.isPending || !rejectionReason}
            >
              <AlertTriangle className="mr-2 h-4 w-4" />
              {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
