import { Calendar, FileText, Loader2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { recurringVouchersApi } from '@/services/api';

import { logger } from '@/lib/logger';
interface RecurringVoucherDetail {
  id: string;
  template_name: string;
  voucher_type_name: string;
  frequency: string;
  total_amount: number;
  next_run_date: string | null;
  completed_occurrences: number;
  total_occurrences: number | null;
  status: string;
  lines: {
    account_name: string;
    account_code: string;
    debit_amount: number;
    credit_amount: number;
  }[];
}

const FREQUENCY_LABELS: Record<string, string> = {
  DAILY: 'Daily',
  WEEKLY: 'Weekly',
  MONTHLY: 'Monthly',
  QUARTERLY: 'Quarterly',
  HALF_YEARLY: 'Half-Yearly',
  YEARLY: 'Yearly',
};

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'bg-emerald-100 text-emerald-700',
  PAUSED: 'bg-amber-100 text-amber-700',
  COMPLETED: 'bg-slate-100 text-slate-700',
  CANCELLED: 'bg-red-100 text-red-700',
};

export function GenerateRecurringVoucher() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [recurringVoucher, setRecurringVoucher] = useState<RecurringVoucherDetail | null>(null);

  const [voucherDate, setVoucherDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchRecurringVoucher = useCallback(
    async (rvId: string) => {
      try {
        setLoading(true);
        const response = await recurringVouchersApi.get(rvId);
        setRecurringVoucher(response.data);
        if (response.data.next_run_date) {
          setVoucherDate(response.data.next_run_date);
        }
      } catch (error) {
        logger.error('Failed to fetch recurring voucher:', error);
        toast({
          title: 'Error',
          description: 'Failed to load recurring voucher',
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    },
    [toast],
  );

  useEffect(() => {
    if (id) {
      fetchRecurringVoucher(id);
    }
  }, [fetchRecurringVoucher, id]);

  const handleSubmit = async () => {
    if (!id) return;

    try {
      setSubmitting(true);
      const response = await recurringVouchersApi.generate(id, { voucher_date: voucherDate });

      if (response.data.success) {
        toast({ title: 'Success', description: response.data.message });
        navigate(`/admin/finance/vouchers/${response.data.voucher_id}`);
      } else {
        toast({ title: 'Error', description: response.data.message, variant: 'destructive' });
      }
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setSubmitting(false);
    }
  };
  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!recurringVoucher) {
    return (
      <div className="py-12 text-center">
        <p className="text-slate-500">Recurring voucher not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate('/admin/finance/recurring-vouchers')}
        >
          Back to Recurring Vouchers
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Generate Voucher"
        subtitle="Manually generate a voucher from this recurring template"
        breadcrumbs={[
          { label: 'Recurring Vouchers', to: '/admin/finance/recurring-vouchers' },
          { label: 'Generate' },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recurring Voucher Info */}
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{recurringVoucher.template_name}</CardTitle>
                  <CardDescription>{recurringVoucher.voucher_type_name}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Badge variant="outline">{FREQUENCY_LABELS[recurringVoucher.frequency]}</Badge>
                  <Badge className={STATUS_COLORS[recurringVoucher.status]}>
                    {recurringVoucher.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">Amount:</span>{' '}
                    <span className="font-mono font-medium">
                      {formatIndianCompactCurrency(recurringVoucher.total_amount)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Next Run:</span>{' '}
                    <span className="font-medium">
                      <DateDisplay date={recurringVoucher.next_run_date} />
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500">Progress:</span>{' '}
                    <span className="font-medium">
                      {recurringVoucher.total_occurrences
                        ? `${recurringVoucher.completed_occurrences} / ${recurringVoucher.total_occurrences}`
                        : `${recurringVoucher.completed_occurrences} generated`}
                    </span>
                  </div>
                </div>

                <div className="overflow-hidden rounded-lg border">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="p-3 text-left font-medium">Account</th>
                        <th className="p-3 text-right font-medium">Debit</th>
                        <th className="p-3 text-right font-medium">Credit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recurringVoucher.lines.map((line, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="p-3">
                            <span className="text-slate-500">{line.account_code}</span> -{' '}
                            {line.account_name}
                          </td>
                          <td className="p-3 text-right font-mono">
                            {line.debit_amount > 0
                              ? formatIndianCompactCurrency(line.debit_amount)
                              : '-'}
                          </td>
                          <td className="p-3 text-right font-mono">
                            {line.credit_amount > 0
                              ? formatIndianCompactCurrency(line.credit_amount)
                              : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-slate-50 font-medium">
                      <tr className="border-t">
                        <td className="p-3">Total</td>
                        <td className="p-3 text-right font-mono">
                          {formatIndianCompactCurrency(recurringVoucher.total_amount)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatIndianCompactCurrency(recurringVoucher.total_amount)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Generate Settings */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Voucher Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Voucher Date *</Label>
                <Input
                  type="date"
                  value={voucherDate}
                  onChange={(e) => setVoucherDate(e.target.value)}
                />
                {recurringVoucher.next_run_date && (
                  <p className="mt-1 text-xs text-slate-500">
                    Scheduled: <DateDisplay date={recurringVoucher.next_run_date} />
                  </p>
                )}
              </div>

              <div className="border-t pt-4">
                <div className="mb-2 flex justify-between text-sm">
                  <span className="text-slate-500">Voucher Amount:</span>
                  <span className="font-mono font-bold">
                    {formatIndianCompactCurrency(recurringVoucher.total_amount)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <Button className="w-full" onClick={handleSubmit} disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Generate Voucher
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default GenerateRecurringVoucher;
