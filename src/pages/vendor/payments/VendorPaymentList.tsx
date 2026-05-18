/**
 * Vendor Payment List
 */

import {
  CreditCard,
  Search,
  Filter,
  Eye,
  Download,
  Loader2,
  TrendingUp,
  Calendar,
  FileText,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { vendorPaymentApi } from '@/services/vendorApi';
import type { VendorPayment, VendorAgingReport } from '@/types/vendor';

import { logger } from "@/lib/logger";
export default function VendorPaymentList() {
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [payments, setPayments] = useState<VendorPayment[]>([]);
  const [total, setTotal] = useState(0);
  const [aging, setAging] = useState<VendorAgingReport | null>(null);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [page, setPage] = useState(1);
  const limit = 20;

  // Statement filters
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  useEffect(() => {
    fetchData();
  }, [page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [paymentsRes, agingRes, summaryRes] = await Promise.all([
        vendorPaymentApi.list({ skip: (page - 1) * limit, limit }),
        vendorPaymentApi.getAging(),
        vendorPaymentApi.getSummary(),
      ]);

      setPayments(paymentsRes.data.items);
      setTotal(paymentsRes.data.total);
      setAging(agingRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      logger.error('Failed to fetch payments:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load payment data',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number | undefined) => {
    if (amount === undefined || amount === null) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleDownloadStatement = async () => {
    if (!fromDate || !toDate) {
      toast({ variant: 'destructive', title: 'Please select date range' });
      return;
    }

    try {
      const response = await vendorPaymentApi.downloadStatement(fromDate, toDate);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `statement_${fromDate}_${toDate}.pdf`;
      a.click();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to download statement',
      });
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payments"
        subtitle="View your payment history and outstanding amounts"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-800">Total Outstanding</span>
            </div>
            <p className="text-2xl font-bold text-green-900 mt-2">
              {formatCurrency(summary?.total_outstanding as number)}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <CreditCard className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">Pending Payments</span>
            </div>
            <p className="text-2xl font-bold text-blue-900 mt-2">
              {(summary?.pending_payments as number) || 0}
            </p>
          </CardContent>
        </Card>
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-800">Last Payment</span>
            </div>
            <DateDisplay date={summary?.last_payment_date as string | null | undefined} className="text-lg font-bold text-purple-900 mt-2" />
          </CardContent>
        </Card>
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-orange-600" />
              <span className="text-sm font-medium text-orange-800">Last Amount</span>
            </div>
            <p className="text-2xl font-bold text-orange-900 mt-2">
              {formatCurrency(summary?.last_payment_amount as number)}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="payments" className="space-y-6">
        <TabsList>
          <TabsTrigger value="payments">Payment History</TabsTrigger>
          <TabsTrigger value="aging">Aging Report</TabsTrigger>
          <TabsTrigger value="statement">Statement</TabsTrigger>
        </TabsList>

        {/* Payment History */}
        <TabsContent value="payments">
          <Card>
            <CardHeader>
              <CardTitle>Payment History</CardTitle>
              <CardDescription>Total {total} payments received</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
                </div>
              ) : payments.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                  <CreditCard className="h-12 w-12 text-gray-300 mb-2" />
                  <p>No payments found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Reference</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Mode</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell className="font-medium">{payment.payment_reference}</TableCell>
                        <TableCell><DateDisplay date={payment.payment_date} /></TableCell>
                        <TableCell>{payment.payment_mode}</TableCell>
                        <TableCell className="text-right">{formatCurrency(payment.amount)}</TableCell>
                        <TableCell>
                          <Badge className="bg-green-100 text-green-800">{payment.status}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Link to={`/vendor/payments/${payment.id}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Aging Report */}
        <TabsContent value="aging">
          <Card>
            <CardHeader>
              <CardTitle>Aging Report</CardTitle>
              <CardDescription>
                Outstanding invoices as of {aging?.as_of_date ? <DateDisplay date={aging.as_of_date} /> : 'today'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {aging ? (
                <div className="space-y-6">
                  {/* Aging Buckets */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {aging.buckets.map((bucket, index) => (
                      <div key={index} className="p-4 bg-gray-50 rounded-lg text-center">
                        <p className="text-sm font-medium text-gray-600">{bucket.label}</p>
                        <p className="text-xl font-bold text-gray-900 mt-1">
                          {formatCurrency(bucket.amount)}
                        </p>
                        <p className="text-xs text-gray-500">{bucket.count} invoices</p>
                      </div>
                    ))}
                  </div>

                  {/* Invoice Details */}
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Invoice #</TableHead>
                        <TableHead>Invoice Date</TableHead>
                        <TableHead>Due Date</TableHead>
                        <TableHead className="text-right">Invoice Amount</TableHead>
                        <TableHead className="text-right">Balance</TableHead>
                        <TableHead className="text-right">Days Overdue</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {aging.invoices.map((inv, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{inv.invoice_number}</TableCell>
                          <TableCell><DateDisplay date={inv.invoice_date} /></TableCell>
                          <TableCell><DateDisplay date={inv.due_date} /></TableCell>
                          <TableCell className="text-right">{formatCurrency(inv.invoice_amount)}</TableCell>
                          <TableCell className="text-right">{formatCurrency(inv.balance_amount)}</TableCell>
                          <TableCell className="text-right">
                            <Badge variant={inv.days_overdue > 0 ? 'destructive' : 'secondary'}>
                              {inv.days_overdue > 0 ? `${inv.days_overdue} days` : 'Current'}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Statement */}
        <TabsContent value="statement">
          <Card>
            <CardHeader>
              <CardTitle>Account Statement</CardTitle>
              <CardDescription>Download your account statement for a period</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div className="space-y-2">
                  <Label>From Date</Label>
                  <Input
                    type="date"
                    value={fromDate}
                    onChange={(e) => setFromDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>To Date</Label>
                  <Input
                    type="date"
                    value={toDate}
                    onChange={(e) => setToDate(e.target.value)}
                  />
                </div>
                <Button onClick={handleDownloadStatement} className="bg-purple-600 hover:bg-purple-700">
                  <Download className="h-4 w-4 mr-2" />
                  Download Statement
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
