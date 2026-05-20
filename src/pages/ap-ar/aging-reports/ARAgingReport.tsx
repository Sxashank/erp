import { format } from 'date-fns';
import {
  ChevronRight,
  FileSpreadsheet,
  Printer,
  RefreshCw,
} from 'lucide-react';
import { useCallback, useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
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
import { agingReportsApi, customersApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

import { logger } from "@/lib/logger";
interface AgingCustomer {
  customer_id: string;
  customer_code: string;
  customer_name: string;
  current: number;
  days_1_30: number;
  days_31_60: number;
  days_61_90: number;
  days_90_plus: number;
  total: number;
}

interface AgingSummary {
  as_of_date: string;
  customers: AgingCustomer[];
  totals: {
    current: number;
    days_1_30: number;
    days_31_60: number;
    days_61_90: number;
    days_90_plus: number;
    total: number;
  };
}

interface Customer {
  id: string;
  code: string;
  name: string;
}

export function ARAgingReport() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const organizationId = useActiveOrganizationId() || '';

  // State
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState(
    searchParams.get('customer_id') || 'all',
  );
  const [asOfDate, setAsOfDate] = useState(
    searchParams.get('as_of_date') || format(new Date(), 'yyyy-MM-dd'),
  );
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<AgingSummary | null>(null);

  // Fetch customers
  useEffect(() => {
    const fetchCustomers = async () => {
      if (!organizationId) return;
      try {
        const response = await customersApi.getActive({});
        setCustomers(response.data || []);
      } catch (error) {
        logger.error('Failed to fetch customers:', error);
      }
    };
    fetchCustomers();
  }, [organizationId]);

  // Fetch report
  const fetchReport = useCallback(async () => {
    if (!organizationId) return;
    setLoading(true);
    try {
      const params: Parameters<typeof agingReportsApi.getARAgingSummary>[0] = {
        as_of_date: asOfDate,
      };
      if (selectedCustomer !== 'all') {
        params.customer_id = selectedCustomer;
      }

      const response = await agingReportsApi.getARAgingSummary(params);
      setReportData(response.data);
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setLoading(false);
    }
  }, [asOfDate, organizationId, selectedCustomer, toast]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getPercentage = (amount: number, total: number) => {
    if (total === 0) return 0;
    return (amount / total) * 100;
  };

  const handlePrint = () => {
    window.print();
  };

  const handleViewDetail = (customerId: string) => {
    navigate(`/admin/ap-ar/aging-reports/ar-detail/${customerId}?as_of_date=${asOfDate}`);
  };

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <PageHeader
          title="AR Aging Report"
          subtitle="Accounts Receivable aging analysis by customer"
          breadcrumbs={[{ label: 'AP / AR', to: '/admin/ap-ar' }, { label: 'AR Aging' }]}
          actions={
            reportData ? (
              <Button variant="outline" onClick={handlePrint}>
                <Printer className="mr-2 h-4 w-4" />
                Print
              </Button>
            ) : undefined
          }
        />
      </div>

      {/* Filters */}
      <Card className="print:hidden">
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <Label>As of Date</Label>
              <Input type="date" value={asOfDate} onChange={(e) => setAsOfDate(e.target.value)} />
            </div>
            <div>
              <Label>Customer</Label>
              <Select value={selectedCustomer} onValueChange={setSelectedCustomer}>
                <SelectTrigger>
                  <SelectValue placeholder="All Customers" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Customers</SelectItem>
                  {customers.map((customer) => (
                    <SelectItem key={customer.id} value={customer.id}>
                      {customer.code} - {customer.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={fetchReport} disabled={loading}>
                {loading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
                Generate Report
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {reportData && (
        <div className="grid gap-4 md:grid-cols-6">
          <Card className="bg-green-50">
            <CardContent className="pt-6">
              <p className="text-sm text-green-700">Current</p>
              <p className="text-xl font-bold text-green-800">
                {formatAmount(reportData.totals.current)}
              </p>
              <Progress
                value={getPercentage(reportData.totals.current, reportData.totals.total)}
                className="mt-2 h-1"
              />
            </CardContent>
          </Card>
          <Card className="bg-blue-50">
            <CardContent className="pt-6">
              <p className="text-sm text-blue-700">1-30 Days</p>
              <p className="text-xl font-bold text-blue-800">
                {formatAmount(reportData.totals.days_1_30)}
              </p>
              <Progress
                value={getPercentage(reportData.totals.days_1_30, reportData.totals.total)}
                className="mt-2 h-1"
              />
            </CardContent>
          </Card>
          <Card className="bg-yellow-50">
            <CardContent className="pt-6">
              <p className="text-sm text-yellow-700">31-60 Days</p>
              <p className="text-xl font-bold text-yellow-800">
                {formatAmount(reportData.totals.days_31_60)}
              </p>
              <Progress
                value={getPercentage(reportData.totals.days_31_60, reportData.totals.total)}
                className="mt-2 h-1"
              />
            </CardContent>
          </Card>
          <Card className="bg-orange-50">
            <CardContent className="pt-6">
              <p className="text-sm text-orange-700">61-90 Days</p>
              <p className="text-xl font-bold text-orange-800">
                {formatAmount(reportData.totals.days_61_90)}
              </p>
              <Progress
                value={getPercentage(reportData.totals.days_61_90, reportData.totals.total)}
                className="mt-2 h-1"
              />
            </CardContent>
          </Card>
          <Card className="bg-red-50">
            <CardContent className="pt-6">
              <p className="text-sm text-red-700">90+ Days</p>
              <p className="text-xl font-bold text-red-800">
                {formatAmount(reportData.totals.days_90_plus)}
              </p>
              <Progress
                value={getPercentage(reportData.totals.days_90_plus, reportData.totals.total)}
                className="mt-2 h-1"
              />
            </CardContent>
          </Card>
          <Card className="bg-slate-50">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-700">Total</p>
              <p className="text-xl font-bold text-slate-800">
                {formatAmount(reportData.totals.total)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Report Table */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : reportData ? (
        <Card className="print:border-0 print:shadow-none">
          <CardHeader className="text-center">
            <CardTitle>AR Aging Summary</CardTitle>
            <CardDescription>
              As of {format(new Date(reportData.as_of_date), 'dd/MM/yyyy')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead className="text-right">Current</TableHead>
                  <TableHead className="text-right">1-30 Days</TableHead>
                  <TableHead className="text-right">31-60 Days</TableHead>
                  <TableHead className="text-right">61-90 Days</TableHead>
                  <TableHead className="text-right">90+ Days</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead className="print:hidden"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reportData.customers.map((customer) => (
                  <TableRow key={customer.customer_id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{customer.customer_name}</p>
                        <p className="text-sm text-slate-500">{customer.customer_code}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-right text-green-600">
                      {formatAmount(customer.current)}
                    </TableCell>
                    <TableCell className="text-right text-blue-600">
                      {formatAmount(customer.days_1_30)}
                    </TableCell>
                    <TableCell className="text-right text-yellow-600">
                      {formatAmount(customer.days_31_60)}
                    </TableCell>
                    <TableCell className="text-right text-orange-600">
                      {formatAmount(customer.days_61_90)}
                    </TableCell>
                    <TableCell className="text-right text-red-600">
                      {formatAmount(customer.days_90_plus)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatAmount(customer.total)}
                    </TableCell>
                    <TableCell className="print:hidden">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetail(customer.customer_id)}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {reportData.customers.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-slate-500">
                      No outstanding receivables found
                    </TableCell>
                  </TableRow>
                )}
                {reportData.customers.length > 0 && (
                  <TableRow className="bg-slate-50 font-bold">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right text-green-600">
                      {formatAmount(reportData.totals.current)}
                    </TableCell>
                    <TableCell className="text-right text-blue-600">
                      {formatAmount(reportData.totals.days_1_30)}
                    </TableCell>
                    <TableCell className="text-right text-yellow-600">
                      {formatAmount(reportData.totals.days_31_60)}
                    </TableCell>
                    <TableCell className="text-right text-orange-600">
                      {formatAmount(reportData.totals.days_61_90)}
                    </TableCell>
                    <TableCell className="text-right text-red-600">
                      {formatAmount(reportData.totals.days_90_plus)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatAmount(reportData.totals.total)}
                    </TableCell>
                    <TableCell className="print:hidden"></TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="flex h-64 flex-col items-center justify-center text-slate-500">
            <FileSpreadsheet className="mb-4 h-12 w-12" />
            <p>No report data available</p>
            <Button variant="link" onClick={fetchReport}>
              Generate Report
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
