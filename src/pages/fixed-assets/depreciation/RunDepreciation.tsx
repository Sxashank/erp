import { zodResolver } from '@hookform/resolvers/zod';
import { Play } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import { FormSection, FormShell, PageHeader } from '@/components/common';
import { Button } from '@/components/ui/button';
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
import { Textarea } from '@/components/ui/textarea';
import { useRunDepreciation } from '@/hooks/fixed-assets/useDepreciation';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import { showErrorToast } from '@/lib/errorToast';
import {
  depreciationRunSchema,
  type DepreciationRunInput,
} from '@/schemas/fixed-assets/depreciationSchema';

export function RunDepreciation(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const navigate = useNavigate();
  const { toast } = useToast();
  const runMutation = useRunDepreciation(organizationId);

  const form = useForm<DepreciationRunInput>({
    resolver: zodResolver(depreciationRunSchema),
    defaultValues: {
      depreciationPeriod: '',
      depreciationBook: 'COMPANIES_ACT',
      remarks: '',
    },
  });

  async function onSubmit(values: DepreciationRunInput) {
    try {
      const run = await runMutation.mutateAsync({
        organizationId,
        depreciationPeriod: values.depreciationPeriod,
        depreciationBook: values.depreciationBook,
        remarks: values.remarks || null,
      });
      toast({ title: `Depreciation run ${run.depreciationPeriod} completed` });
      navigate(`/admin/fixed-assets/depreciation/runs/${run.id}`);
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Run Depreciation"
        subtitle="Create a monthly depreciation run for the current organization."
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Depreciation Runs', to: '/admin/fixed-assets/depreciation' },
          { label: 'Run' },
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
                  onClick={() => navigate('/admin/fixed-assets/depreciation')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  <Play className="mr-2 h-4 w-4" />
                  {form.formState.isSubmitting ? 'Running…' : 'Run depreciation'}
                </Button>
              </>
            }
          >
            <FormSection
              title="Run Parameters"
              description="Pick the accounting book and month to process."
            >
              <FormField
                control={form.control}
                name="depreciationPeriod"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Depreciation period</FormLabel>
                    <FormControl>
                      <Input
                        type="month"
                        value={field.value}
                        onChange={(event) => field.onChange(event.target.value)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="depreciationBook"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Book</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="COMPANIES_ACT">Companies Act</SelectItem>
                        <SelectItem value="IT_ACT">IT Act</SelectItem>
                      </SelectContent>
                    </Select>
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
