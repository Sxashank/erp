/**
 * Borrower Portal Registration — zod schemas.
 *
 * Two onboarding paths:
 *   1. Organisation identity → POST /portal/auth/register
 *   2. Existing loan account → POST /portal/auth/register
 *   3. OTP verify            → POST /portal/auth/register/verify-otp
 *
 * CLAUDE.md §1: this product lends to organisations here. No Aadhaar or
 * consumer-facing personal onboarding data is collected.
 */

import { z } from 'zod';

const CIN_PATTERN = /^[LU][0-9A-Z]{20}$/i;
const GSTIN_PATTERN = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/i;
const LLPIN_PATTERN = /^[A-Z]{3}-[0-9]{4}$/i;
const PAN_PATTERN = /^[A-Z]{5}[0-9]{4}[A-Z]$/i;
const INDIAN_MOBILE_PATTERN = /^\+91[6-9][0-9]{9}$/;
const MONEY_PATTERN = /^\d+(\.\d{1,2})?$/;

export const registrationStartSchema = z
  .object({
    registrationMode: z.enum(['organizationIdentity', 'existingLoan']),
    idType: z.enum(['cin', 'gstin', 'llpin', 'pan']),
    idValue: z.string().trim().default(''),
    loanAccountNumber: z.string().trim().default(''),
    sanctionedAmount: z.string().trim().default(''),
    authorizedSignatoryName: z
      .string()
      .trim()
      .min(2, 'Authorised signatory name is required')
      .max(120, 'Name is too long'),
    mobile: z
      .string()
      .regex(INDIAN_MOBILE_PATTERN, 'Mobile must be +91 followed by a 10-digit Indian number'),
    email: z.string().trim().toLowerCase().email('Enter a valid corporate email'),
  })
  .superRefine((data, ctx) => {
    if (data.registrationMode === 'organizationIdentity') {
      const value = data.idValue.trim().toUpperCase();
      if (!value) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['idValue'],
          message: 'Identifier is required',
        });
        return;
      }

      let ok = true;
      switch (data.idType) {
        case 'cin':
          ok = CIN_PATTERN.test(value);
          break;
        case 'gstin':
          ok = GSTIN_PATTERN.test(value);
          break;
        case 'llpin':
          ok = LLPIN_PATTERN.test(value) || /^[A-Z0-9]{7,8}$/i.test(value);
          break;
        case 'pan':
          ok = PAN_PATTERN.test(value);
          break;
      }
      if (!ok) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['idValue'],
          message: `Enter a valid ${data.idType.toUpperCase()}`,
        });
      }
      return;
    }

    if (!data.loanAccountNumber.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['loanAccountNumber'],
        message: 'Loan account number is required',
      });
    }
    if (!data.sanctionedAmount.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['sanctionedAmount'],
        message: 'Sanctioned amount is required',
      });
    } else if (!MONEY_PATTERN.test(data.sanctionedAmount.trim())) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['sanctionedAmount'],
        message: 'Enter a valid sanctioned amount',
      });
    }
  });

export type RegistrationStartInput = z.input<typeof registrationStartSchema>;
export type RegistrationStartValues = z.output<typeof registrationStartSchema>;

export const otpVerifySchema = z.object({
  otp: z.string().regex(/^\d{6}$/, 'OTP must be 6 digits'),
});

export type OtpVerifyInput = z.infer<typeof otpVerifySchema>;
