import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calculator,
  Calendar,
  Clock,
  Eye,
  Play,
  RefreshCw,
  Send,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { fixedAssetsApi, organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

interface DepreciationRun {
  id: string;
  organization_id: string;
  depreciation_period: string;
  period_from: string;
  period_to: string;
  total_assets: number;
  total_depreciation: number;
  processed_assets: number;
  skipped_assets: number;
  status: string;
  run_started_at?: string;
  run_completed_at?: string;
  run_by?: string;
  voucher_id?: string;
  voucher_number?: string;
  posted_at?: string;
  posted_by?: string;
  remarks?: string;
  created_at: string;
}

export function DepreciationRunPage() {
  const navigate = useNavigate();
  const [runs, setRuns] = useState<DepreciationRun[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const limit = 20;

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchRuns();
    }
  }, [selectedOrgId, skip]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchRuns = async () => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const response = await fixedAssetsApi.listDepreciationRuns({
        organization_id: selectedOrgId,
        skip,
        limit,
      });
      setRuns(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to fetch depreciation runs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePostRun = async (runId: string) => {
    if (!confirm('Are you sure you want to post this depreciation run? This will create GL entries.')) return;
    try {
      await fixedAssetsApi.postDepreciationRun(runId);
      fetchRuns();
    } catch (error: any) {
      console.error('Failed to post depreciation run:', error);
      alert(error.response?.data?.detail || 'Failed to post depreciation run');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Completed</Badge>;
      case 'POSTED':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">Posted</Badge>;
      case 'RUNNING':
        return <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">Running</Badge>;
      case 'FAILED':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatPeriod = (period: string) => {
    const [year, month] = period.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  };

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(skip / limit) + 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Depreciation Run"
        subtitle="Process monthly depreciation for fixed assets"
        actions={
          <Button onClick={() => navigate('/admin/fixed-assets/depreciation/run')}>
            <Play className="mr-2 h-4 w-4" />
            Run Depreciation
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Depreciation Runs</CardTitle>
              <CardDescription>History of depreciation processing runs</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={fetchRuns}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select organization" />
                </SelectTrigger>
                <SelectContent>
                  {organizations.map((org) => (
                    <SelectItem key={org.id} value={org.id}>
                      {org.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : runs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Calculator className="mb-4 h-12 w-12 text-slate-300" />
              <p className="text-sm text-slate-500">No depreciation runs found</p>
              <Button variant="link" onClick={() => navigate('/admin/fixed-assets/depreciation/run')}>
                Run your first depreciation
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Period</TableHead>
                    <TableHead className="text-right">Assets</TableHead>
                    <TableHead className="text-right">Processed</TableHead>
                    <TableHead className="text-right">Skipped</TableHead>
                    <TableHead className="text-right">Total Depreciation</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Voucher</TableHead>
                    <TableHead>Run At</TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow key={run.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-slate-400" />
                          <span className="font-medium">{formatPeriod(run.depreciation_period)}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{run.total_assets}</TableCell>
                      <TableCell className="text-right text-emerald-600">{run.processed_assets}</TableCell>
                      <TableCell className="text-right text-slate-500">{run.skipped_assets}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(run.total_depreciation)}
                      </TableCell>
                      <TableCell>{getStatusBadge(run.status)}</TableCell>
                      <TableCell>
                        {run.voucher_number ? (
                          <Badge variant="outline">{run.voucher_number}</Badge>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm text-slate-500">
                          <Clock className="h-3 w-3" />
                          {formatDateTime(run.run_started_at)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => navigate(`/admin/fixed-assets/depreciation/runs/${run.id}`)}
                            title="View Entries"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {run.status === 'COMPLETED' && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handlePostRun(run.id)}
                              title="Post to GL"
                            >
                              <Send className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-slate-500">
                    Showing {skip + 1} to {Math.min(skip + limit, total)} of {total} runs
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSkip(Math.max(0, skip - limit))}
                      disabled={skip === 0}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSkip(skip + limit)}
                      disabled={currentPage >= totalPages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
