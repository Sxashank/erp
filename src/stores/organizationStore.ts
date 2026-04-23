/**
 * Organization store — the active organization for the current session.
 *
 * See CLAUDE.md §3.4: every page reads organization from this store; no page
 * may hard-code or omit it. Cross-tab sync via BroadcastChannel keeps the
 * active org consistent when the user has multiple tabs open.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Organization {
  id: string;
  code: string;
  name: string;
}

interface OrganizationState {
  organizations: Organization[];
  activeOrganizationId: string | null;

  setOrganizations: (orgs: Organization[]) => void;
  setActiveOrganization: (id: string | null) => void;
  clear: () => void;
}

const CHANNEL_NAME = 'smfc-active-org';
const bc =
  typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel(CHANNEL_NAME) : null;

export const useOrganizationStore = create<OrganizationState>()(
  persist(
    (set, get) => ({
      organizations: [],
      activeOrganizationId: null,
      setOrganizations: (organizations) => {
        // If active org is no longer in the list, reset it to the first available.
        const current = get().activeOrganizationId;
        const stillValid = current && organizations.some((o) => o.id === current);
        const activeOrganizationId =
          stillValid ? current : (organizations[0]?.id ?? null);
        set({ organizations, activeOrganizationId });
      },
      setActiveOrganization: (activeOrganizationId) => {
        set({ activeOrganizationId });
        bc?.postMessage({ type: 'set-active', id: activeOrganizationId });
      },
      clear: () => {
        set({ organizations: [], activeOrganizationId: null });
        bc?.postMessage({ type: 'clear' });
      },
    }),
    {
      name: 'smfc-organization',
      partialize: (state) => ({ activeOrganizationId: state.activeOrganizationId }),
    },
  ),
);

// Cross-tab sync
if (bc) {
  bc.onmessage = (event) => {
    const data = event.data as { type: string; id?: string | null };
    if (data.type === 'set-active') {
      const store = useOrganizationStore.getState();
      if (store.activeOrganizationId !== data.id) {
        useOrganizationStore.setState({ activeOrganizationId: data.id ?? null });
      }
    } else if (data.type === 'clear') {
      useOrganizationStore.setState({ organizations: [], activeOrganizationId: null });
    }
  };
}

export const useActiveOrganizationId = (): string | null =>
  useOrganizationStore((s) => s.activeOrganizationId);
