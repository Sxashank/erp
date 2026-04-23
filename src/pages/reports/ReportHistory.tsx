import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
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
  ArrowLeft,
  History,
  Download,
  Eye,
  RefreshCw,
  Search,
  Filter,
  FileText,
  FileSpreadsheet,
  File,
  CheckCircle,
  XCircle,
  Clock,
  Trash2,
  RotateCcw,
} from 'lucide-react';

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Mock report history data
const reportHistory = [
  {
    id: '1',
    name: 'Daily Collection Report',
    type: 'collection',
    category: 'MIS',
    generatedAt: '2025-01-16 06:00:15',
    generatedBy: 'System (Scheduled)',
    status: 'COMPLETED',
    format: 'xlsx',
    fileSize: 245760,
    duration: 8.5,
    parameters: { fromDate: '2025-01-15', toDate: '2025-01-15' },
    downloadCount: 3,
  },
  {
    id: '2',
    name: 'Portfolio Summary',
    type: 'portfolio_summary',
    category: 'MIS',
    generatedAt: '2025-01-15 14:32:45',
    generatedBy: 'John Manager',
    status: 'COMPLETED',
    format: 'pdf',
    fileSize: 892000,
    duration: 12.3,
    parameters: { asOfDate: '2025-01-15' },
    downloadCount: 5,
  },
  {
    id: '3',
    name: 'NPA Classification Report',
    type: 'npa',
    category: 'Regulatory',
    generatedAt: '2025-01-15 10:15:22',
    generatedBy: 'Compliance Team',
    status: 'COMPLETED',
    format: 'xlsx',
    fileSize: 156000,
    duration: 6.2,
    parameters: { asOfDate: '2025-01-15', detailed: true },
    downloadCount: 2,
  },
  {
    id: '4',
    name: 'ALM Report - Structural',
    type: 'alm',
    category: 'Regulatory',
    generatedAt: '2025-01-15 09:00:00',
    generatedBy: 'System (Scheduled)',
    status: 'FAILED',
    format: 'pdf',
    fileSize: 0,
    duration: 45.0,
    parameters: { asOfDate: '2025-01-15', reportType: 'STRUCTURAL' },
    downloadCount: 0,
    error: 'Database connection timeout',
  },
  {
    id: '5',
    name: 'Delinquency Report',
    type: 'delinquency',
    category: 'MIS',
    generatedAt: '2025-01-15 07:00:10',
    generatedBy: 'System (Scheduled)',
    status: 'COMPLETED',
    format: 'xlsx',
    fileSize: 178000,
    duration: 5.8,
    parameters: { asOfDate: '2025-01-15' },
    downloadCount: 8,
  },
  {
    id: '6',
    name: 'Trial Balance',
    type: 'trial_balance',
    category: 'Financial',
    generatedAt: '2025-01-14 18:30:00',
    generatedBy: 'Finance Team',
    status: 'COMPLETED',
    format: 'xlsx',
    fileSize: 324000,
    duration: 15.2,
    parameters: { asOfDate: '2025-01-14' },
    downloadCount: 4,
  },
  {
    id: '7',
    name: 'CRAR Report',
    type: 'crar',
    category: 'Regulatory',
    generatedAt: '2025-01-14 16:45:33',
    generatedBy: 'Risk Team',
    status: 'COMPLETED',
    format: 'pdf',
    fileSize: 567000,
    duration: 22.1,
    parameters: { asOfDate: '2025-01-14' },
    downloadCount: 3,
  },
  {
    id: '8',
    name: 'Branch Performance Report',
    type: 'branch_performance',
    category: 'MIS',
    generatedAt: '2025-01-14 12:00:00',
    generatedBy: 'Operations Head',
    status: 'PROCESSING',
    format: 'pdf',
    fileSize: 0,
    duration: 0,
    parameters: { fromDate: '2025-01-01', toDate: '2025-01-14' },
    downloadCount: 0,
  },
  {
    id: '9',
    name: 'Disbursement Report',
    type: 'disbursement',
    category: 'MIS',
    generatedAt: '2025-01-13 17:30:00',
    generatedBy: 'Business Team',
    status: 'COMPLETED',
    format: 'xlsx',
    fileSize: 412000,
    duration: 9.4,
    parameters: { fromDate: '2025-01-01', toDate: '2025-01-13', groupBy: 'PRODUCT' },
    downloadCount: 6,
  },
  {
    id: '10',
    name: 'Profit & Loss Statement',
    type: 'profit_loss',
    category: 'Financial',
    generatedAt: '2025-01-13 11:00:00',
    generatedBy: 'CFO Office',
    status: 'COMPLETED',
    format: 'pdf',
    fileSize: 234000,
    duration: 18.7,
    parameters: { fromDate: '2025-01-01', toDate: '2025-01-12' },
    downloadCount: 12,
  },
];

export default function ReportHistory() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('7days');

  const filteredReports = reportHistory.filter(report => {
    const matchesSearch = report.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.generatedBy.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || report.category === categoryFilter;
    const matchesStatus = statusFilter === 'all' || report.status === statusFilter;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>;
      case 'FAILED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      case 'PROCESSING':
        return <Badge variant="secondary"><RefreshCw className="h-3 w-3 mr-1 animate-spin" />Processing</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <FileText className="h-4 w-4 text-red-500" />;
      case 'xlsx':
        return <FileSpreadsheet className="h-4 w-4 text-green-600" />;
      case 'csv':
        return <File className="h-4 w-4 text-blue-500" />;
      default:
        return <File className="h-4 w-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'MIS':
        return 'bg-green-100 text-green-800';
      case 'Regulatory':
        return 'bg-red-100 text-red-800';
      case 'Financial':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Statistics
  const stats = {
    total: reportHistory.length,
    completed: reportHistory.filter(r => r.status === 'COMPLETED').length,
    failed: reportHistory.filter(r => r.status === 'FAILED').length,
    totalSize: reportHistory.reduce((sum, r) => sum + r.fileSize, 0),
    avgDuration: reportHistory.filter(r => r.duration > 0).reduce((sum, r) => sum + r.duration, 0) /
      reportHistory.filter(r => r.duration > 0).length,
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Report History"
        subtitle="View and download previously generated reports"
        breadcrumbs={[
          { label: 'Reports', to: '/admin/reports' },
          { label: 'History' },
        ]}
      />

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Reports</div>
            <div className="text-2xl font-bold mt-1">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Completed</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{stats.completed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Failed</div>
            <div className="text-2xl font-bold mt-1 text-red-600">{stats.failed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Size</div>
            <div className="text-2xl font-bold mt-1">{formatFileSize(stats.totalSize)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Avg Duration</div>
            <div className="text-2xl font-bold mt-1">{stats.avgDuration.toFixed(1)}s</div>
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
                placeholder="Search reports..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="MIS">MIS</SelectItem>
                  <SelectItem value="Regulatory">Regulatory</SelectItem>
                  <SelectItem value="Financial">Financial</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="COMPLETED">Completed</SelectItem>
                <SelectItem value="FAILED">Failed</SelectItem>
                <SelectItem value="PROCESSING">Processing</SelectItem>
              </SelectContent>
            </Select>
            <Select value={dateFilter} onValueChange={setDateFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Date range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="7days">Last 7 Days</SelectItem>
                <SelectItem value="30days">Last 30 Days</SelectItem>
                <SelectItem value="90days">Last 90 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Report History Table */}
      <Card>
        <CardHeader>
          <CardTitle>Generated Reports</CardTitle>
          <CardDescription>
            Showing {filteredReports.length} of {reportHistory.length} reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Report Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Generated At</TableHead>
                <TableHead>Generated By</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Format</TableHead>
                <TableHead className="text-right">Size</TableHead>
                <TableHead className="text-right">Duration</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredReports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>
                    <div className="font-medium">{report.name}</div>
                    {report.error && (
                      <div className="text-xs text-red-500 mt-1">{report.error}</div>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={getCategoryColor(report.category)}>
                      {report.category}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{report.generatedAt}</TableCell>
                  <TableCell className="text-sm">{report.generatedBy}</TableCell>
                  <TableCell>{getStatusBadge(report.status)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      {getFormatIcon(report.format)}
                      <span className="text-sm uppercase">{report.format}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right text-sm">
                    {report.fileSize > 0 ? formatFileSize(report.fileSize) : '-'}
                  </TableCell>
                  <TableCell className="text-right text-sm">
                    {report.duration > 0 ? `${report.duration.toFixed(1)}s` : '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      {report.status === 'COMPLETED' && (
                        <>
                          <Button variant="ghost" size="sm" title="View">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" title="Download">
                            <Download className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      {report.status === 'FAILED' && (
                        <Button variant="ghost" size="sm" title="Retry">
                          <RotateCcw className="h-4 w-4" />
                        </Button>
                      )}
                      <Button variant="ghost" size="sm" title="Delete">
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Storage Info */}
      <Card>
        <CardHeader>
          <CardTitle>Storage Usage</CardTitle>
          <CardDescription>Report storage statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Used Storage</span>
              <span className="font-medium">{formatFileSize(stats.totalSize)} / 10 GB</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full"
                style={{ width: `${(stats.totalSize / (10 * 1024 * 1024 * 1024)) * 100}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Reports auto-delete after 90 days</span>
              <Button variant="outline" size="sm">
                <Trash2 className="h-4 w-4 mr-2" />
                Clear Old Reports
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
