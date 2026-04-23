/**
 * Account Aggregator Request Consent Page
 *
 * Full page form to initiate a new AA consent request.
 * Supports multiple AA providers and FI types.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format, addMonths, addYears } from 'date-fns';
import {
  ArrowLeft,
  Shield,
  Building2,
  Calendar,
  Database,
  User,
  Loader2,
  ExternalLink,
  Copy,
  CheckCircle,
  Info,
} from 'lucide-react';

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
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

// Types
interface Entity {
  entity_id: string;
  name: string;
  pan_number: string;
}

interface ProviderConfig {
  name: string;
  code: string;
  sandbox_available: boolean;
  fi_types_supported: string[];
}

// Available FI Types
const FI_TYPES = [
  { code: 'DEPOSIT', label: 'Savings/Current Account', description: 'Bank account statements' },
  { code: 'TERM_DEPOSIT', label: 'Fixed Deposit', description: 'FD account details' },
  { code: 'RECURRING_DEPOSIT', label: 'Recurring Deposit', description: 'RD account details' },
  { code: 'MUTUAL_FUNDS', label: 'Mutual Funds', description: 'MF holdings and transactions' },
  { code: 'ETF', label: 'ETF', description: 'Exchange traded funds' },
  { code: 'BONDS', label: 'Bonds', description: 'Bond holdings' },
  { code: 'DEBENTURES', label: 'Debentures', description: 'Debenture holdings' },
  { code: 'EQUITIES', label: 'Equities', description: 'Stock holdings from demat' },
  { code: 'INSURANCE_POLICIES', label: 'Insurance', description: 'Insurance policy details' },
  { code: 'NPS', label: 'NPS', description: 'National Pension System' },
  { code: 'PPF', label: 'PPF', description: 'Public Provident Fund' },
  { code: 'GST_GSTR1', label: 'GST Returns', description: 'GST filing data' },
];

// Consent Purposes
const CONSENT_PURPOSES = [
  { code: 'BANK_STATEMENT', label: 'Bank Statement Verification', description: 'For loan underwriting' },
  { code: 'UNDERWRITING', label: 'Loan Underwriting', description: 'Credit assessment' },
  { code: 'WEALTH_MANAGEMENT', label: 'Wealth Management', description: 'Financial advisory' },
  { code: 'ACCOUNT_AGGREGATION', label: 'Account Aggregation', description: 'Consolidated view' },
];

// Frequency Types
const FREQUENCY_TYPES = [
  { code: 'ONETIME', label: 'One Time', description: 'Single data fetch' },
  { code: 'HOURLY', label: 'Hourly', description: 'Fetch data every hour' },
  { code: 'DAILY', label: 'Daily', description: 'Fetch data daily' },
  { code: 'WEEKLY', label: 'Weekly', description: 'Fetch data weekly' },
  { code: 'MONTHLY', label: 'Monthly', description: 'Fetch data monthly' },
  { code: 'YEARLY', label: 'Yearly', description: 'Fetch data yearly' },
];

export default function RequestConsentPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  // Form state
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [consentCreated, setConsentCreated] = useState<{
    consent_handle: string;
    redirect_url: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  // Entities for selection
  const [entities, setEntities] = useState<Entity[]>([]);
  const [providers, setProviders] = useState<ProviderConfig[]>([]);

  // Form fields
  const [formData, setFormData] = useState({
    organization_id: searchParams.get('organization_id') || '',
    entity_id: searchParams.get('entity_id') || '',
    customer_id: '', // VUA (Virtual User Address)
    provider: 'FINVU',
    purpose: 'BANK_STATEMENT',
    fi_types: ['DEPOSIT'] as string[],
    consent_mode: 'VIEW',
    fetch_type: 'ONETIME',
    frequency_type: 'ONETIME',
    frequency_value: 1,
    date_range_from: format(addMonths(new Date(), -12), 'yyyy-MM-dd'),
    date_range_to: format(new Date(), 'yyyy-MM-dd'),
    consent_expiry: format(addYears(new Date(), 1), 'yyyy-MM-dd'),
  });

  // Fetch entities and providers
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch entities
        const entitiesResponse = await fetch('/api/v1/lending/entities?page_size=100');
        if (entitiesResponse.ok) {
          const data = await entitiesResponse.json();
          setEntities(data.items || []);
        }

        // Fetch supported providers
        const providersResponse = await fetch('/api/v1/lending/aa/providers');
        if (providersResponse.ok) {
          const data = await providersResponse.json();
          setProviders(data.providers || [
            { name: 'Finvu', code: 'FINVU', sandbox_available: true, fi_types_supported: FI_TYPES.map(f => f.code) },
            { name: 'OneMoney', code: 'ONEMONEY', sandbox_available: true, fi_types_supported: FI_TYPES.map(f => f.code) },
            { name: 'Setu', code: 'SETU', sandbox_available: true, fi_types_supported: FI_TYPES.map(f => f.code) },
          ]);
        }
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle FI type toggle
  const handleFiTypeToggle = (fiType: string) => {
    setFormData(prev => ({
      ...prev,
      fi_types: prev.fi_types.includes(fiType)
        ? prev.fi_types.filter(t => t !== fiType)
        : [...prev.fi_types, fiType],
    }));
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.customer_id) {
      toast({
        title: 'Customer ID required',
        description: 'Please enter the customer VUA (Virtual User Address).',
        variant: 'destructive',
      });
      return;
    }

    if (formData.fi_types.length === 0) {
      toast({
        title: 'FI Types required',
        description: 'Please select at least one financial information type.',
        variant: 'destructive',
      });
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch('/api/v1/lending/aa/consents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          entity_id: formData.entity_id || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create consent request');
      }

      const data = await response.json();

      setConsentCreated({
        consent_handle: data.consent_handle,
        redirect_url: data.redirect_url,
      });

      toast({
        title: 'Consent request created',
        description: 'Share the consent URL with the customer for approval.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create consent request.',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Copy URL to clipboard
  const handleCopyUrl = async () => {
    if (consentCreated?.redirect_url) {
      await navigator.clipboard.writeText(consentCreated.redirect_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast({
        title: 'Copied',
        description: 'Consent URL copied to clipboard.',
      });
    }
  };

  // Success view after consent creation
  if (consentCreated) {
    return (
      <div className="container mx-auto py-6 max-w-2xl">
        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <CardTitle>Consent Request Created</CardTitle>
            <CardDescription>
              Share this link with the customer to approve the consent
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label className="text-sm text-muted-foreground">Consent Handle</Label>
              <p className="font-mono text-sm mt-1">{consentCreated.consent_handle}</p>
            </div>

            <div>
              <Label className="text-sm text-muted-foreground">Consent URL</Label>
              <div className="flex items-center gap-2 mt-2">
                <Input
                  value={consentCreated.redirect_url}
                  readOnly
                  className="font-mono text-xs"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleCopyUrl}
                >
                  {copied ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  asChild
                >
                  <a
                    href={consentCreated.redirect_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </Button>
              </div>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertTitle>Next Steps</AlertTitle>
              <AlertDescription>
                <ol className="list-decimal list-inside mt-2 space-y-1 text-sm">
                  <li>Share the consent URL with the customer</li>
                  <li>Customer approves consent via their AA app</li>
                  <li>Consent status updates automatically via webhook</li>
                  <li>Once approved, you can fetch financial data</li>
                </ol>
              </AlertDescription>
            </Alert>

            <div className="flex gap-4">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setConsentCreated(null)}
              >
                Create Another
              </Button>
              <Button
                className="flex-1"
                onClick={() => navigate('/lending/aa/consents')}
              >
                View All Consents
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/lending/aa/consents')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Request Consent</h1>
          <p className="text-sm text-muted-foreground">
            Create a new Account Aggregator consent request
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Customer Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Customer Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="customer_id">Customer VUA *</Label>
                    <Input
                      id="customer_id"
                      placeholder="customer@aa-provider"
                      value={formData.customer_id}
                      onChange={(e) => setFormData(prev => ({ ...prev, customer_id: e.target.value }))}
                      required
                    />
                    <p className="text-xs text-muted-foreground">
                      Virtual User Address (e.g., customer@finvu)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="entity_id">Link to Entity (Optional)</Label>
                    <Select
                      value={formData.entity_id}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, entity_id: value }))}
                    >
                      <SelectTrigger id="entity_id">
                        <SelectValue placeholder="Select entity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">None</SelectItem>
                        {entities.map((entity) => (
                          <SelectItem key={entity.entity_id} value={entity.entity_id}>
                            {entity.name} ({entity.pan_number})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Provider & Purpose */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Provider & Purpose
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="provider">AA Provider *</Label>
                    <Select
                      value={formData.provider}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, provider: value }))}
                    >
                      <SelectTrigger id="provider">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FINVU">Finvu</SelectItem>
                        <SelectItem value="ONEMONEY">OneMoney</SelectItem>
                        <SelectItem value="SETU">Setu</SelectItem>
                        <SelectItem value="NADL">NADL</SelectItem>
                        <SelectItem value="CAMS_FINSERV">CAMS Finserv</SelectItem>
                        <SelectItem value="PERFIOS">Perfios</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="purpose">Purpose *</Label>
                    <Select
                      value={formData.purpose}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, purpose: value }))}
                    >
                      <SelectTrigger id="purpose">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CONSENT_PURPOSES.map((purpose) => (
                          <SelectItem key={purpose.code} value={purpose.code}>
                            {purpose.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* FI Types */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Financial Information Types
                </CardTitle>
                <CardDescription>
                  Select the types of financial data to request
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {FI_TYPES.map((fiType) => (
                    <div
                      key={fiType.code}
                      className={`flex items-start space-x-3 p-3 border rounded-lg cursor-pointer hover:bg-muted/50 ${
                        formData.fi_types.includes(fiType.code) ? 'border-primary bg-primary/5' : ''
                      }`}
                      onClick={() => handleFiTypeToggle(fiType.code)}
                    >
                      <Checkbox
                        id={fiType.code}
                        checked={formData.fi_types.includes(fiType.code)}
                        onCheckedChange={() => handleFiTypeToggle(fiType.code)}
                      />
                      <div className="space-y-1">
                        <Label
                          htmlFor={fiType.code}
                          className="text-sm font-medium cursor-pointer"
                        >
                          {fiType.label}
                        </Label>
                        <p className="text-xs text-muted-foreground">
                          {fiType.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Date Range & Frequency */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Date Range & Frequency
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="date_range_from">Data From *</Label>
                    <Input
                      id="date_range_from"
                      type="date"
                      value={formData.date_range_from}
                      onChange={(e) => setFormData(prev => ({ ...prev, date_range_from: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="date_range_to">Data To *</Label>
                    <Input
                      id="date_range_to"
                      type="date"
                      value={formData.date_range_to}
                      onChange={(e) => setFormData(prev => ({ ...prev, date_range_to: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="consent_expiry">Consent Expiry *</Label>
                    <Input
                      id="consent_expiry"
                      type="date"
                      value={formData.consent_expiry}
                      onChange={(e) => setFormData(prev => ({ ...prev, consent_expiry: e.target.value }))}
                      required
                    />
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <Label>Fetch Frequency</Label>
                  <RadioGroup
                    value={formData.frequency_type}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      frequency_type: value,
                      fetch_type: value === 'ONETIME' ? 'ONETIME' : 'PERIODIC',
                    }))}
                    className="grid grid-cols-2 md:grid-cols-3 gap-3"
                  >
                    {FREQUENCY_TYPES.map((freq) => (
                      <div key={freq.code} className="flex items-center space-x-2">
                        <RadioGroupItem value={freq.code} id={freq.code} />
                        <Label htmlFor={freq.code} className="cursor-pointer">
                          {freq.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </div>

                {formData.frequency_type !== 'ONETIME' && (
                  <div className="space-y-2">
                    <Label htmlFor="frequency_value">Number of Fetches</Label>
                    <Input
                      id="frequency_value"
                      type="number"
                      min={1}
                      max={100}
                      value={formData.frequency_value}
                      onChange={(e) => setFormData(prev => ({ ...prev, frequency_value: parseInt(e.target.value) || 1 }))}
                    />
                    <p className="text-xs text-muted-foreground">
                      Maximum number of data fetches allowed
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Summary Sidebar */}
          <div className="space-y-6">
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle className="text-lg">Request Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">Provider</p>
                  <p className="font-medium">{formData.provider}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Purpose</p>
                  <p className="font-medium">
                    {CONSENT_PURPOSES.find(p => p.code === formData.purpose)?.label}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">FI Types Selected</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {formData.fi_types.length === 0 ? (
                      <span className="text-sm text-muted-foreground">None selected</span>
                    ) : (
                      formData.fi_types.map((type) => (
                        <Badge key={type} variant="secondary" className="text-xs">
                          {FI_TYPES.find(f => f.code === type)?.label || type}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Date Range</p>
                  <p className="text-sm">
                    {format(new Date(formData.date_range_from), 'dd MMM yyyy')} -{' '}
                    {format(new Date(formData.date_range_to), 'dd MMM yyyy')}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Frequency</p>
                  <p className="text-sm">
                    {formData.frequency_type}
                    {formData.frequency_type !== 'ONETIME' && ` (${formData.frequency_value}x)`}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Valid Until</p>
                  <p className="text-sm">
                    {format(new Date(formData.consent_expiry), 'dd MMM yyyy')}
                  </p>
                </div>

                <Separator />

                <Button
                  type="submit"
                  className="w-full"
                  disabled={submitting || formData.fi_types.length === 0 || !formData.customer_id}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Shield className="h-4 w-4 mr-2" />
                      Create Consent Request
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}
