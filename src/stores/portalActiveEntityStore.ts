/**
 * Portal Active Entity Store
 *
 * Borrower portal users may have multiple linked entities (one user can be
 * the authorised signatory for several NBFC-funded shipyard orgs).  This
 * Zustand store holds the entity ID currently in focus inside the portal
 * UI — driven by the header switcher rendered by `PortalLayout`.
 *
 * See CLAUDE.md §1: the SaaS is org-isolated; this is a per-borrower-user
 * convenience, not a tenant control. Backend authorisation always derives
 * from the JWT, not from this client-side selection.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface PortalEntityOption {
  id: string;
  legalName: string;
}

interface PortalActiveEntityState {
  /** All entities the current portal user has access to. */
  entities: PortalEntityOption[];
  /** The entity selected in the header switcher. */
  activeEntityId: string | null;

  setEntities: (entities: PortalEntityOption[]) => void;
  setActiveEntityId: (id: string | null) => void;
  clear: () => void;
}

export const usePortalActiveEntityStore = create<PortalActiveEntityState>()(
  persist(
    (set, get) => ({
      entities: [],
      activeEntityId: null,
      setEntities: (entities) => {
        const current = get().activeEntityId;
        const stillValid = current && entities.some((e) => e.id === current) ? current : null;
        const activeEntityId = stillValid ?? entities[0]?.id ?? null;
        set({ entities, activeEntityId });
      },
      setActiveEntityId: (activeEntityId) => set({ activeEntityId }),
      clear: () => set({ entities: [], activeEntityId: null }),
    }),
    {
      name: 'smfc-portal-active-entity',
      partialize: (state) => ({ activeEntityId: state.activeEntityId }),
    },
  ),
);

/**
 * Convenience selectors — keep page components from importing the store
 * directly and ensure stable references.
 */
export const usePortalActiveEntityId = (): string | null =>
  usePortalActiveEntityStore((s) => s.activeEntityId);

export const usePortalEntities = (): PortalEntityOption[] =>
  usePortalActiveEntityStore((s) => s.entities);
