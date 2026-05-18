/**
 * Legal Expense List Page
 * View and manage legal expenses
 */

import {
  IndianRupee,
  Plus,
  Search,
  Loader2,
  Check,
  X,
  Receipt,
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
import { legalExpenseApi } from '@/services/legalApi';
import type { LegalExpense, ExpenseCategory } from '@/types/legal';

import { logger } from "@/lib/logger";
const expenseCategories: { value: ExpenseCategory; label: string }[] = [
  { value: 'COURT_FEE', label: 'Court Fee' },
  { value: 'ADVOCATE_FEE', label: 'Advocate Fee' },
  { value: 'VALUATION_FEE', label: 'Valuation Fee' },
  { value: 'PUBLICATION_FEE', label: 'Publication Fee' },
  { value: 'TRAVEL_EXPENSE', label: 'Travel Expense' },
  { value: 'DOCUMENTATION', label: 'Documentation' },
  { value: 'STAMP_DUTY', label: 'Stamp Duty' },
  { value: 'OTHER', label: 'Other' },
];

const statusColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700',
  APPROVED: 'bg-blue-100 text-blue-700',
  PAID: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
};

const recoveryStatusColors: Record<string, string> = {
  PENDING: 'bg-gray-100 text-gray-700',
  PARTIAL: 'bg-yellow-100 text-yellow-700',
  RECOVERED: 'bg-green-100 text-green-700',
  WRITTEN_OFF: 'bg-red-100 text-red-700',
};

export default function LegalExpenseList() {
  const [loading, setLoading] = useState(true);
  const [expenses, setExpenses] = useState<LegalExpense[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [activeTab, setActiveTab] = useState('all');
  const [showDialog, setShowDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    loan_account_id: '',
    legal_case_id: '',
    category: '',
    description: '',
    amount: '',
    gst_amount: '',
    expense_date: new Date().toISOString().split('T')[0],
    payee_name: '',
    payee_type: 'VENDOR',
    reference_number: '',
    is_tds_applicable: false,
  });

  useEffect(() => {
    fetchExpenses();
  }, [filterCategory, filterStatus]);

  const fetchExpenses = async () => {
    try {
      const response = await legalExpenseApi.getList({
        expense_category: filterCategory !== 'all' ? filterCategory : undefined,
        expense_status: filterStatus !== 'all' ? filterStatus : undefined,
      });
      setExpenses(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch expenses:', error);
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

  const handleApprove = async (id: string) => {
    try {
      await legalExpenseApi.approve(id);
      fetchExpenses();
    } catch (error) {
      logger.error('Failed to approve expense:', error);
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;

    try {
      await legalExpenseApi.reject(id, { reason });
      fetchExpenses();
    } catch (error) {
      logger.error('Failed to reject expense:', error);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await legalExpenseApi.create({
        ...formData,
        amount: parseFloat(formData.amount),
        gst_amount: formData.gst_amount ? parseFloat(formData.gst_amount) : undefined,
        loan_account_id: formData.loan_account_id,
        legal_case_id: formData.legal_case_id || undefined,
      });
      setShowDialog(false);
      fetchExpenses();
    } catch (error) {
      logger.error('Failed to create expense:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const filteredExpenses = expenses.filter((e) => {
    const matchesSearch =
      !searchQuery ||
      e.expense_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.loan_account_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.payee_name.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesTab =
      activeTab === 'all' ||
      (activeTab === 'pending' && e.status === 'PENDING') ||
      (activeTab === 'recovery' && e.recovery_status === 'PENDING');

    return matchesSearch && matchesTab;
  });

  const stats = {
    total: expenses.reduce((sum, e) => sum + e.total_amount, 0),
    pending: expenses
      .filter((e) => e.status === 'PENDING')
      .reduce((sum, e) => sum + e.total_amount, 0),
    approved: expenses
      .filter((e) => e.status === 'APPROVED')
      .reduce((sum, e) => sum + e.total_amount, 0),
    pendingRecovery: expenses
      .filter((e) => e.recovery_status === 'PENDING')
      .reduce((sum, e) => sum + e.total_amount, 0),
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
        title="Legal Expenses"
        subtitle="Track and manage legal expenses"
        actions={
          <Button onClick={() => setShowDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Record Expense
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <IndianRupee className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Expenses</p>
                <p className="text-lg font-bold">{formatCurrency(stats.total)}</p>
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
                <p className="text-sm text-gray-500">Pending Approval</p>
                <p className="text-lg font-bold text-yellow-600">{formatCurrency(stats.pending)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <Check className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Approved</p>
                <p className="text-lg font-bold text-green-600">{formatCurrency(stats.approved)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-orange-100 p-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Pending Recovery</p>
                <p className="text-lg font-bold text-orange-600">
                  {formatCurrency(stats.pendingRecovery)}
                </p>
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
                placeholder="Search by expense number, loan account, payee..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterCategory} onValueChange={setFilterCategory}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {expenseCategories.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
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
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="PAID">Paid</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Expenses Table */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="all">All Expenses</TabsTrigger>
              <TabsTrigger value="pending">Pending Approval</TabsTrigger>
              <TabsTrigger value="recovery">Pending Recovery</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Expense #</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Loan / Case</TableHead>
                <TableHead>Payee</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Recovery</TableHead>
                <TableHead className="w-[100px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredExpenses.map((expense) => (
                <TableRow key={expense.id}>
                  <TableCell className="font-medium">{expense.expense_number}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">
                      {expenseCategories.find((c) => c.value === expense.category)?.label ||
                        expense.category}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <p>{expense.loan_account_number}</p>
                    {expense.case_number && (
                      <p className="text-sm text-gray-500">{expense.case_number}</p>
                    )}
                  </TableCell>
                  <TableCell>
                    <p>{expense.payee_name}</p>
                    <p className="text-sm text-gray-500">{expense.payee_type}</p>
                  </TableCell>
                  <TableCell className="text-right">
                    <p className="font-medium">{formatCurrency(expense.total_amount)}</p>
                    {expense.gst_amount && (
                      <p className="text-xs text-gray-500">
                        GST: {formatCurrency(expense.gst_amount)}
                      </p>
                    )}
                  </TableCell>
                  <TableCell><DateDisplay date={expense.expense_date} /></TableCell>
                  <TableCell>
                    <Badge className={statusColors[expense.status]}>{expense.status}</Badge>
                  </TableCell>
                  <TableCell>
                    {expense.recovery_status && (
                      <div>
                        <Badge className={recoveryStatusColors[expense.recovery_status]}>
                          {expense.recovery_status}
                        </Badge>
                        {expense.recovered_amount && expense.recovered_amount > 0 && (
                          <p className="mt-1 text-xs text-gray-500">
                            {formatCurrency(expense.recovered_amount)}
                          </p>
                        )}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    {expense.status === 'PENDING' && (
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-green-600"
                          onClick={() => handleApprove(expense.id)}
                          title="Approve"
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-red-600"
                          onClick={() => handleReject(expense.id)}
                          title="Reject"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {filteredExpenses.length === 0 && (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-gray-500">
                    <Receipt className="mx-auto mb-4 h-12 w-12 opacity-50" />
                    <p>No expenses found</p>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add Expense Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Record Legal Expense</DialogTitle>
            <DialogDescription>
              Add a new expense for a legal case or loan account
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="col-span-2 space-y-2">
              <Label>Loan Account *</Label>
              <Input
                value={formData.loan_account_id}
                onChange={(e) => setFormData({ ...formData, loan_account_id: e.target.value })}
                placeholder="Enter loan account ID"
              />
            </div>
            <div className="space-y-2">
              <Label>Category *</Label>
              <Select
                value={formData.category}
                onValueChange={(v) => setFormData({ ...formData, category: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {expenseCategories.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Payee Type *</Label>
              <Select
                value={formData.payee_type}
                onValueChange={(v) => setFormData({ ...formData, payee_type: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ADVOCATE">Advocate</SelectItem>
                  <SelectItem value="COURT">Court</SelectItem>
                  <SelectItem value="VENDOR">Vendor</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Payee Name *</Label>
              <Input
                value={formData.payee_name}
                onChange={(e) => setFormData({ ...formData, payee_name: e.target.value })}
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Description *</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label>Amount *</Label>
              <Input
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>GST Amount</Label>
              <Input
                type="number"
                value={formData.gst_amount}
                onChange={(e) => setFormData({ ...formData, gst_amount: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Expense Date *</Label>
              <Input
                type="date"
                value={formData.expense_date}
                onChange={(e) => setFormData({ ...formData, expense_date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Reference Number</Label>
              <Input
                value={formData.reference_number}
                onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={
                !formData.loan_account_id ||
                !formData.category ||
                !formData.payee_name ||
                !formData.amount ||
                submitting
              }
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Record Expense'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
