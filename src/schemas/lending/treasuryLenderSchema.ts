import { z } from 'zod';

import type { CreateLenderRequest, LenderDetail } from '@/services/lending/treasuryApi';

const optionalText = z.string().optional().or(z.literal(''));

export const lenderFormSchema = z.object({
  lenderName: z.string().min(1, 'Lender name is required').max(200),
  lenderType: z.string().min(1, 'Lender type is required'),
  pan: z
    .string()
    .regex(/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/, 'Invalid PAN format')
    .optional()
    .or(z.literal('')),
  cin: z.string().max(25).optional().or(z.literal('')),
  gstin: z
    .string()
    .regex(/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/, 'Invalid GSTIN format')
    .optional()
    .or(z.literal('')),
  rbiRegistration: z.string().max(50).optional().or(z.literal('')),
  registeredAddress: optionalText,
  contactPerson: z.string().max(100).optional().or(z.literal('')),
  contactEmail: z.string().email('Invalid email').optional().or(z.literal('')),
  contactPhone: z.string().max(20).optional().or(z.literal('')),
  bankName: z.string().max(100).optional().or(z.literal('')),
  bankBranch: z.string().max(100).optional().or(z.literal('')),
  bankAccountNumber: z.string().max(30).optional().or(z.literal('')),
  bankIfsc: z
    .string()
    .regex(/^[A-Z]{4}0[A-Z0-9]{6}$/, 'Invalid IFSC code')
    .optional()
    .or(z.literal('')),
  externalRating: z.string().max(20).optional().or(z.literal('')),
  ratingAgency: z.string().max(50).optional().or(z.literal('')),
  ratingDate: optionalText,
  totalSanctionLimit: z.number().nonnegative().optional(),
  remarks: optionalText,
});

export type LenderFormData = z.infer<typeof lenderFormSchema>;

const numberFromDecimal = (value: string | number | null | undefined): number | undefined => {
  if (value === null || value === undefined || value === '') return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const blankToUndefined = (value?: string): string | undefined =>
  value && value.trim().length > 0 ? value : undefined;

export const defaultLenderFormValues: Partial<LenderFormData> = {
  lenderName: '',
  lenderType: '',
  pan: '',
  cin: '',
  gstin: '',
  rbiRegistration: '',
  registeredAddress: '',
  contactPerson: '',
  contactEmail: '',
  contactPhone: '',
  bankName: '',
  bankBranch: '',
  bankAccountNumber: '',
  bankIfsc: '',
  externalRating: '',
  ratingAgency: '',
  ratingDate: '',
  totalSanctionLimit: undefined,
  remarks: '',
};

export const lenderDetailToFormValues = (lender: LenderDetail): Partial<LenderFormData> => ({
  lenderName: lender.lenderName,
  lenderType: lender.lenderType,
  pan: lender.pan ?? '',
  cin: lender.cin ?? '',
  gstin: lender.gstin ?? '',
  rbiRegistration: lender.rbiRegistration ?? '',
  registeredAddress: lender.registeredAddress ?? '',
  contactPerson: lender.contactPerson ?? '',
  contactEmail: lender.contactEmail ?? '',
  contactPhone: lender.contactPhone ?? '',
  bankName: lender.bankName ?? '',
  bankBranch: lender.bankBranch ?? '',
  bankAccountNumber: lender.bankAccountNumber ?? '',
  bankIfsc: lender.bankIfsc ?? '',
  externalRating: lender.externalRating ?? '',
  ratingAgency: lender.ratingAgency ?? '',
  ratingDate: lender.ratingDate ?? '',
  totalSanctionLimit: numberFromDecimal(lender.totalSanctionLimit),
  remarks: lender.remarks ?? '',
});

export const lenderFormToRequest = (data: LenderFormData): CreateLenderRequest => ({
  lenderName: data.lenderName,
  lenderType: data.lenderType,
  pan: blankToUndefined(data.pan),
  cin: blankToUndefined(data.cin),
  gstin: blankToUndefined(data.gstin),
  rbiRegistration: blankToUndefined(data.rbiRegistration),
  registeredAddress: blankToUndefined(data.registeredAddress),
  contactPerson: blankToUndefined(data.contactPerson),
  contactEmail: blankToUndefined(data.contactEmail),
  contactPhone: blankToUndefined(data.contactPhone),
  bankName: blankToUndefined(data.bankName),
  bankBranch: blankToUndefined(data.bankBranch),
  bankAccountNumber: blankToUndefined(data.bankAccountNumber),
  bankIfsc: blankToUndefined(data.bankIfsc),
  externalRating: blankToUndefined(data.externalRating),
  ratingAgency: blankToUndefined(data.ratingAgency),
  ratingDate: blankToUndefined(data.ratingDate),
  totalSanctionLimit: data.totalSanctionLimit,
  remarks: blankToUndefined(data.remarks),
});
