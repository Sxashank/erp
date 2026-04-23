/**
 * DMS (Document Management System) Types
 */

// Enums
export type DocumentStatus = 'active' | 'archived' | 'deleted' | 'pending_review';
export type DocumentAccessLevel = 'private' | 'organization' | 'department' | 'public';

// Document Types
export interface DMSDocument {
  id: string;
  organization_id: string;
  folder_id?: string;
  code: string;
  name: string;
  description?: string;
  file_name: string;
  file_extension?: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  storage_provider: string;
  checksum?: string;
  document_type?: string;
  document_subtype?: string;
  status: DocumentStatus;
  access_level: DocumentAccessLevel;
  current_version: number;
  entity_type?: string;
  entity_id?: string;
  keywords?: string[];
  expiry_date?: string;
  is_ocr_processed: boolean;
  ocr_text?: string;
  download_count: number;
  view_count: number;
  last_accessed_at?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface DocumentCreate {
  folder_id?: string;
  name?: string;
  description?: string;
  document_type?: string;
  document_subtype?: string;
  entity_type?: string;
  entity_id?: string;
  access_level?: string;
  keywords?: string[];
  expiry_date?: string;
}

export interface DocumentUpdate {
  name?: string;
  description?: string;
  folder_id?: string;
  document_type?: string;
  document_subtype?: string;
  access_level?: string;
  keywords?: string[];
  expiry_date?: string;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version_number: number;
  change_notes?: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  checksum?: string;
  is_current: boolean;
  created_by?: string;
  created_at: string;
}

export interface DocumentHistory {
  id: string;
  document_id: string;
  action: string;
  action_details?: Record<string, any>;
  performed_by?: string;
  performed_at: string;
  ip_address?: string;
  user_agent?: string;
}

export interface DocumentListResponse {
  items: DMSDocument[];
  total: number;
  skip: number;
  limit: number;
}

export interface DocumentStats {
  total_documents: number;
  total_size_bytes: number;
  total_size_mb: number;
  total_folders: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_extension: Record<string, number>;
}

// Folder Types
export interface DMSFolder {
  id: string;
  organization_id: string;
  parent_id?: string;
  name: string;
  description?: string;
  path: string;
  level: number;
  folder_type?: string;
  entity_type?: string;
  entity_id?: string;
  access_level: DocumentAccessLevel;
  color?: string;
  icon?: string;
  sort_order: number;
  document_count: number;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface FolderCreate {
  name: string;
  parent_id?: string;
  description?: string;
  folder_type?: string;
  entity_type?: string;
  entity_id?: string;
  access_level?: string;
  color?: string;
  icon?: string;
}

export interface FolderUpdate {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  access_level?: string;
}

export interface FolderTreeNode {
  id: string;
  name: string;
  path: string;
  level: number;
  folder_type?: string;
  color?: string;
  icon?: string;
  document_count: number;
  children: FolderTreeNode[];
}

export interface FolderAccess {
  id: string;
  folder_id: string;
  user_id?: string;
  role_id?: string;
  department_id?: string;
  can_view: boolean;
  can_upload: boolean;
  can_create_subfolder: boolean;
  can_edit: boolean;
  can_delete: boolean;
  expires_at?: string;
  created_by?: string;
  created_at: string;
}

export interface FolderAccessCreate {
  user_id?: string;
  role_id?: string;
  department_id?: string;
  can_view?: boolean;
  can_upload?: boolean;
  can_create_subfolder?: boolean;
  can_edit?: boolean;
  can_delete?: boolean;
  expires_at?: string;
}

// Tag Types
export interface DMSTag {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
  color?: string;
  icon?: string;
  category?: string;
  usage_count: number;
  created_at: string;
  updated_at?: string;
}

export interface TagCreate {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  category?: string;
}

export interface TagUpdate {
  name?: string;
  description?: string;
  color?: string;
  icon?: string;
  category?: string;
}

export interface TagListResponse {
  items: DMSTag[];
  total: number;
}

// Search Types
export interface DocumentSearchParams {
  query?: string;
  folder_id?: string;
  document_type?: string;
  document_subtype?: string;
  mime_type?: string;
  tags?: string;
  entity_type?: string;
  entity_id?: string;
  date_from?: string;
  date_to?: string;
  include_archived?: boolean;
  skip?: number;
  limit?: number;
}

// Document Type Categories
export const DOCUMENT_TYPES = [
  { value: 'contract', label: 'Contract' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'receipt', label: 'Receipt' },
  { value: 'report', label: 'Report' },
  { value: 'kyc', label: 'KYC Document' },
  { value: 'legal', label: 'Legal Document' },
  { value: 'policy', label: 'Policy' },
  { value: 'hr', label: 'HR Document' },
  { value: 'finance', label: 'Finance Document' },
  { value: 'other', label: 'Other' },
];

export const ACCESS_LEVELS = [
  { value: 'private', label: 'Private', description: 'Only you can access' },
  { value: 'organization', label: 'Organization', description: 'All org members can access' },
  { value: 'department', label: 'Department', description: 'Department members can access' },
  { value: 'public', label: 'Public', description: 'Anyone with link can access' },
];

// Helper functions
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function getFileIcon(mimeType: string, extension?: string): string {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.startsWith('video/')) return 'video';
  if (mimeType.startsWith('audio/')) return 'audio';
  if (mimeType === 'application/pdf') return 'pdf';
  if (mimeType.includes('spreadsheet') || extension === 'xlsx' || extension === 'xls') return 'spreadsheet';
  if (mimeType.includes('document') || extension === 'docx' || extension === 'doc') return 'document';
  if (mimeType.includes('presentation') || extension === 'pptx' || extension === 'ppt') return 'presentation';
  if (mimeType.includes('zip') || mimeType.includes('archive')) return 'archive';
  return 'file';
}
