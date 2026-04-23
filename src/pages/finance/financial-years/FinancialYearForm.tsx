import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Lock, Loader2, Save } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
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
import { financialYearsApi, organizationsApi } from '@/services/api';
import type { FinancialYear, FinancialYearCreate, FinancialYearUpdate, Organization, PaginatedResponse } from '@/types';

export function FinancialYearForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [financialYear, setFinancialYear] = useState<FinancialYear | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<FinancialYearCreate | FinancialYearUpdate>();

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      fetchFinancialYear(id);
    }
  }, [id, isEdit]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchFinancialYear = async (fyId: string) => {
    try {
      setLoading(true);
      const response = await financialYearsApi.get(fyId);
      const fy: FinancialYear = response.data;
      setFinancialYear(fy);
      reset({
        code: fy.code,
        name: fy.name,
        start_date: fy.start_date,
        end_date: fy.end_date,
        organization_id: fy.organization_id,
        is_current: fy.is_current,
      });
    } catch (error) {
      console.error('Failed to fetch financial year:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClosePeriod = async (periodId: string) => {
    if (!id || !confirm('Are you sure you want to close this period? This action cannot be undone.')) return;
    try {
      await financialYearsApi.closePeriod(id, periodId);
      fetchFinancialYear(id);
    } catch (error) {
      console.error('Failed to close period:', error);
    }
  };

  const onSubmit = async (data: FinancialYearCreate | FinancialYearUpdate) => {
    try {
      setSubmitting(true);
      if (isEdit && id) {
        await financialYearsApi.update(id, data);
      } else {
        await financialYearsApi.create(data);
      }
      navigate('/admin/finance/financial-years');
    } catch (error) {
      console.error('Failed to save financial year:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/finance/financial-years')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {isEdit ? 'Edit Financial Year' : 'New Financial Year'}
          </h1>
          <p className="text-sm text-slate-500">
            {isEdit ? 'Update financial year details' : 'Create a new financial year with periods'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Financial Year Details</CardTitle>
            <CardDescription>Basic information about the financial year</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="organization_id">Organization *</Label>
                <Select
                  value={watch('organization_id') || ''}
                  onValueChange={(value) => setValue('organization_id', value)}
                  disabled={isEdit}
                >
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
                {errors.organization_id && (
                  <p className="text-sm text-red-500">Organization is required</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="code">Financial Year Code *</Label>
                <Input
                  id="code"
                  {...register('code', { required: 'Code is required' })}
                  placeholder="FY2024-25"
                  disabled={isEdit}
                />
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Financial Year Name *</Label>
              <Input
                id="name"
                {...register('name', { required: 'Name is required' })}
                placeholder="April 2024 - March 2025"
              />
              {errors.name && (
                <p className="text-sm text-red-500">{errors.name.message}</p>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date *</Label>
                <Input
                  id="start_date"
                  type="date"
                  {...register('start_date', { required: 'Start date is required' })}
                  disabled={isEdit}
                />
                {errors.start_date && (
                  <p className="text-sm text-red-500">{errors.start_date.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="end_date">End Date *</Label>
                <Input
                  id="end_date"
                  type="date"
                  {...register('end_date', { required: 'End date is required' })}
                  disabled={isEdit}
                />
                {errors.end_date && (
                  <p className="text-sm text-red-500">{errors.end_date.message}</p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_current"
                checked={watch('is_current') || false}
                onCheckedChange={(checked) => setValue('is_current', checked as boolean)}
              />
              <Label htmlFor="is_current" className="cursor-pointer">
                Set as current financial year
              </Label>
            </div>
          </CardContent>
        </Card>

        {isEdit && financialYear?.periods && financialYear.periods.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Financial Periods</CardTitle>
              <CardDescription>Monthly periods within this financial year</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Period</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Start Date</TableHead>
                    <TableHead>End Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {financialYear.periods.map((period) => (
                    <TableRow key={period.id}>
                      <TableCell className="font-medium">P{period.period_number}</TableCell>
                      <TableCell>{period.name}</TableCell>
                      <TableCell>{formatDate(period.start_date)}</TableCell>
                      <TableCell>{formatDate(period.end_date)}</TableCell>
                      <TableCell>
                        <Badge
                          className={
                            period.is_closed
                              ? 'bg-slate-100 text-slate-600 hover:bg-slate-100'
                              : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-50'
                          }
                        >
                          {period.is_closed ? 'Closed' : 'Open'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {!period.is_closed && !financialYear.is_closed && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => handleClosePeriod(period.id)}
                          >
                            <Lock className="mr-1 h-3 w-3" />
                            Close
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/finance/financial-years')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting || financialYear?.is_closed}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Financial Year' : 'Create Financial Year'}
          </Button>
        </div>
      </form>
    </div>
  );
}
