/**
 * Notification API service
 */

import api from './api';

import type {
  Notification,
  NotificationListResponse,
  NotificationCreate,
  NotificationPreference,
  NotificationPreferenceUpdate,
  NotificationTemplate,
  NotificationTemplateCreate,
  NotificationTemplateUpdate,
  NotificationLogListResponse,
  NotificationTemplateListResponse,
  TemplatePreviewRequest,
  TemplatePreviewResponse,
  SendNotificationRequest,
  BulkNotificationRequest,
  NotificationChannel,
  NotificationCategory,
  NotificationStatus,
  NotificationTemplateType,
} from '@/types/notification';
const BASE_URL = '/notifications';
const COLLECTION_URL = `${BASE_URL}/`;

// Notification endpoints
export const notificationApi = {
  // Get user notifications
  getNotifications: async (params?: {
    category?: NotificationCategory;
    unread_only?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<NotificationListResponse> => {
    const response = await api.get<NotificationListResponse>(COLLECTION_URL, { params });
    return response.data;
  },

  // Get unread count
  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await api.get<{ unread_count: number }>(`${BASE_URL}/unread-count`);
    return response.data;
  },

  getLogs: async (params?: {
    notificationId?: string;
    channel?: NotificationChannel;
    status?: NotificationStatus;
    page?: number;
    pageSize?: number;
  }): Promise<NotificationLogListResponse> => {
    const response = await api.get<NotificationLogListResponse>(`${BASE_URL}/logs`, { params });
    return response.data;
  },

  // Get single notification
  getNotification: async (id: string): Promise<Notification> => {
    const response = await api.get<Notification>(`${BASE_URL}/${id}`);
    return response.data;
  },

  // Create notification
  createNotification: async (data: NotificationCreate): Promise<Notification> => {
    const response = await api.post<Notification>(COLLECTION_URL, data);
    return response.data;
  },

  // Send notification from template
  sendFromTemplate: async (data: SendNotificationRequest): Promise<Notification> => {
    const response = await api.post<Notification>(`${BASE_URL}/send`, data);
    return response.data;
  },

  // Send bulk notifications
  sendBulkNotifications: async (data: BulkNotificationRequest): Promise<{ status: string; message: string }> => {
    const response = await api.post<{ status: string; message: string }>(`${BASE_URL}/bulk`, data);
    return response.data;
  },

  // Mark notifications as read
  markAsRead: async (data: { notification_ids?: string[]; mark_all?: boolean }): Promise<{ marked_read: number }> => {
    const response = await api.post<{ marked_read: number }>(`${BASE_URL}/mark-read`, data);
    return response.data;
  },

  // Mark single notification as read
  markSingleAsRead: async (id: string): Promise<{ status: string }> => {
    const response = await api.post<{ status: string }>(`${BASE_URL}/${id}/read`);
    return response.data;
  },

  // Delete notification
  deleteNotification: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${id}`);
  },

  // Get user preferences
  getPreferences: async (): Promise<NotificationPreference[]> => {
    const response = await api.get<NotificationPreference[]>(`${BASE_URL}/preferences`);
    return response.data;
  },

  // Create or update preference
  updatePreference: async (
    category: NotificationCategory,
    data: NotificationPreferenceUpdate
  ): Promise<NotificationPreference> => {
    const response = await api.put<NotificationPreference>(`${BASE_URL}/preferences/${category}`, data);
    return response.data;
  },
};

// Template endpoints
export const templateApi = {
  // List templates
  getTemplates: async (params?: {
    category?: NotificationCategory;
    template_type?: NotificationTemplateType;
    is_active?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<NotificationTemplateListResponse> => {
    const response = await api.get<NotificationTemplateListResponse>(`${BASE_URL}/templates`, { params });
    return response.data;
  },

  // Get template by ID
  getTemplate: async (id: string): Promise<NotificationTemplate> => {
    const response = await api.get<NotificationTemplate>(`${BASE_URL}/templates/${id}`);
    return response.data;
  },

  // Get template by code
  getTemplateByCode: async (code: string): Promise<NotificationTemplate> => {
    const response = await api.get<NotificationTemplate>(`${BASE_URL}/templates/code/${code}`);
    return response.data;
  },

  // Create template
  createTemplate: async (data: NotificationTemplateCreate): Promise<NotificationTemplate> => {
    const response = await api.post<NotificationTemplate>(`${BASE_URL}/templates`, data);
    return response.data;
  },

  // Update template
  updateTemplate: async (id: string, data: NotificationTemplateUpdate): Promise<NotificationTemplate> => {
    const response = await api.put<NotificationTemplate>(`${BASE_URL}/templates/${id}`, data);
    return response.data;
  },

  // Delete template
  deleteTemplate: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/templates/${id}`);
  },

  // Preview template
  previewTemplate: async (data: TemplatePreviewRequest): Promise<TemplatePreviewResponse> => {
    const response = await api.post<TemplatePreviewResponse>(`${BASE_URL}/templates/preview`, data);
    return response.data;
  },

  // Get template variables
  getTemplateVariables: async (templateId: string): Promise<any[]> => {
    const response = await api.get<any[]>(`${BASE_URL}/templates/${templateId}/variables`);
    return response.data;
  },

  // Add template variable
  addTemplateVariable: async (templateId: string, data: Record<string, unknown>): Promise<unknown> => {
    const response = await api.post<unknown>(`${BASE_URL}/templates/${templateId}/variables`, data);
    return response.data;
  },

  // Delete template variable
  deleteTemplateVariable: async (templateId: string, variableId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/templates/${templateId}/variables/${variableId}`);
  },
};

export default {
  ...notificationApi,
  templates: templateApi,
};
