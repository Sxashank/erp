/**
 * Borrower Portal Registration — zod schemas.
 *
 * Two stages match the BE contract:
 *   1. Org details  → POST /portal/auth/register
 *   2. OTP verify   → POST /portal/auth/register/verify-otp
 *
 * CLAUDE.md §1: this product lends ONLY to organisations (Indian shipyard
 * NBFCs).  No individual KYC, no AADHAAR, no consumer fields — the
 * registration must carry at least one of CIN / GSTIN / LLPIN / PAN.
 */

import { z } from 'zod';

// Light-touch format checks — full validation happens server-side.
// Patterns mirror the standard Indian regulator-issued ID formats.
const CIN_PATTERN = /^[LU][0-9A-Z]{20}$/i;
const GSTIN_PATTERN = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}$/i;
const LLPIN_PATTERN = /^[A-Z]{3}-[0-9]{4}$/i; // accepts the common formatted variant
const PAN_PATTERN = /^[A-Z]{5}[0-9]{4}[A-Z]$/i;
const INDIAN_MOBILE_PATTERN = /^\+91[6-9][0-9]{9}$/;

export const orgDetailsSchema = z
  .object({
    idType: z.enum(['cin', 'gstin', 'llpin', 'pan']),
    idValue: z.string().min(1, 'Identifier is required'),
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
    const v = data.idValue.trim().toUpperCase();
    let ok = true;
    switch (data.idType) {
      case 'cin':
        ok = CIN_PATTERN.test(v);
        break;
      case 'gstin':
        ok = GSTIN_PATTERN.test(v);
        break;
      case 'llpin':
        // The BE accepts the unformatted form too — keep this advisory.
        ok = LLPIN_PATTERN.test(v) || /^[A-Z0-9]{7,8}$/i.test(v);
        break;
      case 'pan':
        ok = PAN_PATTERN.test(v);
        break;
    }
    if (!ok) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['idValue'],
        message: `Enter a valid ${data.idType.toUpperCase()}`,
      });
    }
  });

export type OrgDetailsInput = z.infer<typeof orgDetailsSchema>;

export const otpVerifySchema = z.object({
  otp: z.string().regex(/^\d{6}$/, 'OTP must be 6 digits'),
});

export type OtpVerifyInput = z.infer<typeof otpVerifySchema>;
