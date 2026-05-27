import api from '@/services/api';

export interface LoanProductMutationPayload {
  code: string;
  name: string;
  description?: string | null;
  category: string;
  subCategory?: string | null;
  minAmount: number;
  maxAmount: number;
  minTenureMonths: number;
  maxTenureMonths: number;
  defaultTenureMonths?: number | null;
  allowsMoratorium?: boolean;
  maxMoratoriumMonths?: number | null;
  interestType: string;
  minSpreadBps?: number;
  maxSpreadBps?: number;
  defaultSpreadBps?: number;
  minEffectiveRate?: number | null;
  maxEffectiveRate?: number | null;
  rateResetFrequency?: string | null;
  dayCountConvention: string;
  allowedRepaymentFrequencies?: string[];
  defaultRepaymentFrequency: string;
  allowedRepaymentModes?: string[];
  defaultRepaymentMode?: string;
  allowsPrepayment?: boolean;
  prepaymentLockInMonths?: number | null;
  allowsForeclosure?: boolean;
  foreclosureLockInMonths?: number | null;
  requiresCollateral?: boolean;
  minCollateralCoverage?: number | null;
  requiresGuarantee?: boolean;
  effectiveFrom: string;
  isActive?: boolean;
}

export interface LoanProductMutationResponse extends LoanProductMutationPayload {
  id: string;
  organizationId: string;
  isActive: boolean;
  status?: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface ProductDocumentRequirement {
  id: string;
  productId: string;
  catalogItemId: string;
  code: string;
  name: string;
  description: string | null;
  category: string;
  requiredAtStage: string;
  isMandatory: boolean;
  isMandatoryForDisbursement: boolean;
  applicableEntityTypes: string[] | null;
  allowedFileTypes: string[];
  maxFileSizeMb: number;
  minFileCount: number;
  maxFileCount: number;
  requiresVerification: boolean;
  displayOrder: number;
  helpText: string | null;
  isActive: boolean;
}

export interface ProductDocumentRequirementCreate {
  catalogItemId: string;
  isMandatory?: boolean;
  isMandatoryForDisbursement?: boolean;
  applicableEntityTypes?: string[] | null;
  allowedFileTypes?: string[];
  maxFileSizeMb?: number;
  minFileCount?: number;
  maxFileCount?: number;
  requiresVerification?: boolean;
  displayOrder?: number;
  helpText?: string | null;
}

export type ProductDocumentRequirementUpdate = Partial<ProductDocumentRequirementCreate> & {
  isActive?: boolean;
};

function idempotencyHeaders(): { 'Idempotency-Key': string } {
  return { 'Idempotency-Key': crypto.randomUUID() };
}

export const productApi = {
  async createProduct(payload: LoanProductMutationPayload): Promise<LoanProductMutationResponse> {
    const { data } = await api.post<LoanProductMutationResponse>('/lending/products', payload, {
      headers: idempotencyHeaders(),
    });
    return data;
  },

  async updateProduct(
    productId: string,
    payload: Partial<LoanProductMutationPayload>,
  ): Promise<LoanProductMutationResponse> {
    const { data } = await api.put<LoanProductMutationResponse>(
      `/lending/products/${productId}`,
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async listDocumentRequirements(productId: string): Promise<ProductDocumentRequirement[]> {
    const { data } = await api.get<ProductDocumentRequirement[]>(
      `/lending/products/${productId}/checklist`,
    );
    return data;
  },

  async addDocumentRequirement(
    productId: string,
    payload: ProductDocumentRequirementCreate,
  ): Promise<ProductDocumentRequirement> {
    const { data } = await api.post<ProductDocumentRequirement>(
      `/lending/products/${productId}/checklist`,
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async updateDocumentRequirement(
    requirementId: string,
    payload: ProductDocumentRequirementUpdate,
  ): Promise<ProductDocumentRequirement> {
    const { data } = await api.put<ProductDocumentRequirement>(
      `/lending/products/checklist/${requirementId}`,
      payload,
      { headers: idempotencyHeaders() },
    );
    return data;
  },

  async deleteDocumentRequirement(requirementId: string): Promise<void> {
    await api.delete(`/lending/products/checklist/${requirementId}`, {
      headers: idempotencyHeaders(),
    });
  },
};
