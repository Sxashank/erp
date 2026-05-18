import api from '@/services/api';

export type PortalActorRole =
  | 'scheme_borrower'
  | 'scheme_lender'
  | 'scheme_smfcl_reviewer'
  | 'scheme_smfcl_approver'
  | 'scheme_ministry_viewer'
  | 'scheme_admin';

export type PortalUserStatus = 'ACTIVE' | 'INACTIVE' | 'SUSPENDED' | 'BLOCKED';

export type PortalRegistrationStatus = 'PENDING_APPROVAL' | 'ACTIVE' | 'REJECTED';

export interface AdminPortalUserEntityLink {
  entityId: string;
  legalName: string;
}

export interface AdminPortalUserListItem {
  portalUserId: string;
  mobile: string;
  email?: string | null;
  displayName?: string | null;
  actorRole: PortalActorRole;
  registrationStatus: PortalRegistrationStatus;
  status: PortalUserStatus;
  linkedEntityIds: string[];
  linkedEntities: AdminPortalUserEntityLink[];
  lastLoginAt?: string | null;
  createdAt: string;
}

export interface AdminPortalUserDetail extends AdminPortalUserListItem {
  preferredLanguage?: string | null;
  approvedAt?: string | null;
  approvedBy?: string | null;
  mobileVerified: boolean;
  emailVerified: boolean;
  is2faEnabled: boolean;
  passwordLoginEnabled: boolean;
  invitePending: boolean;
  invitedAt?: string | null;
  inviteExpiresAt?: string | null;
  activatedAt?: string | null;
}

export interface AdminPortalUserListResponse {
  items: AdminPortalUserListItem[];
  total: number;
  page: number;
  pageSize: number;
}

export interface AdminPortalInviteResponse {
  portalUserId: string;
  email: string;
  inviteExpiresAt: string;
  activationToken: string;
  activationUrl: string;
}

export interface CreateAdminPortalUserBody {
  mobile: string;
  email?: string | null;
  displayName: string;
  actorRole: PortalActorRole;
  preferredLanguage?: string;
  status?: PortalUserStatus;
  linkedEntityIds: string[];
}

export interface UpdateAdminPortalUserBody {
  email?: string | null;
  displayName?: string | null;
  actorRole?: PortalActorRole;
  preferredLanguage?: string | null;
  status?: PortalUserStatus;
  linkedEntityIds?: string[];
}

function idempotencyHeaders(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

export const adminPortalUsersApi = {
  list: (params?: {
    actorRole?: PortalActorRole;
    status?: PortalUserStatus;
    search?: string;
    page?: number;
    pageSize?: number;
  }) => api.get<AdminPortalUserListResponse>('/admin/portal-users', { params }),

  get: (id: string) => api.get<AdminPortalUserDetail>(`/admin/portal-users/${id}`),

  create: (body: CreateAdminPortalUserBody) =>
    api.post<AdminPortalUserDetail>('/admin/portal-users', body, {
      headers: idempotencyHeaders(),
    }),

  update: (id: string, body: UpdateAdminPortalUserBody) =>
    api.patch<AdminPortalUserDetail>(`/admin/portal-users/${id}`, body, {
      headers: idempotencyHeaders(),
    }),

  invite: (id: string) =>
    api.post<AdminPortalInviteResponse>(`/admin/portal-users/${id}/invite`, undefined, {
      headers: idempotencyHeaders(),
    }),
};

export default adminPortalUsersApi;
