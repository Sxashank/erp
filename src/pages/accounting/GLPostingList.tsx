import {
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import { vouchersApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

import { logger } from "@/lib/logger";
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

interface GLPosting {
  id: string;
  postingId: string;
  description: string;
  postingDate: string;
  period: string;
  debitAmount: number;
  creditAmount: number;
  entries: number;
  status: string;
  createdBy: string;
}

interface VoucherListItem {
  id: string;
  voucherNumber?: string | null;
  narration?: string | null;
  voucherTypeName?: string | null;
  voucherDate?: string | null;
  financialYearCode?: string | null;
  totalDebit?: number | string | null;
  totalCredit?: number | string | null;
  status?: string | null;
  createdBy?: string | null;
}

export default function GLPostingList() {
  const organizationId = useActiveOrganizationId();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [periodFilter, setPeriodFilter] = useState('all');
  const [glPostings, setGlPostings] = useState<GLPosting[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadPostings = async () => {
      if (!organizationId) return;
      setLoading(true);
      try {
        const response = await vouchersApi.list({
          page_size: 100,
          ...(statusFilter !== 'all' ? { status: statusFilter } : {}),
        });
        const items = (response.data.items || []) as VoucherListItem[];
        setGlPostings(
          items.map((voucher) => ({
            id: voucher.id,
            postingId: voucher.voucherNumber || '-',
            description: voucher.narration || voucher.voucherTypeName || 'Voucher posting',
            postingDate: voucher.voucherDate || '-',
            period: voucher.financialYearCode || '-',
            debitAmount: Number(voucher.totalDebit || 0),
            creditAmount: Number(voucher.totalCredit || 0),
            entries: 0,
            status: voucher.status || 'DRAFT',
            createdBy: voucher.createdBy || '-',
          })),
        );
      } catch (error) {
        logger.error('Failed to load GL postings:', error);
        setGlPostings([]);
      } finally {
        setLoading(false);
      }
    };

    loadPostings();
  }, [organizationId, statusFilter]);

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
                {[...new Set(glPostings.map((posting) => posting.period))].map((period) => (
                  <SelectItem key={period} value={period}>
                    {period}
                  </SelectItem>
                ))}
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
            {loading
              ? 'Loading postings'
              : `Showing ${filteredPostings.length} of ${glPostings.length} postings`}
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
              {!loading && filteredPostings.length === 0 && (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    No GL postings found for the selected filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
