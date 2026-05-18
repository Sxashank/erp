import {
  Calendar,
  ChevronRight,
  Clock,
  FileText,
  Loader2,
  MoreHorizontal,
  Pause,
  Play,
  Plus,
  RefreshCw,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { organizationsApi, recurringVouchersApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Organization {
  id: string;
  name: string;
}

interface RecurringVoucher {
  id: string;
  template_name: string;
  voucher_type_name: string;
  frequency: string;
  total_amount: number;
  next_run_date: string | null;
  last_run_date: string | null;
  completed_occurrences: number;
  total_occurrences: number | null;
  status: string;
  auto_post: boolean;
}

interface RecurringVoucherStats {
  total_active: number;
  total_paused: number;
  due_today: number;
  due_this_week: number;
  total_generated_this_month: number;
  total_amount_this_month: number;
}

interface UpcomingVoucher {
  id: string;
  template_name: string;
  voucher_type_name: string;
  next_run_date: string;
  total_amount: number;
  days_until_due: number;
}

interface ProcessDueResult {
  success: boolean;
}

type RecurringVoucherListParams = Parameters<typeof recurringVouchersApi.list>[0];

const FREQUENCIES = [
  { value: 'DAILY', label: 'Daily' },
  { value: 'WEEKLY', label: 'Weekly' },
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'HALF_YEARLY', label: 'Half-Yearly' },
  { value: 'YEARLY', label: 'Yearly' },
];

const STATUSES = [
  { value: 'ACTIVE', label: 'Active', color: 'bg-emerald-100 text-emerald-700' },
  { value: 'PAUSED', label: 'Paused', color: 'bg-amber-100 text-amber-700' },
  { value: 'COMPLETED', label: 'Completed', color: 'bg-slate-100 text-slate-700' },
  { value: 'CANCELLED', label: 'Cancelled', color: 'bg-red-100 text-red-700' },
];

export function RecurringVouchers() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');

  const [recurringVouchers, setRecurringVouchers] = useState<RecurringVoucher[]>([]);
  const [stats, setStats] = useState<RecurringVoucherStats | null>(null);
  const [upcoming, setUpcoming] = useState<UpcomingVoucher[]>([]);

  const [loading, setLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterFrequency, setFilterFrequency] = useState<string>('');

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      setOrganizations(response.data.items);
      if (response.data.items.length > 0) {
        setSelectedOrgId(response.data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const params: RecurringVoucherListParams = { organization_id: selectedOrgId, page_size: 50 };
      if (filterStatus && filterStatus !== 'ALL') params.status = filterStatus;
      if (filterFrequency && filterFrequency !== 'ALL') params.frequency = filterFrequency;

      const [listRes, statsRes, upcomingRes] = await Promise.all([
        recurringVouchersApi.list(params),
        recurringVouchersApi.getStats(selectedOrgId),
        recurringVouchersApi.getUpcoming(selectedOrgId, 7),
      ]);

      setRecurringVouchers(listRes.data.items);
      setStats(statsRes.data);
      setUpcoming(upcomingRes.data);
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  }, [filterFrequency, filterStatus, selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchData();
    }
  }, [fetchData, selectedOrgId]);

  const handlePause = async (id: string) => {
    try {
      await recurringVouchersApi.pause(id);
      toast({ title: 'Success', description: 'Recurring voucher paused' });
      fetchData();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleResume = async (id: string) => {
    try {
      await recurringVouchersApi.resume(id);
      toast({ title: 'Success', description: 'Recurring voucher resumed' });
      fetchData();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleCancel = async (id: string) => {
    if (!window.confirm('Are you sure you want to cancel this recurring voucher? This cannot be undone.')) return;
    try {
      await recurringVouchersApi.cancel(id);
      toast({ title: 'Success', description: 'Recurring voucher cancelled' });
      fetchData();
    } catch (error) {
      showErrorToast(error, toast);
    }
  };

  const handleProcessDue = async () => {
    try {
      setLoading(true);
      const response = await recurringVouchersApi.processDue(selectedOrgId);
      const results = response.data as ProcessDueResult[];
      const successCount = results.filter((result) => result.success).length;
      toast({ title: 'Processing Complete', description: `${successCount} of ${results.length} vouchers generated successfully` });
      fetchData();
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const s = STATUSES.find((st) => st.value === status);
    return <Badge className={s?.color || 'bg-slate-100'}>{s?.label || status}</Badge>;
  };

  const getFrequencyLabel = (freq: string) => {
    const f = FREQUENCIES.find((fr) => fr.value === freq);
    return f?.label || freq;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recurring Vouchers"
        subtitle="Automate periodic entries like rent, depreciation, salaries"
        actions={
          <div className="flex gap-2">
            <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
              <SelectTrigger className="w-48">
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
            <Button variant="outline" onClick={handleProcessDue} disabled={loading || !stats?.due_today}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Process Due ({stats?.due_today || 0})
            </Button>
            <Button onClick={() => navigate(`/admin/finance/recurring-vouchers/new?org=${selectedOrgId}`)}>
              <Plus className="mr-2 h-4 w-4" />
              New Recurring
            </Button>
          </div>
        }
      />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Active</div>
              <div className="text-2xl font-bold text-emerald-600">{stats.total_active}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Paused</div>
              <div className="text-2xl font-bold text-amber-600">{stats.total_paused}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Due Today</div>
              <div className="text-2xl font-bold text-blue-600">{stats.due_today}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Due This Week</div>
              <div className="text-2xl font-bold text-purple-600">{stats.due_this_week}</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <div className="text-sm text-slate-500">Generated This Month</div>
              <div className="text-2xl font-bold text-slate-800">{stats.total_generated_this_month}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Upcoming Section */}
      {upcoming.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-500" />
              Upcoming This Week
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {upcoming.map((v) => (
                <button
                  type="button"
                  key={v.id}
                  className="flex items-center gap-3 bg-slate-50 rounded-lg px-4 py-2 hover:bg-slate-100 text-left"
                  onClick={() => navigate(`/admin/finance/recurring-vouchers/${v.id}/generate`)}
                >
                  <div>
                    <p className="font-medium text-sm">{v.template_name}</p>
                    <p className="text-xs text-slate-500">
                      {v.days_until_due === 0 ? 'Today' : `In ${v.days_until_due} days`}
                    </p>
                  </div>
                  <Badge variant="outline">
                    <AmountDisplay amount={v.total_amount} />
                  </Badge>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Statuses</SelectItem>
            {STATUSES.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterFrequency} onValueChange={setFilterFrequency}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Frequencies" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Frequencies</SelectItem>
            {FREQUENCIES.map((f) => (
              <SelectItem key={f.value} value={f.value}>
                {f.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : recurringVouchers.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <FileText className="h-12 w-12 mx-auto mb-3 text-slate-300" />
              <p>No recurring vouchers found</p>
              <p className="text-sm">Create one to automate periodic entries</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Template Name</TableHead>
                  <TableHead>Voucher Type</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Next Run</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recurringVouchers.map((rv) => (
                  <TableRow key={rv.id}>
                    <TableCell className="font-medium">{rv.template_name}</TableCell>
                    <TableCell>{rv.voucher_type_name}</TableCell>
                    <TableCell>{getFrequencyLabel(rv.frequency)}</TableCell>
                    <TableCell className="text-right font-mono">
                      <AmountDisplay amount={rv.total_amount} />
                    </TableCell>
                    <TableCell>
                      <DateDisplay date={rv.next_run_date} />
                    </TableCell>
                    <TableCell>
                      {rv.total_occurrences
                        ? `${rv.completed_occurrences} / ${rv.total_occurrences}`
                        : `${rv.completed_occurrences} generated`}
                    </TableCell>
                    <TableCell className="text-center">{getStatusBadge(rv.status)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/admin/finance/recurring-vouchers/${rv.id}/generate`)}>
                            <FileText className="mr-2 h-4 w-4" />
                            Generate Now
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => navigate(`/admin/finance/recurring-vouchers/${rv.id}/edit`)}>
                            <Calendar className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {rv.status === 'ACTIVE' && (
                            <DropdownMenuItem onClick={() => handlePause(rv.id)}>
                              <Pause className="mr-2 h-4 w-4" />
                              Pause
                            </DropdownMenuItem>
                          )}
                          {rv.status === 'PAUSED' && (
                            <DropdownMenuItem onClick={() => handleResume(rv.id)}>
                              <Play className="mr-2 h-4 w-4" />
                              Resume
                            </DropdownMenuItem>
                          )}
                          {(rv.status === 'ACTIVE' || rv.status === 'PAUSED') && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-red-600" onClick={() => handleCancel(rv.id)}>
                                <X className="mr-2 h-4 w-4" />
                                Cancel
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default RecurringVouchers;
