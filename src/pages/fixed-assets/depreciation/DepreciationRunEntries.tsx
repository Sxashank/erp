import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle, Send } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { fixedAssetsApi } from '@/services/api';

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
  voucher_number?: string;
}

interface DepreciationEntry {
  id: string;
  asset_id: string;
  asset_code?: string;
  asset_name?: string;
  depreciation_period: string;
  days_in_period: number;
  opening_wdv: number;
  depreciation_rate: number;
  depreciation_amount: number;
  accumulated_depreciation: number;
  closing_wdv: number;
  is_posted: boolean;
}

export function DepreciationRunEntries() {
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<DepreciationRun | null>(null);
  const [entries, setEntries] = useState<DepreciationEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const limit = 50;

  useEffect(() => {
    if (runId) {
      fetchRun();
      fetchEntries();
    }
  }, [runId, skip]);

  const fetchRun = async () => {
    try {
      const response = await fixedAssetsApi.getDepreciationRun(runId!);
      setRun(response.data);
    } catch (error) {
      console.error('Failed to fetch depreciation run:', error);
    }
  };

  const fetchEntries = async () => {
    try {
      setLoading(true);
      const response = await fixedAssetsApi.getRunEntries(runId!, { skip, limit });
      setEntries(response.data.items || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to fetch depreciation entries:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePostRun = async () => {
    if (!run || !confirm('Are you sure you want to post this depreciation run? This will create GL entries.')) return;
    try {
      setPosting(true);
      await fixedAssetsApi.postDepreciationRun(run.id);
      fetchRun();
      fetchEntries();
    } catch (error: any) {
      console.error('Failed to post depreciation run:', error);
      alert(error.response?.data?.detail || 'Failed to post depreciation run');
    } finally {
      setPosting(false);
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

  const formatPeriod = (period: string) => {
    const [year, month] = period.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
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

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(skip / limit) + 1;

  if (!run && !loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-sm text-slate-500">Depreciation run not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Depreciation Entries${run ? ' - ' + formatPeriod(run.depreciation_period) : ''}`}
        subtitle="View depreciation entries for this run"
        breadcrumbs={[
          { label: 'Depreciation', to: '/admin/fixed-assets/depreciation' },
          { label: 'Entries' },
        ]}
        actions={
          run?.status === 'COMPLETED' ? (
            <Button onClick={handlePostRun} disabled={posting}>
              <Send className="mr-2 h-4 w-4" />
              {posting ? 'Posting...' : 'Post to GL'}
            </Button>
          ) : undefined
        }
      />

      {/* Run Summary */}
      {run && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Run Summary</CardTitle>
                <CardDescription>
                  Period: {run.period_from} to {run.period_to}
                </CardDescription>
              </div>
              {getStatusBadge(run.status)}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-4">
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-2xl font-bold text-slate-900">{run.total_assets}</p>
                <p className="text-sm text-slate-500">Total Assets</p>
              </div>
              <div className="text-center p-4 bg-emerald-50 rounded-lg">
                <p className="text-2xl font-bold text-emerald-700">{run.processed_assets}</p>
                <p className="text-sm text-slate-500">Processed</p>
              </div>
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-2xl font-bold text-slate-600">{run.skipped_assets}</p>
                <p className="text-sm text-slate-500">Skipped</p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-700">{formatCurrency(run.total_depreciation)}</p>
                <p className="text-sm text-slate-500">Total Depreciation</p>
              </div>
            </div>
            {run.voucher_number && (
              <div className="mt-4 p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">
                  GL Voucher: <Badge variant="outline">{run.voucher_number}</Badge>
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Entries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Depreciation Entries</CardTitle>
          <CardDescription>
            {total} entries in this run
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading entries...</p>
            </div>
          ) : entries.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">No entries found</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Asset</TableHead>
                    <TableHead className="text-right">Days</TableHead>
                    <TableHead className="text-right">Opening WDV</TableHead>
                    <TableHead className="text-right">Rate</TableHead>
                    <TableHead className="text-right">Depreciation</TableHead>
                    <TableHead className="text-right">Acc. Dep.</TableHead>
                    <TableHead className="text-right">Closing WDV</TableHead>
                    <TableHead>Posted</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{entry.asset_code}</p>
                          <p className="text-xs text-slate-500">{entry.asset_name}</p>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{entry.days_in_period}</TableCell>
                      <TableCell className="text-right">{formatCurrency(entry.opening_wdv)}</TableCell>
                      <TableCell className="text-right">{entry.depreciation_rate}%</TableCell>
                      <TableCell className="text-right font-medium text-red-600">
                        {formatCurrency(entry.depreciation_amount)}
                      </TableCell>
                      <TableCell className="text-right text-slate-600">
                        {formatCurrency(entry.accumulated_depreciation)}
                      </TableCell>
                      <TableCell className="text-right font-medium text-emerald-600">
                        {formatCurrency(entry.closing_wdv)}
                      </TableCell>
                      <TableCell>
                        {entry.is_posted ? (
                          <CheckCircle className="h-4 w-4 text-emerald-500" />
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <p className="text-sm text-slate-500">
                    Showing {skip + 1} to {Math.min(skip + limit, total)} of {total} entries
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
