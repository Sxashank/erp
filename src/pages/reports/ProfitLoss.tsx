import { FileSpreadsheet, FileText, Filter, Printer, TrendingDown, TrendingUp } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
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
import { reportsApi, organizationsApi, financialYearsApi } from '@/services/api';
import { exportProfitLossToExcel, exportProfitLossToPDF } from '@/utils/exportUtils';

import { logger } from "@/lib/logger";
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

interface ProfitLossItem {
  account_group_code: string;
  account_group_name: string;
  level: number;
  amount: number;
  previous_amount?: number;
}

interface ProfitLossResponse {
  organization_id: string;
  organization_name: string;
  financial_year_id: string;
  financial_year_name: string;
  from_date: string;
  to_date: string;
  income_items: ProfitLossItem[];
  expense_items: ProfitLossItem[];
  total_income: number;
  total_expenses: number;
  net_profit_loss: number;
  profit_loss_type: string;
  generated_at: string;
}

export function ProfitLoss() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedFYId, setSelectedFYId] = useState<string>('');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [reportData, setReportData] = useState<ProfitLossResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedFYId) {
      const fy = financialYears.find(f => f.id === selectedFYId);
      if (fy) {
        setFromDate(fy.start_date);
        setToDate(fy.end_date);
      }
    }
  }, [selectedFYId, financialYears]);

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

  const fetchFinancialYears = useCallback(async () => {
    try {
      const response = await financialYearsApi.list({ organization_id: selectedOrgId, page_size: 100 });
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
      const response = await reportsApi.getProfitLoss({
        organization_id: selectedOrgId,
        financial_year_id: selectedFYId,
        from_date: fromDate,
        to_date: toDate,
      });
      setReportData(response.data);
    } catch (error) {
      logger.error('Failed to generate report:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Profit & Loss Statement"
        subtitle="View income and expenses for the period"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePrint} disabled={!reportData}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportProfitLossToExcel(reportData)}
              disabled={!reportData}
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportProfitLossToPDF(reportData)}
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
              <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </div>
            <div>
              <Label>To Date</Label>
              <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </div>
            <div className="flex items-end">
              <Button onClick={generateReport} disabled={loading || !selectedOrgId || !selectedFYId}>
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
              <h3 className="text-lg font-semibold text-slate-700">Profit & Loss Statement</h3>
              <p className="text-sm text-slate-500">
                For the period <DateDisplay date={reportData.from_date} /> to <DateDisplay date={reportData.to_date} />
              </p>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {/* Income Section */}
              <div className="rounded-lg border border-green-200 bg-green-50/50 p-4">
                <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-green-800">
                  <TrendingUp className="h-5 w-5" />
                  Income
                </h4>
                {reportData.income_items.length === 0 ? (
                  <p className="text-sm text-slate-500">No income recorded</p>
                ) : (
                  <div className="space-y-2">
                    {reportData.income_items.map((item, index) => (
                      <div
                        key={index}
                        className="flex justify-between border-b border-green-200 py-2 last:border-0"
                      >
                        <span className="text-slate-700">{item.account_group_name}</span>
                        <span className="font-mono font-medium text-green-700">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>
                    ))}
                    <div className="flex justify-between border-t-2 border-green-300 pt-3 font-bold">
                      <span className="text-green-800">Total Income</span>
                      <span className="font-mono text-green-700">{formatCurrency(reportData.total_income)}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Expenses Section */}
              <div className="rounded-lg border border-red-200 bg-red-50/50 p-4">
                <h4 className="mb-4 flex items-center gap-2 text-lg font-semibold text-red-800">
                  <TrendingDown className="h-5 w-5" />
                  Expenses
                </h4>
                {reportData.expense_items.length === 0 ? (
                  <p className="text-sm text-slate-500">No expenses recorded</p>
                ) : (
                  <div className="space-y-2">
                    {reportData.expense_items.map((item, index) => (
                      <div
                        key={index}
                        className="flex justify-between border-b border-red-200 py-2 last:border-0"
                      >
                        <span className="text-slate-700">{item.account_group_name}</span>
                        <span className="font-mono font-medium text-red-700">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>
                    ))}
                    <div className="flex justify-between border-t-2 border-red-300 pt-3 font-bold">
                      <span className="text-red-800">Total Expenses</span>
                      <span className="font-mono text-red-700">{formatCurrency(reportData.total_expenses)}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Net Profit/Loss */}
            <div className={`mt-6 rounded-lg p-6 text-center ${
              reportData.profit_loss_type === 'PROFIT'
                ? 'bg-emerald-100 border border-emerald-300'
                : 'bg-rose-100 border border-rose-300'
            }`}>
              <h4 className={`text-lg font-semibold ${
                reportData.profit_loss_type === 'PROFIT' ? 'text-emerald-800' : 'text-rose-800'
              }`}>
                Net {reportData.profit_loss_type === 'PROFIT' ? 'Profit' : 'Loss'}
              </h4>
              <p className={`text-3xl font-bold font-mono mt-2 ${
                reportData.profit_loss_type === 'PROFIT' ? 'text-emerald-700' : 'text-rose-700'
              }`}>
                {formatCurrency(reportData.net_profit_loss)}
              </p>
            </div>

            <div className="mt-4 text-right text-xs text-slate-500 print:mt-8">
              Generated on: {new Date(reportData.generated_at).toLocaleString('en-IN')}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
