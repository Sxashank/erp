/**
 * Dashboard Create Page
 */

import { Loader2, Save } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { biDashboardApi } from '@/services/biApi';
import type { DashboardCreate as DashboardCreateType } from '@/types/bi';

import { logger } from "@/lib/logger";
import { getErrorMessage } from "@/lib/errorMessage";
interface FormData {
  code: string;
  name: string;
  description: string;
  is_default: boolean;
  is_public: boolean;
  auto_refresh: boolean;
  refresh_interval_seconds: number;
}

export function DashboardCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);

  // Get organization ID (simplified - in real app, get from auth context)
  const organizationId = localStorage.getItem('organization_id') || '';

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      code: '',
      name: '',
      description: '',
      is_default: false,
      is_public: false,
      auto_refresh: false,
      refresh_interval_seconds: 60,
    },
  });

  const autoRefresh = watch('auto_refresh');

  const onSubmit = async (data: FormData) => {
    try {
      setSubmitting(true);

      const payload: DashboardCreateType = {
        ...data,
        organization_id: organizationId,
      };

      const response = await biDashboardApi.create(payload);

      toast({
        title: 'Success',
        description: 'Dashboard created successfully',
      });

      // Navigate to edit page to add widgets
      navigate(`/admin/bi/dashboards/${response.data.id}/edit`);
    } catch (error: unknown) {
      logger.error('Error creating dashboard:', error);
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to create dashboard'),
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Dashboard"
        subtitle="Create a new BI dashboard"
        breadcrumbs={[{ label: 'Dashboards', to: '/admin/bi/dashboards' }, { label: 'New' }]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <CardTitle>Dashboard Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="code">Code *</Label>
                <Input
                  id="code"
                  placeholder="SALES_DASHBOARD"
                  {...register('code', {
                    required: 'Code is required',
                    pattern: {
                      value: /^[A-Z0-9_]+$/,
                      message: 'Code must be uppercase letters, numbers, and underscores',
                    },
                  })}
                />
                {errors.code && <p className="text-sm text-red-500">{errors.code.message}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="Sales Dashboard"
                  {...register('name', { required: 'Name is required' })}
                />
                {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Dashboard description..."
                rows={3}
                {...register('description')}
              />
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Default Dashboard</Label>
                  <p className="text-sm text-muted-foreground">
                    Set as the default dashboard for the organization
                  </p>
                </div>
                <Switch
                  checked={watch('is_default')}
                  onCheckedChange={(checked) => setValue('is_default', checked)}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Public Dashboard</Label>
                  <p className="text-sm text-muted-foreground">
                    Make visible to all users without role restrictions
                  </p>
                </div>
                <Switch
                  checked={watch('is_public')}
                  onCheckedChange={(checked) => setValue('is_public', checked)}
                />
              </div>
            </div>

            <div className="border-t pt-6">
              <h3 className="mb-4 font-medium">Auto Refresh Settings</h3>
              <div className="grid grid-cols-2 gap-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Enable Auto Refresh</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically refresh widget data
                    </p>
                  </div>
                  <Switch
                    checked={autoRefresh}
                    onCheckedChange={(checked) => setValue('auto_refresh', checked)}
                  />
                </div>

                {autoRefresh && (
                  <div className="space-y-2">
                    <Label htmlFor="refresh_interval_seconds">Refresh Interval (seconds)</Label>
                    <Input
                      id="refresh_interval_seconds"
                      type="number"
                      min={10}
                      {...register('refresh_interval_seconds', {
                        min: { value: 10, message: 'Minimum 10 seconds' },
                        valueAsNumber: true,
                      })}
                    />
                    {errors.refresh_interval_seconds && (
                      <p className="text-sm text-red-500">
                        {errors.refresh_interval_seconds.message}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/admin/bi/dashboards')}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Save className="mr-2 h-4 w-4" />
                Create & Add Widgets
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
