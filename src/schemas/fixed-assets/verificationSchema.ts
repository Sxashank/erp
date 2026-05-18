import { z } from 'zod';

export const verificationScheduleSchema = z
  .object({
    scheduleName: z.string().trim().min(1, 'Schedule name is required').max(200),
    financialYear: z
      .string()
      .regex(/^\d{4}-\d{2}$/, 'Financial year must be in YYYY-YY format'),
    locationId: z.string().uuid().optional().or(z.literal('')),
    categoryIds: z.array(z.string().uuid()),
    scheduledStartDate: z.string().min(1, 'Start date is required'),
    scheduledEndDate: z.string().min(1, 'End date is required'),
    remarks: z.string().trim().max(1000).optional().or(z.literal('')),
  })
  .superRefine((value, ctx) => {
    if (value.scheduledEndDate < value.scheduledStartDate) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'End date must be on or after the start date',
        path: ['scheduledEndDate'],
      });
    }
  });

export const verifyEntrySchema = z.object({
  verificationDate: z.string().min(1, 'Verification date is required'),
  verificationResult: z.enum(['FOUND', 'MISSING', 'MISPLACED', 'EXCESS']),
  assetCondition: z.enum(['GOOD', 'FAIR', 'POOR', 'DAMAGED', 'NOT_WORKING']).optional(),
  actualLocationId: z.string().uuid().optional().or(z.literal('')),
  actualDepartmentId: z.string().uuid().optional().or(z.literal('')),
  barcodeScan: z.string().trim().max(100).optional().or(z.literal('')),
  conditionNotes: z.string().trim().max(1000).optional().or(z.literal('')),
  remarks: z.string().trim().max(500).optional().or(z.literal('')),
});

export const discrepancyResolutionSchema = z.object({
  status: z.enum(['OPEN', 'INVESTIGATING', 'RESOLVED', 'WRITTEN_OFF']),
  investigationNotes: z.string().trim().max(1000).optional().or(z.literal('')),
  resolution: z.string().trim().max(1000).optional().or(z.literal('')),
  remarks: z.string().trim().max(500).optional().or(z.literal('')),
});

export type VerificationScheduleInput = z.infer<typeof verificationScheduleSchema>;
export type VerifyEntryInput = z.infer<typeof verifyEntrySchema>;
export type DiscrepancyResolutionInput = z.infer<typeof discrepancyResolutionSchema>;
