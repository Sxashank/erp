import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, FileText, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { voucherTemplatesApi } from '@/services/api';

interface TemplateDetail {
  id: string;
  template_name: string;
  voucher_type_name: string;
  total_amount: number;
  default_narration: string | null;
  category: string | null;
  lines: Array<{
    account_name: string;
    account_code: string;
    debit_amount: number;
    credit_amount: number;
  }>;
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

  useEffect(() => {
    if (id) {
      fetchTemplate(id);
    }
  }, [id]);

  const fetchTemplate = async (templateId: string) => {
    try {
      setLoading(true);
      const response = await voucherTemplatesApi.get(templateId);
      setTemplate(response.data);
      setNarration(response.data.default_narration || '');
    } catch (error) {
      console.error('Failed to fetch template:', error);
      toast({ title: 'Error', description: 'Failed to load template', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!id) return;

    try {
      setSubmitting(true);
      const response = await voucherTemplatesApi.use(id, {
        voucher_date: voucherDate,
        narration_override: narration || undefined,
        amount_multiplier: parseFloat(multiplier) || undefined,
      });

      if (response.data.success) {
        toast({ title: 'Success', description: response.data.message });
        navigate(`/admin/finance/vouchers/${response.data.voucher_id}`);
      } else {
        toast({ title: 'Error', description: response.data.message, variant: 'destructive' });
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create voucher',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!template) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-500">Template not found</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/admin/finance/voucher-templates')}>
          Back to Templates
        </Button>
      </div>
    );
  }

  const calculatedAmount = template.total_amount * (parseFloat(multiplier) || 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/finance/voucher-templates')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Use Template</h1>
          <p className="text-sm text-slate-500">Create a voucher from template</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template Info */}
        <div className="lg:col-span-2 space-y-6">
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
                  <span className="font-mono">{formatCurrency(template.total_amount)}</span>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="text-left p-3 font-medium">Account</th>
                        <th className="text-right p-3 font-medium">Debit</th>
                        <th className="text-right p-3 font-medium">Credit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {template.lines.map((line, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="p-3">
                            <span className="text-slate-500">{line.account_code}</span> - {line.account_name}
                          </td>
                          <td className="p-3 text-right font-mono">
                            {line.debit_amount > 0
                              ? formatCurrency(line.debit_amount * (parseFloat(multiplier) || 1))
                              : '-'}
                          </td>
                          <td className="p-3 text-right font-mono">
                            {line.credit_amount > 0
                              ? formatCurrency(line.credit_amount * (parseFloat(multiplier) || 1))
                              : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-slate-50 font-medium">
                      <tr className="border-t">
                        <td className="p-3">Total</td>
                        <td className="p-3 text-right font-mono">{formatCurrency(calculatedAmount)}</td>
                        <td className="p-3 text-right font-mono">{formatCurrency(calculatedAmount)}</td>
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
                  <p className="text-xs text-slate-500 mt-1">Default: {template.default_narration}</p>
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
                <p className="text-xs text-slate-500 mt-1">Use to scale the template amounts</p>
              </div>

              <div className="pt-4 border-t">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-500">Final Amount:</span>
                  <span className="font-bold font-mono">{formatCurrency(calculatedAmount)}</span>
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
