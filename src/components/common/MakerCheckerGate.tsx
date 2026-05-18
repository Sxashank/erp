/**
 * MakerCheckerGate — hides its children when the current user is the maker
 * of the record being approved. The paired frontend half of the §8.4
 * backend invariant enforced by
 * `app.core.maker_checker.ensure_maker_is_not_checker`.
 *
 * Usage (wrap the Approve / Reject buttons on a detail page):
 *
 *     <MakerCheckerGate makerId={record.created_by}>
 *       <Button onClick={handleApprove}>Approve</Button>
 *       <Button onClick={handleReject}>Reject</Button>
 *     </MakerCheckerGate>
 *
 * Multiple maker-id fallbacks are supported — useful for entities whose
 * "maker identity" is a distinct column like `submitted_by_id` that falls
 * back to `created_by`:
 *
 *     <MakerCheckerGate
 *       makerId={record.submitted_by_id ?? record.created_by}
 *     />
 *
 * IMPORTANT: this is a UX convenience — the backend still enforces the
 * invariant on every approve call. Hiding the button here just stops the
 * obvious self-approval attempt before it happens.
 *
 * See CLAUDE.md §8.4 / §9.5.
 */

import type { ReactNode } from 'react';

import { useAuth } from '@/hooks/useAuth';

interface Props {
  /** The user ID of whoever made / submitted the record. */
  makerId: string | null | undefined;
  /** Content to show when the current user is NOT the maker (usually the Approve button). */
  children: ReactNode;
  /** Optional content to show when the current user IS the maker — usually a disabled hint. */
  fallback?: ReactNode;
}

export function MakerCheckerGate({ makerId, children, fallback = null }: Props): JSX.Element {
  const { user } = useAuth();

  // If there's no current user, render nothing — the auth layer should have
  // already redirected, but we defensively hide any approve UI.
  if (!user) return <>{fallback}</>;

  // If makerId is unknown (legacy row without created_by), we let the gate
  // pass. The backend's guard will still catch it; showing a button that
  // might be usable is better than hiding it forever.
  if (!makerId) return <>{children}</>;

  const isSelfApproval = String(user.id) === String(makerId);
  return <>{isSelfApproval ? fallback : children}</>;
}
