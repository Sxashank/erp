import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
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
import { Plus, Search, Eye, Receipt, IndianRupee } from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock data
const expenses = [
  {
    id: '1',
    expenseNumber: 'EXP-2025-001',
    date: '2025-01-15',
    category: 'Travel',
    description: 'Client visit to Mumbai',
    amount: 12500,
    status: 'APPROVED',
    approvedBy: 'Rahul Sharma',
    approvedDate: '2025-01-16',
    paidDate: '2025-01-18',
  },
  {
    id: '2',
    expenseNumber: 'EXP-2025-002',
    date: '2025-01-12',
    category: 'Food & Entertainment',
    description: 'Team lunch - Project completion',
    amount: 3500,
    status: 'PENDING',
    approvedBy: null,
    approvedDate: null,
    paidDate: null,
  },
  {
    id: '3',
    expenseNumber: 'EXP-2025-003',
    date: '2025-01-10',
    category: 'Office Supplies',
    description: 'Stationery purchase',
    amount: 850,
    status: 'REJECTED',
    approvedBy: 'Rahul Sharma',
    approvedDate: '2025-01-11',
    rejectionReason: 'Duplicate claim',
    paidDate: null,
  },
  {
    id: '4',
    expenseNumber: 'EXP-2025-004',
    date: '2025-01-08',
    category: 'Communication',
    description: 'Mobile recharge - Work',
    amount: 599,
    status: 'PAID',
    approvedBy: 'Rahul Sharma',
    approvedDate: '2025-01-09',
    paidDate: '2025-01-12',
  },
  {
    id: '5',
    expenseNumber: 'EXP-2025-005',
    date: '2025-01-05',
    category: 'Travel',
    description: 'Cab to office - late night work',
    amount: 450,
    status: 'DRAFT',
    approvedBy: null,
    approvedDate: null,
    paidDate: null,
  },
];

const categories = [
  { value: '', label: 'All Categories' },
  { value: 'Travel', label: 'Travel' },
  { value: 'Food & Entertainment', label: 'Food & Entertainment' },
  { value: 'Office Supplies', label: 'Office Supplies' },
  { value: 'Communication', label: 'Communication' },
  { value: 'Other', label: 'Other' },
];

const statuses = [
  { value: '', label: 'All Statuses' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'PENDING', label: 'Pending Approval' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'PAID', label: 'Paid' },
];

export default function ESSExpenseList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  const filteredExpenses = expenses.filter((exp) => {
    const matchesSearch = exp.expenseNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      exp.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = !statusFilter || exp.status === statusFilter;
    const matchesCategory = !categoryFilter || exp.category === categoryFilter;
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'PENDING':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'APPROVED':
        return <Badge variant="default" className="bg-blue-500">Approved</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive">Rejected</Badge>;
      case 'PAID':
        return <Badge variant="default" className="bg-green-500">Paid</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const totalPending = expenses.filter(e => e.status === 'PENDING').reduce((sum, e) => sum + e.amount, 0);
  const totalApproved = expenses.filter(e => e.status === 'APPROVED' || e.status === 'PAID').reduce((sum, e) => sum + e.amount, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Expenses"
        subtitle="Submit and track expense claims"
        actions={
          <Button asChild>
            <Link to="/ess/expenses/new">
              <Plus className="h-4 w-4 mr-2" />
              New Expense
            </Link>
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-yellow-100 rounded-lg">
                <IndianRupee className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{formatCurrency(totalPending)}</div>
                <div className="text-sm text-muted-foreground">Pending Approval</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <IndianRupee className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{formatCurrency(totalApproved)}</div>
                <div className="text-sm text-muted-foreground">Approved / Paid</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
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
              <div className="p-3 bg-gray-100 rounded-lg">
                <Receipt className="h-6 w-6 text-gray-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{expenses.filter(e => e.status === 'DRAFT').length}</div>
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
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
              {filteredExpenses.map((expense) => (
                <TableRow key={expense.id}>
                  <TableCell className="font-medium">{expense.expenseNumber}</TableCell>
                  <TableCell>{expense.date}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{expense.category}</Badge>
                  </TableCell>
                  <TableCell className="max-w-xs truncate">{expense.description}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(expense.amount)}
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
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
