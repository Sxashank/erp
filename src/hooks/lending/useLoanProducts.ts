/**
 * useLoanProducts — list query for /lending/products.
 *
 * Wire format is camelCase per Pydantic CamelSchema on the BE.
 * See CLAUDE.md §5.4.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import api from '@/services/api';
import {
  productApi,
  type LoanProductMutationPayload,
  type LoanProductMutationResponse,
} from '@/services/lending/productApi';
import type { PaginatedResponse } from '@/types/lending';

export type ProductCategoryValue = string;

export type InterestTypeValue = string;

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
  const pageSize =
    typeof filters?.pageSize === 'number' ? Math.min(filters.pageSize, 100) : undefined;
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.category) params.append('category', filters.category);
  if (filters?.interestType) params.append('interestType', filters.interestType);
  if (filters?.includeInactive) params.append('includeInactive', String(filters.includeInactive));
  if (filters?.page) params.append('page', String(filters.page));
  if (pageSize) params.append('pageSize', String(pageSize));
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

export function useCreateLoanProduct() {
  const queryClient = useQueryClient();
  return useMutation<LoanProductMutationResponse, unknown, LoanProductMutationPayload>({
    mutationFn: (payload) => productApi.createProduct(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lending', 'products'] });
    },
  });
}

export function useUpdateLoanProduct() {
  const queryClient = useQueryClient();
  return useMutation<
    LoanProductMutationResponse,
    unknown,
    { productId: string; payload: Partial<LoanProductMutationPayload> }
  >({
    mutationFn: ({ productId, payload }) => productApi.updateProduct(productId, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['lending', 'products'] });
      queryClient.invalidateQueries({ queryKey: ['lending', 'products', variables.productId] });
    },
  });
}
