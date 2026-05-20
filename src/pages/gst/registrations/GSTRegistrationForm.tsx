import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Pencil, Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Form,
  FormControl,
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
import {
  useCreateGSTRegistration,
  useGSTRegistration,
  useOrganizations,
  useUnits,
  useUpdateGSTRegistration,
  type GSTRegistrationInput,
} from '@/hooks/tax/useTaxation';
import {
  gstRegistrationSchema,
  type GSTRegistrationFormInput,
  type GSTRegistrationFormValues,
} from '@/schemas/tax/taxSchemas';
import { useActiveOrganizationId } from '@/stores/organizationStore';

const defaultValues: GSTRegistrationFormValues = {
  organizationId: '',
  gstin: '',
  legalName: '',
  tradeName: '',
  registrationType: 'REGULAR',
  stateCode: '',
  stateName: '',
  address: '',
  pincode: '',
  isEInvoiceEnabled: false,
  eInvoiceUsername: '',
  eInvoicePassword: '',
  isEWayBillEnabled: false,
  unitId: '',
  isActive: true,
};

const registrationTypes = ['REGULAR', 'COMPOSITION', 'SEZ', 'ISD', 'TDS', 'TCS', 'NON_RESIDENT'];
const NO_UNIT_VALUE = '__no-unit__';

export function GSTRegistrationForm() {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const activeOrganizationId = useActiveOrganizationId();
  const isEdit = Boolean(id) && location.pathname.endsWith('/edit');
  const isDetail = Boolean(id) && !isEdit;

  const registrationQuery = useGSTRegistration(id);
  const organizationsQuery = useOrganizations();
  const createRegistration = useCreateGSTRegistration();
  const updateRegistration = useUpdateGSTRegistration(id ?? '');

  const form = useForm<GSTRegistrationFormValues, unknown, GSTRegistrationFormInput>({
    resolver: zodResolver(gstRegistrationSchema),
    defaultValues: {
      ...defaultValues ?? '',
    },
  });

  const organizationId = form.watch('organizationId');
  const unitsQuery = useUnits(organizationId || activeOrganizationId || undefined);

  useEffect(() => {
    if (activeOrganizationId && !id) {
      form.setValue('organizationId', activeOrganizationId);
    }
  }, [activeOrganizationId, form, id]);

  useEffect(() => {
    if (!registrationQuery.data) return;
    form.reset({
      organizationId: registrationQuery.data.organizationId,
      gstin: registrationQuery.data.gstin,
      legalName: registrationQuery.data.legalName,
      tradeName: registrationQuery.data.tradeName ?? '',
      registrationType: registrationQuery.data.registrationType,
      stateCode: registrationQuery.data.stateCode,
      stateName: registrationQuery.data.stateName,
      address: registrationQuery.data.address ?? '',
      pincode: registrationQuery.data.pincode ?? '',
      isEInvoiceEnabled: registrationQuery.data.isEInvoiceEnabled,
      eInvoiceUsername: registrationQuery.data.eInvoiceUsername ?? '',
      eInvoicePassword: '',
      isEWayBillEnabled: registrationQuery.data.isEWayBillEnabled,
      unitId: registrationQuery.data.unitId ?? '',
      isActive: registrationQuery.data.isActive,
    });
  }, [form, registrationQuery.data]);

  const mutation = isEdit ? updateRegistration : createRegistration;
  const isReadOnly = isDetail;

  async function onSubmit(values: GSTRegistrationFormInput) {
    const payload: GSTRegistrationInput = {
      ...values,
      tradeName: values.tradeName || undefined,
      address: values.address || undefined,
      pincode: values.pincode || undefined,
      eInvoiceUsername: values.eInvoiceUsername || undefined,
      eInvoicePassword: values.eInvoicePassword || undefined,
      unitId: values.unitId || undefined,
    };
    await mutation.mutateAsync(payload);
    navigate('/admin/gst/registrations');
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isDetail ? 'GST Registration Details' : isEdit ? 'Edit GST Registration' : 'Add GST Registration'}
        subtitle="Maintain GST registration credentials and filing flags"
        breadcrumbs={[{ label: 'GST Registrations', to: '/admin/gst/registrations' }]}
        actions={
          isDetail ? (
            <Button onClick={() => navigate(`/admin/gst/registrations/${id}/edit`)}>
              <Pencil className="mr-2 h-4 w-4" />
              Edit Registration
            </Button>
          ) : undefined
        }
      />

      {mutation.error && <ErrorState error={mutation.error} />}
      {registrationQuery.error && <ErrorState error={registrationQuery.error} onRetry={() => registrationQuery.refetch()} />}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              isReadOnly ? (
                <Button type="button" variant="outline" onClick={() => navigate('/admin/gst/registrations')}>
                  Back
                </Button>
              ) : (
                <>
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/gst/registrations')}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    {mutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="mr-2 h-4 w-4" />
                    )}
                    Save Registration
                  </Button>
                </>
              )
            }
          >
            <FormSection title="Registration Identity">
              <FormField
                control={form.control}
                name="organizationId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Organization</FormLabel>
                    <Select disabled={isReadOnly} value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select organization" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {(organizationsQuery.data?.items ?? []).map((organization) => (
                          <SelectItem key={organization.id} value={organization.id}>
                            {organization.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="unitId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Unit</FormLabel>
                    <Select
                      disabled={isReadOnly}
                      value={field.value || NO_UNIT_VALUE}
                      onValueChange={(value) => field.onChange(value === NO_UNIT_VALUE ? '' : value)}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Optional unit" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value={NO_UNIT_VALUE}>No unit mapping</SelectItem>
                        {(unitsQuery.data?.items ?? []).map((unit) => (
                          <SelectItem key={unit.id} value={unit.id}>
                            {unit.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="gstin"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>GSTIN</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="27ABCDE1234F1Z5" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="registrationType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Registration type</FormLabel>
                    <Select disabled={isReadOnly} value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {registrationTypes.map((type) => (
                          <SelectItem key={type} value={type}>
                            {type.replace('_', ' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Legal Details">
              <FormField
                control={form.control}
                name="legalName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Legal name</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="Registered legal name" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="tradeName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Trade name</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="Optional trade name" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="stateCode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>State code</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="27" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="stateName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>State name</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="Maharashtra" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Address</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="Registered address" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="pincode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>PIN code</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="400001" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Portal Flags">
              <FormField
                control={form.control}
                name="eInvoiceUsername"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>E-invoice username</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={isReadOnly} placeholder="Optional username" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {!isReadOnly && (
                <FormField
                  control={form.control}
                  name="eInvoicePassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>E-invoice password</FormLabel>
                      <FormControl>
                        <Input {...field} type="password" placeholder="Optional password" />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
              <FormField
                control={form.control}
                name="isEInvoiceEnabled"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-2 space-y-0">
                    <FormControl>
                      <Checkbox disabled={isReadOnly} checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel>E-invoice enabled</FormLabel>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="isEWayBillEnabled"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-2 space-y-0">
                    <FormControl>
                      <Checkbox disabled={isReadOnly} checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel>E-way bill enabled</FormLabel>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="isActive"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-2 space-y-0">
                    <FormControl>
                      <Checkbox disabled={isReadOnly} checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel>Active</FormLabel>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>
          </FormShell>
        </form>
      </Form>
    </div>
  );
}
