import { useMemo } from 'react';

import type { PortalActorRole, PortalSessionUser } from '@/services/portalApi';

const DEFAULT_ROLE: PortalActorRole = 'scheme_borrower';

export function readPortalSessionUser(): PortalSessionUser | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const raw = window.localStorage.getItem('portal_user');
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as PortalSessionUser;
  } catch {
    return null;
  }
}

export function resolvePortalActorRole(
  user:
    | Pick<PortalSessionUser, 'actorRole' | 'actor_role'>
    | { actorRole?: string; actor_role?: string }
    | null,
): PortalActorRole {
  const rawRole = user?.actorRole ?? user?.actor_role;
  switch (rawRole) {
    case 'scheme_lender':
    case 'scheme_smfcl_reviewer':
    case 'scheme_smfcl_approver':
    case 'scheme_ministry_viewer':
    case 'scheme_admin':
    case 'scheme_borrower':
      return rawRole;
    default:
      return DEFAULT_ROLE;
  }
}

export function usePortalSession() {
  return useMemo(() => {
    const user = readPortalSessionUser();
    const actorRole = resolvePortalActorRole(user);
    return { user, actorRole };
  }, []);
}
