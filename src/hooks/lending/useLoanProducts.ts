/**
 * useLoanProducts — list query for /lending/products.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type ProductCategoryValue =
  | 'TERM_LOAN'
  | 'WORKING_CAPITAL'
  | 'PROJECT_FINANCE'
  | 'LAP'
  | 'EQUIPMENT_FINANCE'
  | 'BILL_DISCOUNTING';

export type InterestTypeValue = 'FIXED' | 'FLOATING' | 'HYBRID';

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Coerce via `Number(...)` for display arithmetic.
export interface LoanProductListItem {
  id: string;
  code: string;
  name: string;
  category: ProductCategoryValue;
  interestType: InterestTypeValue;
  minAmount: string;
  maxAmount: string;
  minTenureMonths: number;
  maxTenureMonths: number;
  isActive: boolean;
  baseRateValue: string | null;
  spreadBps: number;
  processingFeePercent: string | null;
  status: string | null;
}

export interface LoanProductFilters {
  search?: string;
  category?: ProductCategoryValue;
  interestType?: InterestTypeValue;
  includeInactive?: boolean;
  page?: number;
  pageSize?: number;
}

export const loanProductsQueryKey = (filters?: LoanProductFilters) =>
  ['lending', 'products', filters ?? {}] as const;

async function fetchProducts(filters?: LoanProductFilters) {
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.category) params.append('category', filters.category);
  if (filters?.interestType) params.append('interest_type', filters.interestType);
  if (filters?.includeInactive) params.append('include_inactive', String(filters.includeInactive));
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<LoanProductListItem>>(
    `/lending/products?${params.toString()}`,
  );
  return data;
}

export function useLoanProducts(filters?: LoanProductFilters) {
  return useQuery<PaginatedResponse<LoanProductListItem>>({
    queryKey: loanProductsQueryKey(filters),
    queryFn: () => fetchProducts(filters),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
