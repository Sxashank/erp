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
import { exportCashFlowToExcel, exportCashFlowToPDF } from '@/utils/exportUtils';

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

interface CashFlowItem {
  label: string;
  amount: number;
  is_subtotal: boolean;
}

interface CashFlowSection {
  section_name: string;
  items: CashFlowItem[];
  net_cash_flow: number;
}

interface CashFlowStatementResponse {
  organization_id: string;
  organization_name: string;
  financial_year_id: string;
  financial_year_name: string;
  from_date: string;
  to_date: string;
  net_profit_loss: number;
  profit_loss_type: string;
  operating_activities: CashFlowSection;
  investing_activities: CashFlowSection;
  financing_activities: CashFlowSection;
  net_increase_in_cash: number;
  opening_cash_balance: number;
  closing_cash_balance: number;
  generated_at: string;
}

export function CashFlowStatement() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [financialYears, setFinancialYears] = useState<FinancialYear[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedFYId, setSelectedFYId] = useState<string>('');
  const [fromDate, setFromDate] = useState<string>('');
  const [toDate, setToDate] = useState<string>('');
  const [reportData, setReportData] = useState<CashFlowStatementResponse | null>(null);
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
      const response = await reportsApi.getCashFlowStatement({
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
    }).format(Math.abs(amount));


  const handlePrint = () => {
    window.print();
  };

  const renderCashFlowSection = (section: CashFlowSection, bgColor: string) => (
    <div className={`rounded-lg ${bgColor} p-4 mb-4`}>
      <h3 className="text-lg font-semibold text-slate-800 mb-3">{section.section_name}</h3>
      <div className="space-y-2">
        {section.items.map((item, index) => (
          <div
            key={index}
            className={`flex justify-between items-center py-1 ${
              item.is_subtotal ? 'border-t border-slate-300 pt-2 mt-2 font-semibold' : ''
            }`}
          >
            <span className={`${item.is_subtotal ? 'text-slate-800' : 'text-slate-600'}`}>
              {item.label}
            </span>
            <span
              className={`font-mono ${
                item.amount >= 0 ? 'text-emerald-600' : 'text-red-600'
              } ${item.is_subtotal ? 'text-lg' : ''}`}
            >
              {item.amount < 0 && '('}{formatCurrency(item.amount)}{item.amount < 0 && ')'}
            </span>
          </div>
        ))}
      </div>
      <div className="flex justify-between items-center border-t-2 border-slate-400 pt-3 mt-3">
        <span className="font-bold text-slate-800">Net Cash from {section.section_name.replace('Cash Flow from ', '')}</span>
        <span className={`font-mono font-bold text-lg ${section.net_cash_flow >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
          {section.net_cash_flow < 0 && '('}{formatCurrency(section.net_cash_flow)}{section.net_cash_flow < 0 && ')'}
        </span>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cash Flow Statement"
        subtitle="Analyze cash inflows and outflows (Indirect Method)"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handlePrint} disabled={!reportData}>
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportCashFlowToExcel(reportData)}
              disabled={!reportData}
            >
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              Excel
            </Button>
            <Button
              variant="outline"
              onClick={() => reportData && exportCashFlowToPDF(reportData)}
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
              <Button
                onClick={generateReport}
                disabled={loading || !selectedOrgId || !selectedFYId}
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
              <h3 className="text-lg font-semibold text-slate-700">Cash Flow Statement</h3>
              <p className="text-sm text-slate-500">
                For the period <DateDisplay date={reportData.from_date} /> to <DateDisplay date={reportData.to_date} />
              </p>
              <p className="text-xs text-slate-400 mt-1">(Prepared using Indirect Method)</p>
            </div>
          </CardHeader>
          <CardContent>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-slate-50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-500">Opening Cash Balance</p>
                <p className="text-xl font-bold text-slate-800">
                  {formatCurrency(reportData.opening_cash_balance)}
                </p>
              </div>
              <div className={`rounded-lg p-4 text-center ${reportData.net_increase_in_cash >= 0 ? 'bg-emerald-50' : 'bg-red-50'}`}>
                <p className="text-sm text-slate-500 flex items-center justify-center gap-1">
                  {reportData.net_increase_in_cash >= 0 ? (
                    <>
                      <TrendingUp className="h-4 w-4 text-emerald-600" />
                      Net Increase in Cash
                    </>
                  ) : (
                    <>
                      <TrendingDown className="h-4 w-4 text-red-600" />
                      Net Decrease in Cash
                    </>
                  )}
                </p>
                <p className={`text-xl font-bold ${reportData.net_increase_in_cash >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                  {formatCurrency(reportData.net_increase_in_cash)}
                </p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <p className="text-sm text-slate-500">Closing Cash Balance</p>
                <p className="text-xl font-bold text-blue-700">
                  {formatCurrency(reportData.closing_cash_balance)}
                </p>
              </div>
              <div className={`rounded-lg p-4 text-center ${reportData.profit_loss_type === 'PROFIT' ? 'bg-emerald-50' : 'bg-red-50'}`}>
                <p className="text-sm text-slate-500">
                  Net {reportData.profit_loss_type === 'PROFIT' ? 'Profit' : 'Loss'}
                </p>
                <p className={`text-xl font-bold ${reportData.profit_loss_type === 'PROFIT' ? 'text-emerald-600' : 'text-red-600'}`}>
                  {formatCurrency(reportData.net_profit_loss)}
                </p>
              </div>
            </div>

            {/* Cash Flow Sections */}
            {renderCashFlowSection(reportData.operating_activities, 'bg-blue-50')}
            {renderCashFlowSection(reportData.investing_activities, 'bg-amber-50')}
            {renderCashFlowSection(reportData.financing_activities, 'bg-purple-50')}

            {/* Summary */}
            <div className="bg-slate-800 text-white rounded-lg p-6 mt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex justify-between items-center">
                  <span>Cash from Operating</span>
                  <span className={`font-mono ${reportData.operating_activities.net_cash_flow >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {reportData.operating_activities.net_cash_flow < 0 && '('}
                    {formatCurrency(reportData.operating_activities.net_cash_flow)}
                    {reportData.operating_activities.net_cash_flow < 0 && ')'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Cash from Investing</span>
                  <span className={`font-mono ${reportData.investing_activities.net_cash_flow >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {reportData.investing_activities.net_cash_flow < 0 && '('}
                    {formatCurrency(reportData.investing_activities.net_cash_flow)}
                    {reportData.investing_activities.net_cash_flow < 0 && ')'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Cash from Financing</span>
                  <span className={`font-mono ${reportData.financing_activities.net_cash_flow >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {reportData.financing_activities.net_cash_flow < 0 && '('}
                    {formatCurrency(reportData.financing_activities.net_cash_flow)}
                    {reportData.financing_activities.net_cash_flow < 0 && ')'}
                  </span>
                </div>
              </div>
              <div className="border-t border-slate-600 mt-4 pt-4">
                <div className="flex justify-between items-center text-lg">
                  <span className="font-semibold">Net Change in Cash & Cash Equivalents</span>
                  <span className={`font-mono font-bold text-xl ${reportData.net_increase_in_cash >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {reportData.net_increase_in_cash < 0 && '('}
                    {formatCurrency(reportData.net_increase_in_cash)}
                    {reportData.net_increase_in_cash < 0 && ')'}
                  </span>
                </div>
              </div>
              <div className="mt-4 space-y-2 text-slate-300">
                <div className="flex justify-between">
                  <span>Opening Cash & Cash Equivalents</span>
                  <span className="font-mono">{formatCurrency(reportData.opening_cash_balance)}</span>
                </div>
                <div className="flex justify-between text-white font-semibold border-t border-slate-600 pt-2">
                  <span>Closing Cash & Cash Equivalents</span>
                  <span className="font-mono text-lg">{formatCurrency(reportData.closing_cash_balance)}</span>
                </div>
              </div>
            </div>

            <div className="mt-4 flex justify-between text-xs text-slate-500 print:mt-8">
              <span>Generated on: {new Date(reportData.generated_at).toLocaleString('en-IN')}</span>
              <span>
                {Math.abs(reportData.opening_cash_balance + reportData.net_increase_in_cash - reportData.closing_cash_balance) < 0.01 ? (
                  <span className="text-emerald-600 font-medium">Cash reconciled</span>
                ) : (
                  <span className="text-red-600 font-medium">Cash mismatch detected</span>
                )}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
