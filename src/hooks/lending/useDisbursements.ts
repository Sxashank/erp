/**
 * useDisbursements — list query + mutation hooks for /lending/disbursements.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * Mutations send the BE-required `Idempotency-Key` header (CLAUDE.md §6.3 —
 * the BE idempotency middleware lists `lending/disbursements` as a financial
 * mutation resource). See CLAUDE.md §5.4 for hook conventions.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  approveDisbursementRequest,
  createDisbursement,
  getDisbursements,
  processDisbursementRequest,
  rejectDisbursementRequest,
  verifyDisbursementConditions,
  type ApprovalBody,
  type DisbursementActionResponse,
  type DisbursementCreateBody,
  type DisbursementCreateResponse,
  type DisbursementListItem,
  type ProcessBody,
  type RejectBody,
  type VerifyConditionsBody,
  type VerifyConditionsResponse,
} from '@/services/lending/disbursementApi';
import type { DisbursementFilters, PaginatedResponse } from '@/types/lending';

export const disbursementsQueryKey = (filters?: DisbursementFilters) =>
  ['lending', 'disbursements', filters ?? {}] as const;

export const disbursementQueryKey = (id: string) => ['lending', 'disbursement', id] as const;

export function useDisbursements(filters?: DisbursementFilters) {
  return useQuery<PaginatedResponse<DisbursementListItem>>({
    queryKey: disbursementsQueryKey(filters),
    queryFn: () => getDisbursements(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

/**
 * Invalidate the disbursement list + the specific record. Used by every
 * mutation so the screens that depend on this data refetch automatically.
 */
function invalidateDisbursement(queryClient: ReturnType<typeof useQueryClient>, id?: string) {
  queryClient.invalidateQueries({ queryKey: ['lending', 'disbursements'] });
  if (id) {
    queryClient.invalidateQueries({ queryKey: disbursementQueryKey(id) });
  }
}

/**
 * `POST /lending/disbursements/` — create a new disbursement request.
 */
export function useCreateDisbursement() {
  const queryClient = useQueryClient();
  return useMutation<DisbursementCreateResponse, unknown, DisbursementCreateBody>({
    mutationFn: (body) => createDisbursement(body),
    onSuccess: (data) => invalidateDisbursement(queryClient, data.id),
  });
}

/**
 * `POST /lending/disbursements/approve` — approve a disbursement request.
 */
export function useApproveDisbursement() {
  const queryClient = useQueryClient();
  return useMutation<DisbursementActionResponse, unknown, ApprovalBody>({
    mutationFn: (body) => approveDisbursementRequest(body),
    onSuccess: (data) => invalidateDisbursement(queryClient, data.disbursementId),
  });
}

/**
 * `POST /lending/disbursements/verify-conditions` — mark manual
 * pre-disbursement conditions as verified.
 */
export function useVerifyDisbursementConditions() {
  const queryClient = useQueryClient();
  return useMutation<VerifyConditionsResponse, unknown, VerifyConditionsBody>({
    mutationFn: (body) => verifyDisbursementConditions(body),
    onSuccess: (data) => invalidateDisbursement(queryClient, data.disbursementId),
  });
}

/**
 * `POST /lending/disbursements/reject` — reject a disbursement request.
 */
export function useRejectDisbursement() {
  const queryClient = useQueryClient();
  return useMutation<DisbursementActionResponse, unknown, RejectBody>({
    mutationFn: (body) => rejectDisbursementRequest(body),
    onSuccess: (data) => invalidateDisbursement(queryClient, data.disbursementId),
  });
}

/**
 * `POST /lending/disbursements/process` — release funds for an approved
 * disbursement.
 */
export function useProcessDisbursement() {
  const queryClient = useQueryClient();
  return useMutation<DisbursementActionResponse, unknown, ProcessBody>({
    mutationFn: (body) => processDisbursementRequest(body),
    onSuccess: (data) => invalidateDisbursement(queryClient, data.disbursementId),
  });
}
