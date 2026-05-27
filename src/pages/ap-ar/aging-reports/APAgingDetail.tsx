import { format } from 'date-fns';
import { FileSpreadsheet, Printer, RefreshCw } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
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
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { agingReportsApi, vendorsApi } from '@/services/api';
import { useActiveOrganizationId } from '@/stores/organizationStore';

interface AgingBill {
  bill_id: string;
  bill_number: string;
  bill_date: string;
  due_date: string;
  total_amount: number;
  paid_amount: number;
  balance_amount: number;
  days_overdue: number;
  aging_bucket: string;
}

interface VendorAgingDetail {
  vendor_id: string;
  vendor_code: string;
  vendor_name: string;
  as_of_date: string;
  bills: AgingBill[];
  totals: {
    current: number;
    days_1_30: number;
    days_31_60: number;
    days_61_90: number;
    days_90_plus: number;
    total: number;
  };
}

interface Vendor {
  id: string;
  code: string;
  name: string;
}

export function APAgingDetail() {
  const navigate = useNavigate();
  const { vendorId } = useParams<{ vendorId: string }>();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const organizationId = useActiveOrganizationId() || '';
  const asOfDate = searchParams.get('as_of_date') || format(new Date(), 'yyyy-MM-dd');

  const [loading, setLoading] = useState(false);
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [reportData, setReportData] = useState<VendorAgingDetail | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!organizationId || !vendorId) return;

      setLoading(true);
      try {
        // Fetch vendor details
        const vendorResponse = await vendorsApi.get(vendorId);
        setVendor(vendorResponse.data);

        // Fetch aging detail
        const response = await agingReportsApi.getAPAgingDetail(vendorId, {
          as_of_date: asOfDate,
        });
        setReportData(response.data);
      } catch (error) {
        showErrorToast(error, toast);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [vendorId, asOfDate, organizationId, toast]);

  const formatAmount = (amount: number) => {
    return formatIndianCompactCurrency(amount);
  };

  const getAgingBadge = (bucket: string) => {
    switch (bucket) {
      case 'current':
        return (
          <Badge variant="outline" className="bg-green-50 text-green-700">
            Current
          </Badge>
        );
      case '1-30':
        return (
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            1-30 Days
          </Badge>
        );
      case '31-60':
        return (
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
            31-60 Days
          </Badge>
        );
      case '61-90':
        return (
          <Badge variant="outline" className="bg-orange-50 text-orange-700">
            61-90 Days
          </Badge>
        );
      case '90+':
        return (
          <Badge variant="outline" className="bg-red-50 text-red-700">
            90+ Days
          </Badge>
        );
      default:
        return <Badge variant="outline">{bucket}</Badge>;
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleViewBill = (billId: string) => {
    navigate(`/admin/ap-ar/purchase-bills/${billId}`);
  };

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <PageHeader
          title="AP Aging Detail"
          subtitle={vendor ? `${vendor.code} - ${vendor.name}` : 'Loading...'}
          breadcrumbs={[
            { label: 'AP Aging', to: '/admin/ap-ar/aging-reports/ap' },
            { label: vendor?.code ?? 'Detail' },
          ]}
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

      {/* Bills Table */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : reportData ? (
        <Card className="print:border-0 print:shadow-none">
          <CardHeader className="text-center">
            <CardTitle>Outstanding Bills</CardTitle>
            <CardDescription>
              As of {format(new Date(reportData.as_of_date), 'dd/MM/yyyy')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bill Number</TableHead>
                  <TableHead>Bill Date</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead className="text-right">Bill Amount</TableHead>
                  <TableHead className="text-right">Paid Amount</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead className="text-center">Days Overdue</TableHead>
                  <TableHead>Aging</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reportData.bills.map((bill) => (
                  <TableRow
                    key={bill.bill_id}
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => handleViewBill(bill.bill_id)}
                  >
                    <TableCell className="font-medium">{bill.bill_number}</TableCell>
                    <TableCell>{format(new Date(bill.bill_date), 'dd/MM/yyyy')}</TableCell>
                    <TableCell>{format(new Date(bill.due_date), 'dd/MM/yyyy')}</TableCell>
                    <TableCell className="text-right">{formatAmount(bill.total_amount)}</TableCell>
                    <TableCell className="text-right">{formatAmount(bill.paid_amount)}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatAmount(bill.balance_amount)}
                    </TableCell>
                    <TableCell className="text-center">
                      {bill.days_overdue > 0 ? (
                        <span className="text-red-600">{bill.days_overdue}</span>
                      ) : (
                        <span className="text-green-600">-</span>
                      )}
                    </TableCell>
                    <TableCell>{getAgingBadge(bill.aging_bucket)}</TableCell>
                  </TableRow>
                ))}
                {reportData.bills.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-slate-500">
                      No outstanding bills found
                    </TableCell>
                  </TableRow>
                )}
                {reportData.bills.length > 0 && (
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
