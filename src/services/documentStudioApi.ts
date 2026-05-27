import api from '@/services/api';
import type { DMSDocument, DMSFolder } from '@/types/dms';

export type DocumentModule =
  | 'LENDING'
  | 'TREASURY'
  | 'HRIS'
  | 'PAYROLL'
  | 'LEGAL'
  | 'FINANCE'
  | 'AP_AR'
  | 'VENDOR_PORTAL'
  | 'BORROWER_PORTAL'
  | 'ESS';

export type TemplateStatus = 'DRAFT' | 'IN_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'RETIRED';

export interface DocumentTemplate {
  id: string;
  module: DocumentModule;
  documentType: string;
  code: string;
  name: string;
  description?: string | null;
  productCode?: string | null;
  entityType?: string | null;
  locale: string;
  channel: string;
  priority: number;
  selectionRules: Record<string, unknown>;
  isSystem: boolean;
  versions?: DocumentTemplateVersion[];
}

export interface DocumentTemplateVersion {
  id: string;
  templateId: string;
  versionNumber: number;
  status: TemplateStatus;
  format: 'HTML' | 'MARKDOWN' | 'DOCX' | 'PDF_BACKGROUND';
  body: string;
  header?: string | null;
  footer?: string | null;
  styleConfig: Record<string, unknown>;
  variableSchema: Record<string, unknown>;
  requiredVariables: string[];
  lockedBlocks: Record<string, unknown>[];
  sourceDocumentId?: string | null;
  approvedById?: string | null;
  approvedAt?: string | null;
  publishedAt?: string | null;
  retiredAt?: string | null;
  changeNotes?: string | null;
}

export interface TemplateListResponse {
  items: DocumentTemplate[];
  total: number;
}

export interface VariableDefinition {
  key: string;
  label: string;
  description: string;
  required: boolean;
  formatter?: string | null;
}

export interface FilingRule {
  id: string;
  module: string;
  documentType: string;
  entityType: string;
  pathTemplate: string;
  accessLevel: string;
  retentionPolicy?: string | null;
  portalVisible: boolean;
  defaultTags: string[];
  description?: string | null;
  priority: number;
  isSystem: boolean;
}

export interface GeneratedDocument {
  id: string;
  module: DocumentModule;
  documentType: string;
  documentSubtype?: string | null;
  templateId: string;
  templateVersionId: string;
  templateCode: string;
  templateVersion: number;
  dmsDocumentId: string;
  folderId?: string | null;
  entityType: string;
  entityId: string;
  generatedFrom?: string | null;
  businessNumber?: string | null;
  renderSnapshot: Record<string, unknown>;
  checksum?: string | null;
  portalVisible: boolean;
  finalizedAt: string;
  finalizedById?: string | null;
}

export type DocumentPackageStatus = 'DRAFT' | 'FINALIZED' | 'SENT' | 'ARCHIVED';

export interface DocumentPackageItem {
  id: string;
  packageId: string;
  dmsDocumentId: string;
  generatedDocumentId?: string | null;
  role: string;
  sortOrder: number;
}

export interface DocumentPackage {
  id: string;
  packageNumber: string;
  packageType: string;
  name: string;
  status: DocumentPackageStatus;
  entityType: string;
  entityId: string;
  manifest: Record<string, unknown>;
  finalizedAt?: string | null;
  finalizedById?: string | null;
  items?: DocumentPackageItem[];
}

export interface DocumentPackageListResponse {
  items: DocumentPackage[];
  total: number;
}

export interface EntityVault {
  entityType: string;
  entityId: string;
  folders: DMSFolder[];
  documents: DMSDocument[];
}

function idempotencyHeaders(): { 'Idempotency-Key': string } {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

export const documentStudioApi = {
  async listTemplates(params?: {
    module?: DocumentModule;
    documentType?: string;
  }): Promise<TemplateListResponse> {
    const { data } = await api.get<TemplateListResponse>('/document-studio/templates', {
      params,
    });
    return data;
  },

  async getTemplate(id: string): Promise<DocumentTemplate> {
    const { data } = await api.get<DocumentTemplate>(`/document-studio/templates/${id}`);
    return data;
  },

  async createTemplate(payload: Partial<DocumentTemplate>): Promise<DocumentTemplate> {
    const { data } = await api.post<DocumentTemplate>('/document-studio/templates', payload, {
      headers: idempotencyHeaders(),
    });
    return data;
  },

  async createVersion(
    templateId: string,
    payload: Partial<DocumentTemplateVersion>,
  ): Promise<DocumentTemplateVersion> {
    const { data } = await api.post<DocumentTemplateVersion>(
      `/document-studio/templates/${templateId}/versions`,
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async transitionVersion(
    versionId: string,
    action: 'submit-review' | 'approve' | 'publish',
  ): Promise<DocumentTemplateVersion> {
    const { data } = await api.post<DocumentTemplateVersion>(
      `/document-studio/templates/${versionId}/${action}`,
      undefined,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async variables(params: {
    module: DocumentModule;
    documentType?: string;
  }): Promise<{ items: VariableDefinition[] }> {
    const { data } = await api.get<{ items: VariableDefinition[] }>('/document-studio/variables', {
      params,
    });
    return data;
  },

  async preview(payload: {
    templateVersionId?: string;
    body?: string;
    header?: string;
    footer?: string;
    context: Record<string, unknown>;
  }): Promise<{ renderedHtml: string; missingVariables: string[] }> {
    const { data } = await api.post<{ renderedHtml: string; missingVariables: string[] }>(
      '/document-studio/preview',
      payload,
    );
    return data;
  },

  async generate(payload: Record<string, unknown>): Promise<GeneratedDocument> {
    const { data } = await api.post<GeneratedDocument>('/document-studio/generate', payload, {
      headers: idempotencyHeaders(),
    });
    return data;
  },
};

export const documentPackageApi = {
  async list(params?: {
    entityType?: string;
    entityId?: string;
  }): Promise<DocumentPackageListResponse> {
    const { data } = await api.get<DocumentPackageListResponse>('/documents/packages', {
      params,
    });
    return data;
  },

  async get(id: string): Promise<DocumentPackage> {
    const { data } = await api.get<DocumentPackage>(`/documents/packages/${id}`);
    return data;
  },

  async create(payload: {
    packageType: string;
    name: string;
    entityType: string;
    entityId: string;
    manifest?: Record<string, unknown>;
  }): Promise<DocumentPackage> {
    const { data } = await api.post<DocumentPackage>('/documents/packages', payload, {
      headers: idempotencyHeaders(),
    });
    return data;
  },

  async addItem(
    packageId: string,
    payload: {
      dmsDocumentId: string;
      generatedDocumentId?: string | null;
      role?: string;
      sortOrder?: number;
    },
  ): Promise<DocumentPackageItem> {
    const { data } = await api.post<DocumentPackageItem>(
      `/documents/packages/${packageId}/items`,
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async finalize(
    packageId: string,
    payload: { manifest?: Record<string, unknown> } = {},
  ): Promise<DocumentPackage> {
    const { data } = await api.post<DocumentPackage>(
      `/documents/packages/${packageId}/finalize`,
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },
};

export const dmsFilingApi = {
  async listRules(params?: { module?: string; documentType?: string }): Promise<FilingRule[]> {
    const { data } = await api.get<FilingRule[]>('/dms/filing-rules', { params });
    return data;
  },

  async createRule(payload: Partial<FilingRule>): Promise<FilingRule> {
    const { data } = await api.post<FilingRule>('/dms/filing-rules', payload, {
      headers: idempotencyHeaders(),
    });
    return data;
  },

  async resolveFolder(
    payload: Record<string, unknown>,
  ): Promise<{ folder: DMSFolder; path: string; rule?: FilingRule | null }> {
    const { data } = await api.post<{ folder: DMSFolder; path: string; rule?: FilingRule | null }>(
      '/dms/resolve-folder',
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async entityVault(entityType: string, entityId: string): Promise<EntityVault> {
    const { data } = await api.get<EntityVault>(`/documents/entity/${entityType}/${entityId}`);
    return data;
  },
};
