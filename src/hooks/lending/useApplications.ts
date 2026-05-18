/**
 * useApplications — list query for /lending/applications.
 *
 * Wire format is camelCase per Pydantic CamelSchema. Monetary fields are
 * JSON strings (Pydantic Decimal — CLAUDE.md §6.2).
 */

import { useQuery } from '@tanstack/react-query';

import api from '@/services/api';
import type { PaginatedResponse } from '@/types/lending';

export type ApplicationStageValue =
  | 'LEAD'
  | 'APPLICATION'
  | 'APPRAISAL'
  | 'SANCTION'
  | 'POST_SANCTION'
  | 'DISBURSED'
  | 'CLOSED';

export type ApplicationStatusValue =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'ADDITIONAL_INFO_REQUIRED'
  | 'SANCTIONED'
  | 'REJECTED'
  | 'WITHDRAWN';

export interface ApplicationListItem {
  id: string;
  applicationNumber: string;
  entityId: string;
  entityName: string | null;
  productId: string;
  productName: string | null;
  requestedAmount: string;
  requestedTenureMonths: number;
  stage: ApplicationStageValue;
  status: ApplicationStatusValue;
  priority: string;
  submittedAt: string | null;
  createdAt: string;
}

export interface ApplicationFilters {
  search?: string;
  entityId?: string;
  productId?: string;
  stage?: ApplicationStageValue;
  status?: ApplicationStatusValue;
  fromDate?: string;
  toDate?: string;
  page?: number;
  pageSize?: number;
}

export const applicationsQueryKey = (filters?: ApplicationFilters) =>
  ['lending', 'applications', filters ?? {}] as const;

async function fetchApplications(filters?: ApplicationFilters) {
  const params = new URLSearchParams();
  if (filters?.search) params.append('search', filters.search);
  if (filters?.entityId) params.append('entity_id', filters.entityId);
  if (filters?.productId) params.append('product_id', filters.productId);
  if (filters?.stage) params.append('stage', filters.stage);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.fromDate) params.append('from_date', filters.fromDate);
  if (filters?.toDate) params.append('to_date', filters.toDate);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));
  const { data } = await api.get<PaginatedResponse<ApplicationListItem>>(
    `/lending/applications?${params.toString()}`,
  );
  return data;
}

export function useApplications(filters?: ApplicationFilters) {
  return useQuery<PaginatedResponse<ApplicationListItem>>({
    queryKey: applicationsQueryKey(filters),
    queryFn: () => fetchApplications(filters),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}
