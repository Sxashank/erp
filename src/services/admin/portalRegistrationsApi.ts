/**
 * Admin Portal Registrations API
 *
 * Wraps the admin-side queue for borrower portal registrations.  These are
 * tenant-scoped, RLS-protected, authenticated endpoints — the standard
 * `api` axios instance carries the access token + organization context.
 *
 * Mutations (approve / reject) carry `Idempotency-Key` per CLAUDE.md §6.3
 * (these gate a user's first access to the portal — financial-adjacent).
 */

import api from '@/services/api';

export type PortalRegistrationStatus = 'PENDING_APPROVAL' | 'ACTIVE' | 'REJECTED';

export type EntityMatchStrength =
  | 'EXACT_LOAN_ACCOUNT'
  | 'EXACT_CIN'
  | 'EXACT_GSTIN'
  | 'EXACT_PAN'
  | 'EXACT_LLPIN'
  | 'FUZZY_NAME';

export interface AdminRegistrationListItem {
  portalUserId: string;
  registrationReference: string;
  registrationStatus: PortalRegistrationStatus;
  requestedCin: string | null;
  requestedGstin: string | null;
  requestedLlpin: string | null;
  requestedPan: string | null;
  requestedLoanAccountNumber: string | null;
  requestedSanctionedAmount: string | null;
  authorizedSignatoryName: string;
  mobile: string;
  email: string;
  registeredAt: string;
  approvedAt: string | null;
  rejectionReason: string | null;
}

export interface EntitySuggestion {
  entityId: string;
  legalName: string;
  cin: string | null;
  gstin: string | null;
  pan: string | null;
  llpin: string | null;
  loanAccountNumber: string | null;
  sanctionedAmount: string | null;
  matchStrength: EntityMatchStrength;
}

export interface AdminRegistrationDetail extends AdminRegistrationListItem {
  suggestedEntities: EntitySuggestion[];
  linkedEntityIds: string[];
}

export interface AdminRegistrationListResponse {
  items: AdminRegistrationListItem[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ApproveRegistrationBody {
  entityIds: string[];
}

export interface RejectRegistrationBody {
  reason: string;
}

function idempotencyHeaders(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

export const adminPortalRegistrationsApi = {
  list: (params: { status?: PortalRegistrationStatus; page?: number; pageSize?: number }) =>
    api.get<AdminRegistrationListResponse>('/admin/portal-registrations', {
      params,
    }),

  get: (id: string) => api.get<AdminRegistrationDetail>(`/admin/portal-registrations/${id}`),

  approve: (id: string, body: ApproveRegistrationBody) =>
    api.post<AdminRegistrationDetail>(`/admin/portal-registrations/${id}/approve`, body, {
      headers: idempotencyHeaders(),
    }),

  reject: (id: string, body: RejectRegistrationBody) =>
    api.post<AdminRegistrationDetail>(`/admin/portal-registrations/${id}/reject`, body, {
      headers: idempotencyHeaders(),
    }),
};

export default adminPortalRegistrationsApi;
