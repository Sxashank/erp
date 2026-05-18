export interface OffsetPaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface MasterOption {
  id: string;
  code?: string | null;
  name: string;
}

export type AssetType = 'TANGIBLE' | 'INTANGIBLE' | 'RIGHT_OF_USE';
export type DepreciationMethod =
  | 'SLM'
  | 'WDV'
  | 'UNIT_OF_PRODUCTION'
  | 'NO_DEPRECIATION';
export type AssetStatus =
  | 'DRAFT'
  | 'ACTIVE'
  | 'DISPOSED'
  | 'TRANSFERRED'
  | 'UNDER_MAINTENANCE'
  | 'FULLY_DEPRECIATED';
export type AssetAcquisitionType =
  | 'PURCHASE'
  | 'LEASE'
  | 'DONATION'
  | 'TRANSFER_IN'
  | 'CONSTRUCTED';
export type AssetDisposalType = 'SALE' | 'SCRAP' | 'WRITE_OFF' | 'DONATION' | 'LOSS';
export type ApprovalRequestStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'RETURNED'
  | 'CANCELLED';
export type DepreciationRunStatus = 'RUNNING' | 'COMPLETED' | 'POSTED' | 'FAILED';
export type VerificationScheduleStatus =
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED';
export type VerificationResult = 'FOUND' | 'MISSING' | 'MISPLACED' | 'EXCESS';
export type AssetCondition = 'GOOD' | 'FAIR' | 'POOR' | 'DAMAGED' | 'NOT_WORKING';
export type DiscrepancyStatus = 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'WRITTEN_OFF';
export type DisposalRegisterStatus =
  | 'COMPLETED'
  | 'PENDING_APPROVAL'
  | 'REJECTED'
  | 'RETURNED'
  | 'CANCELLED';

export interface AssetCategory {
  id: string;
  organizationId: string;
  categoryCode: string;
  categoryName: string;
  description: string | null;
  parentCategoryId: string | null;
  parentCategoryName: string | null;
  assetType: AssetType;
  depreciationMethod: DepreciationMethod;
  usefulLifeYears: number;
  residualValuePct: string;
  depreciationRateSlm: string;
  depreciationRateWdv: string;
  itActRate: string | null;
  itActBlock: string | null;
  capitalizationThreshold: string;
  glAssetAccountId: string | null;
  glAssetAccountName: string | null;
  glAccumDepAccountId: string | null;
  glAccumDepAccountName: string | null;
  glDepExpenseAccountId: string | null;
  glDepExpenseAccountName: string | null;
  glDisposalGainAccountId: string | null;
  glDisposalLossAccountId: string | null;
  glRevaluationReserveAccountId: string | null;
  glImpairmentAccountId: string | null;
  requiresInsurance: boolean;
  requiresAmc: boolean;
  assetCount: number;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface AssetCategoryTreeNode {
  id: string;
  categoryCode: string;
  categoryName: string;
  assetType: AssetType;
  depreciationMethod: DepreciationMethod;
  usefulLifeYears: number;
  assetCount: number;
  children: AssetCategoryTreeNode[];
}

export interface FixedAsset {
  id: string;
  organizationId: string;
  assetCode: string;
  assetName: string;
  description: string | null;
  categoryId: string;
  categoryCode: string | null;
  categoryName: string | null;
  locationId: string | null;
  locationName: string | null;
  departmentId: string | null;
  departmentName: string | null;
  custodianEmployeeId: string | null;
  custodianName: string | null;
  acquisitionDate: string;
  putToUseDate: string | null;
  acquisitionType: AssetAcquisitionType;
  vendorId: string | null;
  vendorName: string | null;
  invoiceNumber: string | null;
  invoiceDate: string | null;
  poNumber: string | null;
  acquisitionCost: string;
  installationCost: string;
  otherCosts: string;
  totalCost: string;
  residualValue: string;
  depreciableValue: string;
  usefulLifeMonths: number;
  depreciationMethod: DepreciationMethod;
  depreciationRate: string;
  accumulatedDepreciation: string;
  wdvValue: string;
  lastDepreciationDate: string | null;
  depreciationStartDate: string | null;
  revaluationAmount: string;
  impairmentAmount: string;
  make: string | null;
  model: string | null;
  serialNumber: string | null;
  quantity: number;
  warrantyStartDate: string | null;
  warrantyExpiryDate: string | null;
  insurancePolicyNumber: string | null;
  insuranceProvider: string | null;
  insuranceExpiryDate: string | null;
  insuredValue: string | null;
  amcVendorId: string | null;
  amcVendorName: string | null;
  amcStartDate: string | null;
  amcExpiryDate: string | null;
  amcValue: string | null;
  parentAssetId: string | null;
  isComponent: boolean;
  disposalDate: string | null;
  disposalType: AssetDisposalType | null;
  disposalValue: string | null;
  disposalGainLoss: string | null;
  disposalRemarks: string | null;
  status: AssetStatus;
  tags: Record<string, unknown> | null;
  isFullyDepreciated: boolean;
  itActBlock: string | null;
  itActRate: string;
  itAccumulatedDepreciation: string;
  itWdvValue: string;
  itLastDepreciationDate: string | null;
  itLastDepreciationFy: string | null;
  isAdditionalDepreciationEligible: boolean;
  additionalDepreciationClaimed: string;
  depreciationDifference: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface AssetTransferRecord {
  id: string;
  assetId: string;
  assetCode: string | null;
  assetName: string | null;
  transferDate: string;
  transferReference: string | null;
  fromLocationId: string | null;
  fromLocationName: string | null;
  fromDepartmentId: string | null;
  fromDepartmentName: string | null;
  fromCustodianId: string | null;
  toLocationId: string | null;
  toLocationName: string | null;
  toDepartmentId: string | null;
  toDepartmentName: string | null;
  toCustodianId: string | null;
  reason: string | null;
  status: string;
  remarks: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface AssetRevaluationRecord {
  id: string;
  assetId: string;
  assetCode: string | null;
  assetName: string | null;
  revaluationDate: string;
  revaluationType: string;
  previousValue: string;
  newValue: string;
  revaluationAmount: string;
  valuerName: string | null;
  valuationReportNumber: string | null;
  valuationReportDate: string | null;
  valuationMethod: string | null;
  reason: string | null;
  voucherId: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface DepreciationRun {
  id: string;
  organizationId: string;
  depreciationBook: 'COMPANIES_ACT' | 'IT_ACT';
  depreciationPeriod: string;
  periodFrom: string;
  periodTo: string;
  totalAssets: number;
  totalDepreciation: string;
  processedAssets: number;
  skippedAssets: number;
  status: DepreciationRunStatus;
  runStartedAt: string | null;
  runCompletedAt: string | null;
  runBy: string | null;
  voucherId: string | null;
  voucherNumber: string | null;
  postedAt: string | null;
  postedBy: string | null;
  remarks: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface DepreciationEntry {
  id: string;
  assetId: string;
  assetCode: string | null;
  assetName: string | null;
  depreciationRunId: string | null;
  depreciationPeriod: string;
  periodFrom: string;
  periodTo: string;
  daysInPeriod: number;
  openingWdv: string;
  depreciationRate: string;
  depreciationAmount: string;
  accumulatedDepreciation: string;
  closingWdv: string;
  depreciationType: string;
  depreciationBook: 'COMPANIES_ACT' | 'IT_ACT';
  voucherId: string | null;
  isPosted: boolean;
  isReversed: boolean;
  reversalOfId: string | null;
  reversedById: string | null;
  remarks: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface DepreciationScheduleItem {
  period: string;
  periodFrom: string;
  periodTo: string;
  openingWdv: string;
  depreciationRate: string;
  depreciationAmount: string;
  accumulatedDepreciation: string;
  closingWdv: string;
  isFullyDepreciated: boolean;
}

export interface DepreciationScheduleResponse {
  assetId: string;
  assetCode: string;
  assetName: string;
  totalCost: string;
  residualValue: string;
  depreciableValue: string;
  depreciationMethod: DepreciationMethod;
  depreciationRate: string;
  usefulLifeMonths: number;
  currentWdv: string;
  currentAccumulatedDepreciation: string;
  remainingMonths: number;
  schedule: DepreciationScheduleItem[];
}

export interface DepreciationPostingActionResponse {
  mode: 'posted' | 'submitted_for_approval';
  message: string;
  run: DepreciationRun;
  approvalRequestId: string | null;
  approvalRequestNumber: string | null;
  approvalStatus: ApprovalRequestStatus | null;
}

export interface VerificationSchedule {
  id: string;
  organizationId: string;
  scheduleReference: string;
  scheduleName: string;
  financialYear: string;
  locationId: string | null;
  locationName: string | null;
  categoryIds: string[] | null;
  scheduledStartDate: string;
  scheduledEndDate: string;
  actualStartDate: string | null;
  actualEndDate: string | null;
  assignedTo: string | null;
  assignedToName: string | null;
  teamMembers: string[] | null;
  totalAssets: number;
  verifiedCount: number;
  foundCount: number;
  missingCount: number;
  discrepancyCount: number;
  totalValueVerified: string;
  totalValueMissing: string;
  status: VerificationScheduleStatus;
  remarks: string | null;
  approvedBy: string | null;
  approvedAt: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface VerificationEntry {
  id: string;
  scheduleId: string;
  assetId: string;
  assetCode: string | null;
  assetName: string | null;
  categoryName: string | null;
  expectedLocationId: string | null;
  expectedLocationName: string | null;
  expectedDepartmentId: string | null;
  expectedDepartmentName: string | null;
  verificationDate: string | null;
  verifiedBy: string | null;
  verifiedByName: string | null;
  verificationResult: VerificationResult | null;
  assetCondition: AssetCondition | null;
  actualLocationId: string | null;
  actualLocationName: string | null;
  actualDepartmentId: string | null;
  actualDepartmentName: string | null;
  bookValue: string;
  photoUrls: string[] | null;
  barcodeScan: string | null;
  conditionNotes: string | null;
  remarks: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface Discrepancy {
  id: string;
  entryId: string;
  assetId: string | null;
  assetCode: string | null;
  assetName: string | null;
  discrepancyType: string;
  description: string;
  valueImpact: string;
  status: DiscrepancyStatus;
  investigatedBy: string | null;
  investigationNotes: string | null;
  resolution: string | null;
  resolvedBy: string | null;
  resolvedAt: string | null;
  remarks: string | null;
  isActive: boolean;
  createdAt: string | null;
  updatedAt: string | null;
  createdBy: string | null;
  updatedBy: string | null;
}

export interface VerificationSummary {
  organizationId: string;
  financialYear: string;
  totalSchedules: number;
  completedSchedules: number;
  totalAssetsToVerify: number;
  totalAssetsVerified: number;
  totalFound: number;
  totalMissing: number;
  totalDiscrepancies: number;
  openDiscrepancies: number;
  totalValueVerified: string;
  totalValueMissing: string;
  verificationPercentage: string;
}

export interface DisposalRegisterItem {
  assetId: string;
  organizationId: string;
  assetCode: string;
  assetName: string;
  categoryId: string;
  categoryName: string | null;
  disposalType: AssetDisposalType | null;
  disposalDate: string | null;
  requestDate: string | null;
  requestedBy: string | null;
  requestedByName: string | null;
  approvalRequestId: string | null;
  approvalRequestNumber: string | null;
  approvalStatus: ApprovalRequestStatus | null;
  originalCost: string;
  accumulatedDepreciation: string;
  bookValue: string;
  disposalValue: string | null;
  disposalGainLoss: string | null;
  remarks: string | null;
  buyerName: string | null;
  status: DisposalRegisterStatus;
  source: 'DISPOSED_ASSET' | 'APPROVAL_REQUEST';
}

export interface DisposalActionResponse {
  mode: 'disposed' | 'submitted_for_approval';
  message: string;
  asset: FixedAsset | null;
  disposal: DisposalRegisterItem;
  approvalRequestId: string | null;
  approvalRequestNumber: string | null;
  approvalStatus: ApprovalRequestStatus | null;
}

export interface AssetRegisterItem {
  id: string;
  assetCode: string;
  assetName: string;
  categoryCode: string;
  categoryName: string;
  locationName: string | null;
  departmentName: string | null;
  acquisitionDate: string;
  acquisitionCost: string;
  additions: string;
  disposals: string;
  revaluation: string;
  depreciationForPeriod: string;
  accumulatedDepreciation: string;
  wdvValue: string;
  status: string;
}

export interface AssetRegisterReport {
  organizationId: string;
  asOnDate: string;
  totalCost: string;
  totalAdditions: string;
  totalDisposals: string;
  totalRevaluation: string;
  totalDepreciation: string;
  totalAccumulatedDepreciation: string;
  totalWdv: string;
  assets: AssetRegisterItem[];
}

export interface DepreciationSummaryItem {
  categoryId: string;
  categoryCode: string;
  categoryName: string;
  assetCount: number;
  totalCost: string;
  totalDepreciation: string;
  accumulatedDepreciation: string;
  closingWdv: string;
}

export interface DepreciationSummaryReport {
  organizationId: string;
  depreciationPeriod: string;
  periodFrom: string;
  periodTo: string;
  totalAssets: number;
  totalDepreciation: string;
  byCategory: DepreciationSummaryItem[];
}
