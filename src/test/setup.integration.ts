/**
 * Vitest setup for the integration project. Loads MSW handlers + jest-dom.
 */

import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach, vi } from 'vitest';

// jsdom ships without a few browser APIs that Radix relies on.
// Polyfill them globally so Popover/ScrollArea/Dialog components work.
if (!('ResizeObserver' in globalThis)) {
  class RO {
    observe(): void {
      return undefined;
    }

    unobserve(): void {
      return undefined;
    }

    disconnect(): void {
      return undefined;
    }
  }
  (globalThis as unknown as { ResizeObserver: typeof RO }).ResizeObserver = RO;
}
if (!('scrollTo' in Element.prototype)) {
  (Element.prototype as unknown as { scrollTo: () => void }).scrollTo = vi.fn();
}
if (
  typeof (Element.prototype as unknown as { hasPointerCapture?: unknown }).hasPointerCapture !==
  'function'
) {
  Element.prototype.hasPointerCapture = (() => false) as Element['hasPointerCapture'];
  Element.prototype.releasePointerCapture = (() => undefined) as Element['releasePointerCapture'];
  (Element.prototype as unknown as { setPointerCapture: (id: number) => void }).setPointerCapture =
    () => undefined;
}
if (!('matchMedia' in window)) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
    })),
  });
}

import { TEST_ORG, TEST_USER } from './msw/handlers';
import { server } from './msw/server';

import { useAuthStore } from '@/stores/authStore';
import { useOrganizationStore } from '@/stores/organizationStore';

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// Pre-seed the auth + org stores so hooks that require an auth context don't
// have to walk the full login flow in every test.
beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
  useAuthStore.setState({
    accessToken: 'test-access-token',
    refreshToken: 'test-refresh-token',
    user: {
      id: TEST_USER.id,
      username: TEST_USER.username,
      email: TEST_USER.email,
      fullName: TEST_USER.fullName,
      organizationId: TEST_USER.organizationId,
      defaultUnitId: TEST_USER.defaultUnitId,
      mfaEnabled: TEST_USER.mfaEnabled,
      roles: TEST_USER.roles.map((r) => r.code),
    },
    permissions: new Set(TEST_USER.permissions),
    isBootstrapping: false,
  });
  useOrganizationStore.setState({
    organizations: [TEST_ORG],
    activeOrganizationId: TEST_ORG.id,
  });
});
