import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Plus, Save, Trash2 } from 'lucide-react';

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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';
import {
  organizationsApi,
  voucherTypesApi,
  accountsApi,
  voucherTemplatesApi,
} from '@/services/api';

interface Organization {
  id: string;
  name: string;
}

interface VoucherType {
  id: string;
  name: string;
  code: string;
}

interface Account {
  id: string;
  code: string;
  name: string;
}

interface LineItem {
  account_id: string;
  debit_amount: string;
  credit_amount: string;
  narration: string;
}

const CATEGORIES = [
  'PAYROLL',
  'RENT',
  'UTILITIES',
  'TAX',
  'DEPRECIATION',
  'INSURANCE',
  'INTEREST',
  'MISC',
];

export function VoucherTemplateForm() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [voucherTypes, setVoucherTypes] = useState<VoucherType[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);

  const [selectedOrgId, setSelectedOrgId] = useState<string>(searchParams.get('org') || '');
  const [formData, setFormData] = useState({
    template_name: '',
    description: '',
    voucher_type_id: '',
    default_narration: '',
    category: '',
    is_favorite: false,
  });

  const [lines, setLines] = useState<LineItem[]>([
    { account_id: '', debit_amount: '', credit_amount: '', narration: '' },
    { account_id: '', debit_amount: '', credit_amount: '', narration: '' },
  ]);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchVoucherTypes();
      fetchAccounts();
    }
  }, [selectedOrgId]);

  useEffect(() => {
    if (isEdit && id && selectedOrgId) {
      fetchTemplate(id);
    }
  }, [id, isEdit, selectedOrgId]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      setOrganizations(response.data.items);
      if (!selectedOrgId && response.data.items.length > 0) {
        setSelectedOrgId(response.data.items[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchVoucherTypes = async () => {
    try {
      const response = await voucherTypesApi.list({ organization_id: selectedOrgId, page_size: 100 });
      setVoucherTypes(response.data.items);
    } catch (error) {
      console.error('Failed to fetch voucher types:', error);
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await accountsApi.list({ organization_id: selectedOrgId, page_size: 500 });
      setAccounts(response.data.items.filter((a: any) => a.account_type !== 'GROUP'));
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    }
  };

  const fetchTemplate = async (templateId: string) => {
    try {
      setLoading(true);
      const response = await voucherTemplatesApi.get(templateId);
      const template = response.data;

      setFormData({
        template_name: template.template_name,
        description: template.description || '',
        voucher_type_id: template.voucher_type_id,
        default_narration: template.default_narration || '',
        category: template.category || '',
        is_favorite: template.is_favorite,
      });

      setLines(
        template.lines.map((line: any) => ({
          account_id: line.account_id,
          debit_amount: line.debit_amount.toString(),
          credit_amount: line.credit_amount.toString(),
          narration: line.narration || '',
        }))
      );
    } catch (error) {
      console.error('Failed to fetch template:', error);
      toast({ title: 'Error', description: 'Failed to load template', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    const validLines = lines.filter(
      (l) => l.account_id && (parseFloat(l.debit_amount) > 0 || parseFloat(l.credit_amount) > 0)
    );

    if (validLines.length < 2) {
      toast({ title: 'Error', description: 'At least 2 line items are required', variant: 'destructive' });
      return;
    }

    const totalDebit = validLines.reduce((sum, l) => sum + (parseFloat(l.debit_amount) || 0), 0);
    const totalCredit = validLines.reduce((sum, l) => sum + (parseFloat(l.credit_amount) || 0), 0);

    if (Math.abs(totalDebit - totalCredit) > 0.01) {
      toast({ title: 'Error', description: 'Debit and Credit must be equal', variant: 'destructive' });
      return;
    }

    if (!formData.template_name || !formData.voucher_type_id) {
      toast({ title: 'Error', description: 'Please fill all required fields', variant: 'destructive' });
      return;
    }

    try {
      setSubmitting(true);

      const payload = {
        organization_id: selectedOrgId,
        voucher_type_id: formData.voucher_type_id,
        template_name: formData.template_name,
        description: formData.description || null,
        default_narration: formData.default_narration || null,
        category: formData.category || null,
        is_favorite: formData.is_favorite,
        lines: validLines.map((l) => ({
          account_id: l.account_id,
          debit_amount: parseFloat(l.debit_amount) || 0,
          credit_amount: parseFloat(l.credit_amount) || 0,
          narration: l.narration || null,
        })),
      };

      if (isEdit && id) {
        await voucherTemplatesApi.update(id, payload);
        toast({ title: 'Success', description: 'Template updated successfully' });
      } else {
        await voucherTemplatesApi.create(payload);
        toast({ title: 'Success', description: 'Template created successfully' });
      }

      navigate('/admin/finance/voucher-templates');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save template',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const addLine = () => {
    setLines([...lines, { account_id: '', debit_amount: '', credit_amount: '', narration: '' }]);
  };

  const removeLine = (index: number) => {
    if (lines.length > 2) {
      setLines(lines.filter((_, i) => i !== index));
    }
  };

  const updateLine = (index: number, field: keyof LineItem, value: string) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setLines(newLines);
  };

  const totalDebit = lines.reduce((sum, l) => sum + (parseFloat(l.debit_amount) || 0), 0);
  const totalCredit = lines.reduce((sum, l) => sum + (parseFloat(l.credit_amount) || 0), 0);

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/finance/voucher-templates')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {isEdit ? 'Edit Voucher Template' : 'New Voucher Template'}
          </h1>
          <p className="text-sm text-slate-500">Create a reusable voucher entry template</p>
        </div>
      </div>

      {/* Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Organization *</Label>
                  <Select value={selectedOrgId} onValueChange={setSelectedOrgId} disabled={isEdit}>
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
                  <Label>Voucher Type *</Label>
                  <Select
                    value={formData.voucher_type_id}
                    onValueChange={(v) => setFormData({ ...formData, voucher_type_id: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {voucherTypes.map((vt) => (
                        <SelectItem key={vt.id} value={vt.id}>
                          {vt.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label>Template Name *</Label>
                <Input
                  placeholder="e.g., Monthly Rent Payment"
                  value={formData.template_name}
                  onChange={(e) => setFormData({ ...formData, template_name: e.target.value })}
                />
              </div>

              <div>
                <Label>Description</Label>
                <Textarea
                  placeholder="Optional description..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Additional Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Category</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(v) => setFormData({ ...formData, category: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((c) => (
                        <SelectItem key={c} value={c}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Default Narration</Label>
                  <Input
                    placeholder="Default narration for voucher"
                    value={formData.default_narration}
                    onChange={(e) => setFormData({ ...formData, default_narration: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_favorite"
                  checked={formData.is_favorite}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_favorite: checked === true })}
                />
                <Label htmlFor="is_favorite" className="cursor-pointer">
                  Mark as Favorite
                </Label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Line Items</CardTitle>
              <Button type="button" variant="outline" size="sm" onClick={addLine}>
                <Plus className="h-4 w-4 mr-1" /> Add Line
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40%]">Account</TableHead>
                    <TableHead>Debit</TableHead>
                    <TableHead>Credit</TableHead>
                    <TableHead>Narration</TableHead>
                    <TableHead className="w-10"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.map((line, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Select value={line.account_id} onValueChange={(v) => updateLine(idx, 'account_id', v)}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select account" />
                          </SelectTrigger>
                          <SelectContent>
                            {accounts.map((acc) => (
                              <SelectItem key={acc.id} value={acc.id}>
                                {acc.code} - {acc.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={line.debit_amount}
                          onChange={(e) => updateLine(idx, 'debit_amount', e.target.value)}
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={line.credit_amount}
                          onChange={(e) => updateLine(idx, 'credit_amount', e.target.value)}
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          placeholder="Optional"
                          value={line.narration}
                          onChange={(e) => updateLine(idx, 'narration', e.target.value)}
                        />
                      </TableCell>
                      <TableCell>
                        {lines.length > 2 && (
                          <Button variant="ghost" size="icon" onClick={() => removeLine(idx)}>
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="flex justify-end gap-8 mt-4 text-sm">
                <span>
                  Total Debit: <strong className="font-mono">{formatCurrency(totalDebit)}</strong>
                </span>
                <span>
                  Total Credit: <strong className="font-mono">{formatCurrency(totalCredit)}</strong>
                </span>
              </div>

              {Math.abs(totalDebit - totalCredit) > 0.01 && (
                <p className="text-red-500 text-sm mt-2">Debit and Credit must be equal</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <Button className="w-full" onClick={handleSubmit} disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    {isEdit ? 'Update' : 'Create'} Template
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

export default VoucherTemplateForm;
