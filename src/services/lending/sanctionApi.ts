/**
 * Sanction API Service
 * API calls for Loan Sanction management
 */

import api from '../api';
import type {
  LoanSanction,
  SanctionCondition,
  SanctionFilters,
  PaginatedResponse,
} from '@/types/lending';

const BASE_URL = '/lending/sanctions';

// ============== Sanction CRUD ==============

export async function getSanctions(filters?: SanctionFilters): Promise<PaginatedResponse<LoanSanction>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.application_id) params.append('application_id', filters.application_id);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<LoanSanction>>(`${BASE_URL}?${params.toString()}`);
  return response.data;
}

export async function getSanction(sanctionId: string): Promise<LoanSanction> {
  const response = await api.get<LoanSanction>(`${BASE_URL}/${sanctionId}`);
  return response.data;
}

export async function createSanction(applicationId: string, data: Partial<LoanSanction>): Promise<LoanSanction> {
  const response = await api.post<LoanSanction>(BASE_URL, { application_id: applicationId, ...data });
  return response.data;
}

export async function updateSanction(sanctionId: string, data: Partial<LoanSanction>): Promise<LoanSanction> {
  const response = await api.put<LoanSanction>(`${BASE_URL}/${sanctionId}`, data);
  return response.data;
}

// ============== Sanction Conditions ==============

export async function getSanctionConditions(sanctionId: string): Promise<SanctionCondition[]> {
  const response = await api.get<SanctionCondition[]>(`${BASE_URL}/${sanctionId}/conditions`);
  return response.data;
}

export async function addSanctionCondition(
  sanctionId: string,
  data: Omit<SanctionCondition, 'condition_id' | 'sanction_id'>
): Promise<SanctionCondition> {
  const response = await api.post<SanctionCondition>(`${BASE_URL}/${sanctionId}/conditions`, data);
  return response.data;
}

export async function updateSanctionCondition(
  sanctionId: string,
  conditionId: string,
  data: Partial<SanctionCondition>
): Promise<SanctionCondition> {
  const response = await api.put<SanctionCondition>(
    `${BASE_URL}/${sanctionId}/conditions/${conditionId}`,
    data
  );
  return response.data;
}

export async function deleteSanctionCondition(sanctionId: string, conditionId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${sanctionId}/conditions/${conditionId}`);
}

export async function markConditionComplied(
  sanctionId: string,
  conditionId: string,
  data: { remarks?: string; document_path?: string }
): Promise<SanctionCondition> {
  const response = await api.post<SanctionCondition>(
    `${BASE_URL}/${sanctionId}/conditions/${conditionId}/comply`,
    data
  );
  return response.data;
}

// ============== Workflow Actions ==============

export async function submitSanction(sanctionId: string, remarks?: string): Promise<LoanSanction> {
  const response = await api.post<LoanSanction>(`${BASE_URL}/${sanctionId}/submit`, { remarks });
  return response.data;
}

export async function approveSanction(
  sanctionId: string,
  data: { action: 'APPROVE' | 'REJECT' | 'RETURN'; remarks: string }
): Promise<LoanSanction> {
  const response = await api.post<LoanSanction>(`${BASE_URL}/${sanctionId}/approve`, data);
  return response.data;
}

export async function acceptSanction(
  sanctionId: string,
  data: { accepted: boolean; remarks?: string }
): Promise<LoanSanction> {
  const response = await api.post<LoanSanction>(`${BASE_URL}/${sanctionId}/accept`, data);
  return response.data;
}

// ============== Sanction Letter ==============

export async function generateSanctionLetter(sanctionId: string): Promise<{ document_url: string }> {
  const response = await api.post<{ document_url: string }>(`${BASE_URL}/${sanctionId}/letter/generate`);
  return response.data;
}

export async function getSanctionLetter(sanctionId: string): Promise<Blob> {
  const response = await api.get<Blob>(`${BASE_URL}/${sanctionId}/letter`, {
    responseType: 'blob',
  });
  return response.data;
}

// ============== Export all functions ==============

export const sanctionApi = {
  // Sanction CRUD
  getSanctions,
  getSanction,
  createSanction,
  updateSanction,

  // Conditions
  getSanctionConditions,
  addSanctionCondition,
  updateSanctionCondition,
  deleteSanctionCondition,
  markConditionComplied,

  // Workflow
  submitSanction,
  approveSanction,
  acceptSanction,

  // Letter
  generateSanctionLetter,
  getSanctionLetter,
};

export default sanctionApi;
