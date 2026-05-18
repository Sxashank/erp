import { FileSpreadsheet, FileText, Filter, Printer, Scale } from 'lucide-react';
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
import { exportBalanceSheetToExcel, exportBalanceSheetToPDF } from '@/utils/exportUtils';

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

interface BalanceSheetItem {
  account_group_code: string;
  account_group_name: string;
  level: number;
  amount: number;
  previous_amount?: number;
}

interface BalanceSheetSection {
  section_name: string;
  items: BalanceSheetItem[];
  total: number;
  previous_total?: number;
}

interface BalanceSheetResponse {
  organization_id: string;
  organization_name: string;
  financial_year_id: string;
  financial_year_name: string;
  as_on_date: string;
  assets: BalanceSheetSection;
  liabilities: BalanceSheetSection;
  equity: BalanceSheetSection;
  net_profit_loss: number;
  total_liabilities_equity: number;
  is_balanced: boolean;
  generated_at: string;
}

export function BalanceSheet() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedFYId, setSelectedFYId] = useState<string>('');
  const [asOnDate, setAsOnDate] = useState<string>('');
  const [reportData, setReportData] = useState<BalanceSheetResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedFYId) {
      const fy = financialYears.find(f => f.id === selectedFYId);
      if (fy) {
        setAsOnDate(fy.end_date);
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
      const response = await reportsApi.getBalanceSheet({
        organization_id: selectedOrgId,
        financial_year_id: selectedFYId,
        as_on_date: asOnDate,
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

  const renderSection = (section: BalanceSheetSection, colorClass: string) => (
    <div className={`rounded-lg border p-4 ${colorClass}`}>
      <h4 className="mb-4 text-lg font-semibold">{section.section_name}</h4>
      {section.items.length === 0 ? (
        <p className="text-sm text-slate-500">No items</p>
      ) : (
        <div className="space-y-2">
          {section.items.map((item, index) => (
            <div
              key={index}
              className="flex justify-between border-b border-slate-200 py-2 last:border-0"
              style={{ paddingLeft: `${item.level * 16}px` }}
            >
              <span className="text-slate-700">{item.account_group_name}</span>
              <span className="font-mono font-medium">{formatCurrency(item.amount)}</span>
            </div>
          ))}
          <div className="flex justify-between border-t-2 pt-3 font-bold">
            <span>Total {section.section_name}</span>
            <span className="font-mono">{formatCurrency(section.total)}</span>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Balance Sheet"
        subtitle="View assets, liabilities, and equity as of a date"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePrint} disabled={!reportData}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportBalanceSheetToExcel(reportData)}
              disabled={!reportData}
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportBalanceSheetToPDF(reportData)}
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
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
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
              <Label>As On Date</Label>
              <Input type="date" value={asOnDate} onChange={(e) => setAsOnDate(e.target.value)} />
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
              <h3 className="text-lg font-semibold text-slate-700">Balance Sheet</h3>
              <p className="text-sm text-slate-500">
                As on <DateDisplay date={reportData.as_on_date} />
              </p>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Left Side - Assets */}
              <div className="space-y-6">
                {renderSection(reportData.assets, 'border-blue-200 bg-blue-50/50')}

                {/* Assets Total */}
                <div className="rounded-lg bg-blue-100 p-4 text-center">
                  <h4 className="font-semibold text-blue-800">Total Assets</h4>
                  <p className="text-2xl font-bold font-mono text-blue-700">
                    {formatCurrency(reportData.assets.total)}
                  </p>
                </div>
              </div>

              {/* Right Side - Liabilities + Equity */}
              <div className="space-y-6">
                {renderSection(reportData.liabilities, 'border-red-200 bg-red-50/50')}
                {renderSection(reportData.equity, 'border-purple-200 bg-purple-50/50')}

                {/* Net Profit/Loss */}
                <div className={`rounded-lg p-4 ${
                  reportData.net_profit_loss >= 0
                    ? 'border border-emerald-200 bg-emerald-50/50'
                    : 'border border-rose-200 bg-rose-50/50'
                }`}>
                  <div className="flex justify-between">
                    <span className="font-semibold">
                      Net {reportData.net_profit_loss >= 0 ? 'Profit' : 'Loss'} (Current Year)
                    </span>
                    <span className={`font-mono font-bold ${
                      reportData.net_profit_loss >= 0 ? 'text-emerald-700' : 'text-rose-700'
                    }`}>
                      {formatCurrency(Math.abs(reportData.net_profit_loss))}
                    </span>
                  </div>
                </div>

                {/* Liabilities + Equity Total */}
                <div className="rounded-lg bg-slate-100 p-4 text-center">
                  <h4 className="font-semibold text-slate-800">Total Liabilities + Equity</h4>
                  <p className="text-2xl font-bold font-mono text-slate-700">
                    {formatCurrency(reportData.total_liabilities_equity)}
                  </p>
                </div>
              </div>
            </div>

            {/* Balance Check */}
            <div className={`mt-6 rounded-lg p-4 text-center ${
              reportData.is_balanced
                ? 'bg-emerald-100 border border-emerald-300'
                : 'bg-rose-100 border border-rose-300'
            }`}>
              <div className="flex items-center justify-center gap-2">
                <Scale className={`h-5 w-5 ${reportData.is_balanced ? 'text-emerald-700' : 'text-rose-700'}`} />
                <span className={`font-semibold ${reportData.is_balanced ? 'text-emerald-700' : 'text-rose-700'}`}>
                  {reportData.is_balanced ? 'Balance Sheet is Balanced' : 'Balance Sheet is NOT Balanced'}
                </span>
              </div>
              {!reportData.is_balanced && (
                <p className="mt-1 text-sm text-rose-600">
                  Difference: {formatCurrency(Math.abs(reportData.assets.total - reportData.total_liabilities_equity))}
                </p>
              )}
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
