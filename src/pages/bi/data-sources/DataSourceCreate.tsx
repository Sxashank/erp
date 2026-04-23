/**
 * Data Source Create Page
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { biDataSourceApi } from '@/services/biApi';
import { DataSourceCreate as DataSourceCreateType, DataSourceType, APIMethod } from '@/types/bi';

interface FormData {
  code: string;
  name: string;
  description: string;
  source_type: DataSourceType;
  api_endpoint: string;
  api_method: APIMethod;
  query_template: string;
  static_data: string;
  parameters_schema: string;
  response_transform: string;
  cache_ttl_seconds: number;
}

const SOURCE_TYPES: { value: DataSourceType; label: string; description: string }[] = [
  { value: 'API_ENDPOINT', label: 'API Endpoint', description: 'Fetch data from a REST API' },
  { value: 'SQL_QUERY', label: 'SQL Query', description: 'Execute a database query' },
  { value: 'STATIC', label: 'Static Data', description: 'Use hardcoded JSON data' },
];

const API_METHODS: APIMethod[] = ['GET', 'POST'];

export function DataSourceCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);

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
      source_type: 'API_ENDPOINT',
      api_endpoint: '',
      api_method: 'GET',
      query_template: '',
      static_data: '[]',
      parameters_schema: '{}',
      response_transform: '{}',
      cache_ttl_seconds: 300,
    },
  });

  const sourceType = watch('source_type');

  const onSubmit = async (data: FormData) => {
    try {
      setSubmitting(true);

      let staticData = null;
      let parametersSchema = {};
      let responseTransform = {};

      if (data.source_type === 'STATIC') {
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
        description: data.description || undefined,
        organization_id: organizationId || undefined,
        source_type: data.source_type,
        api_endpoint: data.source_type === 'API_ENDPOINT' ? data.api_endpoint : undefined,
        api_method: data.source_type === 'API_ENDPOINT' ? data.api_method : undefined,
        query_template: data.source_type === 'SQL_QUERY' ? data.query_template : undefined,
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
    } catch (error: any) {
      console.error('Error creating data source:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create data source',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/admin/bi/data-sources')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Create Data Source</h1>
          <p className="text-muted-foreground">
            Configure a new data source for BI widgets
          </p>
        </div>
      </div>

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
                  {errors.code && (
                    <p className="text-sm text-red-500">{errors.code.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    placeholder="Revenue MTD Data"
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
                  placeholder="Fetches month-to-date revenue data"
                  rows={2}
                  {...register('description')}
                />
              </div>

              <div className="space-y-2">
                <Label>Source Type *</Label>
                <Select
                  value={sourceType}
                  onValueChange={(value) => setValue('source_type', value as DataSourceType)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SOURCE_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        <div>
                          <span className="font-medium">{t.label}</span>
                          <span className="text-muted-foreground ml-2 text-sm">
                            - {t.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
              <CardTitle>
                {sourceType === 'API_ENDPOINT' && 'API Configuration'}
                {sourceType === 'SQL_QUERY' && 'SQL Configuration'}
                {sourceType === 'STATIC' && 'Static Data Configuration'}
              </CardTitle>
              <CardDescription>
                {sourceType === 'API_ENDPOINT' && 'Configure the API endpoint to fetch data from'}
                {sourceType === 'SQL_QUERY' && 'Configure the SQL query to execute'}
                {sourceType === 'STATIC' && 'Enter the static JSON data'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {sourceType === 'API_ENDPOINT' && (
                <>
                  <div className="space-y-2">
                    <Label>API Endpoint *</Label>
                    <Input
                      placeholder="/api/v1/reports/revenue"
                      {...register('api_endpoint', {
                        required: sourceType === 'API_ENDPOINT' ? 'API endpoint is required' : false,
                      })}
                    />
                    {errors.api_endpoint && (
                      <p className="text-sm text-red-500">{errors.api_endpoint.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>API Method</Label>
                    <Select
                      value={watch('api_method')}
                      onValueChange={(value) => setValue('api_method', value as APIMethod)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {API_METHODS.map((m) => (
                          <SelectItem key={m} value={m}>
                            {m}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              {sourceType === 'SQL_QUERY' && (
                <div className="space-y-2">
                  <Label>SQL Query *</Label>
                  <Textarea
                    placeholder="SELECT * FROM revenue WHERE month = :month"
                    rows={8}
                    className="font-mono text-sm"
                    {...register('query_template', {
                      required: sourceType === 'SQL_QUERY' ? 'SQL query is required' : false,
                    })}
                  />
                  {errors.query_template && (
                    <p className="text-sm text-red-500">{errors.query_template.message}</p>
                  )}
                  <p className="text-sm text-muted-foreground">
                    Use :paramName for query parameters
                  </p>
                </div>
              )}

              {sourceType === 'STATIC' && (
                <div className="space-y-2">
                  <Label>Static Data (JSON) *</Label>
                  <Textarea
                    placeholder='[{"name": "Item 1", "value": 100}]'
                    rows={10}
                    className="font-mono text-sm"
                    {...register('static_data', {
                      required: sourceType === 'STATIC' ? 'Static data is required' : false,
                    })}
                  />
                  {errors.static_data && (
                    <p className="text-sm text-red-500">{errors.static_data.message}</p>
                  )}
                </div>
              )}
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

        <div className="flex justify-end gap-4 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/bi/data-sources')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting}>
            {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            <Save className="h-4 w-4 mr-2" />
            Create Data Source
          </Button>
        </div>
      </form>
    </div>
  );
}
