/**
 * IIF Fund Utilization Category — create/edit form.
 *
 * react-hook-form + zod via shadcn <Form>/<FormField>. See CLAUDE.md §5.3.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2, Save } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { ErrorState } from '@/components/common/ErrorState';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
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
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  useCreateUtilizationCategory,
  useSubventionSchemes,
  useUpdateUtilizationCategory,
  useUtilizationCategory,
} from '@/hooks/lending/useIif';
import { useToast } from '@/hooks/use-toast';

const NO_SCHEME = '__NONE__';

const categorySchema = z.object({
  code: z.string().trim().min(1, 'Code is required').max(64),
  label: z.string().trim().min(1, 'Label is required').max(256),
  description: z.string().trim().optional(),
  schemeId: z.string(),
  sortOrder: z.coerce.number().int().nonnegative(),
  isActive: z.boolean(),
});

type CategoryFormInput = z.input<typeof categorySchema>;
type CategoryFormValues = z.output<typeof categorySchema>;

export default function CategoryForm(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const categoryQuery = useUtilizationCategory(id);
  const { data: schemesData } = useSubventionSchemes();
  const schemes = schemesData?.items ?? [];

  const form = useForm<CategoryFormInput, unknown, CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      code: '',
      label: '',
      description: '',
      schemeId: NO_SCHEME,
      sortOrder: 0,
      isActive: true,
    },
  });

  useEffect(() => {
    if (!categoryQuery.data) return;
    const c = categoryQuery.data;
    form.reset({
      code: c.code,
      label: c.label,
      description: c.description ?? '',
      schemeId: c.schemeId ?? NO_SCHEME,
      sortOrder: c.sortOrder,
      isActive: c.isActive,
    });
  }, [categoryQuery.data, form]);

  const createMut = useCreateUtilizationCategory({
    onSuccess: () => {
      toast({ title: 'Category created' });
      navigate('/admin/lending/iif/categories');
    },
  });
  const updateMut = useUpdateUtilizationCategory({
    onSuccess: () => {
      toast({ title: 'Category updated' });
      navigate('/admin/lending/iif/categories');
    },
  });

  const submitting = createMut.isPending || updateMut.isPending;

  function onSubmit(values: CategoryFormValues) {
    const payload = {
      code: values.code,
      label: values.label,
      description: values.description || null,
      schemeId: values.schemeId === NO_SCHEME ? null : values.schemeId,
      sortOrder: values.sortOrder,
      isActive: values.isActive,
    };
    if (isEdit && id) {
      updateMut.mutate({ id, payload });
    } else {
      createMut.mutate(payload);
    }
  }

  if (isEdit && categoryQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Edit Category"
          breadcrumbs={[
            { label: 'Lending', to: '/admin/lending' },
            { label: 'Interest Subvention' },
            { label: 'Categories', to: '/admin/lending/iif/categories' },
            { label: 'Edit' },
          ]}
        />
        <ErrorState error={categoryQuery.error} onRetry={categoryQuery.refetch} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Category' : 'New Fund Utilization Category'}
        subtitle={
          isEdit
            ? `Editing ${categoryQuery.data?.label ?? ''}`
            : 'Add a new bucket that loan applicants can split their requested amount across.'
        }
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Interest Subvention' },
          { label: 'Categories', to: '/admin/lending/iif/categories' },
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
                  onClick={() => navigate('/admin/lending/iif/categories')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  {isEdit ? 'Update Category' : 'Create Category'}
                </Button>
              </>
            }
          >
            <FormSection title="Category Details">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Code *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. LAND" {...field} />
                    </FormControl>
                    <FormDescription>Stable identifier used in reports.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="label"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Label *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. Land acquisition" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="schemeId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scheme</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Optional — leave blank for platform default" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value={NO_SCHEME}>Platform default (any scheme)</SelectItem>
                        {schemes.map((s) => (
                          <SelectItem key={s.id} value={s.id}>
                            {s.schemeCode} — {s.schemeName}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Bind this category to a specific scheme, or leave for default.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="sortOrder"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sort Order</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        name={field.name}
                        ref={field.ref}
                        onBlur={field.onBlur}
                        value={(field.value as number | string | undefined) ?? ''}
                        onChange={field.onChange}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="md:col-span-2">
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea rows={2} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="isActive"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-md border p-3 md:col-span-2">
                    <div>
                      <FormLabel>Active</FormLabel>
                      <FormDescription>
                        Inactive categories are hidden from new applications.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
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
