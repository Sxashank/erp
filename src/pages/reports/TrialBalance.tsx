import { ExternalLink, FileSpreadsheet, FileText, Filter, Printer } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
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
import { reportsApi, organizationsApi, financialYearsApi } from '@/services/api';
import { exportTrialBalanceToExcel, exportTrialBalanceToPDF } from '@/utils/exportUtils';

import { logger } from '@/lib/logger';
interface Organization {
  id: string;
  name: string;
}

interface FinancialYear {
  id: string;
  code: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

interface TrialBalanceItem {
  account_id: string;
  account_code: string;
  account_name: string;
  account_group_name: string;
  account_nature: string;
  opening_debit: number;
  opening_credit: number;
  period_debit: number;
  period_credit: number;
  closing_debit: number;
  closing_credit: number;
}

interface TrialBalanceResponse {
  organization_id: string;
  organization_name: string;
  financial_year_id: string;
  financial_year_name: string;
  from_date: string;
  to_date: string;
  as_on_date: string;
  items: TrialBalanceItem[];
  total_opening_debit: number;
  total_opening_credit: number;
  total_period_debit: number;
  total_period_credit: number;
  total_closing_debit: number;
  total_closing_credit: number;
  generated_at: string;
}

export function TrialBalance() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedFYId, setSelectedFYId] = useState<string>('');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [includeZeroBalance, setIncludeZeroBalance] = useState(false);
  const [reportData, setReportData] = useState<TrialBalanceResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDrillDown = (accountId: string) => {
    // Navigate to account ledger with current date range
    navigate(
      `/admin/reports/account-ledger?account_id=${accountId}&from_date=${fromDate}&to_date=${toDate}&organization_id=${selectedOrgId}`,
    );
  };

  useEffect(() => {
    if (selectedFYId) {
      const fy = financialYears.find((f) => f.id === selectedFYId);
      if (fy) {
        setFromDate(fy.start_date ?? '');
        setToDate(fy.end_date ?? '');
      }
    }
  }, [selectedFYId, financialYears]);

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

  const fetchFinancialYears = useCallback(async () => {
    try {
      const response = await financialYearsApi.list({ pageSize: 100 });
      setFinancialYears(response.data.items);
      const currentFY = response.data.items.find((fy: FinancialYear) => fy.is_current);
      if (currentFY) {
        setSelectedFYId(currentFY.id);
      } else if (response.data.items.length > 0) {
        setSelectedFYId(response.data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch financial years:', error);
    }
  }, [selectedOrgId]);

  useEffect(() => {
    fetchOrganizations();
  }, [fetchOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      fetchFinancialYears();
    }
  }, [fetchFinancialYears, selectedOrgId]);

  const generateReport = async () => {
    if (!selectedOrgId || !selectedFYId) return;
    try {
      setLoading(true);
      const response = await reportsApi.getTrialBalance({
        financial_year_id: selectedFYId,
        from_date: fromDate,
        to_date: toDate,
        include_zero_balance: includeZeroBalance,
      });
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

  const getNatureBadgeClass = (nature: string) => {
    switch (nature) {
      case 'ASSETS':
        return 'bg-blue-50 text-blue-700';
      case 'LIABILITIES':
        return 'bg-red-50 text-red-700';
      case 'INCOME':
        return 'bg-green-50 text-green-700';
      case 'EXPENSES':
        return 'bg-amber-50 text-amber-700';
      case 'EQUITY':
        return 'bg-purple-50 text-purple-700';
      default:
        return 'bg-slate-100 text-slate-600';
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Trial Balance"
        subtitle="View debit and credit balances for all accounts"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePrint} disabled={!reportData}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportTrialBalanceToExcel(reportData)}
              disabled={!reportData}
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportTrialBalanceToPDF(reportData)}
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
              <Label>Financial Year</Label>
              <Select value={selectedFYId} onValueChange={setSelectedFYId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select FY" />
                </SelectTrigger>
                <SelectContent>
                  {financialYears.map((fy) => (
                    <SelectItem key={fy.id} value={fy.id}>
                      {fy.name} {fy.is_current && '(Current)'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>From Date</Label>
              <Input
                type="date"
                value={fromDate ?? ''}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>
            <div>
              <Label>To Date</Label>
              <Input type="date" value={toDate ?? ''} onChange={(e) => setToDate(e.target.value)} />
            </div>
            <div className="flex items-end gap-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="zero-balance"
                  checked={includeZeroBalance}
                  onCheckedChange={(checked) => setIncludeZeroBalance(checked === true)}
                />
                <Label htmlFor="zero-balance" className="cursor-pointer text-sm">
                  Include Zero Balance
                </Label>
              </div>
              <Button
                onClick={generateReport}
                disabled={loading || !selectedOrgId || !selectedFYId}
              >
                {loading ? 'Generating...' : 'Generate'}
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
              <h3 className="text-lg font-semibold text-slate-700">Trial Balance</h3>
              <p className="text-sm text-slate-500">
                For the period <DateDisplay date={reportData.from_date} /> to{' '}
                <DateDisplay date={reportData.to_date} />
              </p>
            </div>
          </CardHeader>
          <CardContent>
            {reportData.items.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8">
                <FileSpreadsheet className="mb-4 h-12 w-12 text-slate-300" />
                <p className="text-sm text-slate-500">No data found for the selected period</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead>Code</TableHead>
                    <TableHead>Account Name</TableHead>
                    <TableHead>Group</TableHead>
                    <TableHead className="text-right">Opening Dr</TableHead>
                    <TableHead className="text-right">Opening Cr</TableHead>
                    <TableHead className="text-right">Period Dr</TableHead>
                    <TableHead className="text-right">Period Cr</TableHead>
                    <TableHead className="text-right">Closing Dr</TableHead>
                    <TableHead className="text-right">Closing Cr</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {reportData.items.map((item) => (
                    <TableRow
                      key={item.account_id}
                      className="group cursor-pointer transition-colors hover:bg-blue-50"
                      onClick={() => handleDrillDown(item.account_id)}
                    >
                      <TableCell className="font-mono text-sm">
                        <span className="flex items-center gap-1">
                          {item.account_code}
                          <ExternalLink className="h-3 w-3 text-slate-400 opacity-0 group-hover:opacity-100" />
                        </span>
                      </TableCell>
                      <TableCell className="group-hover:text-blue-600">
                        {item.account_name}
                      </TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${getNatureBadgeClass(item.account_nature)}`}
                        >
                          {item.account_group_name}
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.opening_debit > 0
                          ? formatIndianCompactCurrency(item.opening_debit)
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.opening_credit > 0
                          ? formatIndianCompactCurrency(item.opening_credit)
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.period_debit > 0
                          ? formatIndianCompactCurrency(item.period_debit)
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.period_credit > 0
                          ? formatIndianCompactCurrency(item.period_credit)
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold text-blue-600">
                        {item.closing_debit > 0
                          ? formatIndianCompactCurrency(item.closing_debit)
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold text-red-600">
                        {item.closing_credit > 0
                          ? formatIndianCompactCurrency(item.closing_credit)
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-slate-100 font-bold">
                    <TableCell colSpan={3}>TOTAL</TableCell>
                    <TableCell className="text-right font-mono">
                      {formatIndianCompactCurrency(reportData.total_opening_debit)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatIndianCompactCurrency(reportData.total_opening_credit)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatIndianCompactCurrency(reportData.total_period_debit)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatIndianCompactCurrency(reportData.total_period_credit)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-blue-600">
                      {formatIndianCompactCurrency(reportData.total_closing_debit)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-red-600">
                      {formatIndianCompactCurrency(reportData.total_closing_credit)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            )}
            <div className="mt-4 flex justify-between text-xs text-slate-500 print:mt-8">
              <span>Generated on: {new Date(reportData.generated_at).toLocaleString('en-IN')}</span>
              <span>
                {Math.abs(reportData.total_closing_debit - reportData.total_closing_credit) <
                0.01 ? (
                  <span className="font-medium text-emerald-600">Books are balanced</span>
                ) : (
                  <span className="font-medium text-red-600">
                    Difference:{' '}
                    {formatIndianCompactCurrency(
                      Math.abs(reportData.total_closing_debit - reportData.total_closing_credit),
                    )}
                  </span>
                )}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
