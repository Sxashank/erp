import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
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
import {
  BookOpen,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Download,
  Calendar,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock GL postings data
const glPostings = [
  {
    id: '1',
    postingId: 'GLP2025010001',
    description: 'Interest Accrual - January 2025',
    postingDate: '2025-01-15',
    period: 'Jan 2025',
    debitAmount: 1250000,
    creditAmount: 1250000,
    entries: 45,
    status: 'POSTED',
    createdBy: 'Finance Team',
    createdAt: '2025-01-15 10:30:00',
    approvedBy: 'CFO',
    approvedAt: '2025-01-15 14:00:00',
  },
  {
    id: '2',
    postingId: 'GLP2025010002',
    description: 'Provision for NPA - Q4',
    postingDate: '2025-01-14',
    period: 'Jan 2025',
    debitAmount: 850000,
    creditAmount: 850000,
    entries: 12,
    status: 'PENDING_APPROVAL',
    createdBy: 'Risk Team',
    createdAt: '2025-01-14 16:45:00',
    approvedBy: null,
    approvedAt: null,
  },
  {
    id: '3',
    postingId: 'GLP2025010003',
    description: 'Depreciation Entry - Fixed Assets',
    postingDate: '2025-01-13',
    period: 'Jan 2025',
    debitAmount: 125000,
    creditAmount: 125000,
    entries: 8,
    status: 'DRAFT',
    createdBy: 'Accounts Team',
    createdAt: '2025-01-13 11:00:00',
    approvedBy: null,
    approvedAt: null,
  },
  {
    id: '4',
    postingId: 'GLP2025010004',
    description: 'Salary Accrual - January 2025',
    postingDate: '2025-01-12',
    period: 'Jan 2025',
    debitAmount: 2500000,
    creditAmount: 2500000,
    entries: 25,
    status: 'REJECTED',
    createdBy: 'HR Finance',
    createdAt: '2025-01-12 09:30:00',
    approvedBy: null,
    approvedAt: null,
    rejectionReason: 'Incorrect account mapping',
  },
  {
    id: '5',
    postingId: 'GLP2024120015',
    description: 'Year-end Closing Entries',
    postingDate: '2024-12-31',
    period: 'Dec 2024',
    debitAmount: 5800000,
    creditAmount: 5800000,
    entries: 120,
    status: 'POSTED',
    createdBy: 'Finance Team',
    createdAt: '2024-12-31 18:00:00',
    approvedBy: 'CFO',
    approvedAt: '2024-12-31 20:00:00',
  },
];

export default function GLPostingList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [periodFilter, setPeriodFilter] = useState('all');

  const filteredPostings = glPostings.filter(posting => {
    const matchesSearch =
      posting.postingId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      posting.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || posting.status === statusFilter;
    const matchesPeriod = periodFilter === 'all' || posting.period === periodFilter;
    return matchesSearch && matchesStatus && matchesPeriod;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'POSTED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Posted</Badge>;
      case 'PENDING_APPROVAL':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending Approval</Badge>;
      case 'DRAFT':
        return <Badge variant="outline"><Edit className="h-3 w-3 mr-1" />Draft</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Statistics
  const stats = {
    total: glPostings.length,
    posted: glPostings.filter(p => p.status === 'POSTED').length,
    pending: glPostings.filter(p => p.status === 'PENDING_APPROVAL').length,
    draft: glPostings.filter(p => p.status === 'DRAFT').length,
    totalDebit: glPostings.reduce((sum, p) => sum + p.debitAmount, 0),
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="GL Postings"
        subtitle="Manage general ledger posting entries"
        actions={
          <Link to="/admin/accounting/gl-postings/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Posting
            </Button>
          </Link>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Postings</div>
            <div className="text-2xl font-bold mt-1">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Posted</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{stats.posted}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pending Approval</div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Draft</div>
            <div className="text-2xl font-bold mt-1 text-gray-600">{stats.draft}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Value</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(stats.totalDebit)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by posting ID or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="POSTED">Posted</SelectItem>
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Select value={periodFilter} onValueChange={setPeriodFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Periods</SelectItem>
                <SelectItem value="Jan 2025">Jan 2025</SelectItem>
                <SelectItem value="Dec 2024">Dec 2024</SelectItem>
                <SelectItem value="Nov 2024">Nov 2024</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Postings Table */}
      <Card>
        <CardHeader>
          <CardTitle>GL Posting Entries</CardTitle>
          <CardDescription>
            Showing {filteredPostings.length} of {glPostings.length} postings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Posting ID</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Period</TableHead>
                <TableHead>Posting Date</TableHead>
                <TableHead className="text-right">Debit</TableHead>
                <TableHead className="text-right">Credit</TableHead>
                <TableHead className="text-right">Entries</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPostings.map((posting) => (
                <TableRow key={posting.id}>
                  <TableCell className="font-mono">{posting.postingId}</TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{posting.description}</div>
                      <div className="text-xs text-muted-foreground">by {posting.createdBy}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{posting.period}</Badge>
                  </TableCell>
                  <TableCell>{posting.postingDate}</TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(posting.debitAmount)}</TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(posting.creditAmount)}</TableCell>
                  <TableCell className="text-right">{posting.entries}</TableCell>
                  <TableCell>{getStatusBadge(posting.status)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/admin/accounting/gl-postings/${posting.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                      {posting.status === 'DRAFT' && (
                        <Link to={`/admin/accounting/gl-postings/${posting.id}/edit`}>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                        </Link>
                      )}
                    </div>
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
