/**
 * Auth service — thin typed wrappers over /api/v1/auth/*.
 * Actions (login/logout/refresh/bootstrap) that mutate the auth store live
 * in src/hooks/useAuth.ts; this file is HTTP-only. See CLAUDE.md §3.3.
 */

import axios, { type AxiosInstance } from 'axios';

import { useAuthStore, type AuthUser } from '@/stores/authStore';
import { useOrganizationStore, type Organization } from '@/stores/organizationStore';

import { api } from './api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';

// A bare axios (no interceptors) for refresh calls so we don't recurse.
const bareAxios: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export interface LoginPayload {
  username: string;
  password: string;
  otp?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user?: {
    id: string;
    username: string;
    email: string;
    full_name: string;
    roles: string[];
    permissions: string[];
  };
  requires_mfa?: boolean;
  message?: string;
}

export interface MeResponse {
  id: string;
  username: string;
  email: string;
  full_name: string;
  organization_id: string | null;
  default_unit_id: string | null;
  mfa_enabled: boolean;
  roles: Array<{ id: string; code: string; name: string }>;
  permissions: string[];
}

export interface OrganizationListItem {
  id: string;
  code: string;
  name: string;
}

function mapMeToUser(me: MeResponse): AuthUser {
  return {
    id: me.id,
    username: me.username,
    email: me.email,
    fullName: me.full_name,
    organizationId: me.organization_id,
    defaultUnitId: me.default_unit_id,
    mfaEnabled: me.mfa_enabled,
    roles: me.roles.map((r) => r.code),
  };
}

function mapOrg(o: OrganizationListItem): Organization {
  return { id: o.id, code: o.code, name: o.name };
}

export async function login(payload: LoginPayload): Promise<{ requiresMfa: boolean }> {
  const { data } = await bareAxios.post<TokenResponse>('/auth/login', payload);
  if (data.requires_mfa) {
    return { requiresMfa: true };
  }
  useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
  await hydrateFromServer();
  return { requiresMfa: false };
}

export async function logout(): Promise<void> {
  const refresh = useAuthStore.getState().refreshToken;
  if (refresh) {
    try {
      await api.post('/auth/logout', { refresh_token: refresh });
    } catch {
      // Best-effort; the server may already have revoked it.
    }
  }
  useAuthStore.getState().clear();
  useOrganizationStore.getState().clear();
}

/**
 * Low-level refresh — used by the axios interceptor and by bootstrap().
 * Returns the new access token, or null if the refresh failed.
 */
export async function refreshTokens(): Promise<string | null> {
  const refresh = useAuthStore.getState().refreshToken;
  if (!refresh) return null;
  try {
    const { data } = await bareAxios.post<TokenResponse>('/auth/refresh', {
      refresh_token: refresh,
    });
    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    useAuthStore.getState().clear();
    useOrganizationStore.getState().clear();
    return null;
  }
}

/**
 * Fetch /auth/me and the organizations list; populate the stores.
 * Call after login or during bootstrap.
 */
export async function hydrateFromServer(): Promise<void> {
  const [me, orgs] = await Promise.all([
    api.get<MeResponse>('/auth/me'),
    api.get<{ items: OrganizationListItem[] } | OrganizationListItem[]>('/organizations', {
      params: { limit: 200 },
    }),
  ]);
  useAuthStore.getState().setUser(mapMeToUser(me.data), me.data.permissions);
  const orgList = Array.isArray(orgs.data) ? orgs.data : orgs.data.items;
  useOrganizationStore.getState().setOrganizations(orgList.map(mapOrg));
}

/**
 * Called once on app startup. If a refresh token is persisted, attempt to
 * swap it for a fresh access token and hydrate; otherwise stay signed out.
 */
export async function bootstrap(): Promise<void> {
  const store = useAuthStore.getState();
  store.setBootstrapping(true);
  try {
    if (!store.refreshToken) {
      store.clear();
      return;
    }
    const newAccess = await refreshTokens();
    if (!newAccess) return;
    await hydrateFromServer();
  } finally {
    useAuthStore.getState().setBootstrapping(false);
  }
}
