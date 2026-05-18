/**
 * Account Aggregator Request Consent Page
 *
 * Full page form to initiate a new AA consent request.
 * Supports multiple AA providers and FI types.
 */

import { format, addMonths, addYears } from 'date-fns';
import {
  Shield,
  Calendar,
  Database,
  User,
  Loader2,
  ExternalLink,
  Copy,
  CheckCircle,
  Info,
} from 'lucide-react';
import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useCreateAAConsent } from '@/hooks/lending/useAAConsent';
import { useAAProviders } from '@/hooks/lending/useAAProviders';
import { useEntities } from '@/hooks/lending/useEntities';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';

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
  {
    code: 'BANK_STATEMENT',
    label: 'Bank Statement Verification',
    description: 'For loan underwriting',
  },
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

  const entitiesQuery = useEntities({ pageSize: 100 });
  const providersQuery = useAAProviders();
  const createConsent = useCreateAAConsent();

  const [consentCreated, setConsentCreated] = useState<{
    consentHandle: string;
    redirectUrl: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const entities = entitiesQuery.data?.items ?? [];

  // Form fields
  const [formData, setFormData] = useState({
    organizationId: searchParams.get('organization_id') || '',
    entityId: searchParams.get('entity_id') || '',
    customerId: '', // VUA (Virtual User Address)
    provider: 'FINVU',
    purpose: 'BANK_STATEMENT',
    fiTypes: ['DEPOSIT'] as string[],
    consentMode: 'VIEW',
    fetchType: 'ONETIME',
    frequencyType: 'ONETIME',
    frequencyValue: 1,
    dateRangeFrom: format(addMonths(new Date(), -12), 'yyyy-MM-dd'),
    dateRangeTo: format(new Date(), 'yyyy-MM-dd'),
    consentExpiry: format(addYears(new Date(), 1), 'yyyy-MM-dd'),
  });

  // Handle FI type toggle
  const handleFiTypeToggle = (fiType: string) => {
    setFormData((prev) => ({
      ...prev,
      fiTypes: prev.fiTypes.includes(fiType)
        ? prev.fiTypes.filter((t) => t !== fiType)
        : [...prev.fiTypes, fiType],
    }));
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.customerId) {
      toast({
        title: 'Customer ID required',
        description: 'Please enter the customer VUA (Virtual User Address).',
        variant: 'destructive',
      });
      return;
    }

    if (formData.fiTypes.length === 0) {
      toast({
        title: 'FI Types required',
        description: 'Please select at least one financial information type.',
        variant: 'destructive',
      });
      return;
    }

    createConsent.mutate(
      {
        ...formData,
        entityId: formData.entityId || null,
      },
      {
        onSuccess: (data) => {
          setConsentCreated({
            consentHandle: data.consentHandle,
            redirectUrl: data.redirectUrl,
          });
          toast({
            title: 'Consent request created',
            description: 'Share the consent URL with the customer for approval.',
          });
        },
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  const submitting = createConsent.isPending;
  // `providersQuery` is consulted to mirror the original behaviour of loading
  // provider metadata at mount; the static <Select> below offers the supported
  // codes. We keep the query subscription so future copies of this page can
  // narrow the dropdown to the live list.
  void providersQuery.data;

  // Copy URL to clipboard
  const handleCopyUrl = async () => {
    if (consentCreated?.redirectUrl) {
      await navigator.clipboard.writeText(consentCreated.redirectUrl);
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
      <div className="container mx-auto max-w-2xl py-6">
        <Card>
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
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
              <p className="mt-1 font-mono text-sm">{consentCreated.consentHandle}</p>
            </div>

            <div>
              <Label className="text-sm text-muted-foreground">Consent URL</Label>
              <div className="mt-2 flex items-center gap-2">
                <Input value={consentCreated.redirectUrl} readOnly className="font-mono text-xs" />
                <Button variant="outline" size="icon" onClick={handleCopyUrl}>
                  {copied ? (
                    <CheckCircle className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
                <Button variant="outline" size="icon" asChild>
                  <a href={consentCreated.redirectUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </Button>
              </div>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertTitle>Next Steps</AlertTitle>
              <AlertDescription>
                <ol className="mt-2 list-inside list-decimal space-y-1 text-sm">
                  <li>Share the consent URL with the customer</li>
                  <li>Customer approves consent via their AA app</li>
                  <li>Consent status updates automatically via webhook</li>
                  <li>Once approved, you can fetch financial data</li>
                </ol>
              </AlertDescription>
            </Alert>

            <div className="flex gap-4">
              <Button variant="outline" className="flex-1" onClick={() => setConsentCreated(null)}>
                Create Another
              </Button>
              <Button className="flex-1" onClick={() => navigate('/admin/lending/aa/consents')}>
                View All Consents
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Request Consent"
        subtitle="Create a new Account Aggregator consent request"
        breadcrumbs={[
          { label: 'AA Consents', to: '/admin/lending/aa/consents' },
          { label: 'Request' },
        ]}
      />

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="space-y-6 lg:col-span-2">
            {/* Customer Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <User className="h-5 w-5" />
                  Customer Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="customer_id">Customer VUA *</Label>
                    <Input
                      id="customer_id"
                      placeholder="customer@aa-provider"
                      value={formData.customerId}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, customerId: e.target.value }))
                      }
                      required
                    />
                    <p className="text-xs text-muted-foreground">
                      Virtual User Address (e.g., customer@finvu)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="entity_id">Link to Entity (Optional)</Label>
                    <Select
                      value={formData.entityId || '__none__'}
                      onValueChange={(value) =>
                        setFormData((prev) => ({
                          ...prev,
                          entityId: value === '__none__' ? '' : value,
                        }))
                      }
                    >
                      <SelectTrigger id="entity_id">
                        <SelectValue placeholder="Select entity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {entities.map((entity) => (
                          <SelectItem key={entity.id} value={entity.id}>
                            {entity.legalName} ({entity.pan})
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
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Shield className="h-5 w-5" />
                  Provider & Purpose
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="provider">AA Provider *</Label>
                    <Select
                      value={formData.provider}
                      onValueChange={(value) =>
                        setFormData((prev) => ({ ...prev, provider: value }))
                      }
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
                      onValueChange={(value) =>
                        setFormData((prev) => ({ ...prev, purpose: value }))
                      }
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
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Database className="h-5 w-5" />
                  Financial Information Types
                </CardTitle>
                <CardDescription>Select the types of financial data to request</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {FI_TYPES.map((fiType) => (
                    <div
                      key={fiType.code}
                      className={`flex cursor-pointer items-start space-x-3 rounded-lg border p-3 hover:bg-muted/50 ${
                        formData.fiTypes.includes(fiType.code) ? 'border-primary bg-primary/5' : ''
                      }`}
                      onClick={() => handleFiTypeToggle(fiType.code)}
                    >
                      <Checkbox
                        id={fiType.code}
                        checked={formData.fiTypes.includes(fiType.code)}
                        onCheckedChange={() => handleFiTypeToggle(fiType.code)}
                      />
                      <div className="space-y-1">
                        <Label htmlFor={fiType.code} className="cursor-pointer text-sm font-medium">
                          {fiType.label}
                        </Label>
                        <p className="text-xs text-muted-foreground">{fiType.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Date Range & Frequency */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Calendar className="h-5 w-5" />
                  Date Range & Frequency
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="date_range_from">Data From *</Label>
                    <Input
                      id="date_range_from"
                      type="date"
                      value={formData.dateRangeFrom}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, dateRangeFrom: e.target.value }))
                      }
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="date_range_to">Data To *</Label>
                    <Input
                      id="date_range_to"
                      type="date"
                      value={formData.dateRangeTo}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, dateRangeTo: e.target.value }))
                      }
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="consent_expiry">Consent Expiry *</Label>
                    <Input
                      id="consent_expiry"
                      type="date"
                      value={formData.consentExpiry}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, consentExpiry: e.target.value }))
                      }
                      required
                    />
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <Label>Fetch Frequency</Label>
                  <RadioGroup
                    value={formData.frequencyType}
                    onValueChange={(value) =>
                      setFormData((prev) => ({
                        ...prev,
                        frequencyType: value,
                        fetchType: value === 'ONETIME' ? 'ONETIME' : 'PERIODIC',
                      }))
                    }
                    className="grid grid-cols-2 gap-3 md:grid-cols-3"
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

                {formData.frequencyType !== 'ONETIME' && (
                  <div className="space-y-2">
                    <Label htmlFor="frequency_value">Number of Fetches</Label>
                    <Input
                      id="frequency_value"
                      type="number"
                      min={1}
                      max={100}
                      value={formData.frequencyValue}
                      onChange={(e) =>
                        setFormData((prev) => ({
                          ...prev,
                          frequencyValue: parseInt(e.target.value) || 1,
                        }))
                      }
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
                    {CONSENT_PURPOSES.find((p) => p.code === formData.purpose)?.label}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">FI Types Selected</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {formData.fiTypes.length === 0 ? (
                      <span className="text-sm text-muted-foreground">None selected</span>
                    ) : (
                      formData.fiTypes.map((type) => (
                        <Badge key={type} variant="secondary" className="text-xs">
                          {FI_TYPES.find((f) => f.code === type)?.label || type}
                        </Badge>
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Date Range</p>
                  <p className="text-sm">
                    {format(new Date(formData.dateRangeFrom), 'dd MMM yyyy')} -{' '}
                    {format(new Date(formData.dateRangeTo), 'dd MMM yyyy')}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Frequency</p>
                  <p className="text-sm">
                    {formData.frequencyType}
                    {formData.frequencyType !== 'ONETIME' && ` (${formData.frequencyValue}x)`}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Valid Until</p>
                  <p className="text-sm">
                    {format(new Date(formData.consentExpiry), 'dd MMM yyyy')}
                  </p>
                </div>

                <Separator />

                <Button
                  type="submit"
                  className="w-full"
                  disabled={submitting || formData.fiTypes.length === 0 || !formData.customerId}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Shield className="mr-2 h-4 w-4" />
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
