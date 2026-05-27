/**
 * Approval Checklist API service.
 *
 * Templates are master data and are mounted under
 * `/api/v1/lending/masters/approval-checklist-templates/rows/*`.
 * Per-application checklist operations remain under `/api/v1/lending/checklist/*`.
 *
 * Two surfaces:
 *  - Templates (master CRUD) — schemas of items NBFCs reuse across loans.
 *  - Per-application checklists — applied/replaced from a template; items
 *    transition through PENDING → IN_PROGRESS → MET / WAIVED / NOT_APPLICABLE.
 */

import api from '../api';

// ============================================================================
// Wire shapes
// ============================================================================

export type ChecklistItemCategory =
  | 'DOCUMENT'
  | 'KYC'
  | 'COMPLIANCE'
  | 'COVENANT'
  | 'LEGAL'
  | 'INSURANCE'
  | 'OTHER';

export type ChecklistItemStatus = 'PENDING' | 'IN_PROGRESS' | 'MET' | 'WAIVED' | 'NOT_APPLICABLE';

export type ChecklistAppliesTo = 'LOAN_APPLICATION';

export interface ChecklistTemplateItem {
  id: string;
  templateId: string;
  catalogItemId: string;
  code: string;
  label: string;
  description: string | null;
  category: ChecklistItemCategory;
  isMandatory: boolean;
  sortOrder: number;
  defaultDueOffsetDays: number | null;
  requiresEvidence: boolean;
}

export interface ChecklistTemplate {
  id: string;
  organizationId: string | null;
  code: string;
  name: string;
  description: string | null;
  appliesTo: ChecklistAppliesTo;
  isDefault: boolean;
  items: ChecklistTemplateItem[];
}

export interface LoanChecklistItem {
  id: string;
  checklistId: string;
  templateItemId: string | null;
  catalogItemId: string | null;
  code: string;
  label: string;
  description: string | null;
  category: ChecklistItemCategory;
  isMandatory: boolean;
  sortOrder: number;
  requiresEvidence: boolean;
  status: ChecklistItemStatus;
  metAt: string | null;
  metBy: string | null;
  waivedAt: string | null;
  waivedBy: string | null;
  waiverReason: string | null;
  evidenceDocumentPath: string | null;
  evidenceUploadedAt: string | null;
  dueDate: string | null;
  notes: string | null;
}

export interface LoanChecklist {
  id: string;
  organizationId: string;
  applicationId: string;
  templateId: string | null;
  name: string;
  items: LoanChecklistItem[];
  mandatoryPending: number;
}

// ============================================================================
// Request payloads
// ============================================================================

export interface ChecklistTemplateCreate {
  code: string;
  name: string;
  description?: string | null;
  appliesTo: ChecklistAppliesTo;
  isDefault?: boolean;
}

export type ChecklistTemplateUpdate = Partial<ChecklistTemplateCreate>;

export interface ChecklistTemplateItemCreate {
  catalogItemId: string;
  isMandatory?: boolean;
  sortOrder?: number;
  defaultDueOffsetDays?: number | null;
  requiresEvidence?: boolean;
}

export type ChecklistTemplateItemUpdate = Partial<ChecklistTemplateItemCreate>;

export interface ApplyTemplatePayload {
  templateId: string;
  /** Anchor date used to compute item due_dates from defaultDueOffsetDays. */
  dueDateAnchor?: string;
}

export interface UpdateChecklistItemPayload {
  status?: ChecklistItemStatus;
  dueDate?: string | null;
  notes?: string | null;
  evidenceDocumentPath?: string | null;
}

export interface MarkMetPayload {
  evidenceDocumentPath?: string | null;
  notes?: string | null;
}

export interface WaivePayload {
  waiverReason: string;
}

export interface MarkNAPayload {
  notes?: string | null;
}

// ============================================================================
// Helpers
// ============================================================================

function idempotencyHeader(): { 'Idempotency-Key': string } {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

// ============================================================================
// Templates (master CRUD)
// ============================================================================

export interface ChecklistTemplateListParams {
  appliesTo?: ChecklistAppliesTo;
}

export const checklistTemplatesApi = {
  async list(params?: ChecklistTemplateListParams): Promise<ChecklistTemplate[]> {
    const { data } = await api.get<ChecklistTemplate[] | { items?: ChecklistTemplate[] }>(
      '/lending/masters/approval-checklist-templates/rows',
      { params },
    );
    return Array.isArray(data) ? data : (data.items ?? []);
  },
  async get(id: string): Promise<ChecklistTemplate> {
    const { data } = await api.get<ChecklistTemplate>(
      `/lending/masters/approval-checklist-templates/rows/${id}`,
    );
    return data;
  },
  async create(payload: ChecklistTemplateCreate): Promise<ChecklistTemplate> {
    const { data } = await api.post<ChecklistTemplate>(
      '/lending/masters/approval-checklist-templates/rows',
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async update(id: string, payload: ChecklistTemplateUpdate): Promise<ChecklistTemplate> {
    const { data } = await api.put<ChecklistTemplate>(
      `/lending/masters/approval-checklist-templates/rows/${id}`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/lending/masters/approval-checklist-templates/rows/${id}`, {
      headers: idempotencyHeader(),
    });
  },
  async addItem(
    templateId: string,
    payload: ChecklistTemplateItemCreate,
  ): Promise<ChecklistTemplateItem> {
    const { data } = await api.post<ChecklistTemplateItem>(
      `/lending/masters/approval-checklist-templates/rows/${templateId}/items`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async updateItem(
    templateId: string,
    itemId: string,
    payload: ChecklistTemplateItemUpdate,
  ): Promise<ChecklistTemplateItem> {
    const { data } = await api.put<ChecklistTemplateItem>(
      `/lending/masters/approval-checklist-templates/rows/${templateId}/items/${itemId}`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async deleteItem(templateId: string, itemId: string): Promise<void> {
    await api.delete(
      `/lending/masters/approval-checklist-templates/rows/${templateId}/items/${itemId}`,
      { headers: idempotencyHeader() },
    );
  },
  async setDefault(id: string): Promise<ChecklistTemplate> {
    const { data } = await api.post<ChecklistTemplate>(
      `/lending/masters/approval-checklist-templates/rows/${id}/set-default`,
      null,
      { headers: idempotencyHeader() },
    );
    return data;
  },
};

// ============================================================================
// Per-application checklist
// ============================================================================

export const applicationChecklistApi = {
  async get(applicationId: string): Promise<LoanChecklist | null> {
    const { data } = await api.get<LoanChecklist | null>(
      `/lending/checklist/applications/${applicationId}/checklist`,
    );
    return data;
  },
  async apply(applicationId: string, payload: ApplyTemplatePayload): Promise<LoanChecklist> {
    const { data } = await api.post<LoanChecklist>(
      `/lending/checklist/applications/${applicationId}/checklist/apply`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async replace(applicationId: string, payload: ApplyTemplatePayload): Promise<LoanChecklist> {
    const { data } = await api.post<LoanChecklist>(
      `/lending/checklist/applications/${applicationId}/checklist/replace`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async updateItem(
    applicationId: string,
    itemId: string,
    payload: UpdateChecklistItemPayload,
  ): Promise<LoanChecklistItem> {
    const { data } = await api.put<LoanChecklistItem>(
      `/lending/checklist/applications/${applicationId}/checklist/items/${itemId}`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async markMet(
    applicationId: string,
    itemId: string,
    payload: MarkMetPayload,
  ): Promise<LoanChecklistItem> {
    const { data } = await api.post<LoanChecklistItem>(
      `/lending/checklist/applications/${applicationId}/checklist/items/${itemId}/mark-met`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async waive(
    applicationId: string,
    itemId: string,
    payload: WaivePayload,
  ): Promise<LoanChecklistItem> {
    const { data } = await api.post<LoanChecklistItem>(
      `/lending/checklist/applications/${applicationId}/checklist/items/${itemId}/waive`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async markNotApplicable(
    applicationId: string,
    itemId: string,
    payload: MarkNAPayload,
  ): Promise<LoanChecklistItem> {
    const { data } = await api.post<LoanChecklistItem>(
      `/lending/checklist/applications/${applicationId}/checklist/items/${itemId}/mark-not-applicable`,
      payload,
      { headers: idempotencyHeader() },
    );
    return data;
  },
  async reset(applicationId: string, itemId: string): Promise<LoanChecklistItem> {
    const { data } = await api.post<LoanChecklistItem>(
      `/lending/checklist/applications/${applicationId}/checklist/items/${itemId}/reset`,
      null,
      { headers: idempotencyHeader() },
    );
    return data;
  },
};

export const checklistApi = {
  templates: checklistTemplatesApi,
  applications: applicationChecklistApi,
};

export default checklistApi;
