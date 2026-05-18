import { z } from 'zod';

import type { BorrowingDetail, CreateBorrowingRequest } from '@/services/lending/treasuryApi';

const optionalString = z.string().optional();
const optionalPositiveNumber = z.number().positive().optional();
const optionalNonNegativeNumber = z.number().nonnegative().optional();

export const borrowingTypeSchema = z.enum([
  'TERM_LOAN',
  'WORKING_CAPITAL',
  'CASH_CREDIT',
  'NCD',
  'CP',
  'SUBORDINATED_DEBT',
  'ECB',
  'REFINANCE',
  'ICD',
]);

export const rateTypeSchema = z.enum(['FIXED', 'FLOATING']);

export const repaymentFrequencySchema = z.enum([
  'MONTHLY',
  'QUARTERLY',
  'HALF_YEARLY',
  'YEARLY',
  'BULLET',
]);

export const borrowingFormSchema = z.object({
  lenderId: z.string().min(1, 'Lender is required'),
  borrowingType: borrowingTypeSchema,
  sanctionDate: z.string().min(1, 'Sanction date is required'),
  sanctionReference: optionalString,
  sanctionedAmount: z.number().positive('Amount must be positive'),
  currency: z.string().default('INR'),
  rateType: rateTypeSchema,
  baseRateName: optionalString,
  baseRateValue: optionalNonNegativeNumber,
  spreadBps: z.number().int().nonnegative().default(0),
  effectiveRate: z.number().positive('Effective rate is required'),
  rateResetFrequency: optionalString,
  dayCountConvention: z.string().default('ACT_365'),
  interestPaymentFrequency: repaymentFrequencySchema.default('MONTHLY'),
  principalPaymentFrequency: repaymentFrequencySchema.default('QUARTERLY'),
  tenureMonths: z.number().int().positive('Tenure is required'),
  moratoriumMonths: z.number().int().nonnegative().default(0),
  firstInterestDate: optionalString,
  firstPrincipalDate: optionalString,
  maturityDate: z.string().min(1, 'Maturity date is required'),
  securityType: z.string().default('UNSECURED'),
  securityDescription: optionalString,
  securityCoverRequired: optionalPositiveNumber,
  processingFeePercent: optionalNonNegativeNumber,
  commitmentFeePercent: optionalNonNegativeNumber,
  prepaymentPenaltyPercent: optionalNonNegativeNumber,
  remarks: optionalString,
});

export type BorrowingFormData = z.infer<typeof borrowingFormSchema>;
export type BorrowingFormInput = z.input<typeof borrowingFormSchema>;

const numberFromDecimal = (value: string | number | null | undefined): number | undefined => {
  if (value === null || value === undefined || value === '') return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const blankToUndefined = (value?: string): string | undefined =>
  value && value.trim().length > 0 ? value : undefined;

export const defaultBorrowingFormValues = (): Partial<BorrowingFormData> => ({
  lenderId: '',
  sanctionDate: new Date().toISOString().split('T')[0],
  sanctionReference: '',
  currency: 'INR',
  rateType: 'FLOATING',
  baseRateName: '',
  baseRateValue: undefined,
  spreadBps: 0,
  rateResetFrequency: 'QUARTERLY',
  dayCountConvention: 'ACT_365',
  interestPaymentFrequency: 'MONTHLY',
  principalPaymentFrequency: 'QUARTERLY',
  moratoriumMonths: 0,
  firstInterestDate: '',
  firstPrincipalDate: '',
  securityType: 'UNSECURED',
  securityDescription: '',
  securityCoverRequired: undefined,
  processingFeePercent: undefined,
  commitmentFeePercent: undefined,
  prepaymentPenaltyPercent: undefined,
  remarks: '',
});

export const borrowingDetailToFormValues = (
  borrowing: BorrowingDetail,
): Partial<BorrowingFormData> => ({
  lenderId: borrowing.lenderId,
  borrowingType: borrowing.borrowingType as BorrowingFormData['borrowingType'],
  sanctionDate: borrowing.sanctionDate,
  sanctionReference: borrowing.sanctionReference ?? '',
  sanctionedAmount: numberFromDecimal(borrowing.sanctionedAmount),
  currency: borrowing.currency,
  rateType: borrowing.rateType as BorrowingFormData['rateType'],
  baseRateName: borrowing.baseRateName ?? '',
  baseRateValue: numberFromDecimal(borrowing.baseRateValue),
  spreadBps: borrowing.spreadBps,
  effectiveRate: numberFromDecimal(borrowing.effectiveRate),
  rateResetFrequency: borrowing.rateResetFrequency ?? 'QUARTERLY',
  dayCountConvention: borrowing.dayCountConvention,
  interestPaymentFrequency:
    borrowing.interestPaymentFrequency as BorrowingFormData['interestPaymentFrequency'],
  principalPaymentFrequency:
    borrowing.principalPaymentFrequency as BorrowingFormData['principalPaymentFrequency'],
  tenureMonths: borrowing.tenureMonths,
  moratoriumMonths: borrowing.moratoriumMonths,
  firstInterestDate: borrowing.firstInterestDate ?? '',
  firstPrincipalDate: borrowing.firstPrincipalDate ?? '',
  maturityDate: borrowing.maturityDate,
  securityType: borrowing.securityType,
  securityDescription: borrowing.securityDescription ?? '',
  securityCoverRequired: numberFromDecimal(borrowing.securityCoverRequired),
  processingFeePercent: numberFromDecimal(borrowing.processingFeePercent),
  commitmentFeePercent: numberFromDecimal(borrowing.commitmentFeePercent),
  prepaymentPenaltyPercent: numberFromDecimal(borrowing.prepaymentPenaltyPercent),
  remarks: borrowing.remarks ?? '',
});

export const borrowingFormToRequest = (data: BorrowingFormData): CreateBorrowingRequest => ({
  ...data,
  sanctionReference: blankToUndefined(data.sanctionReference),
  baseRateName: blankToUndefined(data.baseRateName),
  rateResetFrequency: blankToUndefined(data.rateResetFrequency),
  firstInterestDate: blankToUndefined(data.firstInterestDate),
  firstPrincipalDate: blankToUndefined(data.firstPrincipalDate),
  securityDescription: blankToUndefined(data.securityDescription),
  remarks: blankToUndefined(data.remarks),
});
