import { z } from 'zod';

export const assetAcquisitionTypeSchema = z.enum([
  'PURCHASE',
  'LEASE',
  'DONATION',
  'TRANSFER_IN',
  'CONSTRUCTED',
]);

export const fixedAssetSchema = z.object({
  assetName: z.string().trim().min(1, 'Asset name is required').max(200),
  description: z.string().trim().max(1000).optional().or(z.literal('')),
  categoryId: z.string().uuid('Select a category'),
  locationId: z.string().uuid().optional().or(z.literal('')),
  departmentId: z.string().uuid().optional().or(z.literal('')),
  acquisitionDate: z.string().min(1, 'Acquisition date is required'),
  putToUseDate: z.string().optional().or(z.literal('')),
  acquisitionType: assetAcquisitionTypeSchema,
  vendorId: z.string().uuid().optional().or(z.literal('')),
  invoiceNumber: z.string().trim().max(50).optional().or(z.literal('')),
  invoiceDate: z.string().optional().or(z.literal('')),
  poNumber: z.string().trim().max(50).optional().or(z.literal('')),
  acquisitionCost: z.number().min(0),
  installationCost: z.number().min(0),
  otherCosts: z.number().min(0),
  residualValue: z.number().min(0),
  usefulLifeMonths: z.number().int().min(1).optional(),
  depreciationMethod: z.enum(['SLM', 'WDV', 'UNIT_OF_PRODUCTION', 'NO_DEPRECIATION']).optional().or(z.literal('')),
  depreciationRate: z.number().min(0).max(100).optional(),
  make: z.string().trim().max(100).optional().or(z.literal('')),
  model: z.string().trim().max(100).optional().or(z.literal('')),
  serialNumber: z.string().trim().max(100).optional().or(z.literal('')),
  quantity: z.number().int().min(1),
  warrantyStartDate: z.string().optional().or(z.literal('')),
  warrantyExpiryDate: z.string().optional().or(z.literal('')),
});

export type FixedAssetInput = z.infer<typeof fixedAssetSchema>;
