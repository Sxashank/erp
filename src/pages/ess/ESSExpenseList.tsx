import { Plus, Search, Eye, Receipt, IndianRupee } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { useToast } from '@/hooks/use-toast';
import { essReimbursementApi } from '@/services/essApi';
interface ExpenseClaim {
  id: string;
  claim_number: string;
  claim_date: string;
  category?: string;
  description: string;
  claimed_amount: number;
  approved_amount?: number | null;
  status: string;
}

const categories = [
  { value: '__all__', label: 'All Categories' },
  { value: 'Travel', label: 'Travel' },
  { value: 'Food & Entertainment', label: 'Food & Entertainment' },
  { value: 'Office Supplies', label: 'Office Supplies' },
  { value: 'Communication', label: 'Communication' },
  { value: 'Other', label: 'Other' },
];

const statuses = [
  { value: '__all__', label: 'All Statuses' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'SUBMITTED', label: 'Pending Approval' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'PAID', label: 'Paid' },
];

export default function ESSExpenseList() {
  const { toast } = useToast();
  const [expenses, setExpenses] = useState<ExpenseClaim[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('__all__');
  const [categoryFilter, setCategoryFilter] = useState('__all__');

  useEffect(() => {
    let mounted = true;
    const loadExpenses = async () => {
      setIsLoading(true);
      try {
        const response = await essReimbursementApi.getClaims({ limit: 100 });
        if (mounted) setExpenses(response.data.items || []);
      } catch (error) {
        if (mounted) {
          toast({
            title: 'Unable to load expenses',
            description: 'Check your ESS session and reimbursement access.',
            variant: 'destructive',
          });
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    loadExpenses();
    return () => {
      mounted = false;
    };
  }, [toast]);

  const filteredExpenses = useMemo(
    () =>
      expenses.filter((exp) => {
        const matchesSearch =
          exp.claim_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
          exp.description.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = statusFilter === '__all__' || exp.status === statusFilter;
        const matchesCategory = categoryFilter === '__all__' || exp.category === categoryFilter;
        return matchesSearch && matchesStatus && matchesCategory;
      }),
    [categoryFilter, expenses, searchTerm, statusFilter],
  );

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'SUBMITTED':
      case 'PENDING_APPROVAL':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            Pending
          </Badge>
        );
      case 'APPROVED':
        return (
          <Badge variant="default" className="bg-blue-500">
            Approved
          </Badge>
        );
      case 'REJECTED':
        return <Badge variant="destructive">Rejected</Badge>;
      case 'PAID':
        return (
          <Badge variant="default" className="bg-green-500">
            Paid
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const totalPending = expenses
    .filter((expense) => ['SUBMITTED', 'PENDING_APPROVAL'].includes(expense.status))
    .reduce((sum, expense) => sum + expense.claimed_amount, 0);
  const totalApproved = expenses
    .filter((expense) => expense.status === 'APPROVED' || expense.status === 'PAID')
    .reduce((sum, expense) => sum + (expense.approved_amount ?? expense.claimed_amount), 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Expenses"
        subtitle="Submit and track expense claims"
        actions={
          <Button asChild>
            <Link to="/ess/expenses/new">
              <Plus className="mr-2 h-4 w-4" />
              New Expense
            </Link>
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-yellow-100 p-3">
                <IndianRupee className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {formatIndianCompactCurrency(totalPending)}
                </div>
                <div className="text-sm text-muted-foreground">Pending Approval</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-green-100 p-3">
                <IndianRupee className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {formatIndianCompactCurrency(totalApproved)}
                </div>
                <div className="text-sm text-muted-foreground">Approved / Paid</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-blue-100 p-3">
                <Receipt className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{expenses.length}</div>
                <div className="text-sm text-muted-foreground">Total Claims</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-gray-100 p-3">
                <Receipt className="h-6 w-6 text-gray-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {expenses.filter((expense) => expense.status === 'DRAFT').length}
                </div>
                <div className="text-sm text-muted-foreground">Drafts</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="relative min-w-[200px] flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground" />
              <Input
                placeholder="Search expenses..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                {statuses.map((status) => (
                  <SelectItem key={status.value} value={status.value}>
                    {status.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Expenses Table */}
      <Card>
        <CardHeader>
          <CardTitle>Expense Claims ({filteredExpenses.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Expense #</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-sm text-muted-foreground">
                    Loading expenses...
                  </TableCell>
                </TableRow>
              ) : filteredExpenses.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-sm text-muted-foreground">
                    No expense claims found.
                  </TableCell>
                </TableRow>
              ) : (
                filteredExpenses.map((expense) => (
                  <TableRow key={expense.id}>
                    <TableCell className="font-medium">{expense.claim_number}</TableCell>
                    <TableCell>{expense.claim_date}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{expense.category || 'Uncategorized'}</Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">{expense.description}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatIndianCompactCurrency(expense.claimed_amount)}
                    </TableCell>
                    <TableCell>{getStatusBadge(expense.status)}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="icon" asChild>
                        <Link to={`/ess/expenses/${expense.id}`}>
                          <Eye className="h-4 w-4" />
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
