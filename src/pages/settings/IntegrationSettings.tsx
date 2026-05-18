import {
  AlertCircle,
  ArrowRight,
  Building2,
  Check,
  CreditCard,
  Database,
  Eye,
  EyeOff,
  FileText,
  Loader2,
  RefreshCw,
  Save,
  Server,
  Shield,
  TestTube2,
  Trash2,
  Wallet,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
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
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { integrationsApi, organizationsApi } from '@/services/api';

import { logger } from "@/lib/logger";
import { getErrorMessage } from "@/lib/errorMessage";
interface IntegrationType {
  type: string;
  label: string;
  description: string;
  providers: { value: string; label: string }[];
}

interface IntegrationConfig {
  id: string;
  integration_type: string;
  provider: string;
  display_name: string | null;
  config_data: Record<string, unknown>;
  sandbox_mode: boolean;
  is_active: boolean;
  health_status: string;
  last_used_at: string | null;
  last_health_check: string | null;
  total_requests: number;
  failed_requests: number;
}

interface Organization {
  id: string;
  name: string;
  code: string;
}

const INTEGRATION_ICONS: Record<string, React.ReactNode> = {
  NACH: <Wallet className="h-5 w-5" />,
  ACCOUNT_AGGREGATOR: <Database className="h-5 w-5" />,
  GSTN: <FileText className="h-5 w-5" />,
  CREDIT_BUREAU: <Shield className="h-5 w-5" />,
  PAYMENT_GATEWAY: <CreditCard className="h-5 w-5" />,
};

const HEALTH_STATUS_STYLES: Record<string, string> = {
  HEALTHY: 'bg-emerald-100 text-emerald-700',
  DEGRADED: 'bg-amber-100 text-amber-700',
  DOWN: 'bg-red-100 text-red-700',
  UNKNOWN: 'bg-slate-100 text-slate-600',
};

export function IntegrationSettings() {
  const { toast } = useToast();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [integrationTypes, setIntegrationTypes] = useState<IntegrationType[]>([]);
  const [configs, setConfigs] = useState<IntegrationConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('NACH');

  // Form state
  const [formData, setFormData] = useState<Record<string, unknown>>({});
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [sandboxMode, setSandboxMode] = useState(true);
  const [showSecrets, setShowSecrets] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    fetchOrganizations();
    fetchIntegrationTypes();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchConfigs();
    }
  }, [selectedOrgId]);

  useEffect(() => {
    // Load existing config when tab changes
    const existingConfig = configs.find((c) => c.integration_type === activeTab);
    if (existingConfig) {
      setFormData(existingConfig.config_data || {});
      setSelectedProvider(existingConfig.provider);
      setSandboxMode(existingConfig.sandbox_mode);
    } else {
      setFormData({});
      setSelectedProvider('');
      setSandboxMode(true);
    }
  }, [activeTab, configs]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      setOrganizations(response.data.items);
      if (response.data.items.length > 0) {
        setSelectedOrgId(response.data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  };

  const fetchIntegrationTypes = async () => {
    try {
      const response = await integrationsApi.getTypes();
      setIntegrationTypes(response.data);
      if (response.data.length > 0) {
        setActiveTab(response.data[0].type);
      }
    } catch (error) {
      logger.error('Failed to fetch integration types:', error);
    }
  };

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const response = await integrationsApi.list({
        organization_id: selectedOrgId,
        page_size: 50,
      });
      setConfigs(response.data.items);
    } catch (error) {
      logger.error('Failed to fetch configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentTypeConfig = () => {
    return integrationTypes.find((t) => t.type === activeTab);
  };

  const getExistingConfig = () => {
    return configs.find((c) => c.integration_type === activeTab);
  };

  const handleSave = async () => {
    if (!selectedOrgId || !selectedProvider) {
      toast({
        title: 'Error',
        description: 'Please select a provider',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      const existingConfig = getExistingConfig();

      if (existingConfig) {
        // Update existing
        await integrationsApi.update(existingConfig.id, {
          config_data: formData,
          sandbox_mode: sandboxMode,
        });
        toast({
          title: 'Success',
          description: 'Integration configuration updated',
        });
      } else {
        // Create new
        await integrationsApi.create({
          organization_id: selectedOrgId,
          integration_type: activeTab,
          provider: selectedProvider,
          config_data: formData,
          sandbox_mode: sandboxMode,
        });
        toast({
          title: 'Success',
          description: 'Integration configuration created',
        });
      }

      await fetchConfigs();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        title: 'Error',
        description: getErrorMessage(err, 'Failed to save configuration'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    const existingConfig = getExistingConfig();
    if (!existingConfig) {
      toast({
        title: 'Error',
        description: 'Please save the configuration first',
        variant: 'destructive',
      });
      return;
    }

    try {
      setTesting(true);
      const response = await integrationsApi.test(existingConfig.id);
      const result = response.data;

      if (result.success) {
        toast({
          title: 'Connection Successful',
          description: result.message,
        });
      } else {
        toast({
          title: 'Connection Failed',
          description: result.message,
          variant: 'destructive',
        });
      }

      await fetchConfigs();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        title: 'Test Failed',
        description: getErrorMessage(err, 'Failed to test connection'),
        variant: 'destructive',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleDelete = async () => {
    const existingConfig = getExistingConfig();
    if (!existingConfig) return;

    if (!confirm('Are you sure you want to delete this integration configuration?')) {
      return;
    }

    try {
      await integrationsApi.delete(existingConfig.id);
      toast({
        title: 'Success',
        description: 'Integration configuration deleted',
      });
      await fetchConfigs();
      setFormData({});
      setSelectedProvider('');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        title: 'Error',
        description: getErrorMessage(err, 'Failed to delete configuration'),
        variant: 'destructive',
      });
    }
  };

  const renderConfigFields = () => {
    const currentType = getCurrentTypeConfig();
    if (!currentType) return null;

    // Define fields based on integration type
    const fieldConfigs: Record<string, { label: string; type: string; sensitive?: boolean; placeholder?: string }[]> = {
      NACH: [
        { label: 'Merchant ID', type: 'text', placeholder: 'Your merchant ID' },
        { label: 'API Key', type: 'text', sensitive: true, placeholder: 'API Key' },
        { label: 'API Secret', type: 'text', sensitive: true, placeholder: 'API Secret' },
        { label: 'Utility Code', type: 'text', placeholder: 'NPCI Utility Code' },
        { label: 'Sponsor Bank Code', type: 'text', placeholder: 'Sponsor bank IFSC' },
      ],
      ACCOUNT_AGGREGATOR: [
        { label: 'FIU ID', type: 'text', placeholder: 'Financial Information User ID' },
        { label: 'API Key', type: 'text', sensitive: true, placeholder: 'API Key' },
        { label: 'API Secret', type: 'text', sensitive: true, placeholder: 'API Secret' },
        { label: 'Client ID', type: 'text', placeholder: 'OAuth Client ID' },
        { label: 'Client Secret', type: 'text', sensitive: true, placeholder: 'OAuth Client Secret' },
      ],
      GSTN: [
        { label: 'GSTIN', type: 'text', placeholder: '15-digit GSTIN' },
        { label: 'Username', type: 'text', placeholder: 'Portal username' },
        { label: 'Password', type: 'text', sensitive: true, placeholder: 'Portal password' },
        { label: 'ASP ID', type: 'text', placeholder: 'ASP ID (for API access)' },
        { label: 'ASP Secret', type: 'text', sensitive: true, placeholder: 'ASP Secret' },
      ],
      CREDIT_BUREAU: [
        { label: 'Member ID', type: 'text', placeholder: 'Bureau member ID' },
        { label: 'Member Password', type: 'text', sensitive: true, placeholder: 'Bureau password' },
        { label: 'User ID', type: 'text', placeholder: 'API User ID' },
        { label: 'API Key', type: 'text', sensitive: true, placeholder: 'API Key' },
      ],
      PAYMENT_GATEWAY: [
        { label: 'Key ID', type: 'text', placeholder: 'Razorpay Key ID / Merchant ID' },
        { label: 'Key Secret', type: 'text', sensitive: true, placeholder: 'Key Secret / API Secret' },
        { label: 'Webhook Secret', type: 'text', sensitive: true, placeholder: 'Webhook verification secret' },
      ],
    };

    const fields = fieldConfigs[activeTab] || [];

    return (
      <div className="grid gap-4 md:grid-cols-2">
        {fields.map((field) => {
          const fieldKey = field.label.toLowerCase().replace(/\s+/g, '_');
          return (
            <div key={fieldKey} className="space-y-2">
              <Label htmlFor={fieldKey}>{field.label}</Label>
              <div className="relative">
                <Input
                  id={fieldKey}
                  type={field.sensitive && !showSecrets ? 'password' : 'text'}
                  placeholder={field.placeholder}
                  value={(formData[fieldKey] as string) || ''}
                  onChange={(e) => setFormData({ ...formData, [fieldKey]: e.target.value })}
                />
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const existingConfig = getExistingConfig();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Integration Settings"
        subtitle="Configure external service integrations for your organization"
        actions={
          <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
            <SelectTrigger className="w-64">
              <Building2 className="mr-2 h-4 w-4" />
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
        }
      />

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      ) : (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            {integrationTypes.map((type) => {
              const config = configs.find((c) => c.integration_type === type.type);
              return (
                <TabsTrigger
                  key={type.type}
                  value={type.type}
                  className="flex items-center gap-2"
                >
                  {INTEGRATION_ICONS[type.type]}
                  <span className="hidden md:inline">{type.label}</span>
                  {config && (
                    <Badge
                      variant="secondary"
                      className={`ml-1 ${HEALTH_STATUS_STYLES[config.health_status]}`}
                    >
                      {config.health_status === 'HEALTHY' ? (
                        <Check className="h-3 w-3" />
                      ) : (
                        <AlertCircle className="h-3 w-3" />
                      )}
                    </Badge>
                  )}
                </TabsTrigger>
              );
            })}
          </TabsList>

          {integrationTypes.map((type) => (
            <TabsContent key={type.type} value={type.type} className="space-y-4 mt-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {INTEGRATION_ICONS[type.type]}
                        {type.label}
                      </CardTitle>
                      <CardDescription>{type.description}</CardDescription>
                    </div>
                    {existingConfig && (
                      <div className="flex items-center gap-2">
                        <Badge className={HEALTH_STATUS_STYLES[existingConfig.health_status]}>
                          {existingConfig.health_status}
                        </Badge>
                        {existingConfig.last_health_check && (
                          <span className="text-xs text-slate-500">
                            Last checked:{' '}
                            {new Date(existingConfig.last_health_check).toLocaleString()}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Provider Selection */}
                  <div className="space-y-2">
                    <Label>Provider</Label>
                    <Select
                      value={selectedProvider}
                      onValueChange={setSelectedProvider}
                      disabled={!!existingConfig}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select a provider" />
                      </SelectTrigger>
                      <SelectContent>
                        {type.providers.map((provider) => (
                          <SelectItem key={provider.value} value={provider.value}>
                            {provider.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {existingConfig && (
                      <p className="text-xs text-slate-500">
                        Provider cannot be changed once configured. Delete and recreate to change.
                      </p>
                    )}
                  </div>

                  {/* Environment Toggle */}
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <Label>Sandbox Mode</Label>
                      <p className="text-sm text-slate-500">
                        Use test/sandbox environment for development
                      </p>
                    </div>
                    <Switch checked={sandboxMode} onCheckedChange={setSandboxMode} />
                  </div>

                  {/* Secret Toggle */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowSecrets(!showSecrets)}
                    >
                      {showSecrets ? (
                        <EyeOff className="mr-2 h-4 w-4" />
                      ) : (
                        <Eye className="mr-2 h-4 w-4" />
                      )}
                      {showSecrets ? 'Hide' : 'Show'} Secrets
                    </Button>
                  </div>

                  {/* Configuration Fields */}
                  {renderConfigFields()}

                  {/* Usage Statistics */}
                  {existingConfig && (
                    <Alert>
                      <Server className="h-4 w-4" />
                      <AlertDescription>
                        <span className="font-medium">Usage Statistics: </span>
                        {existingConfig.total_requests} total requests,{' '}
                        {existingConfig.failed_requests} failed
                        {existingConfig.last_used_at && (
                          <>
                            {' '}
                            | Last used:{' '}
                            {new Date(existingConfig.last_used_at).toLocaleString()}
                          </>
                        )}
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between border-t pt-4">
                    <div className="flex items-center gap-2">
                      {existingConfig && (
                        <Button variant="destructive" size="sm" onClick={handleDelete}>
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </Button>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        onClick={handleTest}
                        disabled={!existingConfig || testing}
                      >
                        {testing ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <TestTube2 className="mr-2 h-4 w-4" />
                        )}
                        Test Connection
                      </Button>
                      <Button onClick={handleSave} disabled={!selectedProvider || saving}>
                        {saving ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Save className="mr-2 h-4 w-4" />
                        )}
                        {existingConfig ? 'Update' : 'Save'} Configuration
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>
      )}
    </div>
  );
}
