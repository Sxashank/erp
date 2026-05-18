import api from '@/services/api';
import type {
  AssetCategory,
  AssetCategoryTreeNode,
  AssetRegisterReport,
  ApprovalRequestStatus,
  AssetTransferRecord,
  AssetRevaluationRecord,
  DepreciationEntry,
  DepreciationPostingActionResponse,
  DepreciationRun,
  DepreciationScheduleResponse,
  DepreciationSummaryReport,
  Discrepancy,
  DisposalActionResponse,
  DisposalRegisterItem,
  FixedAsset,
  MasterOption,
  OffsetPaginatedResponse,
  VerificationEntry,
  VerificationSchedule,
  VerificationSummary,
} from '@/types/fixed-assets';

export interface FixedAssetListFilters {
  organizationId: string;
  categoryId?: string;
  locationId?: string;
  status?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface AssetCategoryListFilters {
  organizationId: string;
  skip?: number;
  limit?: number;
}

export interface AssetCategoryPayload {
  organizationId: string;
  categoryCode: string;
  categoryName: string;
  description?: string | null;
  parentCategoryId?: string | null;
  assetType: string;
  depreciationMethod: string;
  usefulLifeYears: number;
  residualValuePct: number;
  depreciationRateSlm: number;
  depreciationRateWdv: number;
  itActRate?: number | null;
  itActBlock?: string | null;
  capitalizationThreshold: number;
  glAssetAccountId?: string | null;
  glAccumDepAccountId?: string | null;
  glDepExpenseAccountId?: string | null;
  glDisposalGainAccountId?: string | null;
  glDisposalLossAccountId?: string | null;
  glRevaluationReserveAccountId?: string | null;
  glImpairmentAccountId?: string | null;
  requiresInsurance?: boolean;
  requiresAmc?: boolean;
}

export interface FixedAssetPayload {
  organizationId: string;
  assetName: string;
  description?: string | null;
  categoryId: string;
  locationId?: string | null;
  departmentId?: string | null;
  custodianEmployeeId?: string | null;
  acquisitionDate: string;
  putToUseDate?: string | null;
  acquisitionType: string;
  vendorId?: string | null;
  invoiceNumber?: string | null;
  invoiceDate?: string | null;
  poNumber?: string | null;
  acquisitionCost: number;
  installationCost?: number;
  otherCosts?: number;
  residualValue?: number | null;
  usefulLifeMonths?: number | null;
  depreciationMethod?: string | null;
  depreciationRate?: number | null;
  make?: string | null;
  model?: string | null;
  serialNumber?: string | null;
  quantity?: number;
  warrantyStartDate?: string | null;
  warrantyExpiryDate?: string | null;
  tags?: Record<string, unknown> | null;
}

export interface AssetCapitalizePayload {
  capitalizationDate: string;
  putToUseDate?: string | null;
  depreciationStartDate?: string | null;
  remarks?: string | null;
}

export interface AssetTransferPayload {
  transferDate: string;
  toLocationId?: string | null;
  toDepartmentId?: string | null;
  toCustodianId?: string | null;
  reason?: string | null;
}

export interface AssetRevaluePayload {
  revaluationDate: string;
  newValue: number;
  valuerName?: string | null;
  valuationReportNumber?: string | null;
  valuationReportDate?: string | null;
  valuationMethod?: string | null;
  reason?: string | null;
}

export interface AssetImpairPayload {
  impairmentDate: string;
  impairmentAmount: number;
  reason?: string | null;
}

export interface AssetDisposePayload {
  disposalDate: string;
  disposalType: string;
  disposalValue: number;
  disposalRemarks?: string | null;
  buyerName?: string | null;
  buyerAddress?: string | null;
}

export interface DepreciationRunPayload {
  organizationId: string;
  depreciationPeriod: string;
  depreciationBook?: 'COMPANIES_ACT' | 'IT_ACT';
  remarks?: string | null;
}

export interface VerificationSchedulePayload {
  organizationId: string;
  scheduleName: string;
  financialYear: string;
  locationId?: string | null;
  categoryIds?: string[] | null;
  scheduledStartDate: string;
  scheduledEndDate: string;
  assignedTo?: string | null;
  teamMembers?: string[] | null;
  remarks?: string | null;
}

export interface VerifyEntryPayload {
  assetId: string;
  verificationDate: string;
  verificationResult: string;
  assetCondition?: string | null;
  actualLocationId?: string | null;
  actualDepartmentId?: string | null;
  photoUrls?: string[] | null;
  barcodeScan?: string | null;
  conditionNotes?: string | null;
  remarks?: string | null;
}

export interface DiscrepancyUpdatePayload {
  status?: string;
  investigationNotes?: string | null;
  resolution?: string | null;
  remarks?: string | null;
}

export interface FixedAssetReportFilters {
  organizationId: string;
  categoryId?: string;
  locationId?: string;
  asOnDate?: string;
  includeDisposed?: boolean;
}

function mapOption(item: { id: string; code?: string | null; name?: string | null }): MasterOption {
  return {
    id: item.id,
    code: item.code ?? null,
    name: item.name ?? item.code ?? item.id,
  };
}

function idempotencyHeaders(): Record<string, string> {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

export async function listAssetCategories(
  filters: AssetCategoryListFilters,
): Promise<OffsetPaginatedResponse<AssetCategory>> {
  const { data } = await api.get<OffsetPaginatedResponse<AssetCategory>>('/fixed-assets/categories', {
    params: {
      organization_id: filters.organizationId,
      skip: filters.skip ?? 0,
      limit: filters.limit ?? 100,
    },
  });
  return data;
}

export async function getAssetCategoryTree(
  organizationId: string,
): Promise<AssetCategoryTreeNode[]> {
  const { data } = await api.get<AssetCategoryTreeNode[]>('/fixed-assets/categories/tree', {
    params: { organization_id: organizationId },
  });
  return data;
}

export async function getAssetCategory(id: string): Promise<AssetCategory> {
  const { data } = await api.get<AssetCategory>(`/fixed-assets/categories/${id}`);
  return data;
}

export async function createAssetCategory(payload: AssetCategoryPayload): Promise<AssetCategory> {
  const { data } = await api.post<AssetCategory>('/fixed-assets/categories', payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function updateAssetCategory(
  id: string,
  payload: Partial<AssetCategoryPayload>,
): Promise<AssetCategory> {
  const { data } = await api.put<AssetCategory>(`/fixed-assets/categories/${id}`, payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function deleteAssetCategory(id: string): Promise<void> {
  await api.delete(`/fixed-assets/categories/${id}`, {
    headers: idempotencyHeaders(),
  });
}

export async function listFixedAssets(
  filters: FixedAssetListFilters,
): Promise<OffsetPaginatedResponse<FixedAsset>> {
  const { data } = await api.get<OffsetPaginatedResponse<FixedAsset>>('/fixed-assets/assets', {
    params: {
      organization_id: filters.organizationId,
      category_id: filters.categoryId,
      location_id: filters.locationId,
      status: filters.status,
      search: filters.search,
      skip: filters.skip ?? 0,
      limit: filters.limit ?? 20,
    },
  });
  return data;
}

export async function getFixedAsset(id: string): Promise<FixedAsset> {
  const { data } = await api.get<FixedAsset>(`/fixed-assets/assets/${id}`);
  return data;
}

export async function createFixedAsset(payload: FixedAssetPayload): Promise<FixedAsset> {
  const { data } = await api.post<FixedAsset>('/fixed-assets/assets', payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function updateFixedAsset(
  id: string,
  payload: Partial<FixedAssetPayload>,
): Promise<FixedAsset> {
  const { data } = await api.put<FixedAsset>(`/fixed-assets/assets/${id}`, payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function deleteFixedAsset(id: string): Promise<void> {
  await api.delete(`/fixed-assets/assets/${id}`, {
    headers: idempotencyHeaders(),
  });
}

export async function capitalizeFixedAsset(
  id: string,
  payload: AssetCapitalizePayload,
): Promise<FixedAsset> {
  const { data } = await api.post<FixedAsset>(`/fixed-assets/assets/${id}/capitalize`, payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function transferFixedAsset(
  id: string,
  payload: AssetTransferPayload,
): Promise<AssetTransferRecord> {
  const { data } = await api.post<AssetTransferRecord>(`/fixed-assets/assets/${id}/transfer`, payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function revalueFixedAsset(
  id: string,
  payload: AssetRevaluePayload,
): Promise<AssetRevaluationRecord> {
  const { data } = await api.post<AssetRevaluationRecord>(`/fixed-assets/assets/${id}/revalue`, payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function impairFixedAsset(
  id: string,
  payload: AssetImpairPayload,
): Promise<AssetRevaluationRecord> {
  const { data } = await api.post<AssetRevaluationRecord>(`/fixed-assets/assets/${id}/impair`, payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function disposeFixedAsset(
  id: string,
  payload: AssetDisposePayload,
): Promise<FixedAsset> {
  const { data } = await api.post<FixedAsset>(`/fixed-assets/assets/${id}/dispose`, payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function listDisposals(
  organizationId: string,
  params?: {
    status?: string;
    disposalType?: string;
    search?: string;
    skip?: number;
    limit?: number;
  },
): Promise<OffsetPaginatedResponse<DisposalRegisterItem>> {
  const { data } = await api.get<OffsetPaginatedResponse<DisposalRegisterItem>>('/fixed-assets/disposals', {
    params: {
      organization_id: organizationId,
      status: params?.status,
      disposal_type: params?.disposalType,
      search: params?.search,
      skip: params?.skip ?? 0,
      limit: params?.limit ?? 20,
    },
  });
  return data;
}

export async function getDisposal(assetId: string): Promise<DisposalRegisterItem> {
  const { data } = await api.get<DisposalRegisterItem>(`/fixed-assets/disposals/${assetId}`);
  return data;
}

export async function submitDisposal(
  assetId: string,
  payload: AssetDisposePayload,
): Promise<DisposalActionResponse> {
  const { data } = await api.post<DisposalActionResponse>(
    `/fixed-assets/disposals/${assetId}/submit`,
    payload,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function listDepreciationRuns(
  organizationId: string,
  params?: { skip?: number; limit?: number },
): Promise<OffsetPaginatedResponse<DepreciationRun>> {
  const { data } = await api.get<OffsetPaginatedResponse<DepreciationRun>>('/fixed-assets/depreciation/runs', {
    params: {
      organization_id: organizationId,
      skip: params?.skip ?? 0,
      limit: params?.limit ?? 20,
    },
  });
  return data;
}

export async function getDepreciationRun(runId: string): Promise<DepreciationRun> {
  const { data } = await api.get<DepreciationRun>(`/fixed-assets/depreciation/runs/${runId}`);
  return data;
}

export async function runDepreciation(payload: DepreciationRunPayload): Promise<DepreciationRun> {
  const { data } = await api.post<DepreciationRun>('/fixed-assets/depreciation/run', payload, {
    headers: idempotencyHeaders(),
  });
  return data;
}

export async function submitDepreciationPosting(
  runId: string,
): Promise<DepreciationPostingActionResponse> {
  const { data } = await api.post<DepreciationPostingActionResponse>(
    `/fixed-assets/depreciation/runs/${runId}/submit-posting`,
    undefined,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function getDepreciationRunEntries(
  runId: string,
  params?: { skip?: number; limit?: number },
): Promise<OffsetPaginatedResponse<DepreciationEntry>> {
  const { data } = await api.get<OffsetPaginatedResponse<DepreciationEntry>>(
    `/fixed-assets/depreciation/runs/${runId}/entries`,
    {
      params: {
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 50,
      },
    },
  );
  return data;
}

export async function getAssetDepreciationHistory(
  assetId: string,
  params?: { skip?: number; limit?: number },
): Promise<OffsetPaginatedResponse<DepreciationEntry>> {
  const { data } = await api.get<OffsetPaginatedResponse<DepreciationEntry>>(
    `/fixed-assets/depreciation/history/${assetId}`,
    {
      params: {
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 50,
      },
    },
  );
  return data;
}

export async function getAssetDepreciationSchedule(
  assetId: string,
): Promise<DepreciationScheduleResponse> {
  const { data } = await api.get<DepreciationScheduleResponse>(
    `/fixed-assets/depreciation/schedule/${assetId}`,
  );
  return data;
}

export async function listVerificationSchedules(
  organizationId: string,
  params?: { financialYear?: string; status?: string; skip?: number; limit?: number },
): Promise<OffsetPaginatedResponse<VerificationSchedule>> {
  const { data } = await api.get<OffsetPaginatedResponse<VerificationSchedule>>(
    '/fixed-assets/verification/schedules',
    {
      params: {
        organization_id: organizationId,
        financial_year: params?.financialYear,
        status: params?.status,
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 20,
      },
    },
  );
  return data;
}

export async function getVerificationSchedule(scheduleId: string): Promise<VerificationSchedule> {
  const { data } = await api.get<VerificationSchedule>(
    `/fixed-assets/verification/schedules/${scheduleId}`,
  );
  return data;
}

export async function createVerificationSchedule(
  payload: VerificationSchedulePayload,
): Promise<VerificationSchedule> {
  const { data } = await api.post<VerificationSchedule>(
    '/fixed-assets/verification/schedules',
    payload,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function updateVerificationSchedule(
  scheduleId: string,
  payload: Partial<VerificationSchedulePayload>,
): Promise<VerificationSchedule> {
  const { data } = await api.put<VerificationSchedule>(
    `/fixed-assets/verification/schedules/${scheduleId}`,
    payload,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function startVerificationSchedule(scheduleId: string): Promise<VerificationSchedule> {
  const { data } = await api.post<VerificationSchedule>(
    `/fixed-assets/verification/schedules/${scheduleId}/start`,
    undefined,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function completeVerificationSchedule(
  scheduleId: string,
): Promise<VerificationSchedule> {
  const { data } = await api.post<VerificationSchedule>(
    `/fixed-assets/verification/schedules/${scheduleId}/complete`,
    undefined,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function approveVerificationSchedule(
  scheduleId: string,
): Promise<VerificationSchedule> {
  const { data } = await api.post<VerificationSchedule>(
    `/fixed-assets/verification/schedules/${scheduleId}/approve`,
    undefined,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function listVerificationEntries(
  scheduleId: string,
  params?: { verificationResult?: string; skip?: number; limit?: number },
): Promise<OffsetPaginatedResponse<VerificationEntry>> {
  const { data } = await api.get<OffsetPaginatedResponse<VerificationEntry>>(
    `/fixed-assets/verification/schedules/${scheduleId}/entries`,
    {
      params: {
        verification_result: params?.verificationResult,
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 100,
      },
    },
  );
  return data;
}

export async function verifyVerificationEntry(
  entryId: string,
  payload: VerifyEntryPayload,
): Promise<VerificationEntry> {
  const { data } = await api.put<VerificationEntry>(
    `/fixed-assets/verification/entries/${entryId}/verify`,
    payload,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function listDiscrepancies(
  organizationId: string,
  params?: { status?: string; skip?: number; limit?: number },
): Promise<OffsetPaginatedResponse<Discrepancy>> {
  const { data } = await api.get<OffsetPaginatedResponse<Discrepancy>>(
    '/fixed-assets/verification/discrepancies',
    {
      params: {
        organization_id: organizationId,
        status: params?.status,
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 100,
      },
    },
  );
  return data;
}

export async function updateDiscrepancy(
  discrepancyId: string,
  payload: DiscrepancyUpdatePayload,
): Promise<Discrepancy> {
  const { data } = await api.put<Discrepancy>(
    `/fixed-assets/verification/discrepancies/${discrepancyId}`,
    payload,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}

export async function getVerificationSummary(
  organizationId: string,
  financialYear: string,
): Promise<VerificationSummary> {
  const { data } = await api.get<VerificationSummary>('/fixed-assets/verification/summary', {
    params: {
      organization_id: organizationId,
      financial_year: financialYear,
    },
  });
  return data;
}

export async function getAssetRegisterReport(
  filters: FixedAssetReportFilters,
): Promise<AssetRegisterReport> {
  const { data } = await api.get<AssetRegisterReport>('/fixed-assets/reports/asset-register', {
    params: {
      organization_id: filters.organizationId,
      category_id: filters.categoryId,
      location_id: filters.locationId,
      as_on_date: filters.asOnDate,
      include_disposed: filters.includeDisposed,
    },
  });
  return data;
}

export async function getDepreciationSummaryReport(
  organizationId: string,
  depreciationPeriod: string,
): Promise<DepreciationSummaryReport> {
  const { data } = await api.get<DepreciationSummaryReport>(
    '/fixed-assets/reports/depreciation-summary',
    {
      params: {
        organization_id: organizationId,
        depreciation_period: depreciationPeriod,
      },
    },
  );
  return data;
}

export async function listAccounts(organizationId: string): Promise<MasterOption[]> {
  const { data } = await api.get<{
    items: { id: string; code?: string | null; name?: string | null }[];
  }>('/accounts', {
    params: { organization_id: organizationId, page_size: 100 },
  });
  return (data.items ?? []).map(mapOption);
}

export async function listUnits(organizationId: string): Promise<MasterOption[]> {
  const { data } = await api.get<{
    items: { id: string; code?: string | null; name?: string | null }[];
  }>('/units', {
    params: { organization_id: organizationId, page_size: 100 },
  });
  return (data.items ?? []).map(mapOption);
}

export async function listDepartments(organizationId: string): Promise<MasterOption[]> {
  const { data } = await api.get<{
    items: { id: string; code?: string | null; name?: string | null }[];
  }>('/departments', {
    params: { organization_id: organizationId, page_size: 100 },
  });
  return (data.items ?? []).map(mapOption);
}

export async function listVendors(organizationId: string): Promise<MasterOption[]> {
  const { data } = await api.get<{
    items: { id: string; code?: string | null; name?: string | null }[];
  }>('/vendors', {
    params: { organization_id: organizationId, page_size: 100 },
  });
  return (data.items ?? []).map(mapOption);
}

export interface ApprovalActionPayload {
  action: 'APPROVE' | 'REJECT' | 'RETURN';
  comments?: string | null;
}

export interface ApprovalRequestResponse {
  id: string;
  requestNumber: string;
  workflowType: string;
  entityType: string;
  entityId: string;
  requestAmount: string;
  requestSummary: string;
  requestedAt: string;
  status: ApprovalRequestStatus;
  currentLevel: number;
  totalLevels: number;
}

export async function takeApprovalAction(
  requestId: string,
  payload: ApprovalActionPayload,
): Promise<ApprovalRequestResponse> {
  const { data } = await api.post<ApprovalRequestResponse>(
    `/approvals/requests/${requestId}/action`,
    payload,
    {
      headers: idempotencyHeaders(),
    },
  );
  return data;
}
