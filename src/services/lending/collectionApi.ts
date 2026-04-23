/**
 * Collection API Service
 * API calls for Collections, NPA, OTS, and Legal management
 */

import api from '../api';
import type {
  CollectionFollowUp,
  NPARecord,
  OTSProposal,
  LegalCase,
  CollectionFilters,
  NPAFilters,
  OTSFilters,
  LegalCaseFilters,
  PaginatedResponse,
} from '@/types/lending';

const BASE_URL = '/lending/collections';

// ============== Follow-ups ==============

export async function getFollowUps(filters?: CollectionFilters): Promise<PaginatedResponse<CollectionFollowUp>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.loan_account_id) params.append('loan_account_id', filters.loan_account_id);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to);
  if (filters?.followup_type) params.append('followup_type', filters.followup_type);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<CollectionFollowUp>>(`${BASE_URL}/followups?${params.toString()}`);
  return response.data;
}

export async function getFollowUp(followUpId: string): Promise<CollectionFollowUp> {
  const response = await api.get<CollectionFollowUp>(`${BASE_URL}/followups/${followUpId}`);
  return response.data;
}

export interface CreateFollowUpRequest {
  loan_account_id: string;
  followup_type: 'CALL' | 'VISIT' | 'EMAIL' | 'SMS' | 'NOTICE' | 'LEGAL_NOTICE';
  scheduled_date: string;
  remarks?: string;
  assigned_to?: string;
}

export async function createFollowUp(data: CreateFollowUpRequest): Promise<CollectionFollowUp> {
  const response = await api.post<CollectionFollowUp>(`${BASE_URL}/followups`, data);
  return response.data;
}

export async function updateFollowUp(
  followUpId: string,
  data: Partial<CreateFollowUpRequest>
): Promise<CollectionFollowUp> {
  const response = await api.put<CollectionFollowUp>(`${BASE_URL}/followups/${followUpId}`, data);
  return response.data;
}

export async function recordFollowUpOutcome(
  followUpId: string,
  data: {
    outcome: 'PROMISE_TO_PAY' | 'PARTIAL_PAYMENT' | 'NO_RESPONSE' | 'DISPUTE' | 'OTHER';
    outcome_remarks: string;
    promise_date?: string;
    promise_amount?: number;
    next_followup_date?: string;
  }
): Promise<CollectionFollowUp> {
  const response = await api.post<CollectionFollowUp>(`${BASE_URL}/followups/${followUpId}/outcome`, data);
  return response.data;
}

export async function getFollowUpsByAccount(loanAccountId: string): Promise<CollectionFollowUp[]> {
  const response = await api.get<CollectionFollowUp[]>(`${BASE_URL}/followups/account/${loanAccountId}`);
  return response.data;
}

// ============== NPA Management ==============

export async function getNPAAccounts(filters?: NPAFilters): Promise<PaginatedResponse<NPARecord>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.classification) params.append('classification', filters.classification);
  if (filters?.branch_id) params.append('branch_id', filters.branch_id);
  if (filters?.dpd_from !== undefined) params.append('dpd_from', filters.dpd_from.toString());
  if (filters?.dpd_to !== undefined) params.append('dpd_to', filters.dpd_to.toString());
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<NPARecord>>(`${BASE_URL}/npa?${params.toString()}`);
  return response.data;
}

export async function getNPARecord(npaId: string): Promise<NPARecord> {
  const response = await api.get<NPARecord>(`${BASE_URL}/npa/${npaId}`);
  return response.data;
}

export async function runNPAIdentification(options?: {
  as_of_date?: string;
  dry_run?: boolean;
}): Promise<{
  accounts_identified: number;
  accounts_upgraded: number;
  accounts_downgraded: number;
  details: Array<{
    loan_account_id: string;
    loan_account_number: string;
    old_classification: string;
    new_classification: string;
    dpd: number;
  }>;
}> {
  const response = await api.post(`${BASE_URL}/npa/identify`, options);
  return response.data;
}

export async function requestNPAUpgrade(
  npaId: string,
  data: { remarks: string; supporting_documents?: string[] }
): Promise<NPARecord> {
  const response = await api.post<NPARecord>(`${BASE_URL}/npa/${npaId}/upgrade-request`, data);
  return response.data;
}

export async function approveNPAUpgrade(
  npaId: string,
  data: { action: 'APPROVE' | 'REJECT'; remarks: string }
): Promise<NPARecord> {
  const response = await api.post<NPARecord>(`${BASE_URL}/npa/${npaId}/upgrade-approve`, data);
  return response.data;
}

export async function getNPAMovement(
  month: number,
  year: number
): Promise<{
  opening_npa: number;
  opening_count: number;
  additions: number;
  additions_count: number;
  recoveries: number;
  recoveries_count: number;
  upgrades: number;
  upgrades_count: number;
  write_offs: number;
  write_offs_count: number;
  closing_npa: number;
  closing_count: number;
}> {
  const response = await api.get(`${BASE_URL}/npa/movement?month=${month}&year=${year}`);
  return response.data;
}

export async function getProvisioningSummary(): Promise<{
  total_npa: number;
  total_provision: number;
  coverage_ratio: number;
  by_classification: Array<{
    classification: string;
    outstanding: number;
    provision_rate: number;
    provision_amount: number;
    count: number;
  }>;
}> {
  const response = await api.get(`${BASE_URL}/npa/provisioning`);
  return response.data;
}

// ============== OTS (One-Time Settlement) ==============

export async function getOTSProposals(filters?: OTSFilters): Promise<PaginatedResponse<OTSProposal>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.loan_account_id) params.append('loan_account_id', filters.loan_account_id);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.date_from) params.append('date_from', filters.date_from);
  if (filters?.date_to) params.append('date_to', filters.date_to);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<OTSProposal>>(`${BASE_URL}/ots?${params.toString()}`);
  return response.data;
}

export async function getOTSProposal(otsId: string): Promise<OTSProposal> {
  const response = await api.get<OTSProposal>(`${BASE_URL}/ots/${otsId}`);
  return response.data;
}

export interface CreateOTSRequest {
  loan_account_id: string;
  settlement_amount: number;
  payment_mode: 'LUMPSUM' | 'STRUCTURED';
  settlement_period_months?: number;
  payment_schedule?: Array<{
    due_date: string;
    amount: number;
  }>;
  principal_waiver: number;
  interest_waiver: number;
  penal_waiver: number;
  charges_waiver: number;
  remarks?: string;
}

export async function createOTSProposal(data: CreateOTSRequest): Promise<OTSProposal> {
  const response = await api.post<OTSProposal>(`${BASE_URL}/ots`, data);
  return response.data;
}

export async function updateOTSProposal(otsId: string, data: Partial<CreateOTSRequest>): Promise<OTSProposal> {
  const response = await api.put<OTSProposal>(`${BASE_URL}/ots/${otsId}`, data);
  return response.data;
}

export async function submitOTSProposal(otsId: string, remarks?: string): Promise<OTSProposal> {
  const response = await api.post<OTSProposal>(`${BASE_URL}/ots/${otsId}/submit`, { remarks });
  return response.data;
}

export async function approveOTSProposal(
  otsId: string,
  data: { action: 'APPROVE' | 'REJECT' | 'RETURN'; remarks: string }
): Promise<OTSProposal> {
  const response = await api.post<OTSProposal>(`${BASE_URL}/ots/${otsId}/approve`, data);
  return response.data;
}

export async function recordOTSPayment(
  otsId: string,
  data: { receipt_id: string; amount: number; payment_date: string }
): Promise<OTSProposal> {
  const response = await api.post<OTSProposal>(`${BASE_URL}/ots/${otsId}/payment`, data);
  return response.data;
}

export async function closeOTS(
  otsId: string,
  data: { closure_type: 'SUCCESSFUL' | 'CANCELLED' | 'EXPIRED'; remarks?: string }
): Promise<OTSProposal> {
  const response = await api.post<OTSProposal>(`${BASE_URL}/ots/${otsId}/close`, data);
  return response.data;
}

// ============== Legal Cases ==============

export async function getLegalCases(filters?: LegalCaseFilters): Promise<PaginatedResponse<LegalCase>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.loan_account_id) params.append('loan_account_id', filters.loan_account_id);
  if (filters?.entity_id) params.append('entity_id', filters.entity_id);
  if (filters?.case_type) params.append('case_type', filters.case_type);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.court_name) params.append('court_name', filters.court_name);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<LegalCase>>(`${BASE_URL}/legal?${params.toString()}`);
  return response.data;
}

export async function getLegalCase(caseId: string): Promise<LegalCase> {
  const response = await api.get<LegalCase>(`${BASE_URL}/legal/${caseId}`);
  return response.data;
}

export interface CreateLegalCaseRequest {
  loan_account_id: string;
  case_type: 'SARFAESI' | 'DRT' | 'NCLT' | 'CIVIL' | 'CRIMINAL' | 'ARBITRATION';
  case_number?: string;
  court_name: string;
  filing_date: string;
  claim_amount: number;
  lawyer_name?: string;
  lawyer_contact?: string;
  remarks?: string;
}

export async function createLegalCase(data: CreateLegalCaseRequest): Promise<LegalCase> {
  const response = await api.post<LegalCase>(`${BASE_URL}/legal`, data);
  return response.data;
}

export async function updateLegalCase(caseId: string, data: Partial<CreateLegalCaseRequest>): Promise<LegalCase> {
  const response = await api.put<LegalCase>(`${BASE_URL}/legal/${caseId}`, data);
  return response.data;
}

export interface LegalHearing {
  hearing_id: string;
  case_id: string;
  hearing_date: string;
  hearing_type: string;
  outcome?: string;
  next_hearing_date?: string;
  remarks?: string;
  created_at: string;
}

export async function addHearing(
  caseId: string,
  data: Omit<LegalHearing, 'hearing_id' | 'case_id' | 'created_at'>
): Promise<LegalHearing> {
  const response = await api.post<LegalHearing>(`${BASE_URL}/legal/${caseId}/hearings`, data);
  return response.data;
}

export async function getHearings(caseId: string): Promise<LegalHearing[]> {
  const response = await api.get<LegalHearing[]>(`${BASE_URL}/legal/${caseId}/hearings`);
  return response.data;
}

export async function getUpcomingHearings(days: number = 30): Promise<Array<{
  hearing_id: string;
  case_id: string;
  case_number: string;
  loan_account_number: string;
  entity_name: string;
  case_type: string;
  court_name: string;
  hearing_date: string;
  hearing_type: string;
}>> {
  const response = await api.get(`${BASE_URL}/legal/hearings/upcoming?days=${days}`);
  return response.data;
}

export async function closeLegalCase(
  caseId: string,
  data: { outcome: 'WON' | 'LOST' | 'SETTLED' | 'WITHDRAWN'; closure_date: string; remarks?: string }
): Promise<LegalCase> {
  const response = await api.post<LegalCase>(`${BASE_URL}/legal/${caseId}/close`, data);
  return response.data;
}

// ============== Export all functions ==============

export const collectionApi = {
  // Follow-ups
  getFollowUps,
  getFollowUp,
  createFollowUp,
  updateFollowUp,
  recordFollowUpOutcome,
  getFollowUpsByAccount,

  // NPA
  getNPAAccounts,
  getNPARecord,
  runNPAIdentification,
  requestNPAUpgrade,
  approveNPAUpgrade,
  getNPAMovement,
  getProvisioningSummary,

  // OTS
  getOTSProposals,
  getOTSProposal,
  createOTSProposal,
  updateOTSProposal,
  submitOTSProposal,
  approveOTSProposal,
  recordOTSPayment,
  closeOTS,

  // Legal
  getLegalCases,
  getLegalCase,
  createLegalCase,
  updateLegalCase,
  addHearing,
  getHearings,
  getUpcomingHearings,
  closeLegalCase,
};

export default collectionApi;
