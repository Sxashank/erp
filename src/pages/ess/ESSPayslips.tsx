/**
 * ESS Payslips Page
 * View and download payslips, YTD summary
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download, FileText, TrendingUp, Loader2, Calendar, IndianRupee } from 'lucide-react';
import { essProfileApi } from '@/services/essApi';
import type { Payslip, YTDSummary } from '@/types/ess';

export default function ESSPayslipsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [ytdSummary, setYtdSummary] = useState<YTDSummary | null>(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [downloading, setDownloading] = useState<string | null>(null);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  useEffect(() => {
    const token = localStorage.getItem('ess_access_token');
    if (!token) {
      navigate('/ess/login');
      return;
    }
    fetchData();
  }, [navigate, selectedYear]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [payslipsRes, ytdRes] = await Promise.all([
        essProfileApi.getPayslips({ year: selectedYear }),
        essProfileApi.getYtdSummary(`${selectedYear}-${selectedYear + 1}`),
      ]);
      setPayslips(payslipsRes.data?.items || []);
      setYtdSummary(ytdRes.data);
    } catch (error) {
      console.error('Failed to fetch payslips:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (payslipId: string, month: string) => {
    setDownloading(payslipId);
    try {
      const response = await essProfileApi.downloadPayslip(payslipId);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Payslip_${month.replace(' ', '_')}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download payslip:', error);
    } finally {
      setDownloading(null);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payslips"
        subtitle="View and download your salary slips"
        actions={
          <Select value={String(selectedYear)} onValueChange={(v) => setSelectedYear(Number(v))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {years.map((year) => (
                <SelectItem key={year} value={String(year)}>{year}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      <Tabs defaultValue="payslips" className="space-y-6">
        <TabsList>
          <TabsTrigger value="payslips">Monthly Payslips</TabsTrigger>
          <TabsTrigger value="ytd">YTD Summary</TabsTrigger>
        </TabsList>

        <TabsContent value="payslips">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Earnings</p>
                    <p className="text-lg font-bold">{formatCurrency(ytdSummary?.total_earnings || 0)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <IndianRupee className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Deductions</p>
                    <p className="text-lg font-bold">{formatCurrency(ytdSummary?.total_deductions || 0)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <IndianRupee className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Net Pay (YTD)</p>
                    <p className="text-lg font-bold">{formatCurrency(ytdSummary?.total_net_pay || 0)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Calendar className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Months Paid</p>
                    <p className="text-lg font-bold">{ytdSummary?.months_paid || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Payslips Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Payslips for {selectedYear}</CardTitle>
            </CardHeader>
            <CardContent>
              {payslips.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Month</TableHead>
                      <TableHead className="text-right">Gross Salary</TableHead>
                      <TableHead className="text-right">Deductions</TableHead>
                      <TableHead className="text-right">Net Salary</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payslips.map((payslip) => (
                      <TableRow key={payslip.id}>
                        <TableCell className="font-medium">{payslip.month}</TableCell>
                        <TableCell className="text-right">{formatCurrency(payslip.gross_salary)}</TableCell>
                        <TableCell className="text-right text-red-600">-{formatCurrency(payslip.total_deductions)}</TableCell>
                        <TableCell className="text-right font-bold text-green-600">{formatCurrency(payslip.net_salary)}</TableCell>
                        <TableCell>
                          <Badge variant="secondary" className={payslip.payment_status === 'PAID' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                            {payslip.payment_status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload(payslip.id, payslip.month)}
                            disabled={downloading === payslip.id}
                          >
                            {downloading === payslip.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Download className="h-4 w-4" />
                            )}
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No payslips found for {selectedYear}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ytd">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Earnings Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-green-700">Earnings Breakdown</CardTitle>
                <CardDescription>Year-to-date earnings by component</CardDescription>
              </CardHeader>
              <CardContent>
                {ytdSummary?.breakdown?.earnings ? (
                  <div className="space-y-3">
                    {Object.entries(ytdSummary.breakdown.earnings).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center p-2 bg-green-50 rounded">
                        <span className="text-sm">{key.replace(/_/g, ' ')}</span>
                        <span className="font-medium text-green-700">{formatCurrency(value)}</span>
                      </div>
                    ))}
                    <div className="flex justify-between items-center p-3 bg-green-100 rounded font-bold">
                      <span>Total Earnings</span>
                      <span className="text-green-700">{formatCurrency(ytdSummary.total_earnings)}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">No data available</p>
                )}
              </CardContent>
            </Card>

            {/* Deductions Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-red-700">Deductions Breakdown</CardTitle>
                <CardDescription>Year-to-date deductions by component</CardDescription>
              </CardHeader>
              <CardContent>
                {ytdSummary?.breakdown?.deductions ? (
                  <div className="space-y-3">
                    {Object.entries(ytdSummary.breakdown.deductions).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center p-2 bg-red-50 rounded">
                        <span className="text-sm">{key.replace(/_/g, ' ')}</span>
                        <span className="font-medium text-red-700">{formatCurrency(value)}</span>
                      </div>
                    ))}
                    <div className="flex justify-between items-center p-3 bg-red-100 rounded font-bold">
                      <span>Total Deductions</span>
                      <span className="text-red-700">{formatCurrency(ytdSummary.total_deductions)}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">No data available</p>
                )}
              </CardContent>
            </Card>

            {/* Tax Summary */}
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="text-base">Tax Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-purple-50 rounded-lg text-center">
                    <p className="text-sm text-gray-500">TDS Deducted</p>
                    <p className="text-xl font-bold text-purple-700">{formatCurrency(ytdSummary?.total_tax_deducted || 0)}</p>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg text-center">
                    <p className="text-sm text-gray-500">PF Contribution</p>
                    <p className="text-xl font-bold text-blue-700">{formatCurrency(ytdSummary?.total_pf_contribution || 0)}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Net Pay (YTD)</p>
                    <p className="text-xl font-bold text-green-700">{formatCurrency(ytdSummary?.total_net_pay || 0)}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Months Processed</p>
                    <p className="text-xl font-bold">{ytdSummary?.months_paid || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
