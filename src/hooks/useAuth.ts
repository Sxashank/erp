/**
 * Auth hooks. This is the public surface for components and pages.
 *
 * Usage:
 *   const { user, isAuthenticated, login, logout } = useAuth();
 *
 * See CLAUDE.md §5.6.
 */

import { useShallow } from 'zustand/react/shallow';

import {
  login as loginAction,
  logout as logoutAction,
  refreshTokens as refreshAction,
  hydrateFromServer,
  type LoginPayload,
} from '@/services/auth';
import { useAuthStore, type AuthUser } from '@/stores/authStore';

interface UseAuthReturn {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isBootstrapping: boolean;
  accessToken: string | null;
  login: (payload: LoginPayload) => Promise<{ requiresMfa: boolean }>;
  logout: () => Promise<void>;
  refresh: () => Promise<string | null>;
  reloadProfile: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const slice = useAuthStore(
    useShallow((s) => ({
      user: s.user,
      accessToken: s.accessToken,
      isBootstrapping: s.isBootstrapping,
    })),
  );

  return {
    user: slice.user,
    accessToken: slice.accessToken,
    isAuthenticated: !!slice.accessToken && !!slice.user,
    isBootstrapping: slice.isBootstrapping,
    login: loginAction,
    logout: logoutAction,
    refresh: refreshAction,
    reloadProfile: hydrateFromServer,
  };
}
