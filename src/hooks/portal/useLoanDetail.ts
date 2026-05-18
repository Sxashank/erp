/**
 * Portal loan-detail hooks.
 *
 *  - `usePortalLoan(loanId)`            → GET /portal/loans/:id
 *  - `usePortalLoanSchedule(loanId)`    → GET /portal/loans/:id/schedule
 *  - `usePortalLoanPayments(loanId)`    → GET /portal/loans/:id/payments
 *
 * Server state per CLAUDE.md §5.4 — replaces hand-rolled useEffect+useState
 * data-loading in `src/pages/portal/PortalLoanDetail.tsx`.
 */

import { useQuery } from '@tanstack/react-query';

import { portalDashboardApi } from '@/services/portalApi';
import type {
  LoanDetail,
  PaymentHistory,
  RepaymentScheduleItem,
} from '@/types/portal';

export const portalLoanQueryKey = (loanId: string) =>
  ['portal', 'loan', loanId] as const;

export const portalLoanScheduleQueryKey = (loanId: string) =>
  ['portal', 'loan', loanId, 'schedule'] as const;

export const portalLoanPaymentsQueryKey = (loanId: string) =>
  ['portal', 'loan', loanId, 'payments'] as const;

export function usePortalLoan(loanId: string | undefined) {
  return useQuery<LoanDetail>({
    queryKey: portalLoanQueryKey(loanId ?? ''),
    queryFn: async () => {
      const res = await portalDashboardApi.getLoan(loanId as string);
      return res.data as LoanDetail;
    },
    enabled: Boolean(loanId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalLoanSchedule(loanId: string | undefined) {
  return useQuery<RepaymentScheduleItem[]>({
    queryKey: portalLoanScheduleQueryKey(loanId ?? ''),
    queryFn: async () => {
      const res = await portalDashboardApi.getLoanSchedule(loanId as string);
      return res.data as RepaymentScheduleItem[];
    },
    enabled: Boolean(loanId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function usePortalLoanPayments(loanId: string | undefined) {
  return useQuery<PaymentHistory[]>({
    queryKey: portalLoanPaymentsQueryKey(loanId ?? ''),
    queryFn: async () => {
      const res = await portalDashboardApi.getLoanPayments(loanId as string);
      return res.data as PaymentHistory[];
    },
    enabled: Boolean(loanId),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
