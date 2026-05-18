/**
 * Treasury lender react-query hooks (CLAUDE.md §5.4).
 *
 * Pages consume these hooks only; the service layer owns HTTP details.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createLender,
  getLender,
  getLenders,
  type CreateLenderRequest,
  type LenderDetail,
  updateLender,
} from '@/services/lending/treasuryApi';
import type { LenderListItem, PaginatedResponse } from '@/types/lending';

export interface LenderFilters {
  search?: string;
  lenderType?: string;
  page?: number;
  pageSize?: number;
}

export const lendersBaseKey = ['lending', 'treasury', 'lenders'] as const;

export const lendersQueryKey = (filters?: LenderFilters) =>
  [...lendersBaseKey, 'list', filters ?? {}] as const;

export const lenderQueryKey = (id: string) => [...lendersBaseKey, 'detail', id] as const;

export function useLenders(filters?: LenderFilters) {
  return useQuery<PaginatedResponse<LenderListItem>>({
    queryKey: lendersQueryKey(filters),
    queryFn: () => getLenders(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useLender(id: string | undefined) {
  return useQuery<LenderDetail>({
    queryKey: lenderQueryKey(id ?? ''),
    queryFn: () => getLender(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useCreateLender() {
  const queryClient = useQueryClient();

  return useMutation<LenderDetail, unknown, CreateLenderRequest>({
    mutationFn: (payload) => createLender(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: lendersBaseKey });
    },
  });
}

export function useUpdateLender() {
  const queryClient = useQueryClient();

  return useMutation<
    LenderDetail,
    unknown,
    { lenderId: string; payload: Partial<CreateLenderRequest> }
  >({
    mutationFn: ({ lenderId, payload }) => updateLender(lenderId, payload),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: lendersBaseKey });
      void queryClient.invalidateQueries({ queryKey: lenderQueryKey(variables.lenderId) });
    },
  });
}
