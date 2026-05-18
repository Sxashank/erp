/**
 * Auth store — tokens, user, permissions.
 *
 * Zustand with localStorage persistence for tokens + a non-persisted user
 * object (re-hydrated on bootstrap via /auth/me). See CLAUDE.md §5.5, §5.6.
 *
 * The axios interceptor reads `useAuthStore.getState().accessToken` and
 * `.refresh()` — no direct localStorage access from services.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  fullName: string;
  organizationId: string | null;
  defaultUnitId: string | null;
  mfaEnabled: boolean;
  roles: string[];
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  permissions: Set<string>;
  isBootstrapping: boolean;

  // setters
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: AuthUser | null, permissions: string[]) => void;
  setBootstrapping: (v: boolean) => void;
  clear: () => void;
}

const initialState = {
  accessToken: null as string | null,
  refreshToken: null as string | null,
  user: null as AuthUser | null,
  permissions: new Set<string>(),
  isBootstrapping: true,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      ...initialState,
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      setUser: (user, permissions) => set({ user, permissions: new Set(permissions) }),
      setBootstrapping: (isBootstrapping) => set({ isBootstrapping }),
      clear: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          permissions: new Set(),
          isBootstrapping: false,
        }),
    }),
    {
      name: 'smfc-auth',
      // Only persist tokens. User / permissions are re-fetched from /auth/me on bootstrap
      // to reflect server-side role changes without requiring re-login.
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
);

export const selectIsAuthenticated = (state: AuthState): boolean =>
  !!state.accessToken && !!state.user;

export function isAuthStoreHydrated(): boolean {
  return useAuthStore.persist.hasHydrated();
}

function seedTokensFromPersistedStorage(): void {
  if (typeof window === 'undefined') {
    return;
  }
  const raw = window.localStorage.getItem('smfc-auth');
  if (!raw) {
    return;
  }
  try {
    const parsed = JSON.parse(raw) as {
      state?: { accessToken?: unknown; refreshToken?: unknown };
    };
    const nextAccessToken =
      typeof parsed.state?.accessToken === 'string' ? parsed.state.accessToken : null;
    const nextRefreshToken =
      typeof parsed.state?.refreshToken === 'string' ? parsed.state.refreshToken : null;
    if (!nextAccessToken && !nextRefreshToken) {
      return;
    }
    const current = useAuthStore.getState();
    if (current.accessToken === nextAccessToken && current.refreshToken === nextRefreshToken) {
      return;
    }
    useAuthStore.setState({
      accessToken: current.accessToken ?? nextAccessToken,
      refreshToken: current.refreshToken ?? nextRefreshToken,
    });
  } catch {
    // Ignore malformed persisted auth blobs and let bootstrap fall back to logout.
  }
}

export async function waitForAuthStoreHydration(): Promise<void> {
  if (useAuthStore.persist.hasHydrated()) {
    seedTokensFromPersistedStorage();
    return;
  }
  await useAuthStore.persist.rehydrate();
  seedTokensFromPersistedStorage();
  if (useAuthStore.persist.hasHydrated()) {
    return;
  }
  await new Promise<void>((resolve) => {
    const unsubscribe = useAuthStore.persist.onFinishHydration(() => {
      unsubscribe();
      resolve();
    });
  });
}
