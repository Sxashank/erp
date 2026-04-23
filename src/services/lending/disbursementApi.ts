/**
 * Disbursement API Service
 * API calls for Loan Disbursement management
 */

import api from '../api';
import type {
  Disbursement,
  DisbursementFilters,
  PaginatedResponse,
} from '@/types/lending';

const BASE_URL = '/lending/disbursements';

// ============== Disbursement Request CRUD ==============

export async function getDisbursements(filters?: DisbursementFilters): Promise<PaginatedResponse<Disbursement>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.loan_account_id) params.append('loan_account_id', filters.loan_account_id);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<Disbursement>>(`${BASE_URL}?${params.toString()}`);
  return response.data;
}

export async function getDisbursement(disbursementId: string): Promise<Disbursement> {
  const response = await api.get<Disbursement>(`${BASE_URL}/${disbursementId}`);
  return response.data;
}

export interface CreateDisbursementRequest {
  loan_account_id: string;
  tranche_number?: number;
  requested_amount: number;
  disbursement_date: string;
  bank_account_id: string;
  purpose?: string;
  milestone_id?: string;
  remarks?: string;
}

export async function createDisbursementRequest(data: CreateDisbursementRequest): Promise<Disbursement> {
  const response = await api.post<Disbursement>(`${BASE_URL}/request`, data);
  return response.data;
}

export async function updateDisbursementRequest(
  disbursementId: string,
  data: Partial<CreateDisbursementRequest>
): Promise<Disbursement> {
  const response = await api.put<Disbursement>(`${BASE_URL}/${disbursementId}`, data);
  return response.data;
}

export async function deleteDisbursementRequest(disbursementId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${disbursementId}`);
}

// ============== Condition Verification ==============

export async function getPendingConditions(loanAccountId: string): Promise<Array<{
  condition_id: string;
  condition_type: 'PRE_DISBURSEMENT' | 'POST_DISBURSEMENT';
  description: string;
  is_complied: boolean;
  compliance_date?: string;
}>> {
  const response = await api.get(`${BASE_URL}/conditions/${loanAccountId}/pending`);
  return response.data;
}

export async function verifyCondition(
  conditionId: string,
  data: { is_complied: boolean; remarks?: string; document_path?: string }
): Promise<void> {
  await api.post(`${BASE_URL}/conditions/${conditionId}/verify`, data);
}

// ============== Workflow Actions ==============

export async function submitDisbursement(disbursementId: string, remarks?: string): Promise<Disbursement> {
  const response = await api.post<Disbursement>(`${BASE_URL}/${disbursementId}/submit`, { remarks });
  return response.data;
}

export async function approveDisbursement(
  disbursementId: string,
  data: { action: 'APPROVE' | 'REJECT' | 'RETURN'; remarks: string }
): Promise<Disbursement> {
  const response = await api.post<Disbursement>(`${BASE_URL}/${disbursementId}/approve`, data);
  return response.data;
}

// ============== Fund Transfer ==============

export async function initiateFundTransfer(
  disbursementId: string,
  data?: { payment_mode?: 'NEFT' | 'RTGS' | 'IMPS'; scheduled_time?: string }
): Promise<{
  transfer_id: string;
  status: string;
  utr_number?: string;
}> {
  const response = await api.post(`${BASE_URL}/${disbursementId}/transfer/initiate`, data);
  return response.data;
}

export async function getTransferStatus(disbursementId: string): Promise<{
  transfer_id: string;
  status: 'INITIATED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  utr_number?: string;
  failure_reason?: string;
  completed_at?: string;
}> {
  const response = await api.get(`${BASE_URL}/${disbursementId}/transfer/status`);
  return response.data;
}

export async function confirmDisbursement(
  disbursementId: string,
  data: { utr_number: string; disbursement_date: string; remarks?: string }
): Promise<Disbursement> {
  const response = await api.post<Disbursement>(`${BASE_URL}/${disbursementId}/confirm`, data);
  return response.data;
}

// ============== Tranche Management ==============

export async function getTranches(loanAccountId: string): Promise<Array<{
  tranche_number: number;
  sanctioned_amount: number;
  disbursed_amount: number;
  pending_amount: number;
  status: 'PENDING' | 'PARTIAL' | 'FULLY_DISBURSED';
  disbursements: Disbursement[];
}>> {
  const response = await api.get(`${BASE_URL}/tranches/${loanAccountId}`);
  return response.data;
}

export async function getDisbursementsByAccount(loanAccountId: string): Promise<Disbursement[]> {
  const response = await api.get<Disbursement[]>(`${BASE_URL}/account/${loanAccountId}`);
  return response.data;
}

// ============== Utilization Certificate ==============

export async function uploadUtilizationCertificate(
  disbursementId: string,
  formData: FormData
): Promise<{ document_id: string; document_url: string }> {
  const response = await api.post(`${BASE_URL}/${disbursementId}/utilization-certificate`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function getUtilizationCertificates(loanAccountId: string): Promise<Array<{
  document_id: string;
  disbursement_id: string;
  tranche_number: number;
  document_url: string;
  uploaded_at: string;
  verified: boolean;
}>> {
  const response = await api.get(`${BASE_URL}/utilization-certificates/${loanAccountId}`);
  return response.data;
}

// ============== Export all functions ==============

export const disbursementApi = {
  // CRUD
  getDisbursements,
  getDisbursement,
  createDisbursementRequest,
  updateDisbursementRequest,
  deleteDisbursementRequest,

  // Conditions
  getPendingConditions,
  verifyCondition,

  // Workflow
  submitDisbursement,
  approveDisbursement,

  // Fund Transfer
  initiateFundTransfer,
  getTransferStatus,
  confirmDisbursement,

  // Tranches
  getTranches,
  getDisbursementsByAccount,

  // Utilization
  uploadUtilizationCertificate,
  getUtilizationCertificates,
};

export default disbursementApi;
