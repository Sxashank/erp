/**
 * Data Source Create Page
 */

import { Loader2, Save } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { biDataSourceApi } from '@/services/biApi';
import { logger } from '@/lib/logger';
import type { DataSourceCreate as DataSourceCreateType, DataSourceType } from '@/types/bi';
import { getErrorMessage } from '@/lib/errorMessage';

interface FormData {
  code: string;
  name: string;
  description: string;
  source_type: DataSourceType;
  static_data: string;
  parameters_schema: string;
  response_transform: string;
  cache_ttl_seconds: number;
}

const SOURCE_TYPE: DataSourceType = 'STATIC';

export function DataSourceCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    defaultValues: {
      code: '',
      name: '',
      description: '',
      source_type: SOURCE_TYPE,
      static_data: '[]',
      parameters_schema: '{}',
      response_transform: '{}',
      cache_ttl_seconds: 300,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSubmitting(true);

      let staticData = null;
      let parametersSchema = {};
      let responseTransform = {};

      try {
        staticData = JSON.parse(data.static_data);
      } catch {
        toast({
          title: 'Error',
          description: 'Invalid JSON in static data field',
          variant: 'destructive',
        });
        return;
      }

      try {
        parametersSchema = JSON.parse(data.parameters_schema);
      } catch {
        toast({
          title: 'Error',
          description: 'Invalid JSON in parameters schema field',
          variant: 'destructive',
        });
        return;
      }

      try {
        responseTransform = JSON.parse(data.response_transform);
      } catch {
        toast({
          title: 'Error',
          description: 'Invalid JSON in response transform field',
          variant: 'destructive',
        });
        return;
      }

      const payload: DataSourceCreateType = {
        code: data.code,
        name: data.name,
        description: data.description || undefined || undefined,
        source_type: SOURCE_TYPE,
        static_data: staticData,
        parameters_schema: parametersSchema,
        response_transform: responseTransform,
        cache_ttl_seconds: data.cache_ttl_seconds > 0 ? data.cache_ttl_seconds : undefined,
      };

      await biDataSourceApi.create(payload);

      toast({
        title: 'Success',
        description: 'Data source created successfully',
      });

      navigate('/admin/bi/data-sources');
    } catch (error: unknown) {
      logger.error('Error creating data source:', error);
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to create data source'),
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Data Source"
        subtitle="Configure a manual-first static BI data source for widgets"
        breadcrumbs={[{ label: 'Data Sources', to: '/admin/bi/data-sources' }, { label: 'New' }]}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="code">Code *</Label>
                  <Input
                    id="code"
                    placeholder="DS_REVENUE_MTD"
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
                    placeholder="Revenue MTD Data"
                    {...register('name', { required: 'Name is required' })}
                  />
                  {errors.name && <p className="text-sm text-red-500">{errors.name.message}</p>}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Fetches month-to-date revenue data"
                  rows={2}
                  {...register('description')}
                />
              </div>

              <div className="space-y-2">
                <Label>Supported Source Type</Label>
                <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm">
                  <div className="font-medium">Static Data</div>
                  <p className="text-muted-foreground">
                    This release supports manual-first static JSON data sources only. API endpoint
                    and SQL-query execution are intentionally disabled until their runtime contracts
                    are implemented end to end.
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="cache_ttl_seconds">Cache TTL (seconds)</Label>
                <Input
                  id="cache_ttl_seconds"
                  type="number"
                  min={0}
                  {...register('cache_ttl_seconds', { valueAsNumber: true })}
                />
                <p className="text-sm text-muted-foreground">
                  How long to cache the data (0 = no cache)
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Static Data Configuration</CardTitle>
              <CardDescription>
                Enter the JSON payload that BI widgets should render.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Static Data (JSON) *</Label>
                <Textarea
                  placeholder='[{"name": "Item 1", "value": 100}]'
                  rows={10}
                  className="font-mono text-sm"
                  {...register('static_data', {
                    required: 'Static data is required',
                  })}
                />
                {errors.static_data && (
                  <p className="text-sm text-red-500">{errors.static_data.message}</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Advanced Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>Parameters Schema (JSON)</Label>
                <Textarea
                  placeholder='{"month": {"type": "string", "required": true}}'
                  rows={6}
                  className="font-mono text-sm"
                  {...register('parameters_schema')}
                />
                <p className="text-sm text-muted-foreground">
                  Define the parameters accepted by this data source
                </p>
              </div>

              <div className="space-y-2">
                <Label>Response Transform (JSON)</Label>
                <Textarea
                  placeholder='{"dataPath": "data.items", "valueField": "amount"}'
                  rows={6}
                  className="font-mono text-sm"
                  {...register('response_transform')}
                />
                <p className="text-sm text-muted-foreground">
                  Transform the response data before using
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/bi/data-sources')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            Create Data Source
          </Button>
        </div>
      </form>
    </div>
  );
}
