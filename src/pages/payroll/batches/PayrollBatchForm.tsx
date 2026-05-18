/**
 * Payroll Batch Create Page
 */

import { Save, Calendar } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import payrollService from '@/services/payrollService';
import { getErrorMessage } from "@/lib/errorMessage";

const MONTHS = [
  { value: '1', label: 'January' },
  { value: '2', label: 'February' },
  { value: '3', label: 'March' },
  { value: '4', label: 'April' },
  { value: '5', label: 'May' },
  { value: '6', label: 'June' },
  { value: '7', label: 'July' },
  { value: '8', label: 'August' },
  { value: '9', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
];

export default function PayrollBatchForm() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [saving, setSaving] = useState(false);

  const organizationId = useRequiredActiveOrganizationId();

  const currentDate = new Date();
  const currentYear = currentDate.getFullYear();
  const currentMonth = currentDate.getMonth() + 1;

  const years = Array.from({ length: 3 }, (_, i) => currentYear - i + 1);

  const [formData, setFormData] = useState({
    organization_id: organizationId,
    payroll_month: currentMonth.toString(),
    payroll_year: currentYear.toString(),
    pay_period_from: '',
    pay_period_to: '',
    remarks: '',
  });

  // Auto-generate pay period dates when month/year changes
  const updatePayPeriod = (month: string, year: string) => {
    if (month && year) {
      const m = parseInt(month);
      const y = parseInt(year);
      const startDate = new Date(y, m - 1, 1);
      const endDate = new Date(y, m, 0); // Last day of month

      setFormData((prev) => ({
        ...prev,
        pay_period_from: startDate.toISOString().split('T')[0],
        pay_period_to: endDate.toISOString().split('T')[0],
      }));
    }
  };

  const handleMonthChange = (value: string) => {
    setFormData((prev) => ({ ...prev, payroll_month: value }));
    updatePayPeriod(value, formData.payroll_year);
  };

  const handleYearChange = (value: string) => {
    setFormData((prev) => ({ ...prev, payroll_year: value }));
    updatePayPeriod(formData.payroll_month, value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.payroll_month || !formData.payroll_year) {
      toast({
        title: 'Validation Error',
        description: 'Month and year are required',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.pay_period_from || !formData.pay_period_to) {
      toast({
        title: 'Validation Error',
        description: 'Pay period dates are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);

      const payload = {
        organization_id: formData.organization_id,
        payroll_month: parseInt(formData.payroll_month),
        payroll_year: parseInt(formData.payroll_year),
        pay_period_from: formData.pay_period_from,
        pay_period_to: formData.pay_period_to,
        remarks: formData.remarks || undefined,
      };

      const batch = await payrollService.createBatch(payload);
      toast({
        title: 'Success',
        description: 'Payroll batch created successfully',
      });

      navigate(`/admin/payroll/batches/${batch.id}`);
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to create batch'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="New Payroll Batch"
        subtitle="Create a new payroll batch for processing"
        breadcrumbs={[{ label: 'Payroll Batches', to: '/admin/payroll/batches' }, { label: 'New' }]}
      />

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Payroll Period</CardTitle>
              <CardDescription>Select the month and year for payroll processing</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="payroll_month">Month *</Label>
                  <Select value={formData.payroll_month} onValueChange={handleMonthChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select month" />
                    </SelectTrigger>
                    <SelectContent>
                      {MONTHS.map((month) => (
                        <SelectItem key={month.value} value={month.value}>
                          {month.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="payroll_year">Year *</Label>
                  <Select value={formData.payroll_year} onValueChange={handleYearChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select year" />
                    </SelectTrigger>
                    <SelectContent>
                      {years.map((year) => (
                        <SelectItem key={year} value={year.toString()}>
                          {year}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pay Period Dates</CardTitle>
              <CardDescription>Define the actual date range for salary calculation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="pay_period_from">From Date *</Label>
                  <Input
                    id="pay_period_from"
                    type="date"
                    value={formData.pay_period_from}
                    onChange={(e) => setFormData({ ...formData, pay_period_from: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="pay_period_to">To Date *</Label>
                  <Input
                    id="pay_period_to"
                    type="date"
                    value={formData.pay_period_to}
                    onChange={(e) => setFormData({ ...formData, pay_period_to: e.target.value })}
                  />
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                <Calendar className="mr-1 inline-block h-4 w-4" />
                These dates determine the attendance period for LOP calculation
              </p>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Additional Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label htmlFor="remarks">Remarks</Label>
                <Textarea
                  id="remarks"
                  value={formData.remarks}
                  onChange={(e) => setFormData({ ...formData, remarks: e.target.value })}
                  placeholder="Optional notes about this payroll batch"
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/payroll/batches')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Creating...' : 'Create Batch'}
          </Button>
        </div>
      </form>
    </div>
  );
}
