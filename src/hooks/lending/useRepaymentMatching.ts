import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createMatchedReceipt,
  getRepaymentMatchCandidates,
  getRepaymentMatchingSummary,
  type CreateMatchedReceiptBody,
  type CreateMatchedReceiptResponse,
  type RepaymentMatchingFilters,
  type RepaymentMatchingResponse,
  type RepaymentMatchingSummary,
} from '@/services/lending/repaymentMatchingApi';

export const repaymentMatchingSummaryQueryKey = (filters: RepaymentMatchingFilters = {}) =>
  ['lending', 'repayment-matching', 'summary', filters] as const;

export const repaymentMatchingCandidatesQueryKey = (filters: RepaymentMatchingFilters = {}) =>
  ['lending', 'repayment-matching', 'candidates', filters] as const;

export function useRepaymentMatchingSummary(filters: RepaymentMatchingFilters = {}) {
  return useQuery<RepaymentMatchingSummary>({
    queryKey: repaymentMatchingSummaryQueryKey(filters),
    queryFn: () => getRepaymentMatchingSummary(filters),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}

export function useRepaymentMatchCandidates(filters: RepaymentMatchingFilters = {}) {
  return useQuery<RepaymentMatchingResponse>({
    queryKey: repaymentMatchingCandidatesQueryKey(filters),
    queryFn: () => getRepaymentMatchCandidates(filters),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}

export function useCreateMatchedReceipt() {
  const queryClient = useQueryClient();
  return useMutation<
    CreateMatchedReceiptResponse,
    unknown,
    { statementId: string; body?: CreateMatchedReceiptBody }
  >({
    mutationFn: ({ statementId, body }) => createMatchedReceipt(statementId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['lending', 'repayment-matching'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'receipts'] });
      void queryClient.invalidateQueries({ queryKey: ['lending', 'dashboard'] });
    },
  });
}
