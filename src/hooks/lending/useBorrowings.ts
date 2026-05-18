/**
 * Treasury borrowing react-query hooks (CLAUDE.md §5.4).
 *
 * Borrowing detail screens compose these hooks instead of calling the
 * treasury service directly from the page.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createBorrowing,
  getBorrowing,
  getBorrowingSchedule,
  getBorrowings,
  getRepaymentHistory,
  getTranches,
  recordDrawdown,
  recordRepayment,
  updateBorrowing,
  type BorrowingDetail,
  type BorrowingListItem,
  type BorrowingRepayment,
  type BorrowingScheduleEntry,
  type BorrowingTranche,
  type CreateBorrowingRequest,
} from '@/services/lending/treasuryApi';
import type { PaginatedResponse } from '@/types/lending';

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Coerce via `Number(...)` for display-only sums.
export type { BorrowingListItem };

export interface BorrowingFilters {
  lenderId?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}

export const borrowingsBaseKey = ['lending', 'treasury', 'borrowings'] as const;

export const borrowingsQueryKey = (filters?: BorrowingFilters) =>
  [...borrowingsBaseKey, 'list', filters ?? {}] as const;

export const borrowingQueryKey = (id: string) => [...borrowingsBaseKey, 'detail', id] as const;

export const borrowingTranchesQueryKey = (id: string) =>
  [...borrowingsBaseKey, 'tranches', id] as const;

export const borrowingScheduleQueryKey = (id: string) =>
  [...borrowingsBaseKey, 'schedule', id] as const;

export const borrowingPaymentsQueryKey = (id: string) =>
  [...borrowingsBaseKey, 'payments', id] as const;

export function useBorrowings(filters?: BorrowingFilters) {
  return useQuery<PaginatedResponse<BorrowingListItem>>({
    queryKey: borrowingsQueryKey(filters),
    queryFn: () => getBorrowings(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useBorrowing(id: string | undefined) {
  return useQuery<BorrowingDetail>({
    queryKey: borrowingQueryKey(id ?? ''),
    queryFn: () => getBorrowing(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useBorrowingTranches(id: string | undefined) {
  return useQuery<BorrowingTranche[]>({
    queryKey: borrowingTranchesQueryKey(id ?? ''),
    queryFn: () => getTranches(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useBorrowingSchedule(id: string | undefined) {
  return useQuery<BorrowingScheduleEntry[]>({
    queryKey: borrowingScheduleQueryKey(id ?? ''),
    queryFn: () => getBorrowingSchedule(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useBorrowingPayments(id: string | undefined) {
  return useQuery<BorrowingRepayment[]>({
    queryKey: borrowingPaymentsQueryKey(id ?? ''),
    queryFn: () => getRepaymentHistory(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useCreateBorrowing() {
  const queryClient = useQueryClient();

  return useMutation<BorrowingDetail, unknown, CreateBorrowingRequest>({
    mutationFn: (payload) => createBorrowing(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: borrowingsBaseKey });
    },
  });
}

export function useUpdateBorrowing() {
  const queryClient = useQueryClient();

  return useMutation<
    BorrowingDetail,
    unknown,
    { borrowingId: string; payload: Partial<CreateBorrowingRequest> }
  >({
    mutationFn: ({ borrowingId, payload }) => updateBorrowing(borrowingId, payload),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: borrowingsBaseKey });
      void queryClient.invalidateQueries({
        queryKey: borrowingQueryKey(variables.borrowingId),
      });
    },
  });
}

export function useRecordDrawdown() {
  const queryClient = useQueryClient();

  return useMutation<
    BorrowingTranche,
    unknown,
    {
      borrowingId: string;
      amount: number;
      drawdownDate: string;
      interestRate?: number;
      remarks?: string;
    }
  >({
    mutationFn: ({ borrowingId, ...payload }) => recordDrawdown(borrowingId, payload),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: borrowingsBaseKey });
      void queryClient.invalidateQueries({
        queryKey: borrowingQueryKey(variables.borrowingId),
      });
      void queryClient.invalidateQueries({
        queryKey: borrowingTranchesQueryKey(variables.borrowingId),
      });
    },
  });
}

export function useRecordBorrowingPayment() {
  const queryClient = useQueryClient();

  return useMutation<
    BorrowingRepayment,
    unknown,
    {
      borrowingId: string;
      trancheId?: string;
      paymentDate: string;
      principalAmount: number;
      interestAmount: number;
      referenceNumber?: string;
      remarks?: string;
    }
  >({
    mutationFn: ({ borrowingId, ...payload }) => recordRepayment(borrowingId, payload),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: borrowingsBaseKey });
      void queryClient.invalidateQueries({
        queryKey: borrowingQueryKey(variables.borrowingId),
      });
      void queryClient.invalidateQueries({
        queryKey: borrowingPaymentsQueryKey(variables.borrowingId),
      });
      void queryClient.invalidateQueries({
        queryKey: borrowingScheduleQueryKey(variables.borrowingId),
      });
    },
  });
}
