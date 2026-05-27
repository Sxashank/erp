/**
 * useLoanProduct — detail query for /lending/products/{id}.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';

export interface LoanProductDetail {
  id: string;
  organizationId: string;
  code: string;
  name: string;
  description?: string | null;
  category: string;
  subCategory?: string | null;
  minAmount: string | number;
  maxAmount: string | number;
  minTenureMonths: number;
  maxTenureMonths: number;
  defaultTenureMonths?: number | null;
  allowsMoratorium: boolean;
  maxMoratoriumMonths?: number | null;
  interestType: string;
  minSpreadBps: number;
  maxSpreadBps: number;
  defaultSpreadBps: number;
  minEffectiveRate?: string | number | null;
  maxEffectiveRate?: string | number | null;
  rateResetFrequency?: string | null;
  dayCountConvention: string;
  allowedRepaymentFrequencies: string[];
  defaultRepaymentFrequency: string;
  allowedRepaymentModes: string[];
  defaultRepaymentMode: string;
  allowsPrepayment: boolean;
  prepaymentLockInMonths?: number | null;
  allowsForeclosure: boolean;
  foreclosureLockInMonths?: number | null;
  requiresCollateral: boolean;
  minCollateralCoverage?: string | number | null;
  requiresGuarantee: boolean;
  effectiveFrom: string;
  isActive: boolean;
  createdAt: string;
  updatedAt?: string | null;
}

export function useLoanProduct(id: string | undefined) {
  return useQuery<LoanProductDetail>({
    queryKey: ['lending', 'products', id] as const,
    queryFn: async () => {
      const { data } = await api.get<LoanProductDetail>(`/lending/products/${id}`);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
