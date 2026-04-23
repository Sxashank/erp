import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Download,
  Upload,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Eye,
  FileText,
  RefreshCw,
  Filter,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatDate, formatDateTime } from '@/lib/utils';

// Types
type TransactionType = 'SEARCH' | 'DOWNLOAD' | 'UPLOAD' | 'UPDATE';
type TransactionStatus = 'INITIATED' | 'SUCCESS' | 'FAILED' | 'PENDING';

interface CKYCTransaction {
  id: string;
  transaction_type: TransactionType;
  entity_id: string;
  entity_name: string;
  pan?: string;
  ckyc_number?: string;
  status: TransactionStatus;
  initiated_at: string;
  completed_at?: string;
  initiated_by: string;
  error_message?: string;
  response_summary?: string;
}

// Mock data
const transactionSummary = {
  total_transactions: 156,
  successful: 142,
  failed: 8,
  pending: 6,
};

const transactions: CKYCTransaction[] = [
  {
    id: '1',
    transaction_type: 'SEARCH',
    entity_id: 'ent-001',
    entity_name: 'John Doe',
    pan: 'ABCPD1234F',
    ckyc_number: 'CKYC123456789012345',
    status: 'SUCCESS',
    initiated_at: '2024-12-20T10:30:00',
    completed_at: '2024-12-20T10:30:05',
    initiated_by: 'Admin User',
    response_summary: 'CKYC record found',
  },
  {
    id: '2',
    transaction_type: 'DOWNLOAD',
    entity_id: 'ent-001',
    entity_name: 'John Doe',
    ckyc_number: 'CKYC123456789012345',
    status: 'SUCCESS',
    initiated_at: '2024-12-20T10:32:00',
    completed_at: '2024-12-20T10:32:10',
    initiated_by: 'Admin User',
    response_summary: 'Complete record downloaded',
  },
  {
    id: '3',
    transaction_type: 'SEARCH',
    entity_id: 'ent-002',
    entity_name: 'ABC Corp',
    pan: 'XYZPQ5678G',
    status: 'SUCCESS',
    initiated_at: '2024-12-19T14:15:00',
    completed_at: '2024-12-19T14:15:03',
    initiated_by: 'Admin User',
    response_summary: 'No CKYC record found',
  },
  {
    id: '4',
    transaction_type: 'UPLOAD',
    entity_id: 'ent-002',
    entity_name: 'ABC Corp',
    pan: 'XYZPQ5678G',
    status: 'PENDING',
    initiated_at: '2024-12-19T14:20:00',
    initiated_by: 'Admin User',
    response_summary: 'CKYC registration in progress',
  },
  {
    id: '5',
    transaction_type: 'SEARCH',
    entity_id: 'ent-003',
    entity_name: 'Jane Smith',
    pan: 'LMNRS9012H',
    status: 'FAILED',
    initiated_at: '2024-12-18T09:00:00',
    completed_at: '2024-12-18T09:00:02',
    initiated_by: 'Admin User',
    error_message: 'CKYC API timeout - please retry',
  },
  {
    id: '6',
    transaction_type: 'UPDATE',
    entity_id: 'ent-004',
    entity_name: 'Mike Johnson',
    ckyc_number: 'CKYC987654321098765',
    status: 'SUCCESS',
    initiated_at: '2024-12-17T16:45:00',
    completed_at: '2024-12-17T16:45:15',
    initiated_by: 'Admin User',
    response_summary: 'Address updated successfully',
  },
];

const getTransactionTypeBadge = (type: TransactionType) => {
  const typeConfig: Record<TransactionType, { icon: React.ReactNode; label: string; color: string }> = {
    SEARCH: { icon: <Search className="h-3 w-3 mr-1" />, label: 'Search', color: 'bg-blue-100 text-blue-800' },
    DOWNLOAD: { icon: <Download className="h-3 w-3 mr-1" />, label: 'Download', color: 'bg-green-100 text-green-800' },
    UPLOAD: { icon: <Upload className="h-3 w-3 mr-1" />, label: 'Upload', color: 'bg-purple-100 text-purple-800' },
    UPDATE: { icon: <RefreshCw className="h-3 w-3 mr-1" />, label: 'Update', color: 'bg-orange-100 text-orange-800' },
  };

  const config = typeConfig[type];
  return (
    <Badge variant="secondary" className={`flex items-center w-fit ${config.color}`}>
      {config.icon}
      {config.label}
    </Badge>
  );
};

const getStatusBadge = (status: TransactionStatus) => {
  const statusConfig: Record<TransactionStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    INITIATED: { variant: 'outline', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Initiated' },
    SUCCESS: { variant: 'default', icon: <CheckCircle className="h-3 w-3 mr-1" />, label: 'Success' },
    FAILED: { variant: 'destructive', icon: <XCircle className="h-3 w-3 mr-1" />, label: 'Failed' },
    PENDING: { variant: 'secondary', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Pending' },
  };

  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className="flex items-center w-fit">
      {config.icon}
      {config.label}
    </Badge>
  );
};

export default function CKYCStatus() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredTransactions = transactions.filter((t) => {
    const matchesSearch =
      t.entity_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.pan?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.ckyc_number?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || t.transaction_type === typeFilter;
    const matchesStatus = statusFilter === 'all' || t.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="CKYC Transaction History"
        subtitle="View all CKYC search, download, and upload transactions"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/kyc/ckyc/search')}>
              <Search className="h-4 w-4 mr-2" />
              Search CKYC
            </Button>
            <Button onClick={() => navigate('/admin/kyc/ckyc/upload')}>
              <Upload className="h-4 w-4 mr-2" />
              Upload New
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Transactions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{transactionSummary.total_transactions}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Successful</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {transactionSummary.successful}
            </div>
            <p className="text-xs text-muted-foreground">
              {Math.round((transactionSummary.successful / transactionSummary.total_transactions) * 100)}% success rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Failed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{transactionSummary.failed}</div>
            <p className="text-xs text-muted-foreground">Require attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">{transactionSummary.pending}</div>
            <p className="text-xs text-muted-foreground">In progress</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by entity, PAN, or CKYC number..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="SEARCH">Search</SelectItem>
                <SelectItem value="DOWNLOAD">Download</SelectItem>
                <SelectItem value="UPLOAD">Upload</SelectItem>
                <SelectItem value="UPDATE">Update</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="SUCCESS">Success</SelectItem>
                <SelectItem value="FAILED">Failed</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
          <CardDescription>{filteredTransactions.length} transactions found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>PAN/CKYC</TableHead>
                <TableHead>Initiated</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Result</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTransactions.map((txn) => (
                <TableRow key={txn.id}>
                  <TableCell>{getTransactionTypeBadge(txn.transaction_type)}</TableCell>
                  <TableCell>
                    <div className="font-medium">{txn.entity_name}</div>
                    <div className="text-xs text-muted-foreground">ID: {txn.entity_id}</div>
                  </TableCell>
                  <TableCell>
                    {txn.pan && <div className="font-medium">{txn.pan}</div>}
                    {txn.ckyc_number && (
                      <div className="text-sm text-muted-foreground">{txn.ckyc_number}</div>
                    )}
                    {!txn.pan && !txn.ckyc_number && (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">{formatDateTime(txn.initiated_at)}</div>
                    <div className="text-xs text-muted-foreground">by {txn.initiated_by}</div>
                  </TableCell>
                  <TableCell>{getStatusBadge(txn.status)}</TableCell>
                  <TableCell>
                    {txn.response_summary && (
                      <div className="text-sm text-green-700">{txn.response_summary}</div>
                    )}
                    {txn.error_message && (
                      <div className="text-sm text-red-600 flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" />
                        {txn.error_message}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {txn.status === 'FAILED' && (
                          <DropdownMenuItem>
                            <RefreshCw className="h-4 w-4 mr-2" />
                            Retry
                          </DropdownMenuItem>
                        )}
                        {txn.ckyc_number && txn.status === 'SUCCESS' && (
                          <DropdownMenuItem
                            onClick={() =>
                              navigate(`/admin/kyc/ckyc/download?ckyc=${txn.ckyc_number}`)
                            }
                          >
                            <Download className="h-4 w-4 mr-2" />
                            Download Record
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
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
