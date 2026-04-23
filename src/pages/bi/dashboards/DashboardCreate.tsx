/**
 * Dashboard Create Page
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import { biDashboardApi } from '@/services/biApi';
import { DashboardCreate as DashboardCreateType } from '@/types/bi';

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
    } catch (error: any) {
      console.error('Error creating dashboard:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create dashboard',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/bi/dashboards')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Create Dashboard</h1>
          <p className="text-muted-foreground">
            Create a new BI dashboard
          </p>
        </div>
      </div>

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
                {errors.code && (
                  <p className="text-sm text-red-500">{errors.code.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="Sales Dashboard"
                  {...register('name', { required: 'Name is required' })}
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
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
              <h3 className="font-medium mb-4">Auto Refresh Settings</h3>
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
                      <p className="text-sm text-red-500">{errors.refresh_interval_seconds.message}</p>
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
                {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                <Save className="h-4 w-4 mr-2" />
                Create & Add Widgets
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
}
