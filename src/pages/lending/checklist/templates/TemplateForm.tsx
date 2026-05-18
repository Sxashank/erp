/**
 * Checklist Template — create/edit form.
 *
 * The top header section uses react-hook-form + zod + shadcn <Form> per
 * CLAUDE.md §5.3. The items section below is an inline editable table; we
 * diff edits client-side and issue create/update/delete calls in sequence
 * on save (the BE supports item-level CRUD; bulk replace is not available).
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowDown, ArrowUp, Loader2, Plus, Save, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { ErrorState } from '@/components/common/ErrorState';
import { FormSection, FormShell } from '@/components/common/FormShell';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import {
  useAddTemplateItem,
  useChecklistTemplate,
  useCreateTemplate,
  useDeleteTemplateItem,
  useUpdateTemplate,
  useUpdateTemplateItem,
} from '@/hooks/lending/useChecklist';
import { useToast } from '@/hooks/use-toast';
import type { ChecklistItemCategory, ChecklistTemplateItem } from '@/services/lending/checklistApi';

const CATEGORIES: ChecklistItemCategory[] = [
  'DOCUMENT',
  'KYC',
  'COMPLIANCE',
  'COVENANT',
  'LEGAL',
  'INSURANCE',
  'OTHER',
];

const templateSchema = z.object({
  code: z.string().trim().min(1, 'Code is required').max(64),
  name: z.string().trim().min(1, 'Name is required').max(256),
  description: z.string().trim().optional(),
  appliesTo: z.literal('LOAN_APPLICATION'),
  isDefault: z.boolean(),
});

type TemplateFormInput = z.input<typeof templateSchema>;
type TemplateFormValues = z.output<typeof templateSchema>;

/**
 * A row in the items editor. `id` is undefined for newly added rows. We
 * track `_dirty` and `_deleted` to compute the diff on save.
 */
interface ItemDraft {
  /** Server id, or undefined for unsaved rows. */
  id?: string;
  /** Stable client key — keeps React rows identified during reorder. */
  key: string;
  code: string;
  label: string;
  description: string;
  category: ChecklistItemCategory;
  isMandatory: boolean;
  sortOrder: number;
  defaultDueOffsetDays: number | null;
  requiresEvidence: boolean;
  _dirty: boolean;
  _deleted: boolean;
}

function fromServerItem(item: ChecklistTemplateItem): ItemDraft {
  return {
    id: item.id,
    key: item.id,
    code: item.code,
    label: item.label,
    description: item.description ?? '',
    category: item.category,
    isMandatory: item.isMandatory,
    sortOrder: item.sortOrder,
    defaultDueOffsetDays: item.defaultDueOffsetDays,
    requiresEvidence: item.requiresEvidence,
    _dirty: false,
    _deleted: false,
  };
}

function blankDraft(sortOrder: number): ItemDraft {
  return {
    key: crypto.randomUUID(),
    code: '',
    label: '',
    description: '',
    category: 'DOCUMENT',
    isMandatory: false,
    sortOrder,
    defaultDueOffsetDays: null,
    requiresEvidence: false,
    _dirty: true,
    _deleted: false,
  };
}

export default function TemplateForm(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const templateQuery = useChecklistTemplate(id);

  const form = useForm<TemplateFormInput, unknown, TemplateFormValues>({
    resolver: zodResolver(templateSchema),
    defaultValues: {
      code: '',
      name: '',
      description: '',
      appliesTo: 'LOAN_APPLICATION',
      isDefault: false,
    },
  });

  const [items, setItems] = useState<ItemDraft[]>([]);

  // Seed form + items from server on edit
  useEffect(() => {
    if (!templateQuery.data) return;
    const t = templateQuery.data;
    form.reset({
      code: t.code,
      name: t.name,
      description: t.description ?? '',
      appliesTo: t.appliesTo,
      isDefault: t.isDefault,
    });
    setItems([...t.items].sort((a, b) => a.sortOrder - b.sortOrder).map(fromServerItem));
  }, [templateQuery.data, form]);

  const createMut = useCreateTemplate();
  const updateMut = useUpdateTemplate();
  const addItemMut = useAddTemplateItem();
  const updateItemMut = useUpdateTemplateItem();
  const deleteItemMut = useDeleteTemplateItem();

  const submitting =
    createMut.isPending ||
    updateMut.isPending ||
    addItemMut.isPending ||
    updateItemMut.isPending ||
    deleteItemMut.isPending;

  // --- Item editor handlers -------------------------------------------------

  function updateItem(idx: number, patch: Partial<ItemDraft>): void {
    setItems((prev) => {
      const next = [...prev];
      const current = next[idx];
      if (!current) return prev;
      next[idx] = { ...current, ...patch, _dirty: true };
      return next;
    });
  }

  function addRow(): void {
    setItems((prev) => [...prev, blankDraft(prev.length + 1)]);
  }

  function deleteRow(idx: number): void {
    setItems((prev) => {
      const next = [...prev];
      const current = next[idx];
      if (!current) return prev;
      // If never saved, drop entirely. Otherwise mark for deletion.
      if (!current.id) {
        next.splice(idx, 1);
      } else {
        next[idx] = { ...current, _deleted: true };
      }
      return next;
    });
  }

  function moveRow(idx: number, dir: -1 | 1): void {
    setItems((prev) => {
      const visible = prev.filter((i) => !i._deleted);
      const visibleIdx = visible.findIndex((v) => v === prev[idx]);
      const target = visibleIdx + dir;
      if (target < 0 || target >= visible.length) return prev;
      const next = [...prev];
      const a = visible[visibleIdx];
      const b = visible[target];
      if (!a || !b) return prev;
      const ai = next.indexOf(a);
      const bi = next.indexOf(b);
      next[ai] = b;
      next[bi] = a;
      // Re-flow sortOrder over visible items
      let order = 1;
      for (const row of next) {
        if (!row._deleted) {
          row.sortOrder = order;
          row._dirty = true;
          order += 1;
        }
      }
      return next;
    });
  }

  // --- Submit ---------------------------------------------------------------

  async function persistItems(templateId: string): Promise<void> {
    // Process in three passes — deletes first, then updates, then creates.
    // Each pass is sequential to keep failures attributable to one row.
    const toDelete = items.filter((i) => i.id && i._deleted);
    const toUpdate = items.filter((i) => i.id && !i._deleted && i._dirty);
    const toCreate = items.filter((i) => !i.id && !i._deleted);

    for (const row of toDelete) {
      if (!row.id) continue;
      await deleteItemMut.mutateAsync({ templateId, itemId: row.id });
    }
    for (const row of toUpdate) {
      if (!row.id) continue;
      await updateItemMut.mutateAsync({
        templateId,
        itemId: row.id,
        payload: {
          code: row.code,
          label: row.label,
          description: row.description || null,
          category: row.category,
          isMandatory: row.isMandatory,
          sortOrder: row.sortOrder,
          defaultDueOffsetDays: row.defaultDueOffsetDays,
          requiresEvidence: row.requiresEvidence,
        },
      });
    }
    for (const row of toCreate) {
      await addItemMut.mutateAsync({
        templateId,
        payload: {
          code: row.code,
          label: row.label,
          description: row.description || null,
          category: row.category,
          isMandatory: row.isMandatory,
          sortOrder: row.sortOrder,
          defaultDueOffsetDays: row.defaultDueOffsetDays,
          requiresEvidence: row.requiresEvidence,
        },
      });
    }
  }

  async function onSubmit(values: TemplateFormValues): Promise<void> {
    const headerPayload = {
      code: values.code,
      name: values.name,
      description: values.description || null,
      appliesTo: values.appliesTo,
      isDefault: values.isDefault,
    };
    try {
      let templateId: string;
      if (isEdit && id) {
        await updateMut.mutateAsync({ id, payload: headerPayload });
        templateId = id;
      } else {
        const created = await createMut.mutateAsync(headerPayload);
        templateId = created.id;
      }
      await persistItems(templateId);
      toast({
        title: isEdit ? 'Template updated' : 'Template created',
      });
      navigate('/admin/lending/checklist/templates');
    } catch {
      // showErrorToast already fired from the hook's onError.
    }
  }

  const visibleItems = useMemo(() => items.filter((i) => !i._deleted), [items]);

  if (isEdit && templateQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Edit Template"
          breadcrumbs={[
            { label: 'Lending', to: '/admin/lending' },
            { label: 'Approval Checklists', to: '/admin/lending/checklist/templates' },
            { label: 'Edit' },
          ]}
        />
        <ErrorState error={templateQuery.error} onRetry={templateQuery.refetch} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Checklist Template' : 'New Checklist Template'}
        subtitle={
          isEdit
            ? `Editing ${templateQuery.data?.name ?? ''}`
            : 'Define a reusable list of approval items to apply on loan applications.'
        }
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Approval Checklists', to: '/admin/lending/checklist/templates' },
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
                  onClick={() => navigate('/admin/lending/checklist/templates')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="mr-2 h-4 w-4" />
                  )}
                  {isEdit ? 'Update Template' : 'Create Template'}
                </Button>
              </>
            }
          >
            <FormSection title="Template Details">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Code *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. STD_HOMELOAN" {...field} />
                    </FormControl>
                    <FormDescription>Stable identifier shown in reports.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. Standard Home Loan Checklist" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="appliesTo"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Applies To *</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="LOAN_APPLICATION">Loan Application</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="isDefault"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-md border p-3">
                    <div>
                      <FormLabel>Default Template</FormLabel>
                      <FormDescription>
                        New applications get this template applied automatically.
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
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
            </FormSection>

            <FormSection
              title="Checklist Items"
              description="Each item gates sanction approval until it is marked Met, Waived, or Not Applicable."
            >
              <div className="md:col-span-2">
                <div className="overflow-hidden rounded-lg border bg-background">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[60px]">Sort</TableHead>
                        <TableHead className="w-[140px]">Category</TableHead>
                        <TableHead className="w-[140px]">Code</TableHead>
                        <TableHead>Label / Description</TableHead>
                        <TableHead className="w-[100px] text-center">Mandatory</TableHead>
                        <TableHead className="w-[120px] text-center">Evidence</TableHead>
                        <TableHead className="w-[120px] text-right">Due Offset (days)</TableHead>
                        <TableHead className="w-[100px] text-right" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {visibleItems.length === 0 && (
                        <TableRow>
                          <TableCell
                            colSpan={8}
                            className="py-6 text-center text-sm text-muted-foreground"
                          >
                            No items yet. Click "Add item" to define the first one.
                          </TableCell>
                        </TableRow>
                      )}
                      {items.map((row, idx) => {
                        if (row._deleted) return null;
                        return (
                          <TableRow key={row.key}>
                            <TableCell>
                              <div className="flex flex-col gap-0.5">
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  className="h-5 w-5"
                                  onClick={() => moveRow(idx, -1)}
                                  aria-label="Move up"
                                >
                                  <ArrowUp className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  className="h-5 w-5"
                                  onClick={() => moveRow(idx, 1)}
                                  aria-label="Move down"
                                >
                                  <ArrowDown className="h-3.5 w-3.5" />
                                </Button>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Select
                                value={row.category}
                                onValueChange={(v) =>
                                  updateItem(idx, {
                                    category: v as ChecklistItemCategory,
                                  })
                                }
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {CATEGORIES.map((c) => (
                                    <SelectItem key={c} value={c}>
                                      {c}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </TableCell>
                            <TableCell>
                              <Input
                                value={row.code}
                                onChange={(e) => updateItem(idx, { code: e.target.value })}
                                placeholder="ITEM_CODE"
                                aria-label="Item code"
                              />
                            </TableCell>
                            <TableCell>
                              <div className="space-y-2">
                                <Input
                                  value={row.label}
                                  onChange={(e) => updateItem(idx, { label: e.target.value })}
                                  placeholder="Label"
                                  aria-label="Item label"
                                />
                                <Textarea
                                  value={row.description}
                                  onChange={(e) =>
                                    updateItem(idx, {
                                      description: e.target.value,
                                    })
                                  }
                                  placeholder="Description (optional)"
                                  rows={1}
                                  aria-label="Item description"
                                />
                              </div>
                            </TableCell>
                            <TableCell className="text-center">
                              <Checkbox
                                checked={row.isMandatory}
                                onCheckedChange={(v) =>
                                  updateItem(idx, { isMandatory: Boolean(v) })
                                }
                                aria-label="Mandatory"
                              />
                            </TableCell>
                            <TableCell className="text-center">
                              <Checkbox
                                checked={row.requiresEvidence}
                                onCheckedChange={(v) =>
                                  updateItem(idx, {
                                    requiresEvidence: Boolean(v),
                                  })
                                }
                                aria-label="Requires evidence"
                              />
                            </TableCell>
                            <TableCell className="text-right">
                              <Input
                                type="number"
                                min={0}
                                value={
                                  row.defaultDueOffsetDays === null ? '' : row.defaultDueOffsetDays
                                }
                                onChange={(e) => {
                                  const v = e.target.value;
                                  updateItem(idx, {
                                    defaultDueOffsetDays: v === '' ? null : Number(v),
                                  });
                                }}
                                placeholder="—"
                                className="text-right tabular-nums"
                                aria-label="Due offset days"
                              />
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => deleteRow(idx)}
                                aria-label="Delete item"
                                className="text-destructive hover:text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
                <div className="mt-3 flex justify-end">
                  <Button type="button" variant="outline" size="sm" onClick={addRow}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add item
                  </Button>
                </div>
              </div>
            </FormSection>
          </FormShell>
        </form>
      </Form>
    </div>
  );
}
