/**
 * Application API Service
 * API calls for Loan Application management
 */

import api from '../api';

import type {
  LoanApplication,
  ApplicationDocument,
  ApplicationFee,
  LoanSecurity,
  ProjectMilestone,
  ApplicationFilters,
  PaginatedResponse,
  CreateApplicationRequest,
} from '@/types/lending';

const BASE_URL = '/lending/applications';

export type CreateApplicationDocumentRequest = Omit<
  ApplicationDocument,
  'id' | 'applicationId' | 'createdAt' | 'updatedAt' | 'isActive'
>;

export type CreateProjectMilestoneRequest = Omit<
  ProjectMilestone,
  'id' | 'applicationId' | 'createdAt' | 'updatedAt' | 'isActive'
>;

// ============== Application CRUD ==============

export async function getApplications(
  filters?: ApplicationFilters,
): Promise<PaginatedResponse<LoanApplication>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entityId) params.append('entity_id', filters.entityId);
  if (filters?.productId) params.append('product_id', filters.productId);
  if (filters?.stage) params.append('stage', filters.stage);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.dateFrom) params.append('from_date', filters.dateFrom);
  if (filters?.dateTo) params.append('to_date', filters.dateTo);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('page_size', filters.pageSize.toString());

  const response = await api.get<PaginatedResponse<LoanApplication>>(
    `${BASE_URL}?${params.toString()}`,
  );
  return response.data;
}

export async function getApplication(applicationId: string): Promise<LoanApplication> {
  const response = await api.get<LoanApplication>(`${BASE_URL}/${applicationId}`);
  return response.data;
}

export async function createApplication(data: CreateApplicationRequest): Promise<LoanApplication> {
  const response = await api.post<LoanApplication>(BASE_URL, data);
  return response.data;
}

export async function updateApplication(
  applicationId: string,
  data: Partial<CreateApplicationRequest>,
): Promise<LoanApplication> {
  const response = await api.put<LoanApplication>(`${BASE_URL}/${applicationId}`, data);
  return response.data;
}

export async function deleteApplication(applicationId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${applicationId}`);
}

// ============== Application Documents ==============

export async function getApplicationDocuments(
  applicationId: string,
): Promise<ApplicationDocument[]> {
  const response = await api.get<ApplicationDocument[]>(`${BASE_URL}/${applicationId}/documents`);
  return response.data;
}

export async function uploadApplicationDocument(
  applicationId: string,
  data: CreateApplicationDocumentRequest,
): Promise<ApplicationDocument> {
  const response = await api.post<ApplicationDocument>(
    `${BASE_URL}/${applicationId}/documents`,
    data,
  );
  return response.data;
}

export async function verifyApplicationDocument(
  applicationId: string,
  documentId: string,
  data: { status: 'VERIFIED' | 'REJECTED'; remarks?: string },
): Promise<ApplicationDocument> {
  const response = await api.post<ApplicationDocument>(
    `${BASE_URL}/${applicationId}/documents/${documentId}/verify`,
    data,
  );
  return response.data;
}

export async function deleteApplicationDocument(
  applicationId: string,
  documentId: string,
): Promise<void> {
  await api.delete(`${BASE_URL}/${applicationId}/documents/${documentId}`);
}

// ============== Application Fees ==============

export async function getApplicationFees(applicationId: string): Promise<ApplicationFee[]> {
  const response = await api.get<ApplicationFee[]>(`${BASE_URL}/${applicationId}/fees`);
  return response.data;
}

export async function calculateApplicationFees(applicationId: string): Promise<ApplicationFee[]> {
  const response = await api.post<ApplicationFee[]>(`${BASE_URL}/${applicationId}/fees/calculate`);
  return response.data;
}

export async function recordFeePayment(
  applicationId: string,
  feeId: string,
  data: { amount: number; collectionDate: string },
): Promise<ApplicationFee> {
  const params = new URLSearchParams({
    collected_amount: String(data.amount),
    collected_date: data.collectionDate,
  });
  const response = await api.post<ApplicationFee>(
    `${BASE_URL}/fees/${feeId}/collect?${params.toString()}`,
  );
  return response.data;
}

// ============== Application Securities ==============

export async function getApplicationSecurities(applicationId: string): Promise<LoanSecurity[]> {
  const response = await api.get<LoanSecurity[]>(`${BASE_URL}/${applicationId}/securities`);
  return response.data;
}

export async function addApplicationSecurity(
  applicationId: string,
  data: Omit<LoanSecurity, 'security_id' | 'application_id' | 'created_at'>,
): Promise<LoanSecurity> {
  const response = await api.post<LoanSecurity>(`${BASE_URL}/${applicationId}/securities`, data);
  return response.data;
}

export async function updateApplicationSecurity(
  applicationId: string,
  securityId: string,
  data: Partial<LoanSecurity>,
): Promise<LoanSecurity> {
  const response = await api.put<LoanSecurity>(
    `${BASE_URL}/${applicationId}/securities/${securityId}`,
    data,
  );
  return response.data;
}

export async function deleteApplicationSecurity(
  applicationId: string,
  securityId: string,
): Promise<void> {
  await api.delete(`${BASE_URL}/${applicationId}/securities/${securityId}`);
}

// ============== Project Milestones ==============

export async function getProjectMilestones(applicationId: string): Promise<ProjectMilestone[]> {
  const response = await api.get<ProjectMilestone[]>(`${BASE_URL}/${applicationId}/milestones`);
  return response.data;
}

export async function addProjectMilestone(
  applicationId: string,
  data: CreateProjectMilestoneRequest,
): Promise<ProjectMilestone> {
  const response = await api.post<ProjectMilestone>(
    `${BASE_URL}/${applicationId}/milestones`,
    data,
  );
  return response.data;
}

export async function updateProjectMilestone(
  applicationId: string,
  milestoneId: string,
  data: Partial<ProjectMilestone>,
): Promise<ProjectMilestone> {
  const response = await api.put<ProjectMilestone>(
    `${BASE_URL}/${applicationId}/milestones/${milestoneId}`,
    data,
  );
  return response.data;
}

export async function deleteProjectMilestone(
  applicationId: string,
  milestoneId: string,
): Promise<void> {
  await api.delete(`${BASE_URL}/${applicationId}/milestones/${milestoneId}`);
}

// ============== Workflow Actions ==============

export async function submitApplication(
  applicationId: string,
  remarks?: string,
): Promise<LoanApplication> {
  const response = await api.post<LoanApplication>(`${BASE_URL}/${applicationId}/submit`, {
    remarks,
  });
  return response.data;
}

export async function withdrawApplication(
  applicationId: string,
  remarks: string,
): Promise<LoanApplication> {
  const response = await api.post<LoanApplication>(`${BASE_URL}/${applicationId}/withdraw`, {
    remarks,
  });
  return response.data;
}

export async function approveApplication(
  applicationId: string,
  data: { action: 'APPROVE' | 'REJECT' | 'RETURN'; remarks: string },
): Promise<LoanApplication> {
  const response = await api.post<LoanApplication>(`${BASE_URL}/${applicationId}/approve`, data);
  return response.data;
}

// ============== Draft Management ==============

export async function saveDraft(
  applicationId: string | null,
  data: Partial<CreateApplicationRequest>,
): Promise<LoanApplication> {
  if (applicationId) {
    const response = await api.put<LoanApplication>(`${BASE_URL}/${applicationId}`, data);
    return response.data;
  }

  const response = await api.post<LoanApplication>(BASE_URL, data);
  return response.data;
}

export async function getDraft(applicationId: string): Promise<LoanApplication> {
  const response = await api.get<LoanApplication>(`${BASE_URL}/${applicationId}`);
  return response.data;
}

// ============== Export all functions ==============

export const applicationApi = {
  // Application CRUD
  getApplications,
  getApplication,
  createApplication,
  updateApplication,
  deleteApplication,

  // Documents
  getApplicationDocuments,
  uploadApplicationDocument,
  verifyApplicationDocument,
  deleteApplicationDocument,

  // Fees
  getApplicationFees,
  calculateApplicationFees,
  recordFeePayment,

  // Securities
  getApplicationSecurities,
  addApplicationSecurity,
  updateApplicationSecurity,
  deleteApplicationSecurity,

  // Milestones
  getProjectMilestones,
  addProjectMilestone,
  updateProjectMilestone,
  deleteProjectMilestone,

  // Workflow
  submitApplication,
  withdrawApplication,
  approveApplication,

  // Draft
  saveDraft,
  getDraft,
};

export default applicationApi;
