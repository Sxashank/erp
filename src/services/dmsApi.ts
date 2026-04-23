/**
 * DMS (Document Management System) API Service
 */

import api from './api';
import type {
  DMSDocument,
  DocumentCreate,
  DocumentUpdate,
  DocumentVersion,
  DocumentHistory,
  DocumentListResponse,
  DocumentStats,
  DocumentSearchParams,
  DMSFolder,
  FolderCreate,
  FolderUpdate,
  FolderTreeNode,
  FolderAccess,
  FolderAccessCreate,
  DMSTag,
  TagCreate,
  TagUpdate,
  TagListResponse,
} from '@/types/dms';

// Document API
export const documentApi = {
  // List documents
  list: async (params?: {
    folder_id?: string;
    document_type?: string;
    status?: string;
    entity_type?: string;
    entity_id?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<DocumentListResponse> => {
    const response = await api.get('/dms/documents', { params });
    return response.data;
  },

  // Search documents
  search: async (params: DocumentSearchParams): Promise<DocumentListResponse> => {
    const response = await api.get('/dms/documents/search', { params });
    return response.data;
  },

  // Get recent documents
  getRecent: async (limit?: number): Promise<DMSDocument[]> => {
    const response = await api.get('/dms/documents/recent', { params: { limit } });
    return response.data;
  },

  // Get document stats
  getStats: async (): Promise<DocumentStats> => {
    const response = await api.get('/dms/documents/stats');
    return response.data;
  },

  // Get single document
  get: async (id: string): Promise<DMSDocument> => {
    const response = await api.get(`/dms/documents/${id}`);
    return response.data;
  },

  // Upload document
  upload: async (
    file: File,
    metadata: DocumentCreate
  ): Promise<DMSDocument> => {
    const formData = new FormData();
    formData.append('file', file);

    if (metadata.folder_id) formData.append('folder_id', metadata.folder_id);
    if (metadata.name) formData.append('name', metadata.name);
    if (metadata.description) formData.append('description', metadata.description);
    if (metadata.document_type) formData.append('document_type', metadata.document_type);
    if (metadata.document_subtype) formData.append('document_subtype', metadata.document_subtype);
    if (metadata.entity_type) formData.append('entity_type', metadata.entity_type);
    if (metadata.entity_id) formData.append('entity_id', metadata.entity_id);
    if (metadata.access_level) formData.append('access_level', metadata.access_level);
    if (metadata.keywords) formData.append('keywords', metadata.keywords.join(','));
    if (metadata.expiry_date) formData.append('expiry_date', metadata.expiry_date);

    const response = await api.post('/dms/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Update document
  update: async (id: string, data: DocumentUpdate): Promise<DMSDocument> => {
    const response = await api.patch(`/dms/documents/${id}`, data);
    return response.data;
  },

  // Delete document
  delete: async (id: string, hardDelete?: boolean): Promise<void> => {
    await api.delete(`/dms/documents/${id}`, { params: { hard_delete: hardDelete } });
  },

  // Download document
  download: async (id: string, version?: number): Promise<Blob> => {
    const response = await api.get(`/dms/documents/${id}/download`, {
      params: { version },
      responseType: 'blob',
    });
    return response.data;
  },

  // Upload new version
  uploadVersion: async (
    id: string,
    file: File,
    changeNotes?: string
  ): Promise<DocumentVersion> => {
    const formData = new FormData();
    formData.append('file', file);
    if (changeNotes) formData.append('change_notes', changeNotes);

    const response = await api.post(`/dms/documents/${id}/versions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Get document versions
  getVersions: async (id: string): Promise<DocumentVersion[]> => {
    const response = await api.get(`/dms/documents/${id}/versions`);
    return response.data;
  },

  // Get document history
  getHistory: async (
    id: string,
    params?: { skip?: number; limit?: number }
  ): Promise<DocumentHistory[]> => {
    const response = await api.get(`/dms/documents/${id}/history`, { params });
    return response.data;
  },

  // Add tag to document
  addTag: async (documentId: string, tagId: string): Promise<void> => {
    await api.post(`/dms/documents/${documentId}/tags/${tagId}`);
  },

  // Remove tag from document
  removeTag: async (documentId: string, tagId: string): Promise<void> => {
    await api.delete(`/dms/documents/${documentId}/tags/${tagId}`);
  },
};

// Folder API
export const folderApi = {
  // List folders
  list: async (params?: {
    parent_id?: string;
    folder_type?: string;
    entity_type?: string;
    entity_id?: string;
  }): Promise<DMSFolder[]> => {
    const response = await api.get('/dms/folders', { params });
    return response.data;
  },

  // Get folder tree
  getTree: async (params?: {
    root_folder_id?: string;
    max_depth?: number;
  }): Promise<FolderTreeNode[]> => {
    const response = await api.get('/dms/folders/tree', { params });
    return response.data;
  },

  // Get single folder
  get: async (id: string): Promise<DMSFolder> => {
    const response = await api.get(`/dms/folders/${id}`);
    return response.data;
  },

  // Create folder
  create: async (data: FolderCreate): Promise<DMSFolder> => {
    const response = await api.post('/dms/folders', data);
    return response.data;
  },

  // Update folder
  update: async (id: string, data: FolderUpdate): Promise<DMSFolder> => {
    const response = await api.patch(`/dms/folders/${id}`, data);
    return response.data;
  },

  // Move folder
  move: async (id: string, newParentId?: string): Promise<DMSFolder> => {
    const response = await api.post(`/dms/folders/${id}/move`, {
      new_parent_id: newParentId,
    });
    return response.data;
  },

  // Delete folder
  delete: async (id: string, recursive?: boolean): Promise<void> => {
    await api.delete(`/dms/folders/${id}`, { params: { recursive } });
  },

  // Grant folder access
  grantAccess: async (id: string, data: FolderAccessCreate): Promise<FolderAccess> => {
    const response = await api.post(`/dms/folders/${id}/access`, data);
    return response.data;
  },

  // Revoke folder access
  revokeAccess: async (
    id: string,
    params: { user_id?: string; role_id?: string }
  ): Promise<void> => {
    await api.delete(`/dms/folders/${id}/access`, { params });
  },

  // Get folder documents
  getDocuments: async (
    id: string,
    params?: { skip?: number; limit?: number }
  ): Promise<DocumentListResponse> => {
    const response = await api.get(`/dms/folders/${id}/documents`, { params });
    return response.data;
  },

  // Get folder children
  getChildren: async (id: string): Promise<DMSFolder[]> => {
    const response = await api.get(`/dms/folders/${id}/children`);
    return response.data;
  },
};

// Tag API
export const tagApi = {
  // List tags
  list: async (params?: {
    category?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<TagListResponse> => {
    const response = await api.get('/dms/tags', { params });
    return response.data;
  },

  // Get tag categories
  getCategories: async (): Promise<string[]> => {
    const response = await api.get('/dms/tags/categories');
    return response.data;
  },

  // Get single tag
  get: async (id: string): Promise<DMSTag> => {
    const response = await api.get(`/dms/tags/${id}`);
    return response.data;
  },

  // Create tag
  create: async (data: TagCreate): Promise<DMSTag> => {
    const response = await api.post('/dms/tags', data);
    return response.data;
  },

  // Update tag
  update: async (id: string, data: TagUpdate): Promise<DMSTag> => {
    const response = await api.patch(`/dms/tags/${id}`, data);
    return response.data;
  },

  // Delete tag
  delete: async (id: string): Promise<void> => {
    await api.delete(`/dms/tags/${id}`);
  },

  // Get tag documents
  getDocuments: async (
    id: string,
    params?: { skip?: number; limit?: number }
  ): Promise<DocumentListResponse> => {
    const response = await api.get(`/dms/tags/${id}/documents`, { params });
    return response.data;
  },

  // Bulk tag documents
  bulkTag: async (data: {
    document_ids: string[];
    tag_ids: string[];
  }): Promise<{ added: number }> => {
    const response = await api.post('/dms/tags/bulk-tag', data);
    return response.data;
  },
};

export default {
  document: documentApi,
  folder: folderApi,
  tag: tagApi,
};
