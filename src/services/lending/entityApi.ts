/**
 * Entity API Service
 * API calls for Entity/Borrower management
 */

import api from '../api';
import type {
  Entity,
  EntityContact,
  EntityAddress,
  EntityBankAccount,
  EntityFinancial,
  EntityKYCDocument,
  EntityFilters,
  PaginatedResponse,
  CreateEntityRequest,
} from '@/types/lending';

const BASE_URL = '/lending/entities';

// ============== Entity CRUD ==============

export async function getEntities(filters?: EntityFilters): Promise<PaginatedResponse<Entity>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entity_type) params.append('entity_type', filters.entity_type);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.risk_category) params.append('risk_category', filters.risk_category);
  if (filters?.relationship_manager_id) params.append('relationship_manager_id', filters.relationship_manager_id);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.page_size) params.append('page_size', filters.page_size.toString());

  const response = await api.get<PaginatedResponse<Entity>>(`${BASE_URL}?${params.toString()}`);
  return response.data;
}

export async function getEntity(entityId: string): Promise<Entity> {
  const response = await api.get<Entity>(`${BASE_URL}/${entityId}`);
  return response.data;
}

export async function createEntity(data: CreateEntityRequest): Promise<Entity> {
  const response = await api.post<Entity>(BASE_URL, data);
  return response.data;
}

export async function updateEntity(entityId: string, data: Partial<CreateEntityRequest>): Promise<Entity> {
  const response = await api.put<Entity>(`${BASE_URL}/${entityId}`, data);
  return response.data;
}

export async function deleteEntity(entityId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${entityId}`);
}

// ============== Entity Contacts ==============

export async function getEntityContacts(entityId: string): Promise<EntityContact[]> {
  const response = await api.get<EntityContact[]>(`${BASE_URL}/${entityId}/contacts`);
  return response.data;
}

export async function addEntityContact(entityId: string, data: Omit<EntityContact, 'contact_id' | 'entity_id' | 'created_at'>): Promise<EntityContact> {
  const response = await api.post<EntityContact>(`${BASE_URL}/${entityId}/contacts`, data);
  return response.data;
}

export async function updateEntityContact(entityId: string, contactId: string, data: Partial<EntityContact>): Promise<EntityContact> {
  const response = await api.put<EntityContact>(`${BASE_URL}/${entityId}/contacts/${contactId}`, data);
  return response.data;
}

export async function deleteEntityContact(entityId: string, contactId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${entityId}/contacts/${contactId}`);
}

// ============== Entity Addresses ==============

export async function getEntityAddresses(entityId: string): Promise<EntityAddress[]> {
  const response = await api.get<EntityAddress[]>(`${BASE_URL}/${entityId}/addresses`);
  return response.data;
}

export async function addEntityAddress(entityId: string, data: Omit<EntityAddress, 'address_id' | 'entity_id'>): Promise<EntityAddress> {
  const response = await api.post<EntityAddress>(`${BASE_URL}/${entityId}/addresses`, data);
  return response.data;
}

export async function updateEntityAddress(entityId: string, addressId: string, data: Partial<EntityAddress>): Promise<EntityAddress> {
  const response = await api.put<EntityAddress>(`${BASE_URL}/${entityId}/addresses/${addressId}`, data);
  return response.data;
}

export async function deleteEntityAddress(entityId: string, addressId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${entityId}/addresses/${addressId}`);
}

// ============== Entity Bank Accounts ==============

export async function getEntityBankAccounts(entityId: string): Promise<EntityBankAccount[]> {
  const response = await api.get<EntityBankAccount[]>(`${BASE_URL}/${entityId}/bank-accounts`);
  return response.data;
}

export async function addEntityBankAccount(entityId: string, data: Omit<EntityBankAccount, 'bank_account_id' | 'entity_id'>): Promise<EntityBankAccount> {
  const response = await api.post<EntityBankAccount>(`${BASE_URL}/${entityId}/bank-accounts`, data);
  return response.data;
}

export async function updateEntityBankAccount(entityId: string, accountId: string, data: Partial<EntityBankAccount>): Promise<EntityBankAccount> {
  const response = await api.put<EntityBankAccount>(`${BASE_URL}/${entityId}/bank-accounts/${accountId}`, data);
  return response.data;
}

export async function deleteEntityBankAccount(entityId: string, accountId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${entityId}/bank-accounts/${accountId}`);
}

// ============== Entity Financials ==============

export async function getEntityFinancials(entityId: string): Promise<EntityFinancial[]> {
  const response = await api.get<EntityFinancial[]>(`${BASE_URL}/${entityId}/financials`);
  return response.data;
}

export async function addEntityFinancial(entityId: string, data: Omit<EntityFinancial, 'financial_id' | 'entity_id' | 'created_at'>): Promise<EntityFinancial> {
  const response = await api.post<EntityFinancial>(`${BASE_URL}/${entityId}/financials`, data);
  return response.data;
}

export async function updateEntityFinancial(entityId: string, financialId: string, data: Partial<EntityFinancial>): Promise<EntityFinancial> {
  const response = await api.put<EntityFinancial>(`${BASE_URL}/${entityId}/financials/${financialId}`, data);
  return response.data;
}

export async function deleteEntityFinancial(entityId: string, financialId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${entityId}/financials/${financialId}`);
}

// ============== Entity KYC Documents ==============

export async function getEntityKYCDocuments(entityId: string): Promise<EntityKYCDocument[]> {
  const response = await api.get<EntityKYCDocument[]>(`${BASE_URL}/${entityId}/kyc-documents`);
  return response.data;
}

export async function uploadKYCDocument(entityId: string, formData: FormData): Promise<EntityKYCDocument> {
  const response = await api.post<EntityKYCDocument>(`${BASE_URL}/${entityId}/kyc-documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function verifyKYCDocument(
  entityId: string,
  documentId: string,
  data: { status: 'VERIFIED' | 'REJECTED'; remarks?: string }
): Promise<EntityKYCDocument> {
  const response = await api.post<EntityKYCDocument>(`${BASE_URL}/${entityId}/kyc-documents/${documentId}/verify`, data);
  return response.data;
}

export async function deleteKYCDocument(entityId: string, documentId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${entityId}/kyc-documents/${documentId}`);
}

// ============== Entity Rating ==============

export async function initiateRating(entityId: string): Promise<{ rating_id: string }> {
  const response = await api.post<{ rating_id: string }>(`${BASE_URL}/${entityId}/rating`);
  return response.data;
}

// ============== Export all functions ==============

export const entityApi = {
  // Entity
  getEntities,
  getEntity,
  createEntity,
  updateEntity,
  deleteEntity,

  // Contacts
  getEntityContacts,
  addEntityContact,
  updateEntityContact,
  deleteEntityContact,

  // Addresses
  getEntityAddresses,
  addEntityAddress,
  updateEntityAddress,
  deleteEntityAddress,

  // Bank Accounts
  getEntityBankAccounts,
  addEntityBankAccount,
  updateEntityBankAccount,
  deleteEntityBankAccount,

  // Financials
  getEntityFinancials,
  addEntityFinancial,
  updateEntityFinancial,
  deleteEntityFinancial,

  // KYC Documents
  getEntityKYCDocuments,
  uploadKYCDocument,
  verifyKYCDocument,
  deleteKYCDocument,

  // Rating
  initiateRating,
};

export default entityApi;
