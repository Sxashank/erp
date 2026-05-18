/**
 * Auth provider. Runs bootstrap on mount (tries to restore session via the
 * persisted refresh token); exposes a small, stable context surface for
 * components that cannot subscribe to Zustand directly.
 *
 * Public surface for components: use the hooks in `@/hooks/useAuth`.
 * Writing new code? Prefer the hooks over this context.
 *
 * See CLAUDE.md §5.6, §5.5.
 */

import { createContext, useContext, useEffect, useRef, type ReactNode } from 'react';

import { bootstrap } from '@/services/auth';
import { waitForAuthStoreHydration } from '@/stores/authStore';

interface AuthProviderContextValue {
  // Reserved for future additions; kept empty to avoid accidental prop-drilling.
}

const AuthProviderContext = createContext<AuthProviderContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const bootstrapped = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function runBootstrap(): Promise<void> {
      await waitForAuthStoreHydration();
      if (cancelled || bootstrapped.current) return;
      bootstrapped.current = true;
      await bootstrap();
    }

    void runBootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  return <AuthProviderContext.Provider value={{}}>{children}</AuthProviderContext.Provider>;
}

/** @deprecated Kept for backward-compat while pages migrate to `useAuth`. */
export function useAuthProviderContext(): AuthProviderContextValue {
  const ctx = useContext(AuthProviderContext);
  if (!ctx) {
    throw new Error('useAuthProviderContext must be used within <AuthProvider>');
  }
  return ctx;
}

// Re-export the real public hooks so old `from '@/contexts/AuthContext'`
// imports keep working during the migration.
export { useAuth } from '@/hooks/useAuth';
export { usePermission, useHasAnyPermission, useHasAllPermissions } from '@/hooks/usePermission';
