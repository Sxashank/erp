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

type EntityContactBody = Pick<
  EntityContact,
  | 'contactType'
  | 'name'
  | 'designation'
  | 'din'
  | 'pan'
  | 'phone'
  | 'mobile'
  | 'email'
  | 'isPrimary'
>;
type EntityAddressBody = Pick<
  EntityAddress,
  | 'addressType'
  | 'addressLine1'
  | 'addressLine2'
  | 'city'
  | 'state'
  | 'stateCode'
  | 'pincode'
  | 'country'
  | 'isPrimary'
>;
type EntityBankAccountBody = Pick<
  EntityBankAccount,
  | 'bankName'
  | 'branchName'
  | 'accountNumber'
  | 'ifscCode'
  | 'accountType'
  | 'accountHolderName'
  | 'isPrimary'
>;
type EntityFinancialBody = Omit<EntityFinancial, 'id' | 'entityId' | 'createdAt'>;

// ============== Entity CRUD ==============

export async function getEntities(filters?: EntityFilters): Promise<PaginatedResponse<Entity>> {
  const params = new URLSearchParams();

  if (filters?.search) params.append('search', filters.search);
  if (filters?.entityType) params.append('entityType', filters.entityType);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.riskCategory) params.append('riskCategory', filters.riskCategory);
  if (filters?.relationshipManagerId)
    params.append('relationshipManagerId', filters.relationshipManagerId);
  if (filters?.page) params.append('page', filters.page.toString());
  if (filters?.pageSize) params.append('pageSize', filters.pageSize.toString());

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

export async function updateEntity(
  entityId: string,
  data: Partial<CreateEntityRequest>,
): Promise<Entity> {
  const response = await api.put<Entity>(`${BASE_URL}/${entityId}`, data);
  return response.data;
}

export async function deleteEntity(entityId: string): Promise<void> {
  await api.delete(`${BASE_URL}/${entityId}`);
}

export interface EntityKycDocumentTypeOption {
  id: string;
  code: string;
  name: string;
  category: string;
  isMandatory: boolean;
  hasExpiry: boolean;
  allowedFileTypes: string[];
  maxFileSizeMb: number;
}

export async function getEntityKYCDocumentTypes(): Promise<EntityKycDocumentTypeOption[]> {
  const response = await api.get<EntityKycDocumentTypeOption[]>(`${BASE_URL}/kyc-document-types`);
  return response.data;
}

// ============== Entity Contacts ==============

export async function getEntityContacts(entityId: string): Promise<EntityContact[]> {
  const response = await api.get<EntityContact[]>(`${BASE_URL}/${entityId}/contacts`);
  return response.data;
}

export async function addEntityContact(
  entityId: string,
  data: EntityContactBody,
): Promise<EntityContact> {
  const response = await api.post<EntityContact>(`${BASE_URL}/${entityId}/contacts`, data);
  return response.data;
}

export async function updateEntityContact(
  _entityId: string,
  contactId: string,
  data: Partial<EntityContactBody>,
): Promise<EntityContact> {
  const response = await api.put<EntityContact>(`${BASE_URL}/contacts/${contactId}`, data);
  return response.data;
}

export async function deleteEntityContact(_entityId: string, contactId: string): Promise<void> {
  await api.delete(`${BASE_URL}/contacts/${contactId}`);
}

// ============== Entity Addresses ==============

export async function getEntityAddresses(entityId: string): Promise<EntityAddress[]> {
  const response = await api.get<EntityAddress[]>(`${BASE_URL}/${entityId}/addresses`);
  return response.data;
}

export async function addEntityAddress(
  entityId: string,
  data: EntityAddressBody,
): Promise<EntityAddress> {
  const response = await api.post<EntityAddress>(`${BASE_URL}/${entityId}/addresses`, data);
  return response.data;
}

export async function updateEntityAddress(
  _entityId: string,
  addressId: string,
  data: Partial<EntityAddressBody>,
): Promise<EntityAddress> {
  const response = await api.put<EntityAddress>(`${BASE_URL}/addresses/${addressId}`, data);
  return response.data;
}

export async function deleteEntityAddress(_entityId: string, addressId: string): Promise<void> {
  await api.delete(`${BASE_URL}/addresses/${addressId}`);
}

// ============== Entity Bank Accounts ==============

export async function getEntityBankAccounts(entityId: string): Promise<EntityBankAccount[]> {
  const response = await api.get<EntityBankAccount[]>(`${BASE_URL}/${entityId}/bank-accounts`);
  return response.data;
}

export async function addEntityBankAccount(
  entityId: string,
  data: EntityBankAccountBody,
): Promise<EntityBankAccount> {
  const response = await api.post<EntityBankAccount>(`${BASE_URL}/${entityId}/bank-accounts`, data);
  return response.data;
}

export async function updateEntityBankAccount(
  _entityId: string,
  accountId: string,
  data: Partial<EntityBankAccountBody>,
): Promise<EntityBankAccount> {
  const response = await api.put<EntityBankAccount>(`${BASE_URL}/bank-accounts/${accountId}`, data);
  return response.data;
}

export async function deleteEntityBankAccount(_entityId: string, accountId: string): Promise<void> {
  await api.delete(`${BASE_URL}/bank-accounts/${accountId}`);
}

// ============== Entity Financials ==============

export async function getEntityFinancials(entityId: string): Promise<EntityFinancial[]> {
  const response = await api.get<EntityFinancial[]>(`${BASE_URL}/${entityId}/financials`);
  return response.data;
}

export async function addEntityFinancial(
  entityId: string,
  data: EntityFinancialBody,
): Promise<EntityFinancial> {
  const response = await api.post<EntityFinancial>(`${BASE_URL}/${entityId}/financials`, data);
  return response.data;
}

export async function updateEntityFinancial(
  _entityId: string,
  financialId: string,
  data: Partial<EntityFinancialBody>,
): Promise<EntityFinancial> {
  const response = await api.put<EntityFinancial>(`${BASE_URL}/financials/${financialId}`, data);
  return response.data;
}

export async function deleteEntityFinancial(_entityId: string, financialId: string): Promise<void> {
  await api.delete(`${BASE_URL}/financials/${financialId}`);
}

// ============== Entity KYC Documents ==============

export async function getEntityKYCDocuments(entityId: string): Promise<EntityKYCDocument[]> {
  const response = await api.get<EntityKYCDocument[]>(`${BASE_URL}/${entityId}/kyc-documents`);
  return response.data;
}

export async function uploadKYCDocument(
  entityId: string,
  formData: FormData,
): Promise<EntityKYCDocument> {
  const response = await api.post<EntityKYCDocument>(
    `${BASE_URL}/${entityId}/kyc-documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  );
  return response.data;
}

export async function verifyKYCDocument(
  entityId: string,
  documentId: string,
  data: { status: 'VERIFIED' | 'REJECTED'; remarks?: string },
): Promise<EntityKYCDocument> {
  const response = await api.post<EntityKYCDocument>(
    `${BASE_URL}/${entityId}/kyc-documents/${documentId}/verify`,
    data,
  );
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
  getEntityKYCDocumentTypes,

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
