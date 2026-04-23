/**
 * Vitest setup — loads jest-dom matchers and per-test cleanup.
 */
import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach } from 'vitest';

afterEach(() => {
  cleanup();
});

// Stable localStorage reset so Zustand persist() does not leak between tests.
beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
});
