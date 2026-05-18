/**
 * Sanction API Service
 *
 * The list endpoint emits camelCase via Pydantic CamelSchema on the
 * backend (`response_model_by_alias=True`) — no client-side mapping.
 */

import api from '../api';

import type {
  LoanSanction,
  SanctionCondition,
  SanctionFilters,
  PaginatedResponse,
  SanctionStatus,
} from '@/types/lending';

const BASE_URL = '/lending/sanctions';

// ============== List item (matches LoanSanctionListResponse) ==============

// Monetary + rate fields are JSON strings on the wire (Pydantic Decimal —
// CLAUDE.md §6.2). Pass directly to <AmountDisplay>/<PercentageDisplay>
// (both accept `string`) or coerce via `Number(...)` for display sums.
export interface SanctionListItem {
  id: string;
  sanctionNumber: string;
  applicationId: string;
  applicationNumber: string | null;
  entityId: string;
  entityName: string | null;
  productId: string;
  productName: string | null;
  sanctionedAmount: string;
  effectiveRate: string;
  tenureMonths: number;
  sanctionDate: string;
  validityDate: string;
  status: SanctionStatus;
}

// ============== Sanction CRUD ==============

export interface SanctionConditionCreatePayload {
  conditionType: 'PRE_DISBURSEMENT' | 'POST_DISBURSEMENT' | 'ONGOING' | 'EVENT_BASED';
  category: 'LEGAL' | 'FINANCIAL' | 'SECURITY' | 'REGULATORY' | 'OPERATIONAL' | 'PROJECT';
  description: string;
  detailedRequirement?: string;
  isMandatory?: boolean;
  blocksDisbursement?: boolean;
  frequency?: string;
  displayOrder?: number;
}

export interface SanctionSecurityCreatePayload {
  securityCategory: 'PRIMARY' | 'COLLATERAL' | 'GUARANTEE';
  securityType: string;
  chargeType?: string;
  description: string;
  marketValue?: number;
  forcedSaleValue?: number;
  acceptableValue: number;
  marginPercentage?: number;
}

export interface SanctionCreatePayload {
  applicationId: string;
  sanctionedAmount: number;
  tenureMonths: number;
  moratoriumMonths?: number;
  interestType: 'FIXED' | 'FLOATING';
  spreadBps?: number;
  effectiveRate: number;
  repaymentMode: string;
  repaymentFrequency: string;
  dayCountConvention?: string;
  disbursementType?: string;
  maxTranches?: number;
  sanctionDate: string;
  validityDate: string;
  specialTerms?: string;
  remarks?: string;
  conditions?: SanctionConditionCreatePayload[];
  securities?: SanctionSecurityCreatePayload[];
}

export type SanctionUpdatePayload = Partial<
  Omit<SanctionCreatePayload, 'applicationId' | 'conditions' | 'securities'>
>;

export async function getSanctions(
  filters?: SanctionFilters,
): Promise<PaginatedResponse<SanctionListItem>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entityId) params.append('entity_id', filters.entityId);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.dateFrom) params.append('from_date', filters.dateFrom);
  if (filters?.dateTo) params.append('to_date', filters.dateTo);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('page_size', filters.pageSize.toString());

  const response = await api.get<PaginatedResponse<SanctionListItem>>(
    `${BASE_URL}?${params.toString()}`,
  );
  return response.data;
}

export async function getSanction(sanctionId: string): Promise<LoanSanction> {
  const response = await api.get<LoanSanction>(`${BASE_URL}/${sanctionId}`);
  return response.data;
}

export async function createSanction(
  applicationId: string,
  data: Omit<SanctionCreatePayload, 'applicationId'>,
): Promise<LoanSanction> {
  const response = await api.post<LoanSanction>(BASE_URL, { applicationId, ...data });
  return response.data;
}

export async function updateSanction(
  sanctionId: string,
  data: SanctionUpdatePayload,
): Promise<LoanSanction> {
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
  data: Omit<SanctionCondition, 'id' | 'sanctionId' | 'createdAt' | 'updatedAt' | 'isActive'>,
): Promise<SanctionCondition> {
  const response = await api.post<SanctionCondition>(`${BASE_URL}/${sanctionId}/conditions`, data);
  return response.data;
}

export async function updateSanctionCondition(
  conditionId: string,
  data: Partial<SanctionCondition>,
): Promise<SanctionCondition> {
  const response = await api.put<SanctionCondition>(`${BASE_URL}/conditions/${conditionId}`, data);
  return response.data;
}

export async function markConditionComplied(
  conditionId: string,
  data: { compliedOn: string; remarks?: string; documentPath?: string },
): Promise<SanctionCondition> {
  const params = new URLSearchParams({
    complied_on: data.compliedOn,
  });
  if (data.remarks) params.append('remarks', data.remarks);
  if (data.documentPath) params.append('document_path', data.documentPath);

  const response = await api.post<SanctionCondition>(
    `${BASE_URL}/conditions/${conditionId}/comply?${params.toString()}`,
  );
  return response.data;
}

// ============== Workflow Actions ==============

export async function submitSanction(sanctionId: string, remarks?: string): Promise<LoanSanction> {
  const params = new URLSearchParams();
  if (remarks) params.append('remarks', remarks);
  const query = params.toString();
  const response = await api.post<LoanSanction>(
    `${BASE_URL}/${sanctionId}/submit${query ? `?${query}` : ''}`,
  );
  return response.data;
}

export async function approveSanction(
  sanctionId: string,
  data: { remarks?: string },
): Promise<LoanSanction> {
  const params = new URLSearchParams();
  if (data.remarks) params.append('remarks', data.remarks);
  const query = params.toString();
  const response = await api.post<LoanSanction>(
    `${BASE_URL}/${sanctionId}/approve${query ? `?${query}` : ''}`,
  );
  return response.data;
}

export async function acceptSanction(
  sanctionId: string,
  data: { acceptanceDate: string; documentPath?: string },
): Promise<LoanSanction> {
  const params = new URLSearchParams({
    acceptance_date: data.acceptanceDate,
  });
  if (data.documentPath) params.append('document_path', data.documentPath);
  const response = await api.post<LoanSanction>(
    `${BASE_URL}/${sanctionId}/accept?${params.toString()}`,
  );
  return response.data;
}

// ============== Sanction Letter ==============

export async function generateSanctionLetter(
  sanctionId: string,
): Promise<{ document_url: string }> {
  const response = await api.post<{ document_url: string }>(
    `${BASE_URL}/${sanctionId}/letter/generate`,
  );
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
