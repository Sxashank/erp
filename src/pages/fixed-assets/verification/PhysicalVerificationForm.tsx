import { zodResolver } from '@hookform/resolvers/zod';
import { Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { FormSection, FormShell, PageHeader } from '@/components/common';
import { Button } from '@/components/ui/button';
import { DatePicker } from '@/components/ui/date-picker';
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
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { useAssetCategories } from '@/hooks/fixed-assets/useAssetCategories';
import { useFixedAssetUnits } from '@/hooks/fixed-assets/useMasters';
import { useCreateVerificationSchedule, useUpdateVerificationSchedule, useVerificationSchedule } from '@/hooks/fixed-assets/usePhysicalVerification';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import {
  verificationScheduleSchema,
  type VerificationScheduleInput,
} from '@/schemas/fixed-assets/verificationSchema';

function toDate(value: string | undefined): Date | null {
  return value ? new Date(value) : null;
}

function toIsoDate(value: Date | undefined): string {
  return value ? value.toISOString().slice(0, 10) : '';
}

const defaultValues: VerificationScheduleInput = {
  scheduleName: '',
  financialYear: '',
  locationId: '',
  categoryIds: [],
  scheduledStartDate: '',
  scheduledEndDate: '',
  remarks: '',
};

export function PhysicalVerificationForm(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const scheduleQuery = useVerificationSchedule(id);
  const unitsQuery = useFixedAssetUnits(organizationId);
  const categoriesQuery = useAssetCategories(organizationId);
  const createMutation = useCreateVerificationSchedule(organizationId);
  const updateMutation = useUpdateVerificationSchedule(organizationId, id ?? '');

  const form = useForm<VerificationScheduleInput>({
    resolver: zodResolver(verificationScheduleSchema),
    defaultValues,
  });

  useEffect(() => {
    if (!scheduleQuery.data) return;
    form.reset({
      scheduleName: scheduleQuery.data.scheduleName,
      financialYear: scheduleQuery.data.financialYear,
      locationId: scheduleQuery.data.locationId ?? '',
      categoryIds: scheduleQuery.data.categoryIds ?? [],
      scheduledStartDate: scheduleQuery.data.scheduledStartDate,
      scheduledEndDate: scheduleQuery.data.scheduledEndDate,
      remarks: scheduleQuery.data.remarks ?? '',
    });
  }, [form, scheduleQuery.data]);

  async function onSubmit(values: VerificationScheduleInput) {
    const payload = {
      organizationId,
      scheduleName: values.scheduleName,
      financialYear: values.financialYear,
      locationId: values.locationId || null,
      categoryIds: values.categoryIds.length > 0 ? values.categoryIds : null,
      scheduledStartDate: values.scheduledStartDate,
      scheduledEndDate: values.scheduledEndDate,
      remarks: values.remarks || null,
    };

    try {
      const schedule = isEdit
        ? await updateMutation.mutateAsync(payload)
        : await createMutation.mutateAsync(payload);
      toast({ title: isEdit ? 'Verification schedule updated' : 'Verification schedule created' });
      navigate(`/admin/fixed-assets/verification/${schedule.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  if (scheduleQuery.isLoading && isEdit) {
    return <Skeleton className="h-[420px] w-full" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Verification Schedule' : 'New Verification Schedule'}
        subtitle="Create a real verification workflow for a branch, location, or full-year cycle."
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Physical Verification', to: '/admin/fixed-assets/verification' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <FormShell
            footer={
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/admin/fixed-assets/verification')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  <Save className="mr-2 h-4 w-4" />
                  {form.formState.isSubmitting ? 'Saving…' : 'Save schedule'}
                </Button>
              </>
            }
          >
            <FormSection
              title="Schedule Scope"
              description="Choose the financial year, window, and optionally restrict the location."
            >
              <FormField
                control={form.control}
                name="scheduleName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Schedule name</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="financialYear"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Financial year</FormLabel>
                    <FormControl>
                      <Input placeholder="2025-26" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="locationId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Location</FormLabel>
                    <Select value={field.value || 'ALL'} onValueChange={(value) => field.onChange(value === 'ALL' ? '' : value)}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="All locations" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="ALL">All locations</SelectItem>
                        {(unitsQuery.data ?? []).map((unit) => (
                          <SelectItem key={unit.id} value={unit.id}>
                            {unit.code ? `${unit.code} · ` : ''}
                            {unit.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormItem>
                <FormLabel>Category scope</FormLabel>
                <div className="rounded-lg border p-3 text-sm text-muted-foreground">
                  {(categoriesQuery.data?.items?.length ?? 0) > 0
                    ? 'This schedule currently covers all categories for the selected location. Category-specific scoping can be added later without changing the workflow contract.'
                    : 'No categories are defined yet.'}
                </div>
              </FormItem>
              <FormField
                control={form.control}
                name="scheduledStartDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Start date</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="scheduledEndDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>End date</FormLabel>
                    <FormControl>
                      <DatePicker date={toDate(field.value)} onSelect={(value) => field.onChange(toIsoDate(value))} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="remarks"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Remarks</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
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
