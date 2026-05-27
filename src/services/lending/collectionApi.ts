import api from '../api';

import type { FollowUpFilters, FollowUpListItem } from '@/hooks/lending/useFollowUps';
import type { LegalCaseFilters, LegalCaseListItem } from '@/hooks/lending/useLegalCases';
import type { NPAFilters, NPAAccountListItem } from '@/hooks/lending/useNPAAccounts';
import type { OTSFilters, OTSProposalListItem } from '@/hooks/lending/useOTSProposals';
import type { RestructureFilters, RestructureListItem } from '@/hooks/lending/useRestructures';
import type { PaginatedResponse } from '@/types/lending';

const BASE_URL = '/lending/collections';

export interface OTSPaymentSchedulePayload {
  installmentNumber: number;
  dueDate: string;
  dueAmount: number;
}

export interface OTSProposalCreatePayload {
  loanAccountId: string;
  proposalDate: string;
  principalOutstanding: number;
  interestOutstanding: number;
  penalOutstanding: number;
  otherCharges: number;
  totalOutstanding: number;
  otsAmount: number;
  principalWaiver: number;
  interestWaiver: number;
  penalWaiver: number;
  chargesWaiver: number;
  paymentMode: string;
  upfrontAmount: number;
  upfrontDueDate?: string | null;
  numberOfInstallments: number;
  validTill: string;
  securityReleaseTerms?: string | null;
  termsAndConditions?: string | null;
  remarks?: string | null;
}

export interface RestructureCreatePayload {
  loanAccountId: string;
  restructureType: string;
  proposalDate: string;
  preOutstandingPrincipal: number;
  preOutstandingInterest: number;
  preInterestRate: number;
  preTenureMonths: number;
  preEmiAmount?: number;
  preMaturityDate: string;
  postOutstandingPrincipal: number;
  postInterestRate: number;
  postTenureMonths: number;
  postEmiAmount?: number;
  postMaturityDate: string;
  moratoriumMonths: number;
  moratoriumStartDate?: string;
  moratoriumEndDate?: string;
  moratoriumInterestTreatment?: string;
  interestWaived: number;
  penalWaived: number;
  principalConvertedToFitl: number;
  isStandardRestructure: boolean;
  downgradeRequired: boolean;
  preConditions?: string;
  postConditions?: string;
  justification: string;
  remarks?: string;
}

export interface RestructureApprovalPayload {
  approvedById: string;
  approvedByName: string;
  approvalAuthority: string;
}

export interface RestructureRejectPayload {
  rejectedById: string;
  rejectedByName: string;
  rejectionReason: string;
  approvalAuthority?: string;
}

function appendPaging(params: URLSearchParams, page?: number, pageSize?: number) {
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('pageSize', pageSize.toString());
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

export async function createOTSProposal(
  payload: OTSProposalCreatePayload,
  paymentSchedule?: OTSPaymentSchedulePayload[],
) {
  const response = await api.post(`${BASE_URL}/ots-proposals`, {
    data: payload,
    paymentSchedule: paymentSchedule ?? null,
  });
  return response.data;
}

export async function createRestructure(payload: RestructureCreatePayload) {
  const response = await api.post(`${BASE_URL}/restructures`, payload);
  return response.data;
}

export async function getRestructure(restructureId: string) {
  const response = await api.get(`${BASE_URL}/restructures/${restructureId}`);
  return response.data;
}

export async function approveRestructure(
  restructureId: string,
  payload: RestructureApprovalPayload,
) {
  const response = await api.post(`${BASE_URL}/restructures/${restructureId}/approve`, payload);
  return response.data;
}

export async function rejectRestructure(restructureId: string, payload: RestructureRejectPayload) {
  const response = await api.post(`${BASE_URL}/restructures/${restructureId}/reject`, payload);
  return response.data;
}

export async function getLegalCases(
  filters?: LegalCaseFilters,
): Promise<PaginatedResponse<LegalCaseListItem>> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.caseType) params.append('caseType', filters.caseType);
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
  createOTSProposal,
  getRestructures,
  createRestructure,
  getRestructure,
  approveRestructure,
  rejectRestructure,
  getLegalCases,
};

export default collectionApi;
