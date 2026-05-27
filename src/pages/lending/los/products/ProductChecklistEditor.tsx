import { ArrowLeft, Plus, Save, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import {
  useAddProductDocumentRequirement,
  useDeleteProductDocumentRequirement,
  useProductDocumentRequirements,
  useUpdateProductDocumentRequirement,
} from '@/hooks/lending/useProductDocuments';
import { useLendingMasterRows } from '@/hooks/lending/useLendingMasters';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';

interface DraftRequirement {
  catalogItemId: string;
  isMandatory: boolean;
  isMandatoryForDisbursement: boolean;
}

export default function ProductChecklistEditor(): JSX.Element {
  const { id = '' } = useParams<{ id: string }>();
  const { toast } = useToast();
  const requirementsQuery = useProductDocumentRequirements(id);
  const catalogQuery = useLendingMasterRows('checklist-catalog', { pageSize: 500 });
  const addMutation = useAddProductDocumentRequirement(id);
  const updateMutation = useUpdateProductDocumentRequirement(id);
  const deleteMutation = useDeleteProductDocumentRequirement(id);
  const [draft, setDraft] = useState<DraftRequirement | null>(null);

  const existingCatalogIds = useMemo(
    () => new Set((requirementsQuery.data ?? []).map((item) => item.catalogItemId)),
    [requirementsQuery.data],
  );
  const catalogOptions = (catalogQuery.data?.items ?? []).filter(
    (row) => !existingCatalogIds.has(row.id),
  );

  if (!id) {
    return <ErrorState error={new Error('Missing product id')} />;
  }

  if (requirementsQuery.isLoading || catalogQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Product Document Requirements"
          breadcrumbs={[
            { label: 'Loan Products', to: '/admin/lending/products' },
            { label: 'Document Requirements' },
          ]}
        />
        <SkeletonTable rows={6} columns={5} />
      </div>
    );
  }

  if (requirementsQuery.isError || catalogQuery.isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Product Document Requirements"
          breadcrumbs={[
            { label: 'Loan Products', to: '/admin/lending/products' },
            { label: 'Document Requirements' },
          ]}
        />
        <ErrorState
          error={requirementsQuery.error ?? catalogQuery.error}
          onRetry={() => {
            requirementsQuery.refetch();
            catalogQuery.refetch();
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Product Document Requirements"
        subtitle="Borrower upload requirements are sourced from the Checklist Item Catalog."
        breadcrumbs={[
          { label: 'Loan Products', to: '/admin/lending/products' },
          { label: 'Document Requirements' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link to={`/admin/lending/products/${id}`}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Product
              </Link>
            </Button>
            <Button
              onClick={() =>
                setDraft({
                  catalogItemId: '',
                  isMandatory: true,
                  isMandatoryForDisbursement: false,
                })
              }
              disabled={Boolean(draft)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add requirement
            </Button>
          </div>
        }
      />

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold">Catalog Item</th>
                  <th className="px-3 py-2 text-left font-semibold">Category</th>
                  <th className="px-3 py-2 text-left font-semibold">Stage</th>
                  <th className="px-3 py-2 text-center font-semibold">Mandatory</th>
                  <th className="px-3 py-2 text-center font-semibold">Disbursement Gate</th>
                  <th className="px-3 py-2 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {draft ? (
                  <tr className="border-t bg-emerald-50/40">
                    <td className="px-3 py-2">
                      <Select
                        value={draft.catalogItemId}
                        onValueChange={(value) => setDraft({ ...draft, catalogItemId: value })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select catalog item" />
                        </SelectTrigger>
                        <SelectContent>
                          {catalogOptions.map((row) => (
                            <SelectItem key={row.id} value={row.id}>
                              {String(row.data.label ?? row.data.code)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-3 py-2 text-muted-foreground" colSpan={2}>
                      Definition will be copied from catalog.
                    </td>
                    <td className="px-3 py-2 text-center">
                      <Switch
                        checked={draft.isMandatory}
                        onCheckedChange={(value) =>
                          setDraft({ ...draft, isMandatory: Boolean(value) })
                        }
                      />
                    </td>
                    <td className="px-3 py-2 text-center">
                      <Switch
                        checked={draft.isMandatoryForDisbursement}
                        onCheckedChange={(value) =>
                          setDraft({ ...draft, isMandatoryForDisbursement: Boolean(value) })
                        }
                      />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        size="sm"
                        onClick={() => {
                          if (!draft.catalogItemId) {
                            toast({
                              title: 'Select a catalog item',
                              variant: 'destructive',
                            });
                            return;
                          }
                          addMutation.mutate(draft, {
                            onSuccess: () => {
                              toast({ title: 'Requirement added' });
                              setDraft(null);
                            },
                            onError: (err) => showErrorToast(err, toast),
                          });
                        }}
                        disabled={addMutation.isPending}
                      >
                        <Save className="mr-1 h-4 w-4" />
                        Save
                      </Button>
                    </td>
                  </tr>
                ) : null}

                {(requirementsQuery.data ?? []).length === 0 && !draft ? (
                  <tr className="border-t">
                    <td colSpan={6} className="px-3 py-10 text-center text-muted-foreground">
                      No document requirements configured for this product.
                    </td>
                  </tr>
                ) : null}

                {(requirementsQuery.data ?? []).map((item) => (
                  <tr key={item.id} className="border-t">
                    <td className="px-3 py-2">
                      <div className="font-medium">{item.name}</div>
                      <div className="font-mono text-xs text-muted-foreground">{item.code}</div>
                    </td>
                    <td className="px-3 py-2">{item.category}</td>
                    <td className="px-3 py-2">{item.requiredAtStage.replace(/_/g, ' ')}</td>
                    <td className="px-3 py-2 text-center">
                      <Switch
                        checked={item.isMandatory}
                        onCheckedChange={(value) =>
                          updateMutation.mutate(
                            {
                              requirementId: item.id,
                              payload: { isMandatory: Boolean(value) },
                            },
                            { onError: (err) => showErrorToast(err, toast) },
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-2 text-center">
                      <Switch
                        checked={item.isMandatoryForDisbursement}
                        onCheckedChange={(value) =>
                          updateMutation.mutate(
                            {
                              requirementId: item.id,
                              payload: { isMandatoryForDisbursement: Boolean(value) },
                            },
                            { onError: (err) => showErrorToast(err, toast) },
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive hover:text-destructive"
                        onClick={() =>
                          deleteMutation.mutate(item.id, {
                            onSuccess: () => toast({ title: 'Requirement removed' }),
                            onError: (err) => showErrorToast(err, toast),
                          })
                        }
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
