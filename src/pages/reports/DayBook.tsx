import { BookOpen, Eye, FileSpreadsheet, FileText, Filter, Printer } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { reportsApi, organizationsApi, voucherTypesApi } from '@/services/api';
import { exportDayBookToExcel, exportDayBookToPDF } from '@/utils/exportUtils';

import { logger } from '@/lib/logger';
interface Organization {
  id: string;
  name: string;
}

interface VoucherType {
  id: string;
  code: string;
  name: string;
}

interface DayBookEntry {
  voucher_id: string;
  voucher_number: string;
  voucher_date: string;
  voucher_type: string;
  voucher_type_name: string;
  narration: string | null;
  total_debit: number;
  total_credit: number;
  line_count: number;
  status: string;
}

interface DayBookResponse {
  organization_id: string;
  organization_name: string;
  from_date: string;
  to_date: string;
  entries: DayBookEntry[];
  total_vouchers: number;
  total_debit: number;
  total_credit: number;
  generated_at: string;
}

export function DayBook() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [voucherTypes, setVoucherTypes] = useState<VoucherType[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedVoucherTypeId, setSelectedVoucherTypeId] = useState<string>('all');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [reportData, setReportData] = useState<DayBookResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ pageSize: 100 });
      setOrganizations(response.data.items);
      if (response.data.items.length > 0) {
        setSelectedOrgId(response.data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  }, []);

  const fetchVoucherTypes = useCallback(async () => {
    try {
      const response = await voucherTypesApi.list({ pageSize: 100 });
      setVoucherTypes(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch voucher types:', error);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
    // Set default dates to current month
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    setFromDate(firstDay.toISOString().split('T')[0]);
    setToDate(lastDay.toISOString().split('T')[0]);
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchVoucherTypes();
    }
  }, [fetchVoucherTypes, selectedOrgId]);

  const generateReport = async () => {
    if (!selectedOrgId || !fromDate || !toDate) return;
    try {
      setLoading(true);
      const params: Parameters<typeof reportsApi.getDayBook>[0] = {
        from_date: fromDate,
        to_date: toDate,
      };
      if (selectedVoucherTypeId && selectedVoucherTypeId !== 'all') {
        params.voucher_type_id = selectedVoucherTypeId;
      }
      const response = await reportsApi.getDayBook(params);
      setReportData(response.data);
    } catch (error) {
      logger.error('Failed to generate report:', error);
    } finally {
      setLoading(false);
    }
  };
  const handlePrint = () => {
    window.print();
  };

  const getVoucherTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'JV':
        return 'bg-slate-100 text-slate-700';
      case 'PMT':
        return 'bg-red-50 text-red-700';
      case 'RCT':
        return 'bg-emerald-50 text-emerald-700';
      case 'CNT':
        return 'bg-blue-50 text-blue-700';
      case 'PUR':
        return 'bg-amber-50 text-amber-700';
      case 'SAL':
        return 'bg-purple-50 text-purple-700';
      case 'DN':
        return 'bg-orange-50 text-orange-700';
      case 'CN':
        return 'bg-teal-50 text-teal-700';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  };

  // Group entries by date for the report
  const entriesByDate =
    reportData?.entries.reduce(
      (acc, entry) => {
        const date = entry.voucher_date;
        if (!acc[date]) {
          acc[date] = [];
        }
        acc[date].push(entry);
        return acc;
      },
      {} as Record<string, DayBookEntry[]>,
    ) || {};

  return (
    <div className="space-y-6">
      <PageHeader
        title="Day Book"
        subtitle="Journal Register - All vouchers posted for a period"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePrint} disabled={!reportData}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportDayBookToExcel(reportData)}
              disabled={!reportData}
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportDayBookToPDF(reportData)}
              disabled={!reportData}
            >
              <FileText className="mr-2 h-4 w-4" />
              PDF
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Report Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
            <div>
              <Label>Organization</Label>
              <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
                <SelectTrigger>
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
            <div>
              <Label>Voucher Type</Label>
              <Select value={selectedVoucherTypeId} onValueChange={setSelectedVoucherTypeId}>
                <SelectTrigger>
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {voucherTypes.map((vt) => (
                    <SelectItem key={vt.id} value={vt.id}>
                      {vt.name} ({vt.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>From Date</Label>
              <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </div>
            <div>
              <Label>To Date</Label>
              <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </div>
            <div className="flex items-end">
              <Button
                onClick={generateReport}
                disabled={loading || !selectedOrgId || !fromDate || !toDate}
                className="w-full"
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {reportData && (
        <Card className="print:shadow-none">
          <CardHeader className="print:pb-2">
            <div className="text-center">
              <h2 className="text-xl font-bold">{reportData.organization_name}</h2>
              <h3 className="text-lg font-semibold text-slate-700">Day Book / Journal Register</h3>
              <p className="text-sm text-slate-500">
                From <DateDisplay date={reportData.from_date} /> to{' '}
                <DateDisplay date={reportData.to_date} />
              </p>
            </div>
          </CardHeader>
          <CardContent>
            {/* Summary Cards */}
            <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
              <div className="rounded-lg bg-slate-50 p-4 text-center">
                <p className="text-sm text-slate-500">Total Vouchers</p>
                <p className="text-2xl font-bold text-slate-800">{reportData.total_vouchers}</p>
              </div>
              <div className="rounded-lg bg-blue-50 p-4 text-center">
                <p className="text-sm text-slate-500">Total Debit</p>
                <p className="text-xl font-bold text-blue-700">
                  {formatIndianCompactCurrency(reportData.total_debit)}
                </p>
              </div>
              <div className="rounded-lg bg-red-50 p-4 text-center">
                <p className="text-sm text-slate-500">Total Credit</p>
                <p className="text-xl font-bold text-red-700">
                  {formatIndianCompactCurrency(reportData.total_credit)}
                </p>
              </div>
              <div
                className={`rounded-lg p-4 text-center ${
                  Math.abs(reportData.total_debit - reportData.total_credit) < 0.01
                    ? 'bg-emerald-50'
                    : 'bg-amber-50'
                }`}
              >
                <p className="text-sm text-slate-500">Balance Check</p>
                <p
                  className={`text-lg font-bold ${
                    Math.abs(reportData.total_debit - reportData.total_credit) < 0.01
                      ? 'text-emerald-600'
                      : 'text-amber-600'
                  }`}
                >
                  {Math.abs(reportData.total_debit - reportData.total_credit) < 0.01
                    ? 'Balanced'
                    : `Diff: ${formatIndianCompactCurrency(Math.abs(reportData.total_debit - reportData.total_credit))}`}
                </p>
              </div>
            </div>

            {reportData.entries.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <BookOpen className="mb-4 h-12 w-12 text-slate-300" />
                <p className="text-sm text-slate-500">No vouchers found for the selected period</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead className="w-[100px]">Date</TableHead>
                    <TableHead className="w-[120px]">Voucher No.</TableHead>
                    <TableHead className="w-[100px]">Type</TableHead>
                    <TableHead>Narration</TableHead>
                    <TableHead className="w-[60px] text-center">Lines</TableHead>
                    <TableHead className="w-[130px] text-right">Debit</TableHead>
                    <TableHead className="w-[130px] text-right">Credit</TableHead>
                    <TableHead className="w-[60px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(entriesByDate).map(([dateStr, entries]) => (
                    <>
                      {/* Date Header Row */}
                      <TableRow key={`header-${dateStr}`} className="bg-slate-100">
                        <TableCell colSpan={8} className="font-semibold text-slate-700">
                          <DateDisplay date={dateStr} /> - {entries.length} voucher(s)
                        </TableCell>
                      </TableRow>
                      {/* Voucher Rows */}
                      {entries.map((entry) => (
                        <TableRow key={entry.voucher_id} className="hover:bg-slate-50">
                          <TableCell className="font-mono text-sm text-slate-500">
                            <DateDisplay date={entry.voucher_date} />
                          </TableCell>
                          <TableCell className="font-medium text-blue-600">
                            {entry.voucher_number}
                          </TableCell>
                          <TableCell>
                            <Badge
                              className={`${getVoucherTypeBadgeClass(entry.voucher_type)} hover:${getVoucherTypeBadgeClass(entry.voucher_type)}`}
                            >
                              {entry.voucher_type}
                            </Badge>
                          </TableCell>
                          <TableCell
                            className="max-w-[300px] truncate"
                            title={entry.narration || '-'}
                          >
                            {entry.narration || '-'}
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-slate-200 text-xs font-medium">
                              {entry.line_count}
                            </span>
                          </TableCell>
                          <TableCell className="text-right font-mono text-blue-600">
                            {formatIndianCompactCurrency(entry.total_debit)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-red-600">
                            {formatIndianCompactCurrency(entry.total_credit)}
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() =>
                                navigate(`/admin/finance/vouchers/${entry.voucher_id}`)
                              }
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </>
                  ))}
                  {/* Total Row */}
                  <TableRow className="bg-slate-800 font-bold text-white">
                    <TableCell colSpan={5}>
                      GRAND TOTAL ({reportData.total_vouchers} vouchers)
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatIndianCompactCurrency(reportData.total_debit)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatIndianCompactCurrency(reportData.total_credit)}
                    </TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            )}

            <div className="mt-4 flex justify-between text-xs text-slate-500 print:mt-8">
              <span>Generated on: {new Date(reportData.generated_at).toLocaleString('en-IN')}</span>
              <span>
                Entries: {reportData.total_vouchers} | Total:{' '}
                {formatIndianCompactCurrency(reportData.total_debit)}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
