/**
 * Organization hook. Every page that makes API calls must read the active
 * organization from here; do not hard-code or omit it. See CLAUDE.md §3.4.
 */

import { useShallow } from 'zustand/react/shallow';

import { useOrganizationStore, type Organization } from '@/stores/organizationStore';

interface UseOrganizationReturn {
  organizations: Organization[];
  activeOrganizationId: string | null;
  activeOrganization: Organization | null;
  setActiveOrganization: (id: string | null) => void;
}

export function useOrganization(): UseOrganizationReturn {
  const slice = useOrganizationStore(
    useShallow((s) => ({
      organizations: s.organizations,
      activeOrganizationId: s.activeOrganizationId,
      setActiveOrganization: s.setActiveOrganization,
    })),
  );

  const active =
    slice.organizations.find((o) => o.id === slice.activeOrganizationId) ?? null;

  return {
    organizations: slice.organizations,
    activeOrganizationId: slice.activeOrganizationId,
    activeOrganization: active,
    setActiveOrganization: slice.setActiveOrganization,
  };
}

/** Throws if no active organization is set — use on pages that require one. */
export function useRequiredActiveOrganizationId(): string {
  const id = useOrganizationStore((s) => s.activeOrganizationId);
  if (!id) {
    throw new Error(
      'No active organization is set. This page requires an organization context.',
    );
  }
  return id;
}
