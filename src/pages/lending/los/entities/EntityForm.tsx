/**
 * Entity Form Page
 * Multi-tab form for creating/editing entities (NO MODALS)
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Loader2 } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import EntityAddressesTab from './tabs/EntityAddressesTab';
import EntityBankAccountsTab from './tabs/EntityBankAccountsTab';
import EntityContactsTab from './tabs/EntityContactsTab';
import EntityFinancialsTab from './tabs/EntityFinancialsTab';
import EntityKYCTab from './tabs/EntityKYCTab';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { masterRowsToOptions, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/errorMessage';
import { logger } from '@/lib/logger';
import { createEntitySchema, type CreateEntityInput } from '@/schemas/lending';
import { entityApi } from '@/services/lending';
import type { Entity } from '@/types/lending';

// Sub-components for each tab

const ENTITY_STATUSES = [
  { value: 'PROSPECT', label: 'Prospect' },
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'BLACKLISTED', label: 'Blacklisted' },
];

export default function EntityForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const savingRef = useRef(false);
  const [entity, setEntity] = useState<Entity | null>(null);
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'basic');
  const entityTypesQuery = useLendingOptionRows('ENTITY_TYPE_CORPORATE');
  const riskGradesQuery = useLendingOptionRows('RISK_GRADE');
  const entityTypes = masterRowsToOptions(entityTypesQuery.data?.items);
  const riskGrades = masterRowsToOptions(riskGradesQuery.data?.items);

  // Form setup
  const form = useForm<CreateEntityInput>({
    resolver: zodResolver(createEntitySchema),
    defaultValues: {
      entityType: 'CORPORATE',
      legalName: '',
      pan: '',
      riskCategory: 'MEDIUM',
      status: 'PROSPECT',
    },
  });

  // Load entity data for edit mode
  useEffect(() => {
    if (isEditMode && id) {
      loadEntity(id);
    }
  }, [id, isEditMode]);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab) setActiveTab(tab);
  }, [searchParams]);

  const loadEntity = async (entityId: string) => {
    setLoading(true);
    try {
      const data = await entityApi.getEntity(entityId);
      setEntity(data);
      // Populate form with existing data
      form.reset({
        entityType: data.entityType,
        legalName: data.legalName,
        cin: data.cin || undefined,
        pan: data.pan,
        gstin: data.gstin || undefined,
        dateOfIncorporation: data.dateOfIncorporation || undefined,
        status: data.status,
        riskCategory: data.riskCategory || undefined,
        remarks: data.remarks || undefined,
      });
    } catch (error) {
      logger.error('Failed to load entity:', error);
      toast({
        title: 'Failed to load entity',
        description: getErrorMessage(error, 'Please try again.'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveEntity = async (data: CreateEntityInput, nextTab?: string) => {
    if (savingRef.current) return;
    savingRef.current = true;
    setSaving(true);
    try {
      if (isEditMode && id) {
        await entityApi.updateEntity(id, data);
        toast({ title: 'Entity updated', description: 'Changes saved successfully.' });
        if (nextTab) setActiveTab(nextTab);
      } else {
        const newEntity = await entityApi.createEntity(data);
        setEntity(newEntity);
        toast({
          title: 'Entity created',
          description:
            'Basic details saved. Continue with contacts, addresses, bank details, financials and KYC.',
        });
        navigate(`/admin/lending/entities/${newEntity.id}/edit?tab=${nextTab || 'contacts'}`, {
          replace: true,
        });
        return;
      }
      // Reload entity data after update
      loadEntity(id!);
    } catch (error) {
      logger.error('Failed to save entity:', error);
      toast({
        title: 'Save failed',
        description: getErrorMessage(error, 'Please check the form and try again.'),
        variant: 'destructive',
      });
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  };

  // Handle form submission
  const onSubmit = async (data: CreateEntityInput) => {
    await saveEntity(data, isEditMode ? undefined : 'contacts');
  };

  const handleTabChange = async (tab: string) => {
    if (tab === 'basic') {
      setActiveTab(tab);
      return;
    }

    if (entity?.id || id) {
      setActiveTab(tab);
      return;
    }

    const isValid = await form.trigger();
    if (!isValid) {
      toast({
        title: 'Save basic details first',
        description: 'Complete the required basic information before opening this section.',
        variant: 'destructive',
      });
      return;
    }

    await saveEntity(form.getValues(), tab);
  };

  // Watch entity type to show/hide CIN field
  const entityType = form.watch('entityType');
  const showCIN = ['CORPORATE', 'COMPANY', 'LLP'].includes(entityType);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEditMode ? 'Edit Entity' : 'New Entity'}
        subtitle={
          isEditMode
            ? `Editing ${entity?.legalName} (${entity?.entityCode})`
            : 'Create a new borrower entity'
        }
        breadcrumbs={[
          { label: 'Entities', to: '/admin/lending/entities' },
          { label: isEditMode ? 'Edit' : 'New' },
        ]}
      />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="contacts">Contacts</TabsTrigger>
          <TabsTrigger value="addresses">Addresses</TabsTrigger>
          <TabsTrigger value="bank">Bank Accounts</TabsTrigger>
          <TabsTrigger value="financials">Financials</TabsTrigger>
          <TabsTrigger value="kyc">KYC</TabsTrigger>
        </TabsList>

        {/* Basic Info Tab */}
        <TabsContent value="basic" className="mt-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Entity Information</CardTitle>
                  <CardDescription>Basic details about the borrower entity</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    {/* Entity Type */}
                    <FormField
                      control={form.control}
                      name="entityType"
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
                              {entityTypes.map((type) => (
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
                      name="legalName"
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
                                placeholder={
                                  entityType === 'LLP' ? 'AAA-0000' : 'U12345XX0000XXX000000'
                                }
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
                      name="dateOfIncorporation"
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
                      name="riskCategory"
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
                              {riskGrades.map((risk) => (
                                <SelectItem key={risk.value} value={risk.value}>
                                  {risk.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormDescription>Internal risk classification</FormDescription>
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
                <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={saving}>
                  {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Save className="mr-2 h-4 w-4" />
                  {isEditMode ? 'Save Changes' : 'Create & Continue'}
                </Button>
              </div>
            </form>
          </Form>
        </TabsContent>

        {/* Contacts Tab */}
        <TabsContent value="contacts" className="mt-6">
          {entity && <EntityContactsTab entityId={entity.id} />}
        </TabsContent>

        {/* Addresses Tab */}
        <TabsContent value="addresses" className="mt-6">
          {entity && <EntityAddressesTab entityId={entity.id} />}
        </TabsContent>

        {/* Bank Accounts Tab */}
        <TabsContent value="bank" className="mt-6">
          {entity && <EntityBankAccountsTab entityId={entity.id} />}
        </TabsContent>

        {/* Financials Tab */}
        <TabsContent value="financials" className="mt-6">
          {entity && <EntityFinancialsTab entityId={entity.id} />}
        </TabsContent>

        {/* KYC Tab */}
        <TabsContent value="kyc" className="mt-6">
          {entity && <EntityKYCTab entityId={entity.id} />}
        </TabsContent>
      </Tabs>
    </div>
  );
}
