import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Download,
  FileSpreadsheet,
  Printer,
  RefreshCw,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { agingReportsApi, customersApi } from '@/services/api';

interface AgingInvoice {
  invoice_id: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  total_amount: number;
  received_amount: number;
  balance_amount: number;
  days_overdue: number;
  aging_bucket: string;
}

interface CustomerAgingDetail {
  customer_id: string;
  customer_code: string;
  customer_name: string;
  as_of_date: string;
  invoices: AgingInvoice[];
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

export function ARAgingDetail() {
  const navigate = useNavigate();
  const { customerId } = useParams<{ customerId: string }>();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const organizationId = localStorage.getItem('organization_id') || '';
  const asOfDate = searchParams.get('as_of_date') || format(new Date(), 'yyyy-MM-dd');

  const [loading, setLoading] = useState(false);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [reportData, setReportData] = useState<CustomerAgingDetail | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!customerId) return;

      setLoading(true);
      try {
        // Fetch customer details
        const customerResponse = await customersApi.get(customerId);
        setCustomer(customerResponse.data);

        // Fetch aging detail
        const response = await agingReportsApi.getARAgingDetail(customerId, {
          organization_id: organizationId,
          as_of_date: asOfDate,
        });
        setReportData(response.data);
      } catch (error: any) {
        toast({
          title: 'Error',
          description: error.response?.data?.detail || 'Failed to fetch report',
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [customerId, asOfDate, organizationId]);

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getAgingBadge = (bucket: string) => {
    switch (bucket) {
      case 'current':
        return <Badge variant="outline" className="bg-green-50 text-green-700">Current</Badge>;
      case '1-30':
        return <Badge variant="outline" className="bg-blue-50 text-blue-700">1-30 Days</Badge>;
      case '31-60':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700">31-60 Days</Badge>;
      case '61-90':
        return <Badge variant="outline" className="bg-orange-50 text-orange-700">61-90 Days</Badge>;
      case '90+':
        return <Badge variant="outline" className="bg-red-50 text-red-700">90+ Days</Badge>;
      default:
        return <Badge variant="outline">{bucket}</Badge>;
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleViewInvoice = (invoiceId: string) => {
    navigate(`/admin/ap-ar/sales-invoices/${invoiceId}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 print:hidden">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">AR Aging Detail</h1>
          <p className="text-sm text-slate-500">
            {customer ? `${customer.code} - ${customer.name}` : 'Loading...'}
          </p>
        </div>
        {reportData && (
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="mr-2 h-4 w-4" />
            Print
          </Button>
        )}
      </div>

      {/* Summary Cards */}
      {reportData && (
        <div className="grid gap-4 md:grid-cols-6">
          <Card className="bg-green-50">
            <CardContent className="pt-6">
              <p className="text-sm text-green-700">Current</p>
              <p className="text-xl font-bold text-green-800">
                {formatAmount(reportData.totals.current)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50">
            <CardContent className="pt-6">
              <p className="text-sm text-blue-700">1-30 Days</p>
              <p className="text-xl font-bold text-blue-800">
                {formatAmount(reportData.totals.days_1_30)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-yellow-50">
            <CardContent className="pt-6">
              <p className="text-sm text-yellow-700">31-60 Days</p>
              <p className="text-xl font-bold text-yellow-800">
                {formatAmount(reportData.totals.days_31_60)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-orange-50">
            <CardContent className="pt-6">
              <p className="text-sm text-orange-700">61-90 Days</p>
              <p className="text-xl font-bold text-orange-800">
                {formatAmount(reportData.totals.days_61_90)}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-red-50">
            <CardContent className="pt-6">
              <p className="text-sm text-red-700">90+ Days</p>
              <p className="text-xl font-bold text-red-800">
                {formatAmount(reportData.totals.days_90_plus)}
              </p>
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

      {/* Invoices Table */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : reportData ? (
        <Card className="print:border-0 print:shadow-none">
          <CardHeader className="text-center">
            <CardTitle>Outstanding Invoices</CardTitle>
            <CardDescription>
              As of {format(new Date(reportData.as_of_date), 'dd/MM/yyyy')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Invoice Number</TableHead>
                  <TableHead>Invoice Date</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead className="text-right">Invoice Amount</TableHead>
                  <TableHead className="text-right">Received Amount</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead className="text-center">Days Overdue</TableHead>
                  <TableHead>Aging</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reportData.invoices.map((invoice) => (
                  <TableRow
                    key={invoice.invoice_id}
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => handleViewInvoice(invoice.invoice_id)}
                  >
                    <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                    <TableCell>{format(new Date(invoice.invoice_date), 'dd/MM/yyyy')}</TableCell>
                    <TableCell>{format(new Date(invoice.due_date), 'dd/MM/yyyy')}</TableCell>
                    <TableCell className="text-right">{formatAmount(invoice.total_amount)}</TableCell>
                    <TableCell className="text-right">{formatAmount(invoice.received_amount)}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatAmount(invoice.balance_amount)}
                    </TableCell>
                    <TableCell className="text-center">
                      {invoice.days_overdue > 0 ? (
                        <span className="text-red-600">{invoice.days_overdue}</span>
                      ) : (
                        <span className="text-green-600">-</span>
                      )}
                    </TableCell>
                    <TableCell>{getAgingBadge(invoice.aging_bucket)}</TableCell>
                  </TableRow>
                ))}
                {reportData.invoices.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-slate-500">
                      No outstanding invoices found
                    </TableCell>
                  </TableRow>
                )}
                {reportData.invoices.length > 0 && (
                  <TableRow className="bg-slate-50 font-bold">
                    <TableCell colSpan={5}>Total</TableCell>
                    <TableCell className="text-right">
                      {formatAmount(reportData.totals.total)}
                    </TableCell>
                    <TableCell colSpan={2}></TableCell>
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
          </CardContent>
        </Card>
      )}
    </div>
  );
}
