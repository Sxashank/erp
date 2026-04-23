/**
 * Notification system types
 */

export type NotificationChannel = 'email' | 'sms' | 'push' | 'in_app' | 'whatsapp';
export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent';
export type NotificationStatus = 'pending' | 'queued' | 'sent' | 'delivered' | 'read' | 'failed' | 'cancelled';
export type NotificationCategory = 'system' | 'workflow' | 'loan' | 'payment' | 'collection' | 'reminder' | 'alert' | 'announcement' | 'marketing';
export type NotificationTemplateType = 'transactional' | 'marketing' | 'system' | 'reminder' | 'alert';

export interface Notification {
  id: string;
  organization_id: string;
  user_id?: string;
  recipient_email?: string;
  recipient_phone?: string;
  template_id?: string;

  title: string;
  message: string;
  html_content?: string;

  category: NotificationCategory;
  priority: NotificationPriority;
  channels: NotificationChannel[];
  status: NotificationStatus;

  read_at?: string;
  sent_at?: string;
  delivered_at?: string;

  entity_type?: string;
  entity_id?: string;
  entity_reference?: string;

  action_url?: string;
  action_label?: string;

  metadata?: Record<string, any>;
  scheduled_at?: string;
  expires_at?: string;

  retry_count: number;
  max_retries: number;

  created_at: string;
  created_by?: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
  unread_count: number;
}

export interface NotificationCreate {
  title: string;
  message: string;
  html_content?: string;

  user_id?: string;
  recipient_email?: string;
  recipient_phone?: string;

  category?: NotificationCategory;
  priority?: NotificationPriority;
  channels?: NotificationChannel[];

  entity_type?: string;
  entity_id?: string;
  entity_reference?: string;

  action_url?: string;
  action_label?: string;

  template_id?: string;
  metadata?: Record<string, any>;

  scheduled_at?: string;
  expires_at?: string;
}

export interface NotificationPreference {
  id: string;
  user_id: string;
  organization_id?: string;
  category: NotificationCategory;

  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  whatsapp_enabled: boolean;

  digest_mode: boolean;
  digest_frequency?: string;
  quiet_hours_start?: string;
  quiet_hours_end?: string;

  created_at: string;
  updated_at?: string;
}

export interface NotificationPreferenceUpdate {
  email_enabled?: boolean;
  sms_enabled?: boolean;
  push_enabled?: boolean;
  in_app_enabled?: boolean;
  whatsapp_enabled?: boolean;

  digest_mode?: boolean;
  digest_frequency?: string;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

export interface NotificationLog {
  id: string;
  notification_id: string;
  channel: NotificationChannel;
  status: NotificationStatus;
  attempt_number: number;
  attempted_at: string;
  response_code?: string;
  response_message?: string;
  provider?: string;
  provider_message_id?: string;
  cost?: number;
  currency?: string;
}

export interface NotificationStats {
  total_notifications: number;
  unread_count: number;
  read_count: number;
  sent_count: number;
  failed_count: number;
  pending_count: number;
  by_category: Record<string, number>;
  by_channel: Record<string, number>;
  by_priority: Record<string, number>;
}

// Template types
export interface TemplateVariable {
  id: string;
  template_id: string;
  name: string;
  display_name: string;
  description?: string;
  data_type: string;
  format_pattern?: string;
  default_value?: string;
  is_required: boolean;
  validation_regex?: string;
  sample_value?: string;
  display_order: number;
}

export interface NotificationTemplate {
  id: string;
  organization_id?: string;

  code: string;
  name: string;
  description?: string;

  template_type: NotificationTemplateType;
  category: NotificationCategory;

  channels: NotificationChannel[];

  email_subject?: string;
  email_body_html?: string;
  email_body_text?: string;

  sms_body?: string;

  push_title?: string;
  push_body?: string;
  push_image_url?: string;

  in_app_title?: string;
  in_app_message?: string;

  whatsapp_template_id?: string;
  whatsapp_template_params?: string[];

  variables?: string[];
  default_values?: Record<string, string>;

  trigger_event?: string;
  is_active: boolean;
  usage_count: number;

  variable_definitions: TemplateVariable[];

  created_at: string;
  updated_at?: string;
}

export interface NotificationTemplateCreate {
  code: string;
  name: string;
  description?: string;

  template_type?: NotificationTemplateType;
  category?: NotificationCategory;

  channels?: NotificationChannel[];

  email_subject?: string;
  email_body_html?: string;
  email_body_text?: string;

  sms_body?: string;

  push_title?: string;
  push_body?: string;
  push_image_url?: string;

  in_app_title?: string;
  in_app_message?: string;

  whatsapp_template_id?: string;
  whatsapp_template_params?: string[];

  variables?: string[];
  default_values?: Record<string, string>;

  trigger_event?: string;
  is_active?: boolean;
}

export interface NotificationTemplateUpdate {
  name?: string;
  description?: string;

  template_type?: NotificationTemplateType;
  category?: NotificationCategory;

  channels?: NotificationChannel[];

  email_subject?: string;
  email_body_html?: string;
  email_body_text?: string;

  sms_body?: string;

  push_title?: string;
  push_body?: string;
  push_image_url?: string;

  in_app_title?: string;
  in_app_message?: string;

  whatsapp_template_id?: string;
  whatsapp_template_params?: string[];

  variables?: string[];
  default_values?: Record<string, string>;

  trigger_event?: string;
  is_active?: boolean;
}

export interface NotificationTemplateListResponse {
  items: NotificationTemplate[];
  total: number;
  page: number;
  page_size: number;
}

export interface TemplatePreviewRequest {
  template_id?: string;
  template_code?: string;
  context: Record<string, any>;
  channel: NotificationChannel;
}

export interface TemplatePreviewResponse {
  channel: NotificationChannel;
  title?: string;
  subject?: string;
  body: string;
  html_body?: string;
  variables_used: string[];
  missing_variables: string[];
}

export interface SendNotificationRequest {
  template_code: string;
  context: Record<string, any>;
  user_id?: string;
  recipient_email?: string;
  recipient_phone?: string;
  entity_type?: string;
  entity_id?: string;
  entity_reference?: string;
}

export interface BulkNotificationRequest {
  title: string;
  message: string;
  category?: NotificationCategory;
  priority?: NotificationPriority;
  channels?: NotificationChannel[];
  user_ids?: string[];
  department_ids?: string[];
  role_ids?: string[];
  all_users?: boolean;
  action_url?: string;
  action_label?: string;
  metadata?: Record<string, any>;
  scheduled_at?: string;
}
