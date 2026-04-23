/**
 * Unit tests for `src/lib/logger.ts`. Verifies dev/prod gating per CLAUDE.md §5.12.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('logger', () => {
  let infoSpy: ReturnType<typeof vi.spyOn>;
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    infoSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    infoSpy.mockRestore();
    warnSpy.mockRestore();
    errorSpy.mockRestore();
    vi.resetModules();
  });

  it('in development emits debug/info/warn/error', async () => {
    vi.stubEnv('MODE', 'development');
    const { logger } = await import('./logger');

    logger.debug('hello');
    logger.info('hi');
    logger.warn('careful');
    logger.error('bad');

    expect(infoSpy).toHaveBeenCalled(); // debug + info both route to console.info
    expect(warnSpy).toHaveBeenCalled();
    expect(errorSpy).toHaveBeenCalled();

    vi.unstubAllEnvs();
  });

  it('in production suppresses debug/info/warn but keeps error', async () => {
    vi.stubEnv('MODE', 'production');
    const { logger } = await import('./logger');

    logger.debug('x');
    logger.info('x');
    logger.warn('x');
    logger.error('x');

    expect(infoSpy).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalled();
    expect(errorSpy).toHaveBeenCalled();

    vi.unstubAllEnvs();
  });
});
