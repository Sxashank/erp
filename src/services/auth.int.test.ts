/**
 * Integration test: auth flow through MSW.
 */

import { describe, expect, it } from 'vitest';

import { login, logout, refreshTokens } from './auth';

import { useAuthStore } from '@/stores/authStore';
import { useOrganizationStore } from '@/stores/organizationStore';

describe('auth service (integration)', () => {
  it('login stores tokens and hydrates user + organizations', async () => {
    // Reset state pre-test (the setup seeds a user; we need to clear to see the effect)
    useAuthStore.getState().clear();
    useOrganizationStore.getState().clear();

    await login({ username: 'admin', password: 'correct-horse' });

    const s = useAuthStore.getState();
    expect(s.accessToken).toBe('test-access-token');
    expect(s.user?.username).toBe('admin');
    expect(s.permissions.has('voucher.post')).toBe(true);
    expect(useOrganizationStore.getState().activeOrganizationId).toBeTruthy();
  });

  it('refreshTokens rotates and returns the new access token', async () => {
    useAuthStore.setState({ accessToken: 'old', refreshToken: 'r-old' });
    const newAccess = await refreshTokens();
    expect(newAccess).toBe('test-access-token-rotated');
    expect(useAuthStore.getState().accessToken).toBe('test-access-token-rotated');
  });

  it('logout clears both auth and organization stores', async () => {
    useAuthStore.setState({ accessToken: 'x', refreshToken: 'y' });
    await logout();
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useOrganizationStore.getState().activeOrganizationId).toBeNull();
  });
});
