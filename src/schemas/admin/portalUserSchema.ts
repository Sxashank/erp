import { z } from 'zod';

const actorRoles = [
  'scheme_borrower',
  'scheme_lender',
  'scheme_smfcl_reviewer',
  'scheme_smfcl_approver',
  'scheme_ministry_viewer',
  'scheme_admin',
] as const;

const statuses = ['ACTIVE', 'INACTIVE', 'SUSPENDED', 'BLOCKED'] as const;

export const createPortalUserSchema = z
  .object({
    mobile: z.string().trim().min(10, 'Required').max(15, 'Required'),
    email: z.string().trim().email('Enter a valid email').optional().or(z.literal('')),
    displayName: z.string().trim().min(2, 'Required'),
    actorRole: z.enum(actorRoles),
    preferredLanguage: z.string().trim().min(2, 'Required').max(5, 'Required'),
    status: z.enum(statuses),
    linkedEntityIds: z.array(z.string().uuid()),
  })
  .superRefine((value, ctx) => {
    if (value.actorRole === 'scheme_borrower' && value.linkedEntityIds.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Borrower actors require at least one linked entity',
        path: ['linkedEntityIds'],
      });
    }
  });

export const updatePortalUserSchema = z
  .object({
    email: z.string().trim().email('Enter a valid email').optional().or(z.literal('')),
    displayName: z.string().trim().min(2, 'Required'),
    actorRole: z.enum(actorRoles),
    preferredLanguage: z.string().trim().min(2, 'Required').max(5, 'Required'),
    status: z.enum(statuses),
    linkedEntityIds: z.array(z.string().uuid()),
  })
  .superRefine((value, ctx) => {
    if (value.actorRole === 'scheme_borrower' && value.linkedEntityIds.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Borrower actors require at least one linked entity',
        path: ['linkedEntityIds'],
      });
    }
  });

export type CreatePortalUserInput = z.infer<typeof createPortalUserSchema>;
export type UpdatePortalUserInput = z.infer<typeof updatePortalUserSchema>;
