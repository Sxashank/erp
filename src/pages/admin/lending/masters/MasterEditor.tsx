import { ArrowLeft, Plus, Save, Trash2, X } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import {
  useCreateLendingMasterRow,
  useDeleteLendingMasterRow,
  useLendingMasterCatalog,
  useLendingMasterRows,
  useUpdateLendingMasterRow,
} from '@/hooks/lending/useLendingMasters';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type { MasterFieldDescriptor, MasterRow } from '@/services/lending/masterDataApi';

type RowData = Record<string, unknown>;

function humanize(value: string): string {
  return value
    .replace(/([A-Z])/g, ' $1')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim();
}

function emptyValue(field: MasterFieldDescriptor): string | number | boolean | null {
  if (field.dataType === 'boolean') return false;
  if (field.dataType === 'number') return null;
  return '';
}

function isPrimitive(value: unknown): value is string | number | boolean | null {
  return value === null || ['string', 'number', 'boolean'].includes(typeof value);
}

function renderValue(value: unknown): JSX.Element | string {
  if (value === null || value === undefined || value === '') {
    return <span className="text-muted-foreground">-</span>;
  }
  if (typeof value === 'boolean') {
    return (
      <span className={value ? 'text-emerald-700' : 'text-muted-foreground'}>
        {value ? 'Yes' : 'No'}
      </span>
    );
  }
  if (typeof value === 'object') {
    return <code className="text-xs">{JSON.stringify(value)}</code>;
  }
  return String(value);
}

export default function MasterEditor(): JSX.Element {
  const { masterKey = '' } = useParams<{ masterKey: string }>();
  const { toast } = useToast();
  const catalogQuery = useLendingMasterCatalog();
  const rowsQuery = useLendingMasterRows(masterKey, { pageSize: 500 });
  const createMut = useCreateLendingMasterRow(masterKey);
  const updateMut = useUpdateLendingMasterRow(masterKey);
  const deleteMut = useDeleteLendingMasterRow(masterKey);

  const master = catalogQuery.data?.items.find((item) => item.key === masterKey);
  const editableFields = useMemo(
    () => (master?.fields ?? []).filter((field) => field.editable),
    [master],
  );
  const visibleFields = useMemo(() => master?.fields ?? [], [master]);

  const [draft, setDraft] = useState<RowData | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editRow, setEditRow] = useState<RowData | null>(null);

  function startAdd(): void {
    const blank: RowData = {};
    editableFields.forEach((field) => {
      blank[field.key] = emptyValue(field);
    });
    setDraft(blank);
  }

  function startEdit(row: MasterRow): void {
    const copy: RowData = {};
    editableFields.forEach((field) => {
      copy[field.key] = row.data[field.key] ?? emptyValue(field);
    });
    setEditingId(row.id);
    setEditRow(copy);
  }

  function renderInput(
    field: MasterFieldDescriptor,
    value: unknown,
    onChange: (value: unknown) => void,
  ): JSX.Element {
    if (field.dataType === 'boolean' || typeof value === 'boolean') {
      return <Switch checked={Boolean(value)} onCheckedChange={onChange} />;
    }
    if (field.dataType === 'number') {
      return (
        <Input
          type="number"
          value={value === null || value === undefined ? '' : String(value)}
          onChange={(event) => {
            const next = event.target.value;
            onChange(next === '' ? null : Number(next));
          }}
          className="h-8 text-sm"
        />
      );
    }
    return (
      <Input
        type={field.dataType === 'date' ? 'date' : 'text'}
        value={value === null || value === undefined ? '' : String(value)}
        onChange={(event) => onChange(event.target.value)}
        className="h-8 text-sm"
      />
    );
  }

  if (!masterKey) {
    return <ErrorState error={new Error('Missing master key in URL')} />;
  }

  if (catalogQuery.isLoading || rowsQuery.isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title={humanize(masterKey)}
          breadcrumbs={[
            { label: 'Lending', to: '/admin/lending' },
            { label: 'Master Data', to: '/admin/lending/masters' },
            { label: humanize(masterKey) },
          ]}
        />
        <SkeletonTable rows={6} columns={5} />
      </div>
    );
  }

  if (catalogQuery.isError || rowsQuery.isError || !master) {
    return (
      <div className="space-y-6">
        <PageHeader
          title={humanize(masterKey)}
          breadcrumbs={[
            { label: 'Lending', to: '/admin/lending' },
            { label: 'Master Data', to: '/admin/lending/masters' },
            { label: humanize(masterKey) },
          ]}
        />
        <ErrorState
          error={catalogQuery.error ?? rowsQuery.error ?? new Error('Master not found')}
          onRetry={() => {
            catalogQuery.refetch();
            rowsQuery.refetch();
          }}
        />
      </div>
    );
  }

  const rows = rowsQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={master.label}
        subtitle={master.description}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Master Data', to: '/admin/lending/masters' },
          { label: master.label },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link to="/admin/lending/masters">
                <ArrowLeft className="mr-2 h-4 w-4" />
                All masters
              </Link>
            </Button>
            <Button onClick={startAdd} disabled={Boolean(draft)}>
              <Plus className="mr-2 h-4 w-4" />
              Add row
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
                  {visibleFields.map((field) => (
                    <th key={field.key} className="px-3 py-2 text-left font-semibold">
                      {field.label}
                    </th>
                  ))}
                  <th className="px-3 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {draft ? (
                  <tr className="border-t bg-emerald-50/40">
                    {visibleFields.map((field) => (
                      <td key={field.key} className="px-3 py-2 align-top">
                        {field.editable ? (
                          renderInput(field, draft[field.key], (value) =>
                            setDraft({ ...draft, [field.key]: value }),
                          )
                        ) : (
                          <span className="text-muted-foreground">system</span>
                        )}
                      </td>
                    ))}
                    <td className="px-3 py-2 text-right">
                      <Button
                        size="sm"
                        onClick={() =>
                          createMut.mutate(
                            { data: draft },
                            {
                              onSuccess: () => {
                                toast({ title: 'Row added' });
                                setDraft(null);
                              },
                              onError: (err) => showErrorToast(err, toast),
                            },
                          )
                        }
                        disabled={createMut.isPending}
                      >
                        <Save className="mr-1 h-4 w-4" />
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setDraft(null)}
                        className="ml-2"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ) : null}

                {rows.length === 0 && !draft ? (
                  <tr className="border-t">
                    <td
                      colSpan={visibleFields.length + 1}
                      className="px-3 py-10 text-center text-muted-foreground"
                    >
                      No rows configured yet.
                    </td>
                  </tr>
                ) : null}

                {rows.map((row) => {
                  const isEditing = editingId === row.id;
                  const isSystem = row.data.isSystem === true;
                  return (
                    <tr key={row.id} className="border-t hover:bg-muted/20">
                      {visibleFields.map((field) => {
                        const value = isEditing ? editRow?.[field.key] : row.data[field.key];
                        if (isEditing && field.editable && isPrimitive(value)) {
                          return (
                            <td key={field.key} className="px-3 py-2">
                              {renderInput(field, value, (next) =>
                                setEditRow({ ...(editRow ?? {}), [field.key]: next }),
                              )}
                            </td>
                          );
                        }
                        return (
                          <td key={field.key} className="px-3 py-2 align-top">
                            {renderValue(value)}
                          </td>
                        );
                      })}
                      <td className="whitespace-nowrap px-3 py-2 text-right">
                        {isEditing ? (
                          <>
                            <Button
                              size="sm"
                              onClick={() =>
                                editRow &&
                                updateMut.mutate(
                                  { rowId: row.id, payload: { data: editRow } },
                                  {
                                    onSuccess: () => {
                                      toast({ title: 'Row saved' });
                                      setEditingId(null);
                                      setEditRow(null);
                                    },
                                    onError: (err) => showErrorToast(err, toast),
                                  },
                                )
                              }
                              disabled={updateMut.isPending}
                            >
                              <Save className="mr-1 h-4 w-4" />
                              Save
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setEditingId(null);
                                setEditRow(null);
                              }}
                              className="ml-2"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </>
                        ) : (
                          <>
                            <Button size="sm" variant="outline" onClick={() => startEdit(row)}>
                              Edit
                            </Button>
                            {isSystem ? (
                              <span className="ml-2 text-xs text-muted-foreground">system</span>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="ml-2 text-destructive hover:text-destructive"
                                onClick={() =>
                                  deleteMut.mutate(row.id, {
                                    onSuccess: () => toast({ title: 'Row deactivated' }),
                                    onError: (err) => showErrorToast(err, toast),
                                  })
                                }
                                disabled={deleteMut.isPending}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
