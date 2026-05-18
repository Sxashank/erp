/**
 * Workflow API service — typed wrappers around `/workflows/*` endpoints.
 *
 * Wire format is snake_case (the BE workflow schemas inherit from
 * `BaseSchema`, not `CamelSchema`). See `backend/app/schemas/workflow/`.
 *
 * Mutating endpoints (POST/PUT/DELETE) send an `Idempotency-Key` header.
 * Workflow approvals trigger downstream maker-checker effects so they are
 * treated as financial-adjacent mutations (CLAUDE.md §6.3, §8.4).
 */

import api from '../api';

// ============== Enums (mirror backend `app/models/workflow/enums.py`) ==============

export type WorkflowEntityType =
  | 'VOUCHER'
  | 'PURCHASE_BILL'
  | 'SALES_INVOICE'
  | 'PAYMENT'
  | 'JOURNAL_ENTRY'
  | 'LOAN_APPLICATION'
  | 'LOAN_SANCTION'
  | 'LOAN_RATING';

export type WorkflowStepType = 'APPROVAL' | 'NOTIFICATION' | 'CONDITIONAL' | 'PARALLEL_GATE';

export type ApprovalMode = 'SEQUENTIAL' | 'PARALLEL_ANY' | 'PARALLEL_ALL';

export type ApproverType =
  | 'USER'
  | 'ROLE'
  | 'DESIGNATION'
  | 'DEPARTMENT_HEAD'
  | 'REPORTING_MANAGER'
  | 'DYNAMIC';

export type EscalationType = 'NOTIFY' | 'REASSIGN' | 'AUTO_APPROVE' | 'AUTO_REJECT';

export type StepAction = 'NEXT' | 'COMPLETE' | 'GOTO' | 'REJECT' | 'PREVIOUS';

export type WorkflowInstanceStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'ESCALATED';

export type TaskStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'ESCALATED' | 'SKIPPED';

// ============== Shared wire shapes ==============

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============== Definition shapes ==============

export interface ApprovalRuleCreate {
  sequence?: number;
  approver_type: ApproverType;
  user_id?: string | null;
  role_id?: string | null;
  designation?: string | null;
  dynamic_field?: string | null;
  conditions?: Record<string, unknown> | null;
  is_mandatory?: boolean;
  can_self_approve?: boolean;
  fallback_to_admin?: boolean;
}

export interface ApprovalRuleResponse {
  id: string;
  sequence: number;
  approver_type: ApproverType;
  user_id: string | null;
  role_id: string | null;
  designation: string | null;
  dynamic_field: string | null;
  conditions: Record<string, unknown> | null;
  is_mandatory: boolean;
  can_self_approve: boolean;
  fallback_to_admin: boolean;
}

export interface EscalationRuleCreate {
  level?: number;
  timeout_hours: number;
  escalation_type: EscalationType;
  escalate_to_type?: ApproverType | null;
  escalate_to_user_id?: string | null;
  escalate_to_role_id?: string | null;
  notify_current_approver?: boolean;
  notify_initiator?: boolean;
  notification_template_id?: string | null;
}

export interface EscalationRuleResponse {
  id: string;
  level: number;
  timeout_hours: number;
  escalation_type: EscalationType;
  escalate_to_type: ApproverType | null;
  escalate_to_user_id: string | null;
  escalate_to_role_id: string | null;
  notify_current_approver: boolean;
  notify_initiator: boolean;
  notification_template_id: string | null;
}

export interface WorkflowStepCreate {
  step_number: number;
  name: string;
  description?: string | null;
  step_type?: WorkflowStepType;
  approval_mode?: ApprovalMode;
  parent_step_id?: string | null;
  branch_name?: string | null;
  entry_conditions?: Record<string, unknown> | null;
  exit_conditions?: Record<string, unknown> | null;
  on_approve_step_id?: string | null;
  on_reject_step_id?: string | null;
  on_approve_action?: StepAction;
  on_reject_action?: StepAction;
  allow_delegation?: boolean;
  sla_hours?: number | null;
  reminder_hours?: number | null;
  approval_rules?: ApprovalRuleCreate[];
  escalation_rules?: EscalationRuleCreate[];
}

export interface WorkflowStepResponse {
  id: string;
  step_number: number;
  name: string;
  description: string | null;
  step_type: WorkflowStepType;
  approval_mode: ApprovalMode;
  parent_step_id: string | null;
  branch_name: string | null;
  entry_conditions: Record<string, unknown> | null;
  exit_conditions: Record<string, unknown> | null;
  on_approve_step_id: string | null;
  on_reject_step_id: string | null;
  on_approve_action: StepAction;
  on_reject_action: StepAction;
  allow_delegation: boolean;
  sla_hours: number | null;
  reminder_hours: number | null;
  approval_rules: ApprovalRuleResponse[];
  escalation_rules: EscalationRuleResponse[];
}

export interface WorkflowDefinitionCreate {
  organization_id: string;
  name: string;
  code: string;
  description?: string | null;
  entity_type: WorkflowEntityType;
  is_default?: boolean;
  priority?: number;
  activation_conditions?: Record<string, unknown> | null;
  allow_parallel_branches?: boolean;
  require_comments_on_reject?: boolean;
  notify_initiator_on_complete?: boolean;
  allow_withdrawal?: boolean;
  steps?: WorkflowStepCreate[];
}

export interface WorkflowDefinitionUpdate {
  name?: string;
  description?: string | null;
  is_default?: boolean;
  priority?: number;
  activation_conditions?: Record<string, unknown> | null;
  allow_parallel_branches?: boolean;
  require_comments_on_reject?: boolean;
  notify_initiator_on_complete?: boolean;
  allow_withdrawal?: boolean;
}

export interface WorkflowDefinitionResponse {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  description: string | null;
  entity_type: WorkflowEntityType;
  is_default: boolean;
  priority: number;
  activation_conditions: Record<string, unknown> | null;
  allow_parallel_branches: boolean;
  require_comments_on_reject: boolean;
  notify_initiator_on_complete: boolean;
  allow_withdrawal: boolean;
  version: number;
  created_at: string;
  updated_at: string | null;
  created_by: string | null;
  updated_by: string | null;
  is_active: boolean;
}

export interface WorkflowDefinitionWithStepsResponse extends WorkflowDefinitionResponse {
  steps: WorkflowStepResponse[];
}

// ============== Instance + Task shapes ==============

export interface WorkflowTaskResponse {
  id: string;
  workflow_instance_id: string;
  workflow_step_id: string;
  step_name: string | null;
  step_number: number | null;
  assigned_to: string;
  assignee_name: string | null;
  assigned_at: string;
  status: TaskStatus;
  action_taken: string | null;
  comments: string | null;
  acted_at: string | null;
  delegated_from: string | null;
  delegated_reason: string | null;
  delegated_at: string | null;
  escalation_level: number;
  escalated_at: string | null;
  due_at: string | null;
  is_overdue: boolean;
  sequence: number;
  created_at: string;
  updated_at: string | null;
  created_by: string | null;
  updated_by: string | null;
  is_active: boolean;
}

export interface WorkflowHistoryResponse {
  id: string;
  action: string;
  action_by: string;
  actor_name: string | null;
  action_at: string;
  from_step_id: string | null;
  from_step_name: string | null;
  to_step_id: string | null;
  to_step_name: string | null;
  from_status: string | null;
  to_status: string;
  comments: string | null;
  action_metadata: Record<string, unknown> | null;
}

export interface WorkflowInstanceResponse {
  id: string;
  workflow_definition_id: string;
  workflow_name: string | null;
  organization_id: string;
  entity_type: WorkflowEntityType;
  entity_id: string;
  entity_reference: string;
  current_step_id: string | null;
  current_step_name: string | null;
  current_step_number: number;
  status: WorkflowInstanceStatus;
  started_at: string;
  started_by: string;
  initiator_name: string | null;
  completed_at: string | null;
  completed_by: string | null;
  cancelled_at: string | null;
  cancelled_by: string | null;
  cancellation_reason: string | null;
  created_at: string;
  updated_at: string | null;
  created_by: string | null;
  updated_by: string | null;
  is_active: boolean;
}

export interface WorkflowInstanceDetailResponse extends WorkflowInstanceResponse {
  context_data: Record<string, unknown> | null;
  tasks: WorkflowTaskResponse[];
  history: WorkflowHistoryResponse[];
}

// ============== Filter shapes ==============

export interface DefinitionListFilters {
  organization_id: string;
  entity_type?: WorkflowEntityType;
  page?: number;
  page_size?: number;
}

export interface InstanceListFilters {
  organization_id: string;
  entity_type?: WorkflowEntityType;
  status?: WorkflowInstanceStatus;
  page?: number;
  page_size?: number;
}

export interface PendingTaskFilters {
  organization_id?: string;
}

// ============== Action request bodies ==============

export interface ApprovalActionRequest {
  action: 'APPROVE' | 'REJECT';
  comments?: string | null;
}

export interface DelegateTaskRequest {
  delegate_to: string;
  reason: string;
}

export interface CancelWorkflowRequest {
  reason: string;
}

// ============== Helpers ==============

/**
 * Build an `Idempotency-Key` header. Workflow mutations are routed through
 * the BE maker-checker engine — they MUST be idempotent so a retried POST
 * does not double-approve a task.
 */
function idempotencyHeaders(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

function buildParams(filters: object | undefined): string {
  if (!filters) return '';
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === '') continue;
    params.append(key, String(value));
  }
  const s = params.toString();
  return s ? `?${s}` : '';
}

// ============== Definitions API ==============

const DEFINITIONS_BASE = '/workflows/definitions';

export const definitionsApi = {
  list: async (
    filters: DefinitionListFilters,
  ): Promise<PaginatedResponse<WorkflowDefinitionResponse>> => {
    const response = await api.get<PaginatedResponse<WorkflowDefinitionResponse>>(
      `${DEFINITIONS_BASE}${buildParams(filters)}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<WorkflowDefinitionWithStepsResponse> => {
    const response = await api.get<WorkflowDefinitionWithStepsResponse>(
      `${DEFINITIONS_BASE}/${id}`,
    );
    return response.data;
  },

  create: async (body: WorkflowDefinitionCreate): Promise<WorkflowDefinitionWithStepsResponse> => {
    const response = await api.post<WorkflowDefinitionWithStepsResponse>(DEFINITIONS_BASE, body, {
      headers: idempotencyHeaders(),
    });
    return response.data;
  },

  update: async (
    id: string,
    body: WorkflowDefinitionUpdate,
  ): Promise<WorkflowDefinitionResponse> => {
    const response = await api.put<WorkflowDefinitionResponse>(`${DEFINITIONS_BASE}/${id}`, body, {
      headers: idempotencyHeaders(),
    });
    return response.data;
  },

  delete: async (id: string): Promise<{ message: string }> => {
    const response = await api.delete<{ message: string }>(`${DEFINITIONS_BASE}/${id}`, {
      headers: idempotencyHeaders(),
    });
    return response.data;
  },

  setDefault: async (id: string): Promise<WorkflowDefinitionResponse> => {
    const response = await api.post<WorkflowDefinitionResponse>(
      `${DEFINITIONS_BASE}/${id}/set-default`,
      null,
      { headers: idempotencyHeaders() },
    );
    return response.data;
  },
};

// ============== Instances API ==============

const INSTANCES_BASE = '/workflows/instances';

export const instancesApi = {
  list: async (
    filters: InstanceListFilters,
  ): Promise<PaginatedResponse<WorkflowInstanceResponse>> => {
    const response = await api.get<PaginatedResponse<WorkflowInstanceResponse>>(
      `${INSTANCES_BASE}${buildParams(filters)}`,
    );
    return response.data;
  },

  get: async (id: string): Promise<WorkflowInstanceDetailResponse> => {
    const response = await api.get<WorkflowInstanceDetailResponse>(`${INSTANCES_BASE}/${id}`);
    return response.data;
  },

  history: async (id: string): Promise<WorkflowHistoryResponse[]> => {
    const response = await api.get<WorkflowHistoryResponse[]>(`${INSTANCES_BASE}/${id}/history`);
    return response.data;
  },

  cancel: async (id: string, body: CancelWorkflowRequest): Promise<WorkflowInstanceResponse> => {
    const response = await api.post<WorkflowInstanceResponse>(
      `${INSTANCES_BASE}/${id}/cancel`,
      body,
      { headers: idempotencyHeaders() },
    );
    return response.data;
  },
};

// ============== Tasks API ==============

const TASKS_BASE = '/workflows/tasks';

export const tasksApi = {
  pending: async (filters?: PendingTaskFilters): Promise<WorkflowTaskResponse[]> => {
    const response = await api.get<WorkflowTaskResponse[]>(
      `${TASKS_BASE}/pending${buildParams(filters)}`,
    );
    return response.data;
  },

  approve: async (
    id: string,
    body: ApprovalActionRequest,
  ): Promise<WorkflowInstanceDetailResponse> => {
    const response = await api.post<WorkflowInstanceDetailResponse>(
      `${TASKS_BASE}/${id}/approve`,
      body,
      { headers: idempotencyHeaders() },
    );
    return response.data;
  },

  delegate: async (id: string, body: DelegateTaskRequest): Promise<WorkflowTaskResponse> => {
    const response = await api.post<WorkflowTaskResponse>(`${TASKS_BASE}/${id}/delegate`, body, {
      headers: idempotencyHeaders(),
    });
    return response.data;
  },
};

export const workflowApi = {
  definitions: definitionsApi,
  instances: instancesApi,
  tasks: tasksApi,
};

export default workflowApi;
