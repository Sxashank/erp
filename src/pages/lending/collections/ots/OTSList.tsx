import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  CheckCircle,
  Clock,
  FileText,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import {
  useOTSProposals,
  type OTSProposalListItem,
  type OTSStatusValue,
  type OTSFilters,
} from '@/hooks/lending/useOTSProposals';

const statusConfig: Record<
  OTSStatusValue,
  { label: string; color: string; icon: React.ElementType }
> = {
  DRAFT: { label: 'Draft', color: 'bg-gray-100 text-gray-700', icon: FileText },
  PROPOSED: { label: 'Proposed', color: 'bg-blue-100 text-blue-700', icon: FileText },
  NEGOTIATION: { label: 'Negotiation', color: 'bg-blue-100 text-blue-700', icon: Clock },
  PENDING_APPROVAL: {
    label: 'Pending Approval',
    color: 'bg-yellow-100 text-yellow-700',
    icon: Clock,
  },
  APPROVED: { label: 'Approved', color: 'bg-blue-100 text-blue-700', icon: CheckCircle },
  ACCEPTED: { label: 'Accepted', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  COMPLETED: { label: 'Completed', color: 'bg-green-200 text-green-800', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: Clock },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-200 text-gray-700', icon: Clock },
  DEFAULTED: { label: 'Defaulted', color: 'bg-red-200 text-red-800', icon: Clock },
};

export default function OTSList() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filters: OTSFilters = {
    pageSize: 100,
    ...(statusFilter !== 'ALL' && { status: statusFilter as OTSStatusValue }),
  };
  const { data, isLoading, isError, error, refetch } = useOTSProposals(filters);

  const all: OTSProposalListItem[] = data?.items ?? [];
  const proposals = all.filter((p) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      p.otsReference.toLowerCase().includes(q) ||
      (p.entityName ?? '').toLowerCase().includes(q) ||
      (p.loanAccountNumber ?? '').toLowerCase().includes(q)
    );
  });

  // Wire amounts are strings (Decimal precision); coerce once for display-only sums.
  const totalSettlement = proposals
    .filter((p) => ['APPROVED', 'ACCEPTED', 'COMPLETED'].includes(p.status))
    .reduce((sum, p) => sum + Number(p.otsAmount), 0);
  const totalHaircut = proposals
    .filter((p) => ['APPROVED', 'ACCEPTED', 'COMPLETED'].includes(p.status))
    .reduce((sum, p) => sum + Number(p.haircutAmount), 0);
  const pendingApproval = proposals.filter((p) => p.status === 'PENDING_APPROVAL').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="OTS Proposals"
        subtitle="Manage one-time settlement proposals for NPA recovery"
        actions={
          <Button onClick={() => navigate('/admin/lending/collections/ots/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New OTS Proposal
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Proposals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data?.total ?? proposals.length}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Settlement Value</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalSettlement}
              abbreviated
              className="text-2xl font-bold text-green-600"
            />
            <p className="text-xs text-muted-foreground">Approved/Completed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Haircut</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay
              amount={totalHaircut}
              abbreviated
              className="text-2xl font-bold text-red-600"
            />
            <p className="text-xs text-muted-foreground">Write-off amount</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingApproval}</div>
            <p className="text-xs text-muted-foreground">Awaiting decision</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by OTS reference, entity, or loan account..."
                className="pl-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <Filter className="mr-2 h-4 w-4" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="DRAFT">Draft</SelectItem>
                  <SelectItem value="PROPOSED">Proposed</SelectItem>
                  <SelectItem value="NEGOTIATION">Negotiation</SelectItem>
                  <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                  <SelectItem value="APPROVED">Approved</SelectItem>
                  <SelectItem value="ACCEPTED">Accepted</SelectItem>
                  <SelectItem value="COMPLETED">Completed</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                  <SelectItem value="DEFAULTED">Defaulted</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>OTS Reference</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-right">Settlement</TableHead>
                <TableHead className="text-right">Haircut</TableHead>
                <TableHead>Valid Until</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading OTS proposals...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8">
                    <ErrorState
                      title="Could not load OTS proposals"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : proposals.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No OTS proposals found
                  </TableCell>
                </TableRow>
              ) : (
                proposals.map((proposal) => {
                  const status = statusConfig[proposal.status];
                  const StatusIcon = status.icon;
                  return (
                    <TableRow
                      key={proposal.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/admin/lending/collections/ots/${proposal.id}`)}
                    >
                      <TableCell>
                        <div className="font-mono text-sm">{proposal.otsReference}</div>
                        <div className="text-xs text-muted-foreground">
                          {proposal.loanAccountNumber ?? '—'}
                        </div>
                      </TableCell>
                      <TableCell>{proposal.entityName ?? '—'}</TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={proposal.totalOutstanding} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={proposal.otsAmount} abbreviated />
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={proposal.haircutAmount} abbreviated />
                        <div className="text-xs text-muted-foreground">
                          <PercentageDisplay value={proposal.haircutPercent} />
                        </div>
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={proposal.validTill} />
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={status.color}>
                          <StatusIcon className="mr-1 h-3 w-3" />
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/admin/lending/collections/ots/${proposal.id}`);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
