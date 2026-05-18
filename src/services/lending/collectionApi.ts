import api from '../api';

import type { FollowUpFilters, FollowUpListItem } from '@/hooks/lending/useFollowUps';
import type { LegalCaseFilters, LegalCaseListItem } from '@/hooks/lending/useLegalCases';
import type { NPAFilters, NPAAccountListItem } from '@/hooks/lending/useNPAAccounts';
import type { OTSFilters, OTSProposalListItem } from '@/hooks/lending/useOTSProposals';
import type { RestructureFilters, RestructureListItem } from '@/hooks/lending/useRestructures';
import type { PaginatedResponse } from '@/types/lending';

const BASE_URL = '/lending/collections';

function appendPaging(params: URLSearchParams, page?: number, pageSize?: number) {
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
}

export async function getFollowUps(
  filters?: FollowUpFilters,
): Promise<PaginatedResponse<FollowUpListItem>> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  appendPaging(params, filters?.page, filters?.pageSize);
  const response = await api.get<PaginatedResponse<FollowUpListItem>>(
    `${BASE_URL}/follow-ups?${params.toString()}`,
  );
  return response.data;
}

export async function getNPAAccounts(
  filters?: NPAFilters,
): Promise<PaginatedResponse<NPAAccountListItem>> {
  const params = new URLSearchParams();
  if (filters?.classification) params.append('classification', filters.classification);
  appendPaging(params, filters?.page, filters?.pageSize);
  const response = await api.get<PaginatedResponse<NPAAccountListItem>>(
    `${BASE_URL}/npa-accounts?${params.toString()}`,
  );
  return response.data;
}

export async function getOTSProposals(
  filters?: OTSFilters,
): Promise<PaginatedResponse<OTSProposalListItem>> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  appendPaging(params, filters?.page, filters?.pageSize);
  const response = await api.get<PaginatedResponse<OTSProposalListItem>>(
    `${BASE_URL}/ots-proposals?${params.toString()}`,
  );
  return response.data;
}

export async function getRestructures(
  filters?: RestructureFilters,
): Promise<PaginatedResponse<RestructureListItem>> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  appendPaging(params, filters?.page, filters?.pageSize);
  const response = await api.get<PaginatedResponse<RestructureListItem>>(
    `${BASE_URL}/restructures?${params.toString()}`,
  );
  return response.data;
}

export async function getLegalCases(
  filters?: LegalCaseFilters,
): Promise<PaginatedResponse<LegalCaseListItem>> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.caseType) params.append('case_type', filters.caseType);
  appendPaging(params, filters?.page, filters?.pageSize);
  const response = await api.get<PaginatedResponse<LegalCaseListItem>>(
    `${BASE_URL}/legal-cases?${params.toString()}`,
  );
  return response.data;
}

export const collectionApi = {
  getFollowUps,
  getNPAAccounts,
  getOTSProposals,
  getRestructures,
  getLegalCases,
};

export default collectionApi;
