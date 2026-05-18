/**
 * useLoanAccount — detail query for /lending/loan-accounts/{id}.
 *
 * Wire format is camelCase per Pydantic CamelSchema. Monetary + rate
 * fields are JSON strings (Pydantic Decimal — CLAUDE.md §6.2).
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';

export interface LoanAccountView {
  id: string;
  loanAccountNumber: string;
  status: string;
  entityId: string;
  entityName: string | null;
  entityLegalName: string | null;
  entityPan: string | null;
  entityCode: string | null;
  productId: string;
  productName: string | null;
  productCode: string | null;
  productCategory: string | null;
  sanctionId: string;
  sanctionedAmount: string;
  totalDisbursedAmount: string;
  undisbursedAmount: string;
  principalOutstanding: string;
  interestOutstanding: string;
  penalInterestOutstanding: string;
  chargesOutstanding: string;
  totalOutstanding: string;
  interestType: string;
  currentInterestRate: string;
  penalInterestRate: string;
  currentBaseRate: string | null;
  spreadBps: number;
  repaymentFrequency: string;
  repaymentMode: string;
  dayCountConvention: string;
  tenureMonths: number;
  moratoriumMonths: number;
  moratoriumEndDate: string | null;
  accountOpenDate: string;
  firstDisbursementDate: string | null;
  repaymentStartDate: string | null;
  maturityDate: string | null;
  lastRateResetDate: string | null;
  nextRateResetDate: string | null;
  daysPastDue: number;
  assetClassification: string;
  npaDate: string | null;
  currentEmiAmount: string | null;
  createdAt: string;
}

export function useLoanAccount(id: string | undefined) {
  return useQuery<LoanAccountView>({
    queryKey: ['lending', 'loan-accounts', id] as const,
    queryFn: async () => {
      const { data } = await api.get<LoanAccountView>(`/lending/loan-accounts/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
