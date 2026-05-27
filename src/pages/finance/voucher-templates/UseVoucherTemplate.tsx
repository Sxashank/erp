import { FileText, Loader2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { voucherTemplatesApi } from '@/services/api';

import { logger } from '@/lib/logger';
interface TemplateDetail {
  id: string;
  template_name: string;
  voucher_type_name: string;
  total_amount: number;
  default_narration: string | null;
  category: string | null;
  lines: {
    account_name: string;
    account_code: string;
    debit_amount: number;
    credit_amount: number;
  }[];
}

export function UseVoucherTemplate() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [template, setTemplate] = useState<TemplateDetail | null>(null);

  const [voucherDate, setVoucherDate] = useState(new Date().toISOString().split('T')[0]);
  const [narration, setNarration] = useState('');
  const [multiplier, setMultiplier] = useState('1');

  const fetchTemplate = useCallback(
    async (templateId: string) => {
      try {
        setLoading(true);
        const response = await voucherTemplatesApi.get(templateId);
        setTemplate(response.data);
        setNarration(response.data.default_narration || '');
      } catch (error) {
        logger.error('Failed to fetch template:', error);
        toast({ title: 'Error', description: 'Failed to load template', variant: 'destructive' });
      } finally {
        setLoading(false);
      }
    },
    [toast],
  );

  useEffect(() => {
    if (id) {
      fetchTemplate(id);
    }
  }, [fetchTemplate, id]);

  const handleSubmit = async () => {
    if (!id) return;

    try {
      setSubmitting(true);
      const response = await voucherTemplatesApi.use(id, {
        voucherDate,
        narrationOverride: narration || undefined,
        amountMultiplier: parseFloat(multiplier) || undefined,
      });

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

  if (!template) {
    return (
      <div className="py-12 text-center">
        <p className="text-slate-500">Template not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate('/admin/finance/voucher-templates')}
        >
          Back to Templates
        </Button>
      </div>
    );
  }

  const calculatedAmount = template.total_amount * (parseFloat(multiplier) || 1);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Use Template"
        subtitle="Create a voucher from template"
        breadcrumbs={[
          { label: 'Voucher Templates', to: '/admin/finance/voucher-templates' },
          { label: 'Use' },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Template Info */}
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{template.template_name}</CardTitle>
                  <CardDescription>{template.voucher_type_name}</CardDescription>
                </div>
                {template.category && <Badge variant="outline">{template.category}</Badge>}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-slate-600">
                  <span className="font-medium">Base Amount:</span>{' '}
                  <span className="font-mono">
                    {formatIndianCompactCurrency(template.total_amount)}
                  </span>
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
                      {template.lines.map((line, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="p-3">
                            <span className="text-slate-500">{line.account_code}</span> -{' '}
                            {line.account_name}
                          </td>
                          <td className="p-3 text-right font-mono">
                            {line.debit_amount > 0
                              ? formatIndianCompactCurrency(
                                  line.debit_amount * (parseFloat(multiplier) || 1),
                                )
                              : '-'}
                          </td>
                          <td className="p-3 text-right font-mono">
                            {line.credit_amount > 0
                              ? formatIndianCompactCurrency(
                                  line.credit_amount * (parseFloat(multiplier) || 1),
                                )
                              : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-slate-50 font-medium">
                      <tr className="border-t">
                        <td className="p-3">Total</td>
                        <td className="p-3 text-right font-mono">
                          {formatIndianCompactCurrency(calculatedAmount)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatIndianCompactCurrency(calculatedAmount)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Voucher Settings */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Voucher Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Voucher Date *</Label>
                <Input
                  type="date"
                  value={voucherDate}
                  onChange={(e) => setVoucherDate(e.target.value)}
                />
              </div>

              <div>
                <Label>Narration</Label>
                <Input
                  placeholder="Leave empty to use default"
                  value={narration}
                  onChange={(e) => setNarration(e.target.value)}
                />
                {template.default_narration && (
                  <p className="mt-1 text-xs text-slate-500">
                    Default: {template.default_narration}
                  </p>
                )}
              </div>

              <div>
                <Label>Amount Multiplier</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="1.00"
                  value={multiplier}
                  onChange={(e) => setMultiplier(e.target.value)}
                />
                <p className="mt-1 text-xs text-slate-500">Use to scale the template amounts</p>
              </div>

              <div className="border-t pt-4">
                <div className="mb-2 flex justify-between text-sm">
                  <span className="text-slate-500">Final Amount:</span>
                  <span className="font-mono font-bold">
                    {formatIndianCompactCurrency(calculatedAmount)}
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
                    Creating...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Create Voucher
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

export default UseVoucherTemplate;
