/**
 * Account Aggregator Consent List Page
 * Displays all AA consents with filtering and management options.
 *
 * Data source: GET /lending/aa/consents (camelCase via Pydantic CamelSchema).
 */

import {
  Plus,
  Search,
  MoreHorizontal,
  Eye,
  RefreshCw,
  Ban,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Link,
  Database,
  User,
  Loader2,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
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
  useAAConsents,
  type AAConsentListItem,
  type AAConsentStatusValue,
  type AAProviderValue,
  type AAConsentFilters,
} from '@/hooks/lending/useAAConsents';

const statusColors: Record<AAConsentStatusValue, string> = {
  PENDING: 'bg-amber-100 text-amber-700 border-amber-300',
  APPROVED: 'bg-blue-100 text-blue-700 border-blue-300',
  ACTIVE: 'bg-green-100 text-green-700 border-green-300',
  REJECTED: 'bg-red-100 text-red-700 border-red-300',
  PAUSED: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  REVOKED: 'bg-slate-100 text-slate-700 border-slate-300',
  EXPIRED: 'bg-gray-100 text-gray-600 border-gray-300',
  FAILED: 'bg-red-200 text-red-800 border-red-400',
};

const StatusIcon = ({ status }: { status: AAConsentStatusValue }) => {
  switch (status) {
    case 'ACTIVE':
    case 'APPROVED':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'PENDING':
      return <Clock className="h-4 w-4 text-amber-600" />;
    case 'REJECTED':
    case 'FAILED':
      return <XCircle className="h-4 w-4 text-red-600" />;
    case 'REVOKED':
    case 'EXPIRED':
      return <Ban className="h-4 w-4 text-slate-500" />;
    case 'PAUSED':
      return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    default:
      return null;
  }
};

export default function ConsentList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [providerFilter, setProviderFilter] = useState<string>('all');

  const filters: AAConsentFilters = {
    pageSize: 100,
    ...(statusFilter !== 'all' && { status: statusFilter as AAConsentStatusValue }),
    ...(providerFilter !== 'all' && { provider: providerFilter as AAProviderValue }),
  };
  const { data, isLoading, isError, error, refetch } = useAAConsents(filters);

  const all: AAConsentListItem[] = data?.items ?? [];
  const consents = all.filter((c) => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      (c.customerName ?? '').toLowerCase().includes(q) ||
      (c.consentHandle ?? '').toLowerCase().includes(q) ||
      c.customerId.toLowerCase().includes(q) ||
      (c.entityName ?? '').toLowerCase().includes(q)
    );
  });

  const stats = {
    total: data?.total ?? consents.length,
    active: consents.filter((c) => c.status === 'ACTIVE').length,
    pending: consents.filter((c) => c.status === 'PENDING').length,
    expired: consents.filter((c) => c.status === 'EXPIRED' || c.status === 'REVOKED').length,
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Account Aggregator Consents"
        subtitle="Manage customer consents for fetching financial data via Account Aggregator"
        actions={
          <Button onClick={() => navigate('/admin/lending/aa/consents/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Request Consent
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Consents</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Consents</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.active}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expired/Revoked</CardTitle>
            <Ban className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-600">{stats.expired}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="min-w-[200px] flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by customer name, VUA, or handle..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="ACTIVE">Active</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
                <SelectItem value="REVOKED">Revoked</SelectItem>
                <SelectItem value="EXPIRED">Expired</SelectItem>
                <SelectItem value="PAUSED">Paused</SelectItem>
                <SelectItem value="FAILED">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={providerFilter} onValueChange={setProviderFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                <SelectItem value="FINVU">Finvu</SelectItem>
                <SelectItem value="ONEMONEY">OneMoney</SelectItem>
                <SelectItem value="SETU">Setu</SelectItem>
                <SelectItem value="NADL">NADL</SelectItem>
                <SelectItem value="CAMS_FINSERV">CAMS Finserv</SelectItem>
                <SelectItem value="PERFIOS">Perfios</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Consent Handle</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Purpose</TableHead>
                <TableHead>FI Types</TableHead>
                <TableHead>Data Range</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Fetches</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                    <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />
                    Loading consents...
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8">
                    <ErrorState
                      title="Could not load AA consents"
                      error={error}
                      onRetry={() => refetch()}
                    />
                  </TableCell>
                </TableRow>
              ) : consents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-12">
                    <div className="text-center">
                      <Database className="mx-auto h-12 w-12 text-muted-foreground" />
                      <h3 className="mt-4 text-lg font-medium">No consents found</h3>
                      <p className="text-muted-foreground">
                        Try adjusting your search or filter criteria
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                consents.map((consent) => (
                  <TableRow key={consent.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-mono text-sm font-medium">
                          {consent.consentHandle ?? '—'}
                        </div>
                        {consent.entityName && (
                          <div className="text-xs text-muted-foreground">{consent.entityName}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{consent.customerName ?? '—'}</span>
                        </div>
                        <div className="text-xs text-muted-foreground">{consent.customerId}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono">
                        {consent.provider}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{consent.purpose.replace(/_/g, ' ')}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {consent.fiTypes.slice(0, 2).map((type) => (
                          <Badge key={type} variant="secondary" className="text-xs">
                            {type}
                          </Badge>
                        ))}
                        {consent.fiTypes.length > 2 && (
                          <Badge variant="secondary" className="text-xs">
                            +{consent.fiTypes.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {consent.fiDataFrom && consent.fiDataTo ? (
                          <>
                            <DateDisplay date={consent.fiDataFrom} format="short" /> →{' '}
                            <DateDisplay date={consent.fiDataTo} format="short" />
                          </>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`border font-medium ${statusColors[consent.status]}`}
                      >
                        <StatusIcon status={consent.status} />
                        <span className="ml-1">{consent.status}</span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-center">
                        <div className="font-medium">{consent.fetchSessionCount}</div>
                        {consent.lastFetchAt && (
                          <div className="text-xs text-muted-foreground">
                            Last: <DateDisplay date={consent.lastFetchAt} format="relative" />
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => navigate(`/admin/lending/aa/consents/${consent.id}`)}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          {consent.status === 'PENDING' && (
                            <DropdownMenuItem onClick={() => refetch()}>
                              <RefreshCw className="mr-2 h-4 w-4" />
                              Refresh Status
                            </DropdownMenuItem>
                          )}
                          {(consent.status === 'ACTIVE' || consent.status === 'APPROVED') && (
                            <>
                              <DropdownMenuItem
                                onClick={() =>
                                  navigate(`/admin/lending/aa/consents/${consent.id}/fetch`)
                                }
                              >
                                <Database className="mr-2 h-4 w-4" />
                                Fetch Data
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-red-600">
                                <Ban className="mr-2 h-4 w-4" />
                                Revoke Consent
                              </DropdownMenuItem>
                            </>
                          )}
                          {consent.status === 'PENDING' && consent.consentHandle && (
                            <DropdownMenuItem
                              onClick={() =>
                                window.open(
                                  `https://aa-provider.example/consent/${consent.consentHandle}`,
                                  '_blank',
                                )
                              }
                            >
                              <Link className="mr-2 h-4 w-4" />
                              Open Consent Link
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
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
