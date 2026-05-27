/**
 * useEntities — list query for /lending/entities.
 *
 * Wire format is camelCase per Pydantic CamelSchema.
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type EntityTypeValue = string;

export type EntityStatusValue = 'PROSPECT' | 'ACTIVE' | 'INACTIVE' | 'BLACKLISTED';

export type RiskCategoryValue = string;

export interface EntityListItem {
  id: string;
  entityCode: string;
  entityType: EntityTypeValue;
  legalName: string;
  tradeName: string | null;
  pan: string;
  gstin: string | null;
  industrySector: string | null;
  internalRating: string | null;
  riskCategory: RiskCategoryValue | null;
  status: EntityStatusValue;
  isActive: boolean;
  createdAt: string | null;
}

export interface EntityFilters {
  search?: string;
  entityType?: EntityTypeValue;
  status?: EntityStatusValue;
  riskCategory?: RiskCategoryValue;
  includeInactive?: boolean;
  page?: number;
  pageSize?: number;
}

export const entitiesQueryKey = (filters?: EntityFilters) =>
  ['lending', 'entities', filters ?? {}] as const;

async function fetchEntities(filters?: EntityFilters) {
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.entityType) params.append('entityType', filters.entityType);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.riskCategory) params.append('riskCategory', filters.riskCategory);
  if (filters?.includeInactive) params.append('includeInactive', String(filters.includeInactive));
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('pageSize', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<EntityListItem>>(
    `/lending/entities?${params.toString()}`,
  );
  return data;
}

export function useEntities(filters?: EntityFilters) {
  return useQuery<PaginatedResponse<EntityListItem>>({
    queryKey: entitiesQueryKey(filters),
    queryFn: () => fetchEntities(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
