/**
 * Workflow API service — typed wrappers around `/workflows/*` endpoints.
 *
 * Wire format is camelCase via the backend `BaseSchema` alias contract.
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
  pageSize: number;
  totalPages: number;
}

// ============== Definition shapes ==============

export interface ApprovalRuleCreate {
  sequence?: number;
  approverType: ApproverType;
  userId?: string | null;
  roleId?: string | null;
  designation?: string | null;
  dynamicField?: string | null;
  conditions?: Record<string, unknown> | null;
  isMandatory?: boolean;
  canSelfApprove?: boolean;
  fallbackToAdmin?: boolean;
}

export interface ApprovalRuleResponse {
  id: string;
  sequence: number;
  approverType: ApproverType;
  userId: string | null;
  roleId: string | null;
  designation: string | null;
  dynamicField: string | null;
  conditions: Record<string, unknown> | null;
  isMandatory: boolean;
  canSelfApprove: boolean;
  fallbackToAdmin: boolean;
}

export interface EscalationRuleCreate {
  level?: number;
  timeoutHours: number;
  escalationType: EscalationType;
  escalateToType?: ApproverType | null;
  escalateToUserId?: string | null;
  escalateToRoleId?: string | null;
  notifyCurrentApprover?: boolean;
  notifyInitiator?: boolean;
  notificationTemplateId?: string | null;
}

export interface EscalationRuleResponse {
  id: string;
  level: number;
  timeoutHours: number;
  escalationType: EscalationType;
  escalateToType: ApproverType | null;
  escalateToUserId: string | null;
  escalateToRoleId: string | null;
  notifyCurrentApprover: boolean;
  notifyInitiator: boolean;
  notificationTemplateId: string | null;
}

export interface WorkflowStepCreate {
  stepNumber: number;
  name: string;
  description?: string | null;
  stepType?: WorkflowStepType;
  approvalMode?: ApprovalMode;
  parentStepId?: string | null;
  branchName?: string | null;
  entryConditions?: Record<string, unknown> | null;
  exitConditions?: Record<string, unknown> | null;
  onApproveStepId?: string | null;
  onRejectStepId?: string | null;
  onApproveAction?: StepAction;
  onRejectAction?: StepAction;
  allowDelegation?: boolean;
  slaHours?: number | null;
  reminderHours?: number | null;
  approvalRules?: ApprovalRuleCreate[];
  escalationRules?: EscalationRuleCreate[];
}

export interface WorkflowStepResponse {
  id: string;
  stepNumber: number;
  name: string;
  description: string | null;
  stepType: WorkflowStepType;
  approvalMode: ApprovalMode;
  parentStepId: string | null;
  branchName: string | null;
  entryConditions: Record<string, unknown> | null;
  exitConditions: Record<string, unknown> | null;
  onApproveStepId: string | null;
  onRejectStepId: string | null;
  onApproveAction: StepAction;
  onRejectAction: StepAction;
  allowDelegation: boolean;
  slaHours: number | null;
  reminderHours: number | null;
  approvalRules: ApprovalRuleResponse[];
  escalationRules: EscalationRuleResponse[];
}

export interface WorkflowDefinitionCreate {
  name: string;
  code: string;
  description?: string | null;
  entityType: WorkflowEntityType;
  isDefault?: boolean;
  priority?: number;
  activationConditions?: Record<string, unknown> | null;
  allowParallelBranches?: boolean;
  requireCommentsOnReject?: boolean;
  notifyInitiatorOnComplete?: boolean;
  allowWithdrawal?: boolean;
  steps?: WorkflowStepCreate[];
}

export interface WorkflowDefinitionUpdate {
  name?: string;
  description?: string | null;
  isDefault?: boolean;
  priority?: number;
  activationConditions?: Record<string, unknown> | null;
  allowParallelBranches?: boolean;
  requireCommentsOnReject?: boolean;
  notifyInitiatorOnComplete?: boolean;
  allowWithdrawal?: boolean;
}

export interface WorkflowDefinitionResponse {
  id: string;
  name: string;
  code: string;
  description: string | null;
  entityType: WorkflowEntityType;
  isDefault: boolean;
  priority: number;
  activationConditions: Record<string, unknown> | null;
  allowParallelBranches: boolean;
  requireCommentsOnReject: boolean;
  notifyInitiatorOnComplete: boolean;
  allowWithdrawal: boolean;
  version: number;
  createdAt: string;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
  isActive: boolean;
}

export interface WorkflowDefinitionWithStepsResponse extends WorkflowDefinitionResponse {
  steps: WorkflowStepResponse[];
}

// ============== Instance + Task shapes ==============

export interface WorkflowTaskResponse {
  id: string;
  workflowInstanceId: string;
  workflowStepId: string;
  stepName: string | null;
  stepNumber: number | null;
  assignedTo: string;
  assigneeName: string | null;
  assignedAt: string;
  status: TaskStatus;
  actionTaken: string | null;
  comments: string | null;
  actedAt: string | null;
  delegatedFrom: string | null;
  delegatedReason: string | null;
  delegatedAt: string | null;
  escalationLevel: number;
  escalatedAt: string | null;
  dueAt: string | null;
  isOverdue: boolean;
  sequence: number;
  createdAt: string;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
  isActive: boolean;
}

export interface WorkflowHistoryResponse {
  id: string;
  action: string;
  actionBy: string;
  actorName: string | null;
  actionAt: string;
  fromStepId: string | null;
  fromStepName: string | null;
  toStepId: string | null;
  toStepName: string | null;
  fromStatus: string | null;
  toStatus: string;
  comments: string | null;
  actionMetadata: Record<string, unknown> | null;
}

export interface WorkflowInstanceResponse {
  id: string;
  workflowDefinitionId: string;
  workflowName: string | null;
  entityType: WorkflowEntityType;
  entityId: string;
  entityReference: string;
  currentStepId: string | null;
  currentStepName: string | null;
  currentStepNumber: number;
  status: WorkflowInstanceStatus;
  startedAt: string;
  startedBy: string;
  initiatorName: string | null;
  completedAt: string | null;
  completedBy: string | null;
  cancelledAt: string | null;
  cancelledBy: string | null;
  cancellationReason: string | null;
  createdAt: string;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
  isActive: boolean;
}

export interface WorkflowInstanceDetailResponse extends WorkflowInstanceResponse {
  contextData: Record<string, unknown> | null;
  tasks: WorkflowTaskResponse[];
  history: WorkflowHistoryResponse[];
}

// ============== Filter shapes ==============

export interface DefinitionListFilters {
  entityType?: WorkflowEntityType;
  page?: number;
  pageSize?: number;
}

export interface InstanceListFilters {
  entityType?: WorkflowEntityType;
  status?: WorkflowInstanceStatus;
  page?: number;
  pageSize?: number;
}

export type PendingTaskFilters = Record<string, never>;

// ============== Action request bodies ==============

export interface ApprovalActionRequest {
  action: 'APPROVE' | 'REJECT';
  comments?: string | null;
}

export interface DelegateTaskRequest {
  delegateTo: string;
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
