/**
 * Data Source Edit Page
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ArrowLeft, Loader2, Save, Eye } from 'lucide-react';
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { useToast } from '@/hooks/use-toast';
import { biDataSourceApi } from '@/services/biApi';
import { DataSource, DataSourceType, APIMethod } from '@/types/bi';

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

const SOURCE_TYPES: { value: DataSourceType; label: string }[] = [
  { value: 'API_ENDPOINT', label: 'API Endpoint' },
  { value: 'SQL_QUERY', label: 'SQL Query' },
  { value: 'STATIC', label: 'Static Data' },
];

const API_METHODS: APIMethod[] = ['GET', 'POST'];

export function DataSourceEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [dataSource, setDataSource] = useState<DataSource | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Preview drawer state
  const [previewDrawerOpen, setPreviewDrawerOpen] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

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

  const fetchDataSource = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const response = await biDataSourceApi.get(id);
      setDataSource(response.data);

      // Set form values
      const ds = response.data;
      setValue('code', ds.code);
      setValue('name', ds.name);
      setValue('description', ds.description || '');
      setValue('source_type', ds.source_type);
      setValue('api_endpoint', ds.api_endpoint || '');
      setValue('api_method', ds.api_method || 'GET');
      setValue('query_template', ds.query_template || '');
      setValue('static_data', JSON.stringify(ds.static_data || [], null, 2));
      setValue('parameters_schema', JSON.stringify(ds.parameters_schema || {}, null, 2));
      setValue('response_transform', JSON.stringify(ds.response_transform || {}, null, 2));
      setValue('cache_ttl_seconds', ds.cache_ttl_seconds || 0);
    } catch (error) {
      console.error('Error fetching data source:', error);
      toast({
        title: 'Error',
        description: 'Failed to load data source',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDataSource();
  }, [id]);

  const onSubmit = async (data: FormData) => {
    if (!id) return;

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

      await biDataSourceApi.update(id, {
        code: data.code,
        name: data.name,
        description: data.description || undefined,
        source_type: data.source_type,
        api_endpoint: data.source_type === 'API_ENDPOINT' ? data.api_endpoint : undefined,
        api_method: data.source_type === 'API_ENDPOINT' ? data.api_method : undefined,
        query_template: data.source_type === 'SQL_QUERY' ? data.query_template : undefined,
        static_data: staticData,
        parameters_schema: parametersSchema,
        response_transform: responseTransform,
        cache_ttl_seconds: data.cache_ttl_seconds > 0 ? data.cache_ttl_seconds : undefined,
      });

      toast({
        title: 'Success',
        description: 'Data source updated successfully',
      });

      navigate('/admin/bi/data-sources');
    } catch (error: any) {
      console.error('Error updating data source:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update data source',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handlePreview = async () => {
    if (!id) return;

    setPreviewDrawerOpen(true);
    setPreviewLoading(true);

    try {
      const response = await biDataSourceApi.preview(id);
      setPreviewData(response.data);
    } catch (error) {
      console.error('Error fetching preview:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch data preview',
        variant: 'destructive',
      });
      setPreviewData(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!dataSource) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Data source not found</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate('/admin/bi/data-sources')}
        >
          Back to Data Sources
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/admin/bi/data-sources')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Edit Data Source</h1>
            <p className="text-muted-foreground">{dataSource.code}</p>
          </div>
        </div>
        <Button variant="outline" onClick={handlePreview}>
          <Eye className="h-4 w-4 mr-2" />
          Preview Data
        </Button>
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
                        {t.label}
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
                </div>
              )}

              {sourceType === 'STATIC' && (
                <div className="space-y-2">
                  <Label>Static Data (JSON) *</Label>
                  <Textarea
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
                  rows={6}
                  className="font-mono text-sm"
                  {...register('parameters_schema')}
                />
              </div>

              <div className="space-y-2">
                <Label>Response Transform (JSON)</Label>
                <Textarea
                  rows={6}
                  className="font-mono text-sm"
                  {...register('response_transform')}
                />
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
            Save Changes
          </Button>
        </div>
      </form>

      {/* Preview Drawer */}
      <Sheet open={previewDrawerOpen} onOpenChange={setPreviewDrawerOpen}>
        <SheetContent className="sm:max-w-xl">
          <SheetHeader>
            <SheetTitle>Data Preview</SheetTitle>
            <SheetDescription>
              Preview data from this data source
            </SheetDescription>
          </SheetHeader>

          <div className="py-6">
            {previewLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : previewData ? (
              <div className="space-y-4">
                {previewData.data && Array.isArray(previewData.data) ? (
                  <div className="max-h-96 overflow-auto">
                    <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto">
                      {JSON.stringify(previewData.data.slice(0, 10), null, 2)}
                    </pre>
                    {previewData.data.length > 10 && (
                      <p className="text-sm text-muted-foreground mt-2">
                        Showing first 10 of {previewData.data.length} records
                      </p>
                    )}
                  </div>
                ) : (
                  <pre className="text-xs bg-muted p-4 rounded-lg overflow-x-auto max-h-96">
                    {JSON.stringify(previewData, null, 2)}
                  </pre>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No data available or error fetching data
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
