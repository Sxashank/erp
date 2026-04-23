/**
 * Account Aggregator Consent List Page
 * Displays all AA consents with filtering and management options
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Filter,
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
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

// AA Consent Status
type AAConsentStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'ACTIVE'
  | 'REJECTED'
  | 'PAUSED'
  | 'REVOKED'
  | 'EXPIRED'
  | 'FAILED';

type AAProvider = 'FINVU' | 'ONEMONEY' | 'SETU' | 'NADL' | 'CAMS_FINSERV' | 'PERFIOS';

type AAPurpose =
  | 'UNDERWRITING'
  | 'MONITORING'
  | 'BANK_STATEMENT_ANALYSIS'
  | 'INCOME_VERIFICATION'
  | 'ACCOUNT_AGGREGATION';

interface AAConsent {
  id: string;
  consentHandle: string;
  consentId?: string;
  customerId: string;
  customerName: string;
  customerMobile?: string;
  provider: AAProvider;
  purpose: AAPurpose;
  fiTypes: string[];
  dataFrom: string;
  dataTo: string;
  status: AAConsentStatus;
  consentExpiry?: string;
  entityName?: string;
  loanApplicationNumber?: string;
  fetchSessionCount: number;
  lastFetchAt?: string;
  createdAt: string;
  approvedAt?: string;
  rejectedAt?: string;
  revokedAt?: string;
}

// Status badge colors
const statusColors: Record<AAConsentStatus, string> = {
  PENDING: 'bg-amber-100 text-amber-700 border-amber-300',
  APPROVED: 'bg-blue-100 text-blue-700 border-blue-300',
  ACTIVE: 'bg-green-100 text-green-700 border-green-300',
  REJECTED: 'bg-red-100 text-red-700 border-red-300',
  PAUSED: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  REVOKED: 'bg-slate-100 text-slate-700 border-slate-300',
  EXPIRED: 'bg-gray-100 text-gray-600 border-gray-300',
  FAILED: 'bg-red-200 text-red-800 border-red-400',
};

const StatusIcon = ({ status }: { status: AAConsentStatus }) => {
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

// Mock data
const mockConsents: AAConsent[] = [
  {
    id: '1',
    consentHandle: 'CNS-2025-001',
    consentId: 'AA-FV-CNS-001',
    customerId: 'user@finvu',
    customerName: 'Rahul Sharma',
    customerMobile: '9876543210',
    provider: 'FINVU',
    purpose: 'UNDERWRITING',
    fiTypes: ['DEPOSIT', 'TERM_DEPOSIT'],
    dataFrom: '2024-01-01',
    dataTo: '2025-01-14',
    status: 'ACTIVE',
    consentExpiry: '2025-07-14',
    entityName: 'ABC Industries Pvt Ltd',
    loanApplicationNumber: 'APP-2025-0001',
    fetchSessionCount: 3,
    lastFetchAt: '2025-01-10T14:30:00',
    createdAt: '2025-01-05T10:00:00',
    approvedAt: '2025-01-05T10:15:00',
  },
  {
    id: '2',
    consentHandle: 'CNS-2025-002',
    customerId: 'customer@onemoney',
    customerName: 'Priya Patel',
    customerMobile: '9876543211',
    provider: 'ONEMONEY',
    purpose: 'BANK_STATEMENT_ANALYSIS',
    fiTypes: ['DEPOSIT'],
    dataFrom: '2024-07-01',
    dataTo: '2025-01-14',
    status: 'PENDING',
    entityName: 'XYZ Trading Co',
    loanApplicationNumber: 'APP-2025-0015',
    fetchSessionCount: 0,
    createdAt: '2025-01-14T09:00:00',
  },
  {
    id: '3',
    consentHandle: 'CNS-2025-003',
    consentId: 'AA-ST-CNS-003',
    customerId: 'user123@setu',
    customerName: 'Amit Kumar',
    customerMobile: '9876543212',
    provider: 'SETU',
    purpose: 'MONITORING',
    fiTypes: ['DEPOSIT', 'RECURRING_DEPOSIT', 'MUTUAL_FUNDS'],
    dataFrom: '2024-01-01',
    dataTo: '2025-01-14',
    status: 'REJECTED',
    entityName: 'Kumar Enterprises',
    fetchSessionCount: 0,
    createdAt: '2025-01-12T11:00:00',
    rejectedAt: '2025-01-12T11:05:00',
  },
  {
    id: '4',
    consentHandle: 'CNS-2025-004',
    consentId: 'AA-FV-CNS-004',
    customerId: 'test@finvu',
    customerName: 'Sneha Reddy',
    customerMobile: '9876543213',
    provider: 'FINVU',
    purpose: 'INCOME_VERIFICATION',
    fiTypes: ['DEPOSIT'],
    dataFrom: '2023-01-01',
    dataTo: '2025-01-14',
    status: 'ACTIVE',
    consentExpiry: '2025-06-01',
    entityName: 'Reddy & Sons',
    loanApplicationNumber: 'APP-2024-0089',
    fetchSessionCount: 5,
    lastFetchAt: '2025-01-13T16:45:00',
    createdAt: '2024-12-01T14:00:00',
    approvedAt: '2024-12-01T14:20:00',
  },
  {
    id: '5',
    consentHandle: 'CNS-2024-099',
    consentId: 'AA-OM-CNS-099',
    customerId: 'expired@onemoney',
    customerName: 'Vikram Singh',
    provider: 'ONEMONEY',
    purpose: 'UNDERWRITING',
    fiTypes: ['DEPOSIT'],
    dataFrom: '2024-01-01',
    dataTo: '2024-06-30',
    status: 'EXPIRED',
    consentExpiry: '2024-12-31',
    entityName: 'Singh Industries',
    fetchSessionCount: 2,
    lastFetchAt: '2024-06-15T10:00:00',
    createdAt: '2024-06-01T09:00:00',
    approvedAt: '2024-06-01T09:30:00',
  },
];

export default function ConsentList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [providerFilter, setProviderFilter] = useState<string>('all');

  // Filter consents
  const filteredConsents = mockConsents.filter((consent) => {
    const matchesSearch =
      searchTerm === '' ||
      consent.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      consent.consentHandle.toLowerCase().includes(searchTerm.toLowerCase()) ||
      consent.customerId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      consent.entityName?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || consent.status === statusFilter;
    const matchesProvider = providerFilter === 'all' || consent.provider === providerFilter;

    return matchesSearch && matchesStatus && matchesProvider;
  });

  // Calculate statistics
  const stats = {
    total: mockConsents.length,
    active: mockConsents.filter((c) => c.status === 'ACTIVE').length,
    pending: mockConsents.filter((c) => c.status === 'PENDING').length,
    expired: mockConsents.filter((c) => c.status === 'EXPIRED' || c.status === 'REVOKED').length,
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Account Aggregator Consents"
        subtitle="Manage customer consents for fetching financial data via Account Aggregator"
        actions={
          <Button onClick={() => navigate('/lending/aa/request-consent')}>
            <Plus className="mr-2 h-4 w-4" />
            Request Consent
          </Button>
        }
      />

      {/* Statistics Cards */}
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

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
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
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Consents Table */}
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
              {filteredConsents.map((consent) => (
                <TableRow key={consent.id}>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="font-medium">{consent.consentHandle}</div>
                      {consent.entityName && (
                        <div className="text-xs text-muted-foreground">{consent.entityName}</div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{consent.customerName}</span>
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
                      <DateDisplay date={consent.dataFrom} format="short" /> -
                      <DateDisplay date={consent.dataTo} format="short" />
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={`font-medium border ${statusColors[consent.status]}`}
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
                          onClick={() => navigate(`/lending/aa/consents/${consent.id}`)}
                        >
                          <Eye className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        {consent.status === 'PENDING' && (
                          <>
                            <DropdownMenuItem
                              onClick={() =>
                                window.open(
                                  `https://aa-provider.example/consent/${consent.consentHandle}`,
                                  '_blank'
                                )
                              }
                            >
                              <Link className="mr-2 h-4 w-4" />
                              Open Consent Link
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <RefreshCw className="mr-2 h-4 w-4" />
                              Refresh Status
                            </DropdownMenuItem>
                          </>
                        )}
                        {(consent.status === 'ACTIVE' || consent.status === 'APPROVED') && (
                          <>
                            <DropdownMenuItem
                              onClick={() =>
                                navigate(`/lending/aa/consents/${consent.id}/fetch`)
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
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {filteredConsents.length === 0 && (
            <div className="text-center py-12">
              <Database className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium">No consents found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search or filter criteria
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
