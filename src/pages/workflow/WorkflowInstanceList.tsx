import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  GitBranch,
  Loader2,
  MoreHorizontal,
  RefreshCw,
  Search,
  XCircle,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import {
  ConfirmDialog,
  EmptyState,
  ErrorState,
  PageHeader,
  SkeletonTable,
} from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { useOrganization } from '@/hooks/useOrganization';
import { useCancelInstance, useWorkflowInstances } from '@/hooks/workflow/useWorkflowInstances';
import { showErrorToast } from '@/lib/errorToast';
import type {
  WorkflowEntityType,
  WorkflowInstanceResponse,
  WorkflowInstanceStatus,
} from '@/services/workflow/workflowApi';

const ENTITY_TYPES: { value: WorkflowEntityType | 'all'; label: string }[] = [
  { value: 'all', label: 'All Entity Types' },
  { value: 'VOUCHER', label: 'Voucher' },
  { value: 'PURCHASE_BILL', label: 'Purchase Bill' },
  { value: 'SALES_INVOICE', label: 'Sales Invoice' },
  { value: 'PAYMENT', label: 'Payment' },
  { value: 'JOURNAL_ENTRY', label: 'Journal Entry' },
  { value: 'LOAN_APPLICATION', label: 'Loan Application' },
  { value: 'LOAN_SANCTION', label: 'Loan Sanction' },
  { value: 'LOAN_RATING', label: 'Loan Rating' },
];

const STATUS_STYLES: Record<WorkflowInstanceStatus, { bg: string; icon: JSX.Element }> = {
  PENDING: {
    bg: 'bg-slate-50 text-slate-700',
    icon: <Clock className="mr-1 h-3 w-3" />,
  },
  IN_PROGRESS: {
    bg: 'bg-blue-50 text-blue-700',
    icon: <Activity className="mr-1 h-3 w-3" />,
  },
  APPROVED: {
    bg: 'bg-emerald-50 text-emerald-700',
    icon: <CheckCircle className="mr-1 h-3 w-3" />,
  },
  REJECTED: {
    bg: 'bg-red-50 text-red-700',
    icon: <XCircle className="mr-1 h-3 w-3" />,
  },
  CANCELLED: {
    bg: 'bg-slate-100 text-slate-500',
    icon: <XCircle className="mr-1 h-3 w-3" />,
  },
  ESCALATED: {
    bg: 'bg-orange-50 text-orange-700',
    icon: <AlertTriangle className="mr-1 h-3 w-3" />,
  },
};

function StatusBadge({ status }: { status: WorkflowInstanceStatus }): JSX.Element {
  const style = STATUS_STYLES[status];
  return (
    <Badge className={`${style.bg} hover:${style.bg} flex items-center`}>
      {style.icon}
      {status.replace(/_/g, ' ')}
    </Badge>
  );
}

function EntityBadge({ entity }: { entity: WorkflowEntityType }): JSX.Element {
  const colors: Record<string, string> = {
    LOAN_APPLICATION: 'bg-blue-50 text-blue-700',
    LOAN_SANCTION: 'bg-indigo-50 text-indigo-700',
    LOAN_RATING: 'bg-violet-50 text-violet-700',
    VOUCHER: 'bg-emerald-50 text-emerald-700',
    PURCHASE_BILL: 'bg-orange-50 text-orange-700',
    SALES_INVOICE: 'bg-cyan-50 text-cyan-700',
    PAYMENT: 'bg-amber-50 text-amber-700',
    JOURNAL_ENTRY: 'bg-purple-50 text-purple-700',
  };
  const cls = colors[entity] ?? 'bg-slate-50 text-slate-700';
  return <Badge className={`${cls} hover:${cls}`}>{entity.replace(/_/g, ' ')}</Badge>;
}

function formatDateTime(dateString: string | null): string {
  if (!dateString) return '—';
  return new Date(dateString).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

const ACTIVE_STATUSES: WorkflowInstanceStatus[] = ['PENDING', 'IN_PROGRESS', 'ESCALATED'];
const TERMINAL_STATUSES: WorkflowInstanceStatus[] = ['APPROVED', 'REJECTED', 'CANCELLED'];

export function WorkflowInstanceList(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const definitionId = searchParams.get('definition_id');
  const { toast } = useToast();
  const { activeOrganizationId } = useOrganization();

  const [activeTab, setActiveTab] = useState<'active' | 'completed' | 'all'>('active');
  const [entityFilter, setEntityFilter] = useState<WorkflowEntityType | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [cancelTarget, setCancelTarget] = useState<WorkflowInstanceResponse | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const filters = activeOrganizationId
    ? {
        ...(entityFilter !== 'all' && { entityType: entityFilter }),
        page: 1,
        pageSize: 100,
      }
    : undefined;

  const instancesQuery = useWorkflowInstances(filters);
  const cancelMutation = useCancelInstance();

  const allInstances = useMemo(() => instancesQuery.data?.items ?? [], [instancesQuery.data?.items]);

  const filteredInstances = useMemo(() => {
    let next = allInstances;
    if (activeTab === 'active') {
      next = next.filter((i) => ACTIVE_STATUSES.includes(i.status));
    } else if (activeTab === 'completed') {
      next = next.filter((i) => TERMINAL_STATUSES.includes(i.status));
    }
    if (definitionId) {
      next = next.filter((i) => i.workflowDefinitionId === definitionId);
    }
    const q = searchQuery.trim().toLowerCase();
    if (q) {
      next = next.filter(
        (i) =>
          i.entityReference.toLowerCase().includes(q) ||
          (i.workflowName ?? '').toLowerCase().includes(q) ||
          (i.initiatorName ?? '').toLowerCase().includes(q),
      );
    }
    return next;
  }, [allInstances, activeTab, definitionId, searchQuery]);

  const activeCount = allInstances.filter((i) => ACTIVE_STATUSES.includes(i.status)).length;
  const escalatedCount = allInstances.filter((i) => i.status === 'ESCALATED').length;
  const rejectedCount = allInstances.filter((i) => i.status === 'REJECTED').length;
  const completedCount = allInstances.filter((i) => i.status === 'APPROVED').length;

  const confirmCancel = () => {
    if (!cancelTarget) return;
    const reason = cancelReason.trim();
    if (!reason) {
      toast({
        title: 'Reason required',
        description: 'Please describe why this workflow is being cancelled.',
        variant: 'destructive',
      });
      return;
    }
    cancelMutation.mutate(
      { id: cancelTarget.id, body: { reason } },
      {
        onSuccess: () => {
          toast({
            title: 'Workflow cancelled',
            description: `${cancelTarget.entityReference} has been cancelled.`,
          });
          setCancelTarget(null);
          setCancelReason('');
        },
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow Instances"
        subtitle="Track all running and completed workflow instances"
        actions={
          <Button
            variant="outline"
            onClick={() => instancesQuery.refetch()}
            disabled={instancesQuery.isFetching}
          >
            {instancesQuery.isFetching ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Refresh
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Instances</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{activeCount}</div>
            <p className="text-xs text-muted-foreground">Pending completion</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escalated</CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{escalatedCount}</div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rejected</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{rejectedCount}</div>
            <p className="text-xs text-muted-foreground">Failed approvals</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{completedCount}</div>
            <p className="text-xs text-muted-foreground">Completed workflows</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList>
          <TabsTrigger value="active">Active ({activeCount})</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="all">All Instances</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab}>
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Workflow Instances</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search..."
                      className="w-[200px] pl-8"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select
                    value={entityFilter}
                    onValueChange={(v) => setEntityFilter(v as WorkflowEntityType | 'all')}
                  >
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Entity Type" />
                    </SelectTrigger>
                    <SelectContent>
                      {ENTITY_TYPES.map((t) => (
                        <SelectItem key={t.value} value={t.value}>
                          {t.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {!activeOrganizationId ? (
                <EmptyState
                  title="Select an organization"
                  subtitle="Switch to an organization to view its workflow instances."
                />
              ) : instancesQuery.isLoading ? (
                <SkeletonTable rows={6} columns={7} />
              ) : instancesQuery.isError ? (
                <ErrorState error={instancesQuery.error} onRetry={() => instancesQuery.refetch()} />
              ) : filteredInstances.length === 0 ? (
                <EmptyState
                  title="No workflow instances found"
                  subtitle="Submit an item that triggers a workflow to populate this list."
                  icon={GitBranch}
                />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Entity</TableHead>
                      <TableHead>Workflow</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Current Step</TableHead>
                      <TableHead>Initiator</TableHead>
                      <TableHead>Started</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredInstances.map((instance) => (
                      <TableRow key={instance.id}>
                        <TableCell>
                          <p className="font-medium">{instance.entityReference}</p>
                        </TableCell>
                        <TableCell>
                          <p className="text-sm">{instance.workflowName ?? '—'}</p>
                        </TableCell>
                        <TableCell>
                          <EntityBadge entity={instance.entityType} />
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="text-sm font-medium">
                              {instance.currentStepName ?? '—'}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Step {instance.currentStepNumber}
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">{instance.initiatorName ?? '—'}</span>
                        </TableCell>
                        <TableCell className="text-sm tabular-nums">
                          {formatDateTime(instance.startedAt)}
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={instance.status} />
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => navigate(`/admin/workflow/instances/${instance.id}`)}
                              >
                                <Eye className="mr-2 h-4 w-4" />
                                View Details
                              </DropdownMenuItem>
                              {ACTIVE_STATUSES.includes(instance.status) && (
                                <>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    className="text-red-600"
                                    onClick={() => {
                                      setCancelTarget(instance);
                                      setCancelReason('');
                                    }}
                                  >
                                    Cancel Instance
                                  </DropdownMenuItem>
                                </>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <ConfirmDialog
        open={cancelTarget !== null}
        onOpenChange={(open) => {
          if (!open) {
            setCancelTarget(null);
            setCancelReason('');
          }
        }}
        title="Cancel workflow instance?"
        description={
          <div className="space-y-3">
            <p>
              This will cancel <span className="font-medium">{cancelTarget?.entityReference}</span>{' '}
              and stop all pending approvals. This cannot be undone.
            </p>
            <Textarea
              placeholder="Reason for cancellation (required)"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              rows={3}
            />
          </div>
        }
        variant="destructive"
        confirmLabel="Cancel Workflow"
        cancelLabel="Keep Running"
        loading={cancelMutation.isPending}
        onConfirm={confirmCancel}
      />
    </div>
  );
}
