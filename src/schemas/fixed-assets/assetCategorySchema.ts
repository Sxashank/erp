import { z } from 'zod';

export const assetTypeSchema = z.enum(['TANGIBLE', 'INTANGIBLE', 'RIGHT_OF_USE']);
export const depreciationMethodSchema = z.enum([
  'SLM',
  'WDV',
  'UNIT_OF_PRODUCTION',
  'NO_DEPRECIATION',
]);

export const assetCategorySchema = z.object({
  categoryCode: z.string().trim().min(1, 'Category code is required').max(20),
  categoryName: z.string().trim().min(1, 'Category name is required').max(100),
  description: z.string().trim().max(500).optional().or(z.literal('')),
  parentCategoryId: z.string().uuid().optional().or(z.literal('')),
  assetType: assetTypeSchema,
  depreciationMethod: depreciationMethodSchema,
  usefulLifeYears: z.number().int().min(1).max(100),
  residualValuePct: z.number().min(0).max(100),
  depreciationRateSlm: z.number().min(0).max(100),
  depreciationRateWdv: z.number().min(0).max(100),
  itActRate: z.number().min(0).max(100).optional(),
  itActBlock: z.string().trim().max(10).optional().or(z.literal('')),
  capitalizationThreshold: z.number().min(0),
  glAssetAccountId: z.string().uuid().optional().or(z.literal('')),
  glAccumDepAccountId: z.string().uuid().optional().or(z.literal('')),
  glDepExpenseAccountId: z.string().uuid().optional().or(z.literal('')),
  glDisposalGainAccountId: z.string().uuid().optional().or(z.literal('')),
  glDisposalLossAccountId: z.string().uuid().optional().or(z.literal('')),
  glRevaluationReserveAccountId: z.string().uuid().optional().or(z.literal('')),
  glImpairmentAccountId: z.string().uuid().optional().or(z.literal('')),
  requiresInsurance: z.boolean(),
  requiresAmc: z.boolean(),
}).superRefine((value, ctx) => {
  if (!value.glAssetAccountId) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Asset account is required',
      path: ['glAssetAccountId'],
    });
  }

  if (value.depreciationMethod === 'NO_DEPRECIATION') {
    return;
  }

  if (!value.glAccumDepAccountId) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Accumulated depreciation account is required',
      path: ['glAccumDepAccountId'],
    });
  }

  if (!value.glDepExpenseAccountId) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Depreciation expense account is required',
      path: ['glDepExpenseAccountId'],
    });
  }
});

export type AssetCategoryInput = z.infer<typeof assetCategorySchema>;
