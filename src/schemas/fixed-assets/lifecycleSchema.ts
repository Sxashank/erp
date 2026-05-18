import { z } from 'zod';

export const assetCapitalizeSchema = z.object({
  capitalizationDate: z.string().min(1, 'Capitalization date is required'),
  putToUseDate: z.string().optional().or(z.literal('')),
  depreciationStartDate: z.string().optional().or(z.literal('')),
  remarks: z.string().trim().max(500).optional().or(z.literal('')),
});

export const assetTransferSchema = z.object({
  transferDate: z.string().min(1, 'Transfer date is required'),
  toLocationId: z.string().uuid().optional().or(z.literal('')),
  toDepartmentId: z.string().uuid().optional().or(z.literal('')),
  toCustodianId: z.string().uuid().optional().or(z.literal('')),
  reason: z.string().trim().max(500).optional().or(z.literal('')),
});

export const assetRevalueSchema = z.object({
  revaluationDate: z.string().min(1, 'Revaluation date is required'),
  newValue: z.number().min(0),
  valuerName: z.string().trim().max(200).optional().or(z.literal('')),
  valuationReportNumber: z.string().trim().max(100).optional().or(z.literal('')),
  valuationReportDate: z.string().optional().or(z.literal('')),
  valuationMethod: z.string().trim().max(100).optional().or(z.literal('')),
  reason: z.string().trim().max(500).optional().or(z.literal('')),
});

export const assetImpairSchema = z.object({
  impairmentDate: z.string().min(1, 'Impairment date is required'),
  impairmentAmount: z.number().min(0),
  reason: z.string().trim().max(500).optional().or(z.literal('')),
});

export const assetDisposeSchema = z.object({
  disposalDate: z.string().min(1, 'Disposal date is required'),
  disposalType: z.enum(['SALE', 'SCRAP', 'WRITE_OFF', 'DONATION', 'LOSS']),
  disposalValue: z.number().min(0),
  disposalRemarks: z.string().trim().max(500).optional().or(z.literal('')),
  buyerName: z.string().trim().max(200).optional().or(z.literal('')),
  buyerAddress: z.string().trim().max(500).optional().or(z.literal('')),
});

export type AssetCapitalizeInput = z.infer<typeof assetCapitalizeSchema>;
export type AssetTransferInput = z.infer<typeof assetTransferSchema>;
export type AssetRevalueInput = z.infer<typeof assetRevalueSchema>;
export type AssetImpairInput = z.infer<typeof assetImpairSchema>;
export type AssetDisposeInput = z.infer<typeof assetDisposeSchema>;
