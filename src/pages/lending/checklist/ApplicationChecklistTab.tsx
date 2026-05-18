/**
 * Approval Checklist tab — embedded inside the Loan Application detail page.
 *
 * Shows the current checklist (or an "Apply Template" CTA if none is attached),
 * a banner of mandatory pending items, and a DataTable of items with row-level
 * actions: Mark Met, Waive, Mark Not Applicable, Reset.
 *
 * Per CLAUDE.md §5.7, list view renders Skeleton / EmptyState / ErrorState.
 */

import {
  AlertTriangle,
  CheckCircle2,
  FileText,
  MoreHorizontal,
  Plus,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { useState } from 'react';

import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { ChecklistStatusPill } from '@/components/lending/common/ChecklistStatusPill';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import {
  useApplicationChecklist,
  useApplyTemplateToApplication,
  useChecklistTemplates,
  useMarkChecklistItemMet,
  useMarkChecklistItemNA,
  useReplaceApplicationTemplate,
  useResetChecklistItem,
  useWaiveChecklistItem,
} from '@/hooks/lending/useChecklist';
import { useToast } from '@/hooks/use-toast';
import type { LoanChecklistItem } from '@/services/lending/checklistApi';

interface ApplicationChecklistTabProps {
  applicationId: string;
}

type ActionKind = 'mark-met' | 'waive' | 'mark-na';

interface ActiveAction {
  kind: ActionKind;
  item: LoanChecklistItem;
}

export function ApplicationChecklistTab({
  applicationId,
}: ApplicationChecklistTabProps): JSX.Element {
  const { toast } = useToast();
  const checklistQuery = useApplicationChecklist(applicationId);
  const templatesQuery = useChecklistTemplates();

  const [applyOpen, setApplyOpen] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [useSanctionDate, setUseSanctionDate] = useState(true);

  const [action, setAction] = useState<ActiveAction | null>(null);
  const [evidence, setEvidence] = useState('');
  const [notes, setNotes] = useState('');
  const [waiverReason, setWaiverReason] = useState('');

  const applyMut = useApplyTemplateToApplication({
    onSuccess: () => {
      toast({ title: 'Checklist applied' });
      setApplyOpen(false);
    },
  });
  const replaceMut = useReplaceApplicationTemplate({
    onSuccess: () => {
      toast({ title: 'Checklist replaced' });
      setApplyOpen(false);
    },
  });
  const markMetMut = useMarkChecklistItemMet({
    onSuccess: () => {
      toast({ title: 'Item marked Met' });
      setAction(null);
    },
  });
  const waiveMut = useWaiveChecklistItem({
    onSuccess: () => {
      toast({ title: 'Item waived' });
      setAction(null);
    },
  });
  const markNAMut = useMarkChecklistItemNA({
    onSuccess: () => {
      toast({ title: 'Item marked Not Applicable' });
      setAction(null);
    },
  });
  const resetMut = useResetChecklistItem({
    onSuccess: () => toast({ title: 'Item reset to Pending' }),
  });

  function openAction(kind: ActionKind, item: LoanChecklistItem): void {
    setEvidence(item.evidenceDocumentPath ?? '');
    setNotes(item.notes ?? '');
    setWaiverReason('');
    setAction({ kind, item });
  }

  function submitActiveAction(): void {
    if (!action) return;
    const { kind, item } = action;
    if (kind === 'mark-met') {
      markMetMut.mutate({
        applicationId,
        itemId: item.id,
        payload: {
          evidenceDocumentPath: evidence || null,
          notes: notes || null,
        },
      });
    } else if (kind === 'waive') {
      waiveMut.mutate({
        applicationId,
        itemId: item.id,
        payload: { waiverReason },
      });
    } else if (kind === 'mark-na') {
      markNAMut.mutate({
        applicationId,
        itemId: item.id,
        payload: { notes: notes || null },
      });
    }
  }

  if (checklistQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (checklistQuery.isError) {
    return <ErrorState error={checklistQuery.error} onRetry={() => checklistQuery.refetch()} />;
  }

  const checklist = checklistQuery.data;
  const templates = templatesQuery.data ?? [];

  // No checklist yet — show CTA
  if (!checklist) {
    return (
      <>
        <EmptyState
          title="No checklist applied"
          subtitle="Apply a template to start tracking the approval items required for this loan application."
          action={
            <Button onClick={() => setApplyOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Apply Template
            </Button>
          }
        />
        <ApplyTemplateDialog
          open={applyOpen}
          onOpenChange={setApplyOpen}
          mode="apply"
          templates={templates}
          loadingTemplates={templatesQuery.isLoading}
          selectedTemplateId={selectedTemplateId}
          onSelectTemplate={setSelectedTemplateId}
          useSanctionDate={useSanctionDate}
          onToggleSanctionDate={setUseSanctionDate}
          submitting={applyMut.isPending}
          onSubmit={() => {
            if (!selectedTemplateId) return;
            applyMut.mutate({
              applicationId,
              payload: {
                templateId: selectedTemplateId,
                ...(useSanctionDate
                  ? { dueDateAnchor: new Date().toISOString().slice(0, 10) }
                  : {}),
              },
            });
          }}
        />
      </>
    );
  }

  const columns: Column<LoanChecklistItem>[] = [
    {
      key: 'sortOrder',
      header: '#',
      width: '60px',
      align: 'right',
      sortable: true,
    },
    {
      key: 'category',
      header: 'Category',
      render: (row) => <Badge variant="secondary">{row.category}</Badge>,
    },
    {
      key: 'label',
      header: 'Item',
      render: (row) => (
        <div>
          <div className="flex items-center gap-2 font-medium">
            {row.label}
            {row.isMandatory && (
              <Badge variant="outline" className="border-red-300 bg-red-50 text-red-700">
                Mandatory
              </Badge>
            )}
          </div>
          {row.description && (
            <p className="mt-0.5 text-xs text-muted-foreground">{row.description}</p>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <ChecklistStatusPill status={row.status} />,
    },
    {
      key: 'dueDate',
      header: 'Due',
      render: (row) => (row.dueDate ? <DateDisplay date={row.dueDate} /> : '—'),
    },
    {
      key: 'evidence',
      header: 'Evidence',
      render: (row) =>
        row.evidenceDocumentPath ? (
          <a
            className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
            href={row.evidenceDocumentPath}
            target="_blank"
            rel="noreferrer"
          >
            <FileText className="h-3.5 w-3.5" />
            View
          </a>
        ) : (
          '—'
        ),
    },
    {
      key: 'lastAction',
      header: 'Last Action',
      render: (row) => {
        if (row.status === 'MET' && row.metAt) {
          return (
            <div className="text-xs">
              <div className="text-green-700">Met</div>
              <div className="text-muted-foreground">
                <DateDisplay date={row.metAt} />
                {row.metBy && ` · ${row.metBy.slice(0, 8)}`}
              </div>
            </div>
          );
        }
        if (row.status === 'WAIVED' && row.waivedAt) {
          return (
            <div className="text-xs">
              <div className="text-amber-700">Waived</div>
              <div className="text-muted-foreground">
                <DateDisplay date={row.waivedAt} />
                {row.waivedBy && ` · ${row.waivedBy.slice(0, 8)}`}
              </div>
              {row.waiverReason && (
                <div className="mt-0.5 italic text-muted-foreground">{row.waiverReason}</div>
              )}
            </div>
          );
        }
        return '—';
      },
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (row) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Open item actions"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => openAction('mark-met', row)}>
              <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />
              Mark Met
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => openAction('waive', row)}>
              <AlertTriangle className="mr-2 h-4 w-4 text-amber-600" />
              Waive
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => openAction('mark-na', row)}>
              <XCircle className="mr-2 h-4 w-4 text-slate-500" />
              Mark Not Applicable
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => resetMut.mutate({ applicationId, itemId: row.id })}
              disabled={resetMut.isPending}
            >
              <RefreshCw className="mr-2 h-4 w-4 text-blue-600" />
              Reset to Pending
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 pt-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Template</p>
            <p className="text-base font-semibold">{checklist.name}</p>
            <p className="text-xs text-muted-foreground">
              {checklist.items.length} item
              {checklist.items.length === 1 ? '' : 's'} · {checklist.mandatoryPending} mandatory
              pending
            </p>
          </div>
          <Button variant="outline" onClick={() => setApplyOpen(true)}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Replace Template
          </Button>
        </CardContent>
      </Card>

      {checklist.mandatoryPending > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Mandatory items pending</AlertTitle>
          <AlertDescription>
            Cannot approve sanction until {checklist.mandatoryPending} mandatory item
            {checklist.mandatoryPending === 1 ? '' : 's'} are addressed (Met, Waived, or Not
            Applicable).
          </AlertDescription>
        </Alert>
      )}

      <DataTable<LoanChecklistItem>
        data={[...checklist.items].sort((a, b) => a.sortOrder - b.sortOrder)}
        columns={columns}
        getRowId={(r) => r.id}
        emptyTitle="Checklist is empty"
        emptySubtitle="The applied template has no items."
      />

      {/* Apply / Replace template dialog */}
      <ApplyTemplateDialog
        open={applyOpen}
        onOpenChange={setApplyOpen}
        mode="replace"
        templates={templates}
        loadingTemplates={templatesQuery.isLoading}
        selectedTemplateId={selectedTemplateId}
        onSelectTemplate={setSelectedTemplateId}
        useSanctionDate={useSanctionDate}
        onToggleSanctionDate={setUseSanctionDate}
        submitting={replaceMut.isPending}
        onSubmit={() => {
          if (!selectedTemplateId) return;
          replaceMut.mutate({
            applicationId,
            payload: {
              templateId: selectedTemplateId,
              ...(useSanctionDate ? { dueDateAnchor: new Date().toISOString().slice(0, 10) } : {}),
            },
          });
        }}
      />

      {/* Per-item action dialogs */}
      <Dialog open={action !== null} onOpenChange={(open) => !open && setAction(null)}>
        <DialogContent>
          {action && action.kind === 'mark-met' && (
            <>
              <DialogHeader>
                <DialogTitle>Mark item Met</DialogTitle>
                <DialogDescription>
                  <span className="font-medium">{action.item.label}</span>
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="evidence-path">
                    Evidence Document Path{' '}
                    {action.item.requiresEvidence && <span className="text-destructive">*</span>}
                  </Label>
                  <Input
                    id="evidence-path"
                    value={evidence}
                    onChange={(e) => setEvidence(e.target.value)}
                    placeholder="e.g. /dms/applications/123/kyc.pdf"
                  />
                </div>
                <div>
                  <Label htmlFor="met-notes">Notes (optional)</Label>
                  <Textarea
                    id="met-notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setAction(null)}>
                  Cancel
                </Button>
                <Button
                  onClick={submitActiveAction}
                  disabled={
                    markMetMut.isPending || (action.item.requiresEvidence && !evidence.trim())
                  }
                >
                  Mark Met
                </Button>
              </DialogFooter>
            </>
          )}
          {action && action.kind === 'waive' && (
            <>
              <DialogHeader>
                <DialogTitle>Waive item</DialogTitle>
                <DialogDescription>
                  <span className="font-medium">{action.item.label}</span>
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="waiver-reason">
                    Waiver Reason <span className="text-destructive">*</span>
                  </Label>
                  <Textarea
                    id="waiver-reason"
                    value={waiverReason}
                    onChange={(e) => setWaiverReason(e.target.value)}
                    rows={3}
                    placeholder="Document why this is being waived (min 5 chars)"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setAction(null)}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={submitActiveAction}
                  disabled={waiveMut.isPending || waiverReason.trim().length < 5}
                >
                  Waive item
                </Button>
              </DialogFooter>
            </>
          )}
          {action && action.kind === 'mark-na' && (
            <>
              <DialogHeader>
                <DialogTitle>Mark Not Applicable</DialogTitle>
                <DialogDescription>
                  <span className="font-medium">{action.item.label}</span>
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3">
                <div>
                  <Label htmlFor="na-notes">Notes (optional)</Label>
                  <Textarea
                    id="na-notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setAction(null)}>
                  Cancel
                </Button>
                <Button onClick={submitActiveAction} disabled={markNAMut.isPending}>
                  Mark Not Applicable
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface ApplyTemplateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'apply' | 'replace';
  templates: { id: string; name: string; code: string; isDefault: boolean }[];
  loadingTemplates: boolean;
  selectedTemplateId: string;
  onSelectTemplate: (id: string) => void;
  useSanctionDate: boolean;
  onToggleSanctionDate: (b: boolean) => void;
  submitting: boolean;
  onSubmit: () => void;
}

function ApplyTemplateDialog({
  open,
  onOpenChange,
  mode,
  templates,
  loadingTemplates,
  selectedTemplateId,
  onSelectTemplate,
  useSanctionDate,
  onToggleSanctionDate,
  submitting,
  onSubmit,
}: ApplyTemplateDialogProps): JSX.Element {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {mode === 'apply' ? 'Apply Checklist Template' : 'Replace Checklist Template'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'apply'
              ? 'Pick a template to start tracking approval items for this application.'
              : 'Replacing the current checklist will discard the in-progress items.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div>
            <Label htmlFor="template-select">Template</Label>
            {loadingTemplates ? (
              <Skeleton className="h-9 w-full" />
            ) : (
              <Select value={selectedTemplateId} onValueChange={onSelectTemplate}>
                <SelectTrigger id="template-select">
                  <SelectValue placeholder="Select a template" />
                </SelectTrigger>
                <SelectContent>
                  {templates.map((t) => (
                    <SelectItem key={t.id} value={t.id}>
                      {t.name} {t.isDefault && '(default)'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Checkbox
              id="use-sanction-date"
              checked={useSanctionDate}
              onCheckedChange={(v) => onToggleSanctionDate(Boolean(v))}
            />
            <Label htmlFor="use-sanction-date" className="text-sm">
              Use sanction date as due-date anchor
            </Label>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={!selectedTemplateId || submitting}>
            {mode === 'apply' ? 'Apply' : 'Replace'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
