/**
 * Entity Form Page
 * Multi-tab form for creating/editing entities (NO MODALS)
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { logger } from '@/lib/logger';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { entityApi } from '@/services/lending';
import { createEntitySchema, type CreateEntityInput } from '@/schemas/lending';
import type { Entity } from '@/types/lending';

// Sub-components for each tab
import EntityContactsTab from './tabs/EntityContactsTab';
import EntityAddressesTab from './tabs/EntityAddressesTab';
import EntityBankAccountsTab from './tabs/EntityBankAccountsTab';
import EntityFinancialsTab from './tabs/EntityFinancialsTab';
import EntityKYCTab from './tabs/EntityKYCTab';

// Entity types for corporate/wholesale lending (Individual hidden per NBFC-IFC model)
const ENTITY_TYPES = [
  { value: 'CORPORATE', label: 'Corporate / Company' },
  { value: 'LLP', label: 'Limited Liability Partnership' },
  { value: 'PARTNERSHIP', label: 'Partnership Firm' },
  { value: 'TRUST', label: 'Trust' },
  { value: 'PROPRIETORSHIP', label: 'Proprietorship Firm' },
  { value: 'SOCIETY', label: 'Society / Association' },
];

// Infrastructure sectors for NBFC-IFC classification
const INFRASTRUCTURE_SECTORS = [
  { value: 'POWER', label: 'Power Generation & Distribution' },
  { value: 'ROADS', label: 'Roads & Highways' },
  { value: 'PORTS', label: 'Ports & Shipping' },
  { value: 'AIRPORTS', label: 'Airports' },
  { value: 'RAILWAYS', label: 'Railways' },
  { value: 'TELECOM', label: 'Telecommunications' },
  { value: 'INDUSTRIAL', label: 'Industrial Infrastructure' },
  { value: 'WATER', label: 'Water Supply & Sanitation' },
  { value: 'URBAN', label: 'Urban Infrastructure' },
  { value: 'OTHER_INFRA', label: 'Other Infrastructure' },
  { value: 'NON_INFRA', label: 'Non-Infrastructure' },
];

const ENTITY_STATUSES = [
  { value: 'PROSPECT', label: 'Prospect' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'BLACKLISTED', label: 'Blacklisted' },
];

const RISK_CATEGORIES = [
  { value: 'LOW', label: 'Low Risk' },
  { value: 'MEDIUM', label: 'Medium Risk' },
  { value: 'HIGH', label: 'High Risk' },
];

export default function EntityForm() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [entity, setEntity] = useState<Entity | null>(null);
  const [activeTab, setActiveTab] = useState('basic');

  // Form setup
  const form = useForm<CreateEntityInput>({
    resolver: zodResolver(createEntitySchema) as any,
    defaultValues: {
      entity_type: 'CORPORATE',
      legal_name: '',
      pan: '',
      status: 'PROSPECT',
    },
  });

  // Load entity data for edit mode
  useEffect(() => {
    if (isEditMode && id) {
      loadEntity(id);
    }
  }, [id, isEditMode]);

  const loadEntity = async (entityId: string) => {
    setLoading(true);
    try {
      const data = await entityApi.getEntity(entityId);
      setEntity(data);
      // Populate form with existing data
      form.reset({
        entity_type: data.entity_type,
        legal_name: data.legal_name,
        cin: data.cin || undefined,
        pan: data.pan,
        gstin: data.gstin || undefined,
        date_of_incorporation: data.date_of_incorporation || undefined,
        status: data.status,
        risk_category: data.risk_category || undefined,
        remarks: data.remarks || undefined,
      } as any);
    } catch (error) {
      logger.error('Failed to load entity:', error);
      toast({
        title: 'Failed to load entity',
        description:
          (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
          'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle form submission
  const onSubmit = async (data: CreateEntityInput) => {
    setSaving(true);
    try {
      if (isEditMode && id) {
        await entityApi.updateEntity(id, data);
        toast({ title: 'Entity updated', description: 'Changes saved successfully.' });
      } else {
        const newEntity = await entityApi.createEntity(data);
        toast({ title: 'Entity created', description: 'New entity saved successfully.' });
        navigate(`/admin/lending/entities/${newEntity.entity_id}`);
        return;
      }
      // Reload entity data after update
      loadEntity(id!);
    } catch (error) {
      logger.error('Failed to save entity:', error);
      toast({
        title: 'Save failed',
        description:
          (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
          'Please check the form and try again.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  // Watch entity type to show/hide CIN field
  const entityType = form.watch('entity_type');
  const showCIN = entityType === 'CORPORATE' || entityType === 'LLP';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              {isEditMode ? 'Edit Entity' : 'New Entity'}
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              {isEditMode
                ? `Editing ${entity?.legal_name} (${entity?.entity_code})`
                : 'Create a new borrower entity'}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="contacts" disabled={!isEditMode}>Contacts</TabsTrigger>
          <TabsTrigger value="addresses" disabled={!isEditMode}>Addresses</TabsTrigger>
          <TabsTrigger value="bank" disabled={!isEditMode}>Bank Accounts</TabsTrigger>
          <TabsTrigger value="financials" disabled={!isEditMode}>Financials</TabsTrigger>
          <TabsTrigger value="kyc" disabled={!isEditMode}>KYC</TabsTrigger>
        </TabsList>

        {/* Basic Info Tab */}
        <TabsContent value="basic" className="mt-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Entity Information</CardTitle>
                  <CardDescription>
                    Basic details about the borrower entity
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Entity Type */}
                    <FormField
                      control={form.control}
                      name="entity_type"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Entity Type *</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select entity type" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {ENTITY_TYPES.map((type) => (
                                <SelectItem key={type.value} value={type.value}>
                                  {type.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Status */}
                    <FormField
                      control={form.control}
                      name="status"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Status *</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select status" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {ENTITY_STATUSES.map((status) => (
                                <SelectItem key={status.value} value={status.value}>
                                  {status.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Legal Name */}
                    <FormField
                      control={form.control}
                      name="legal_name"
                      render={({ field }) => (
                        <FormItem className="md:col-span-2">
                          <FormLabel>Legal Name *</FormLabel>
                          <FormControl>
                            <Input placeholder="Enter legal name as per registration" {...field} />
                          </FormControl>
                          <FormDescription>
                            Full legal name as per incorporation/registration documents
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* CIN (for Corporate/LLP) */}
                    {showCIN && (
                      <FormField
                        control={form.control}
                        name="cin"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>CIN / LLPIN</FormLabel>
                            <FormControl>
                              <Input
                                placeholder={entityType === 'LLP' ? 'AAA-0000' : 'U12345XX0000XXX000000'}
                                {...field}
                                value={field.value || ''}
                              />
                            </FormControl>
                            <FormDescription>
                              {entityType === 'LLP'
                                ? 'Limited Liability Partnership Identification Number'
                                : 'Corporate Identification Number from MCA'}
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    )}

                    {/* PAN */}
                    <FormField
                      control={form.control}
                      name="pan"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>PAN *</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="XXXXX0000X"
                              {...field}
                              onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                              maxLength={10}
                            />
                          </FormControl>
                          <FormDescription>
                            Permanent Account Number (10 characters)
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* GSTIN */}
                    <FormField
                      control={form.control}
                      name="gstin"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>GSTIN</FormLabel>
                          <FormControl>
                            <Input
                              placeholder="00XXXXX0000X0X0"
                              {...field}
                              value={field.value || ''}
                              onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                              maxLength={15}
                            />
                          </FormControl>
                          <FormDescription>
                            GST Identification Number (15 characters)
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Date of Incorporation */}
                    <FormField
                      control={form.control}
                      name="date_of_incorporation"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Date of Incorporation</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} value={field.value || ''} />
                          </FormControl>
                          <FormDescription>
                            Date when entity was incorporated/registered
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Risk Category */}
                    <FormField
                      control={form.control}
                      name="risk_category"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Risk Category</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value || ''}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select risk category" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {RISK_CATEGORIES.map((risk) => (
                                <SelectItem key={risk.value} value={risk.value}>
                                  {risk.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormDescription>
                            Internal risk classification
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Remarks */}
                    <FormField
                      control={form.control}
                      name="remarks"
                      render={({ field }) => (
                        <FormItem className="md:col-span-2">
                          <FormLabel>Remarks</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Any additional notes about this entity..."
                              {...field}
                              value={field.value || ''}
                              rows={3}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Form Actions */}
              <div className="flex items-center justify-end gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate(-1)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Save className="mr-2 h-4 w-4" />
                  {isEditMode ? 'Save Changes' : 'Create Entity'}
                </Button>
              </div>
            </form>
          </Form>
        </TabsContent>

        {/* Contacts Tab */}
        <TabsContent value="contacts" className="mt-6">
          {entity && <EntityContactsTab entityId={entity.entity_id} />}
        </TabsContent>

        {/* Addresses Tab */}
        <TabsContent value="addresses" className="mt-6">
          {entity && <EntityAddressesTab entityId={entity.entity_id} />}
        </TabsContent>

        {/* Bank Accounts Tab */}
        <TabsContent value="bank" className="mt-6">
          {entity && <EntityBankAccountsTab entityId={entity.entity_id} />}
        </TabsContent>

        {/* Financials Tab */}
        <TabsContent value="financials" className="mt-6">
          {entity && <EntityFinancialsTab entityId={entity.entity_id} />}
        </TabsContent>

        {/* KYC Tab */}
        <TabsContent value="kyc" className="mt-6">
          {entity && <EntityKYCTab entityId={entity.entity_id} />}
        </TabsContent>
      </Tabs>
    </div>
  );
}
