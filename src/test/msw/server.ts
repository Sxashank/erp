/**
 * MSW node server used by Vitest integration tests. See CLAUDE.md §10.2.
 */

import { setupServer } from 'msw/node';

import { handlers } from './handlers';

export const server = setupServer(...handlers);
