/**
 * Unit tests for the auth store. See CLAUDE.md §5.5, §5.6.
 */

import { describe, expect, it } from 'vitest';

import { selectIsAuthenticated, useAuthStore } from './authStore';

function reset(): void {
  useAuthStore.setState({
    accessToken: null,
    refreshToken: null,
    user: null,
    permissions: new Set(),
    isBootstrapping: true,
  });
}

describe('authStore', () => {
  it('starts unauthenticated', () => {
    reset();
    expect(selectIsAuthenticated(useAuthStore.getState())).toBe(false);
  });

  it('setTokens + setUser makes the selector true', () => {
    reset();
    useAuthStore.getState().setTokens('access', 'refresh');
    useAuthStore.getState().setUser(
      {
        id: 'u1',
        username: 'alice',
        email: 'alice@example.com',
        fullName: 'Alice',
        organizationId: 'o1',
        defaultUnitId: null,
        mfaEnabled: true,
        roles: ['admin'],
      },
      ['voucher.post', 'loan_application.approve'],
    );

    expect(selectIsAuthenticated(useAuthStore.getState())).toBe(true);
    expect(useAuthStore.getState().permissions.has('voucher.post')).toBe(true);
  });

  it('clear() wipes state and ends bootstrap', () => {
    reset();
    useAuthStore.getState().setTokens('a', 'r');
    useAuthStore.getState().clear();
    const s = useAuthStore.getState();
    expect(s.accessToken).toBeNull();
    expect(s.refreshToken).toBeNull();
    expect(s.user).toBeNull();
    expect(s.permissions.size).toBe(0);
    expect(s.isBootstrapping).toBe(false);
  });
});
