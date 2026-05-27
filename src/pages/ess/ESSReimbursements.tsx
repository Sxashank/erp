/**
 * ESS Reimbursements Page
 * Submit and track expense reimbursement claims
 */

import {
  Plus,
  Receipt,
  Loader2,
  Eye,
  Send,
  Trash2,
  Clock,
  CheckCircle,
  XCircle,
  IndianRupee,
  Calendar,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { essReimbursementApi } from '@/services/essApi';
import { useEssAuthStore } from '@/stores/essAuthStore';
import type {
  ReimbursementClaim,
  ReimbursementCategory,
  ReimbursementSummary,
  ClaimStatus,
} from '@/types/ess';

import { logger } from '@/lib/logger';
export default function ESSReimbursementsPage() {
  const navigate = useNavigate();
  const accessToken = useEssAuthStore((state) => state.accessToken);
  const [loading, setLoading] = useState(true);
  const [claims, setClaims] = useState<ReimbursementClaim[]>([]);
  const [categories, setCategories] = useState<ReimbursementCategory[]>([]);
  const [summary, setSummary] = useState<ReimbursementSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedClaim, setSelectedClaim] = useState<ReimbursementClaim | null>(null);
  const [claimPendingDelete, setClaimPendingDelete] = useState<ReimbursementClaim | null>(null);

  useEffect(() => {
    if (!accessToken) {
      navigate('/ess/login');
      return;
    }
    fetchData();
  }, [accessToken, navigate, statusFilter]);

  const fetchData = async () => {
    try {
      const [claimsRes, categoriesRes, summaryRes] = await Promise.all([
        essReimbursementApi.getClaims({
          status: statusFilter !== 'ALL' ? statusFilter : undefined,
        }),
        essReimbursementApi.getCategories(),
        essReimbursementApi.getSummary(),
      ]);
      setClaims(claimsRes.data?.items || []);
      setCategories(categoriesRes.data || []);
      setSummary(summaryRes.data);
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClaim = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    setSubmitting(true);
    try {
      await essReimbursementApi.createClaim({
        category_id: (formData.get('category_id') as string) || undefined,
        claim_type: formData.get('claim_type') as string,
        expense_from: formData.get('expense_from') as string,
        expense_to: formData.get('expense_to') as string,
        description: formData.get('description') as string,
        claimed_amount: Number(formData.get('claimed_amount') || 0),
        purpose: formData.get('purpose') as string,
      });
      setCreateDialogOpen(false);
      fetchData();
    } catch (error) {
      logger.error('Failed to create claim:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitClaim = async (claimId: string) => {
    try {
      await essReimbursementApi.submitClaim(claimId);
      fetchData();
    } catch (error) {
      logger.error('Failed to submit claim:', error);
    }
  };

  const handleDeleteClaim = async () => {
    if (!claimPendingDelete) return;
    try {
      await essReimbursementApi.deleteClaim(claimPendingDelete.id);
      setClaimPendingDelete(null);
      fetchData();
    } catch (error) {
      logger.error('Failed to delete claim:', error);
    }
  };

  const getStatusBadge = (status: ClaimStatus) => {
    const styles: Record<ClaimStatus, string> = {
      DRAFT: 'bg-gray-100 text-gray-700',
      SUBMITTED: 'bg-blue-100 text-blue-700',
      PENDING_APPROVAL: 'bg-yellow-100 text-yellow-700',
      APPROVED: 'bg-green-100 text-green-700',
      PARTIALLY_APPROVED: 'bg-orange-100 text-orange-700',
      REJECTED: 'bg-red-100 text-red-700',
      PAID: 'bg-emerald-100 text-emerald-700',
      CANCELLED: 'bg-gray-100 text-gray-500',
    };
    return <Badge className={styles[status]}>{status.replace('_', ' ')}</Badge>;
  };
  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const createClaimDialog = (
    <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Claim
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Create Reimbursement Claim</DialogTitle>
          <DialogDescription>Submit a new expense claim for reimbursement</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleCreateClaim} className="space-y-4">
          <div>
            <Label htmlFor="claim_type">Claim Type</Label>
            <Select name="claim_type" required>
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="MEDICAL">Medical</SelectItem>
                <SelectItem value="TRAVEL">Travel</SelectItem>
                <SelectItem value="CONVEYANCE">Conveyance</SelectItem>
                <SelectItem value="MOBILE">Mobile</SelectItem>
                <SelectItem value="INTERNET">Internet</SelectItem>
                <SelectItem value="FOOD">Food & Meals</SelectItem>
                <SelectItem value="TRAINING">Training</SelectItem>
                <SelectItem value="CERTIFICATION">Certification</SelectItem>
                <SelectItem value="OTHER">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="expense_from">Expense From</Label>
              <Input type="date" id="expense_from" name="expense_from" required />
            </div>
            <div>
              <Label htmlFor="expense_to">Expense To</Label>
              <Input type="date" id="expense_to" name="expense_to" required />
            </div>
          </div>
          <div>
            <Label htmlFor="claimed_amount">Claimed Amount</Label>
            <Input
              type="number"
              id="claimed_amount"
              name="claimed_amount"
              min="1"
              step="0.01"
              required
            />
          </div>
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              name="description"
              placeholder="Describe the expense"
              required
            />
          </div>
          <div>
            <Label htmlFor="purpose">Purpose</Label>
            <Input id="purpose" name="purpose" placeholder="Business purpose" />
          </div>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Claim
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reimbursements"
        subtitle="Submit and track your expense claims"
        actions={createClaimDialog}
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <Receipt className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Claims</p>
                <p className="text-lg font-bold">{summary?.total_claims || 0}</p>
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
                <p className="text-lg font-bold">{summary?.pending_claims || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <IndianRupee className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Claimed Amount</p>
                <p className="text-lg font-bold">
                  {formatIndianCompactCurrency(summary?.total_claimed_amount || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-100 p-2">
                <CheckCircle className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Paid Amount</p>
                <p className="text-lg font-bold">
                  {formatIndianCompactCurrency(summary?.total_paid_amount || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Claims List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">My Claims</CardTitle>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="SUBMITTED">Submitted</SelectItem>
                <SelectItem value="PENDING_APPROVAL">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="PAID">Paid</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {claims.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Claim #</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {claims.map((claim) => (
                  <TableRow key={claim.id}>
                    <TableCell className="font-medium">{claim.claim_number}</TableCell>
                    <TableCell>{claim.claim_type}</TableCell>
                    <TableCell className="text-sm text-gray-500">
                      <DateDisplay date={claim.expense_from} /> -{' '}
                      <DateDisplay date={claim.expense_to} />
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatIndianCompactCurrency(claim.claimed_amount)}
                      {claim.approved_amount && claim.approved_amount !== claim.claimed_amount && (
                        <span className="block text-sm text-green-600">
                          Approved: {formatIndianCompactCurrency(claim.approved_amount)}
                        </span>
                      )}
                    </TableCell>
                    <TableCell>{getStatusBadge(claim.status)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="sm" onClick={() => setSelectedClaim(claim)}>
                          <Eye className="h-4 w-4" />
                        </Button>
                        {claim.status === 'DRAFT' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleSubmitClaim(claim.id)}
                            >
                              <Send className="h-4 w-4 text-blue-600" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setClaimPendingDelete(claim)}
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-8 text-center text-gray-500">
              <Receipt className="mx-auto mb-2 h-8 w-8 opacity-50" />
              <p>No claims found</p>
              <Button variant="link" onClick={() => setCreateDialogOpen(true)}>
                Create your first claim
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Claim Detail Dialog */}
      <Dialog open={!!selectedClaim} onOpenChange={() => setSelectedClaim(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Claim Details - {selectedClaim?.claim_number}</DialogTitle>
          </DialogHeader>
          {selectedClaim && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Claim Type</p>
                  <p className="font-medium">{selectedClaim.claim_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Status</p>
                  {getStatusBadge(selectedClaim.status)}
                </div>
                <div>
                  <p className="text-sm text-gray-500">Expense Period</p>
                  <p className="font-medium">
                    <DateDisplay date={selectedClaim.expense_from} /> -{' '}
                    <DateDisplay date={selectedClaim.expense_to} />
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Claimed Amount</p>
                  <p className="text-lg font-medium">
                    {formatIndianCompactCurrency(selectedClaim.claimed_amount)}
                  </p>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-500">Description</p>
                <p>{selectedClaim.description}</p>
              </div>
              {selectedClaim.purpose && (
                <div>
                  <p className="text-sm text-gray-500">Purpose</p>
                  <p>{selectedClaim.purpose}</p>
                </div>
              )}
              {selectedClaim.rejection_reason && (
                <div className="rounded-lg bg-red-50 p-3">
                  <p className="text-sm font-medium text-red-700">Rejection Reason</p>
                  <p className="text-red-600">{selectedClaim.rejection_reason}</p>
                </div>
              )}
              {selectedClaim.line_items && selectedClaim.line_items.length > 0 && (
                <div>
                  <p className="mb-2 text-sm text-gray-500">Line Items</p>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedClaim.line_items.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell>
                            <DateDisplay date={item.expense_date} />
                          </TableCell>
                          <TableCell>{item.description}</TableCell>
                          <TableCell className="text-right">
                            {formatIndianCompactCurrency(item.amount)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog
        open={!!claimPendingDelete}
        onOpenChange={(open) => !open && setClaimPendingDelete(null)}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Draft Claim</DialogTitle>
            <DialogDescription>
              This will cancel claim {claimPendingDelete?.claim_number}. This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => setClaimPendingDelete(null)}>
              Cancel
            </Button>
            <Button type="button" variant="destructive" onClick={handleDeleteClaim}>
              Delete Claim
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
