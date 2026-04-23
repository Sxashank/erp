import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Plus, Save, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  recurringVouchersApi,
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

const FREQUENCIES = [
  { value: 'DAILY', label: 'Daily' },
  { value: 'WEEKLY', label: 'Weekly' },
  { value: 'MONTHLY', label: 'Monthly' },
  { value: 'QUARTERLY', label: 'Quarterly' },
  { value: 'HALF_YEARLY', label: 'Half-Yearly' },
  { value: 'YEARLY', label: 'Yearly' },
];

export function RecurringVoucherForm() {
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
    frequency: 'MONTHLY',
    day_of_month: 1,
    day_of_week: 0,
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    total_occurrences: '',
    auto_post: false,
    auto_approve: false,
    narration_template: '',
    notify_on_generation: true,
    notify_days_before: 0,
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
      fetchRecurringVoucher(id);
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

  const fetchRecurringVoucher = async (rvId: string) => {
    try {
      setLoading(true);
      const response = await recurringVouchersApi.get(rvId);
      const rv = response.data;

      setFormData({
        template_name: rv.template_name,
        description: rv.description || '',
        voucher_type_id: rv.voucher_type_id,
        frequency: rv.frequency,
        day_of_month: rv.day_of_month || 1,
        day_of_week: rv.day_of_week || 0,
        start_date: rv.start_date,
        end_date: rv.end_date || '',
        total_occurrences: rv.total_occurrences?.toString() || '',
        auto_post: rv.auto_post,
        auto_approve: rv.auto_approve,
        narration_template: rv.narration_template || '',
        notify_on_generation: rv.notify_on_generation,
        notify_days_before: rv.notify_days_before || 0,
      });

      setLines(
        rv.lines.map((line: any) => ({
          account_id: line.account_id,
          debit_amount: line.debit_amount.toString(),
          credit_amount: line.credit_amount.toString(),
          narration: line.narration || '',
        }))
      );
    } catch (error) {
      console.error('Failed to fetch recurring voucher:', error);
      toast({ title: 'Error', description: 'Failed to load recurring voucher', variant: 'destructive' });
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
        frequency: formData.frequency,
        day_of_month: ['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY'].includes(formData.frequency)
          ? formData.day_of_month
          : null,
        day_of_week: formData.frequency === 'WEEKLY' ? formData.day_of_week : null,
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        total_occurrences: formData.total_occurrences ? parseInt(formData.total_occurrences) : null,
        auto_post: formData.auto_post,
        auto_approve: formData.auto_approve,
        narration_template: formData.narration_template || null,
        notify_on_generation: formData.notify_on_generation,
        notify_days_before: formData.notify_days_before,
        lines: validLines.map((l) => ({
          account_id: l.account_id,
          debit_amount: parseFloat(l.debit_amount) || 0,
          credit_amount: parseFloat(l.credit_amount) || 0,
          narration: l.narration || null,
        })),
      };

      if (isEdit && id) {
        await recurringVouchersApi.update(id, payload);
        toast({ title: 'Success', description: 'Recurring voucher updated successfully' });
      } else {
        await recurringVouchersApi.create(payload);
        toast({ title: 'Success', description: 'Recurring voucher created successfully' });
      }

      navigate('/admin/finance/recurring-vouchers');
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save recurring voucher',
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
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/finance/recurring-vouchers')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {isEdit ? 'Edit Recurring Voucher' : 'New Recurring Voucher'}
          </h1>
          <p className="text-sm text-slate-500">Set up automated periodic voucher entries</p>
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
                  placeholder="e.g., Monthly Rent - Head Office"
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
              <CardTitle>Schedule</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Frequency *</Label>
                  <Select
                    value={formData.frequency}
                    onValueChange={(v) => setFormData({ ...formData, frequency: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FREQUENCIES.map((f) => (
                        <SelectItem key={f.value} value={f.value}>
                          {f.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY'].includes(formData.frequency) && (
                  <div>
                    <Label>Day of Month</Label>
                    <Input
                      type="number"
                      min={1}
                      max={31}
                      value={formData.day_of_month}
                      onChange={(e) =>
                        setFormData({ ...formData, day_of_month: parseInt(e.target.value) || 1 })
                      }
                    />
                  </div>
                )}

                {formData.frequency === 'WEEKLY' && (
                  <div>
                    <Label>Day of Week</Label>
                    <Select
                      value={String(formData.day_of_week)}
                      onValueChange={(v) => setFormData({ ...formData, day_of_week: parseInt(v) })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0">Monday</SelectItem>
                        <SelectItem value="1">Tuesday</SelectItem>
                        <SelectItem value="2">Wednesday</SelectItem>
                        <SelectItem value="3">Thursday</SelectItem>
                        <SelectItem value="4">Friday</SelectItem>
                        <SelectItem value="5">Saturday</SelectItem>
                        <SelectItem value="6">Sunday</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div>
                  <Label>Start Date *</Label>
                  <Input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>End Date (optional)</Label>
                  <Input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Total Occurrences (optional)</Label>
                  <Input
                    type="number"
                    min={1}
                    placeholder="Unlimited"
                    value={formData.total_occurrences}
                    onChange={(e) => setFormData({ ...formData, total_occurrences: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Narration Template</Label>
                  <Input
                    placeholder="{month} {year} Rent"
                    value={formData.narration_template}
                    onChange={(e) => setFormData({ ...formData, narration_template: e.target.value })}
                  />
                </div>
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
            <CardHeader>
              <CardTitle>Options</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="auto_post"
                  checked={formData.auto_post}
                  onCheckedChange={(checked) => setFormData({ ...formData, auto_post: checked === true })}
                />
                <Label htmlFor="auto_post" className="cursor-pointer">
                  Auto-Post generated vouchers
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="auto_approve"
                  checked={formData.auto_approve}
                  onCheckedChange={(checked) => setFormData({ ...formData, auto_approve: checked === true })}
                  disabled={!formData.auto_post}
                />
                <Label htmlFor="auto_approve" className="cursor-pointer">
                  Auto-Approve (requires auto-post)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="notify"
                  checked={formData.notify_on_generation}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, notify_on_generation: checked === true })
                  }
                />
                <Label htmlFor="notify" className="cursor-pointer">
                  Notify on generation
                </Label>
              </div>
            </CardContent>
          </Card>

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
                    {isEdit ? 'Update' : 'Create'} Recurring Voucher
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

export default RecurringVoucherForm;
