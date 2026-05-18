import { zodResolver } from '@hookform/resolvers/zod';
import { Copy, Loader2, Pencil, Plus, Send } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';

import {
  DataTable,
  DateDisplay,
  FilterBar,
  FormSection,
  FormShell,
  PageHeader,
  StatusPill,
  type Column,
} from '@/components/common';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
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
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useAdminPortalUser,
  useAdminPortalUsers,
  useCreateAdminPortalUser,
  useInviteAdminPortalUser,
  useUpdateAdminPortalUser,
} from '@/hooks/admin/usePortalUsers';
import { useEntities } from '@/hooks/lending/useEntities';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import {
  createPortalUserSchema,
  type CreatePortalUserInput,
} from '@/schemas/admin/portalUserSchema';
import type {
  AdminPortalInviteResponse,
  AdminPortalUserDetail,
  AdminPortalUserListItem,
  PortalActorRole,
  PortalUserStatus,
} from '@/services/admin/portalUsersApi';

const ROLE_OPTIONS: { value: PortalActorRole; label: string }[] = [
  { value: 'scheme_borrower', label: 'Borrower' },
  { value: 'scheme_lender', label: 'Lender' },
  { value: 'scheme_smfcl_reviewer', label: 'SMFCL Reviewer' },
  { value: 'scheme_smfcl_approver', label: 'SMFCL Approver' },
  { value: 'scheme_ministry_viewer', label: 'Ministry Viewer' },
  { value: 'scheme_admin', label: 'Scheme Admin' },
];

const STATUS_OPTIONS: { value: PortalUserStatus; label: string }[] = [
  { value: 'ACTIVE', label: 'Active' },
  { value: 'INACTIVE', label: 'Inactive' },
  { value: 'SUSPENDED', label: 'Suspended' },
  { value: 'BLOCKED', label: 'Blocked' },
];

const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi' },
];

const EMPTY_FORM_VALUES: CreatePortalUserInput = {
  mobile: '',
  email: '',
  displayName: '',
  actorRole: 'scheme_borrower',
  preferredLanguage: 'en',
  status: 'ACTIVE',
  linkedEntityIds: [],
};

function formatRole(role: string): string {
  return role
    .replace(/^scheme_/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .replace('Smfcl', 'SMFCL');
}

function mapDetailToForm(detail: AdminPortalUserDetail): CreatePortalUserInput {
  return {
    mobile: detail.mobile,
    email: detail.email ?? '',
    displayName: detail.displayName ?? '',
    actorRole: detail.actorRole,
    preferredLanguage: detail.preferredLanguage ?? 'en',
    status: detail.status,
    linkedEntityIds: detail.linkedEntityIds ?? [],
  };
}

export default function AdminPortalUsers(): JSX.Element {
  const [search, setSearch] = useState('');
  const [actorRole, setActorRole] = useState<PortalActorRole | 'ALL'>('ALL');
  const [status, setStatus] = useState<PortalUserStatus | 'ALL'>('ALL');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');

  const query = useAdminPortalUsers({
    actorRole: actorRole === 'ALL' ? undefined : actorRole,
    status: status === 'ALL' ? undefined : status,
    search: search.trim() || undefined,
    page: 1,
    pageSize: 50,
  });

  const columns: Column<AdminPortalUserListItem>[] = useMemo(
    () => [
      {
        key: 'displayName',
        header: 'Portal user',
        render: (row) => (
          <div>
            <div className="font-medium">{row.displayName ?? 'Unnamed user'}</div>
            <div className="text-xs text-muted-foreground">{formatRole(row.actorRole)}</div>
          </div>
        ),
      },
      {
        key: 'contact',
        header: 'Contact',
        render: (row) => (
          <div>
            <div className="font-mono text-xs">{row.mobile}</div>
            <div className="text-xs text-muted-foreground">{row.email ?? 'No email on file'}</div>
          </div>
        ),
      },
      {
        key: 'linkedEntities',
        header: 'Linked entities',
        render: (row) => (
          <div>
            <div className="font-medium">{row.linkedEntities.length}</div>
            <div className="text-xs text-muted-foreground">
              {row.linkedEntities
                .slice(0, 2)
                .map((entity) => entity.legalName)
                .join(', ') || 'No entity links'}
            </div>
          </div>
        ),
      },
      {
        key: 'status',
        header: 'Access status',
        render: (row) => (
          <div className="space-y-1">
            <StatusPill type="entity" status={row.status} />
            <div className="text-xs text-muted-foreground">
              Registration {row.registrationStatus.replace(/_/g, ' ').toLowerCase()}
            </div>
          </div>
        ),
      },
      {
        key: 'lastLoginAt',
        header: 'Last login',
        render: (row) => <DateDisplay date={row.lastLoginAt ?? row.createdAt} />,
        sortable: true,
        sortValue: (row) => row.lastLoginAt ?? row.createdAt,
      },
      {
        key: 'actions',
        header: '',
        align: 'right',
        render: (row) => (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => {
              setDialogMode('edit');
              setEditingUserId(row.portalUserId);
              setIsDialogOpen(true);
            }}
          >
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
        ),
      },
    ],
    [],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scheme Portal Users"
        subtitle="Provision borrower, lender, SMFCL, ministry, and admin actors inside the current tenant."
        breadcrumbs={[{ label: 'Administration' }, { label: 'Portal Users' }]}
        actions={
          <Button
            type="button"
            className="bg-emerald-600 hover:bg-emerald-700"
            onClick={() => {
              setDialogMode('create');
              setEditingUserId(null);
              setIsDialogOpen(true);
            }}
          >
            <Plus className="mr-2 h-4 w-4" />
            New portal user
          </Button>
        }
      />

      <FilterBar
        search={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search by mobile, email, or display name"
        onClear={() => {
          setSearch('');
          setActorRole('ALL');
          setStatus('ALL');
        }}
      >
        <div className="flex items-center gap-2">
          <Label htmlFor="actor-role-filter" className="text-sm">
            Actor role
          </Label>
          <Select
            value={actorRole}
            onValueChange={(value) => setActorRole(value as PortalActorRole | 'ALL')}
          >
            <SelectTrigger id="actor-role-filter" className="w-[220px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All roles</SelectItem>
              {ROLE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="portal-status-filter" className="text-sm">
            Status
          </Label>
          <Select
            value={status}
            onValueChange={(value) => setStatus(value as PortalUserStatus | 'ALL')}
          >
            <SelectTrigger id="portal-status-filter" className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All statuses</SelectItem>
              {STATUS_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </FilterBar>

      <DataTable<AdminPortalUserListItem>
        data={query.data?.items ?? []}
        columns={columns}
        getRowId={(row) => row.portalUserId}
        isLoading={query.isLoading}
        error={query.isError ? query.error : undefined}
        onRetry={() => query.refetch()}
        emptyTitle="No scheme portal users"
        emptySubtitle="Create borrower or internal actor accounts for this tenant to start the integrated portal workflows."
      />

      {isDialogOpen && (
        <PortalUserDialog
          mode={dialogMode}
          portalUserId={editingUserId}
          onClose={() => {
            setIsDialogOpen(false);
            setEditingUserId(null);
          }}
        />
      )}
    </div>
  );
}

function PortalUserDialog({
  mode,
  portalUserId,
  onClose,
}: {
  mode: 'create' | 'edit';
  portalUserId: string | null;
  onClose: () => void;
}): JSX.Element {
  const isEdit = mode === 'edit';
  const { toast } = useToast();
  const detailQuery = useAdminPortalUser(isEdit ? (portalUserId ?? undefined) : undefined);
  const entitiesQuery = useEntities({ includeInactive: false, pageSize: 200 });
  const createMutation = useCreateAdminPortalUser();
  const inviteMutation = useInviteAdminPortalUser();
  const updateMutation = useUpdateAdminPortalUser();
  const [invitePreview, setInvitePreview] = useState<AdminPortalInviteResponse | null>(null);

  const form = useForm<CreatePortalUserInput>({
    resolver: zodResolver(createPortalUserSchema),
    defaultValues: EMPTY_FORM_VALUES,
  });

  const entityOptions = useMemo(
    () =>
      (entitiesQuery.data?.items ?? [])
        .filter((entity) => entity.entityType !== 'INDIVIDUAL')
        .sort((left, right) => left.legalName.localeCompare(right.legalName)),
    [entitiesQuery.data?.items],
  );

  useEffect(() => {
    if (!isEdit) {
      form.reset(EMPTY_FORM_VALUES);
      setInvitePreview(null);
      return;
    }
    if (detailQuery.data) {
      form.reset(mapDetailToForm(detailQuery.data));
      setInvitePreview(null);
    }
  }, [detailQuery.data, form, isEdit]);

  const actorRole = form.watch('actorRole');
  const isSaving = createMutation.isPending || updateMutation.isPending;
  const isInternalActor = actorRole !== 'scheme_borrower';

  async function handleInvite(): Promise<void> {
    if (!portalUserId) return;
    try {
      const invite = await inviteMutation.mutateAsync(portalUserId);
      setInvitePreview(invite);
      toast({
        title: 'Activation link prepared',
        description: 'Share the generated activation URL with the internal actor.',
      });
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  async function onSubmit(values: CreatePortalUserInput): Promise<void> {
    try {
      if (isEdit && portalUserId) {
        await updateMutation.mutateAsync({
          id: portalUserId,
          body: {
            email: values.email || null,
            displayName: values.displayName,
            actorRole: values.actorRole,
            preferredLanguage: values.preferredLanguage,
            status: values.status,
            linkedEntityIds: values.linkedEntityIds,
          },
        });
        toast({
          title: 'Portal user updated',
          description: 'Access scope and role assignment were saved.',
        });
      } else {
        await createMutation.mutateAsync({
          mobile: values.mobile,
          email: values.email || null,
          displayName: values.displayName,
          actorRole: values.actorRole,
          preferredLanguage: values.preferredLanguage,
          status: values.status,
          linkedEntityIds: values.linkedEntityIds,
        });
        toast({
          title: 'Portal user created',
          description: 'The actor can now use the scheme portal based on the assigned role.',
        });
      }
      onClose();
    } catch (error) {
      showErrorToast(error, toast);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-4xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit portal user' : 'Create portal user'}</DialogTitle>
          <DialogDescription>
            Borrower actors must be linked only to institutional borrower entities. Internal scheme
            actors can be provisioned here without self-registration.
          </DialogDescription>
        </DialogHeader>

        {isEdit && detailQuery.isLoading && !detailQuery.data ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-1/3" />
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : (
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormShell
                footer={
                  <>
                    <Button type="button" variant="outline" onClick={onClose}>
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      className="bg-emerald-600 hover:bg-emerald-700"
                      disabled={isSaving}
                    >
                      {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                      {isEdit ? 'Save changes' : 'Create portal user'}
                    </Button>
                  </>
                }
              >
                <FormSection
                  title="Identity and access"
                  description="Define the actor’s sign-in identity, scheme role, and current access state. Internal actors use email/password after invite activation."
                >
                  <FormField
                    control={form.control}
                    name="displayName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Display name</FormLabel>
                        <FormControl>
                          <Input placeholder="SMFCL Review Officer" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="mobile"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Mobile number</FormLabel>
                        <FormControl>
                          <Input placeholder="9876543210" {...field} disabled={isEdit} />
                        </FormControl>
                        <FormDescription>
                          {isEdit
                            ? 'Mobile number is fixed after creation to preserve portal session identity.'
                            : 'Used for portal OTP and sign-in.'}
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email address</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="officer@smfcl.gov.in"
                            {...field}
                            value={field.value ?? ''}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="actorRole"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Actor role</FormLabel>
                        <Select
                          value={field.value}
                          onValueChange={(value) => field.onChange(value as PortalActorRole)}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Choose role" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {ROLE_OPTIONS.map((option) => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
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
                    name="status"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Portal status</FormLabel>
                        <Select
                          value={field.value}
                          onValueChange={(value) => field.onChange(value as PortalUserStatus)}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Choose status" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {STATUS_OPTIONS.map((option) => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
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
                    name="preferredLanguage"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Preferred language</FormLabel>
                        <Select value={field.value} onValueChange={field.onChange}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Choose language" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {LANGUAGE_OPTIONS.map((option) => (
                              <SelectItem key={option.value} value={option.value}>
                                {option.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </FormSection>

                <FormSection
                  title="Entity links"
                  description="Borrower actors require at least one linked institutional entity. Internal actors can stay unlinked until queue scoping rules are finalized."
                >
                  <FormField
                    control={form.control}
                    name="linkedEntityIds"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Accessible borrower entities</FormLabel>
                        <div className="rounded-lg border">
                          <ScrollArea className="h-56">
                            <div className="space-y-3 p-4">
                              {entitiesQuery.isLoading ? (
                                <div className="space-y-2">
                                  <Skeleton className="h-10 w-full" />
                                  <Skeleton className="h-10 w-full" />
                                  <Skeleton className="h-10 w-full" />
                                </div>
                              ) : entityOptions.length === 0 ? (
                                <p className="text-sm text-muted-foreground">
                                  No institutional borrower entities are available in this tenant
                                  yet.
                                </p>
                              ) : (
                                entityOptions.map((entity) => {
                                  const checked = field.value.includes(entity.id);
                                  const checkboxId = `portal-entity-${entity.id}`;
                                  return (
                                    <div
                                      key={entity.id}
                                      className="flex items-start gap-3 rounded-md border p-3"
                                    >
                                      <Checkbox
                                        id={checkboxId}
                                        checked={checked}
                                        onCheckedChange={(nextChecked) => {
                                          const nextIds = nextChecked
                                            ? [...field.value, entity.id]
                                            : field.value.filter((value) => value !== entity.id);
                                          field.onChange(nextIds);
                                        }}
                                      />
                                      <Label
                                        htmlFor={checkboxId}
                                        className="min-w-0 cursor-pointer"
                                      >
                                        <div className="font-medium">{entity.legalName}</div>
                                        <div className="text-xs text-muted-foreground">
                                          {entity.entityCode} · {entity.entityType}
                                        </div>
                                      </Label>
                                    </div>
                                  );
                                })
                              )}
                            </div>
                          </ScrollArea>
                        </div>
                        <FormDescription>
                          {actorRole === 'scheme_borrower'
                            ? 'Required for borrower self-service access.'
                            : 'Optional today for internal roles; leave blank for tenant-wide queue access.'}
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </FormSection>

                {isEdit && detailQuery.data ? (
                  <FormSection
                    title="Current verification state"
                    description="Operational flags from the current portal user record."
                  >
                    <ReadOnlyItem
                      label="Registration status"
                      value={detailQuery.data.registrationStatus}
                    />
                    <ReadOnlyItem
                      label="Approved at"
                      value={detailQuery.data.approvedAt ?? 'Not approved'}
                    />
                    <ReadOnlyItem
                      label="Mobile verification"
                      value={detailQuery.data.mobileVerified ? 'Verified' : 'Pending'}
                    />
                    <ReadOnlyItem
                      label="Email verification"
                      value={detailQuery.data.emailVerified ? 'Verified' : 'Pending'}
                    />
                    <ReadOnlyItem
                      label="Two-factor authentication"
                      value={detailQuery.data.is2faEnabled ? 'Enabled' : 'Disabled'}
                    />
                    <ReadOnlyItem
                      label="Password login"
                      value={
                        detailQuery.data.passwordLoginEnabled ? 'Enabled' : 'Pending activation'
                      }
                    />
                    <ReadOnlyItem
                      label="Invite status"
                      value={
                        detailQuery.data.invitePending
                          ? `Pending until ${detailQuery.data.inviteExpiresAt ?? 'expiry not available'}`
                          : detailQuery.data.activatedAt
                            ? `Activated ${detailQuery.data.activatedAt}`
                            : 'No active invite'
                      }
                    />
                    <ReadOnlyItem
                      label="Last login"
                      value={detailQuery.data.lastLoginAt ?? 'No successful sign-in yet'}
                    />
                  </FormSection>
                ) : null}

                {isEdit && detailQuery.data && isInternalActor ? (
                  <FormSection
                    title="Activation link"
                    description="Generate or rotate the invite link for lender, SMFCL, ministry, and scheme-admin actors."
                  >
                    <div className="flex flex-wrap gap-3 md:col-span-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => void handleInvite()}
                        disabled={inviteMutation.isPending || !detailQuery.data.email}
                      >
                        {inviteMutation.isPending ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="mr-2 h-4 w-4" />
                        )}
                        {detailQuery.data.invitePending ? 'Regenerate invite' : 'Generate invite'}
                      </Button>
                      {!detailQuery.data.email ? (
                        <p className="text-sm text-muted-foreground">
                          Add an email address before generating an invite.
                        </p>
                      ) : null}
                    </div>

                    {invitePreview ? (
                      <div className="space-y-3 rounded-lg border bg-slate-50 p-4 md:col-span-2">
                        <ReadOnlyItem label="Invite expiry" value={invitePreview.inviteExpiresAt} />
                        <div className="space-y-2">
                          <Label htmlFor="portal-activation-url">Activation URL</Label>
                          <div className="flex gap-2">
                            <Input
                              id="portal-activation-url"
                              value={invitePreview.activationUrl}
                              readOnly
                            />
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() =>
                                void navigator.clipboard.writeText(invitePreview.activationUrl)
                              }
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </FormSection>
                ) : null}
              </FormShell>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}

function ReadOnlyItem({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-medium">{value}</div>
    </div>
  );
}
