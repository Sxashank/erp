/**
 * Approval Checklist Templates — list page.
 *
 * Master CRUD entry point. CLAUDE.md §9.2 / §9.3.
 */

import { Check, Edit, Eye, Plus, Star, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { DataTable, type Column } from '@/components/common/DataTable';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  useChecklistTemplates,
  useDeleteTemplate,
  useSetDefaultTemplate,
} from '@/hooks/lending/useChecklist';
import { useToast } from '@/hooks/use-toast';
import type { ChecklistTemplate } from '@/services/lending/checklistApi';

export default function TemplateList(): JSX.Element {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { data, isLoading, error, refetch } = useChecklistTemplates();
  const items = data ?? [];

  const [pendingDelete, setPendingDelete] = useState<ChecklistTemplate | null>(null);

  const deleteMut = useDeleteTemplate({
    onSuccess: () => {
      toast({ title: 'Template deleted' });
      setPendingDelete(null);
    },
  });

  const setDefaultMut = useSetDefaultTemplate({
    onSuccess: (t) => {
      toast({ title: `'${t.name}' is now the default template` });
    },
  });

  const columns: Column<ChecklistTemplate>[] = [
    {
      key: 'name',
      header: 'Name',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{row.name}</span>
          {row.isDefault && (
            <Badge variant="default" className="border-amber-300 bg-amber-100 text-amber-700">
              <Star className="mr-1 h-3 w-3" /> Default
            </Badge>
          )}
        </div>
      ),
    },
    {
      key: 'code',
      header: 'Code',
      sortable: true,
      render: (row) => <span className="font-mono text-sm">{row.code}</span>,
    },
    {
      key: 'items',
      header: 'Items',
      align: 'right',
      render: (row) => row.items.length,
    },
    {
      key: 'mandatory',
      header: 'Mandatory',
      align: 'right',
      render: (row) => row.items.filter((i) => i.isMandatory).length,
    },
    {
      key: 'appliesTo',
      header: 'Applies To',
      render: (row) => <Badge variant="secondary">{row.appliesTo.replace(/_/g, ' ')}</Badge>,
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (row) => (
        <div className="flex justify-end gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/admin/lending/checklist/templates/${row.id}`);
            }}
            aria-label="View template"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/admin/lending/checklist/templates/${row.id}`);
            }}
            aria-label="Edit template"
          >
            <Edit className="h-4 w-4" />
          </Button>
          {!row.isDefault && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setDefaultMut.mutate(row.id);
              }}
              disabled={setDefaultMut.isPending}
              aria-label="Set as default"
              title="Set as default"
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              setPendingDelete(row);
            }}
            aria-label="Delete template"
            title="Delete"
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Approval Checklist Templates"
        subtitle="Reusable checklists applied to loan applications before sanction approval."
        breadcrumbs={[{ label: 'Lending', to: '/admin/lending' }, { label: 'Approval Checklists' }]}
        actions={
          <Button onClick={() => navigate('/admin/lending/checklist/templates/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Template
          </Button>
        }
      />

      <DataTable<ChecklistTemplate>
        data={items}
        columns={columns}
        getRowId={(r) => r.id}
        isLoading={isLoading}
        error={error}
        onRetry={refetch}
        emptyTitle="No checklist templates"
        emptySubtitle="Create a template to start gating sanctions on a fixed list of approvals."
        emptyAction={
          <Button onClick={() => navigate('/admin/lending/checklist/templates/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Template
          </Button>
        }
      />

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title="Delete checklist template?"
        description={
          pendingDelete ? (
            <>
              This will delete <span className="font-semibold">{pendingDelete.name}</span> and all
              its items. Loans already using this template are not affected. Type the template code
              to confirm.
            </>
          ) : null
        }
        confirmLabel="Delete template"
        variant="destructive"
        requireConfirmation={pendingDelete?.code}
        loading={deleteMut.isPending}
        onConfirm={() => {
          if (pendingDelete) deleteMut.mutate(pendingDelete.id);
        }}
      />
    </div>
  );
}
