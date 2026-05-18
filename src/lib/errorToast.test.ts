/**
 * Tests for the error-code → toast mapper (STAGE-4-PENDING-004b closure).
 *
 * We don't mount a toast provider here — we test the pure mapping. The
 * `showErrorToast` convenience wrapper is tested with a spy to prove it
 * forwards the mapped payload verbatim.
 */

import type { AxiosError } from 'axios';
import { describe, expect, it, vi } from 'vitest';

import { getErrorEnvelope, mapErrorToToast, showErrorToast } from './errorToast';

function makeAxiosError(data: Record<string, unknown> | undefined, status = 400): AxiosError {
  return {
    isAxiosError: true,
    response: {
      data,
      status,
      statusText: 'Bad Request',
      headers: {},
      config: {} as never,
    },
    config: {} as never,
    name: 'AxiosError',
    message: 'Request failed',
    toJSON: () => ({}),
  } as unknown as AxiosError;
}

describe('getErrorEnvelope', () => {
  it('returns the envelope when the response carries error_code', () => {
    const err = makeAxiosError({
      error_code: 'MAKER_EQUALS_CHECKER',
      message: 'Maker cannot approve their own submission',
      correlation_id: 'abc-123',
    });
    const env = getErrorEnvelope(err);
    expect(env?.error_code).toBe('MAKER_EQUALS_CHECKER');
  });

  it('returns the envelope when only `message` is present', () => {
    const err = makeAxiosError({ message: 'Legacy error shape' });
    expect(getErrorEnvelope(err)?.message).toBe('Legacy error shape');
  });

  it('returns undefined for FastAPI default {detail: ...} shape', () => {
    const err = makeAxiosError({ detail: 'Not Found' });
    expect(getErrorEnvelope(err)).toBeUndefined();
  });

  it('returns undefined for network errors (no response)', () => {
    expect(getErrorEnvelope(new Error('network down'))).toBeUndefined();
  });

  it('returns undefined when response.data is not an object', () => {
    const err = makeAxiosError(undefined);
    expect(getErrorEnvelope(err)).toBeUndefined();
  });
});

describe('mapErrorToToast — known codes', () => {
  it('tunes the MAKER_EQUALS_CHECKER message for user clarity', () => {
    const err = makeAxiosError({
      error_code: 'MAKER_EQUALS_CHECKER',
      message: 'Maker cannot approve their own submission',
    });
    const toast = mapErrorToToast(err);
    expect(toast.title).toBe('Approval blocked — maker-checker');
    expect(toast.description).toMatch(/cannot also approve/);
    expect(toast.variant).toBe('destructive');
  });

  it('appends a short correlation-id suffix for support traceability', () => {
    const err = makeAxiosError({
      error_code: 'MAKER_EQUALS_CHECKER',
      correlation_id: 'abcdef12-3456-7890-abcd-ef1234567890',
    });
    const toast = mapErrorToToast(err);
    expect(toast.description).toMatch(/\(ref: abcdef12\)$/);
  });

  it('handles WEBHOOK_NOT_CONFIGURED with operational hint', () => {
    const err = makeAxiosError({ error_code: 'WEBHOOK_NOT_CONFIGURED' });
    const toast = mapErrorToToast(err);
    expect(toast.title).toBe('Integration not configured');
    expect(toast.description).toMatch(/Admin → Integrations/);
  });

  it('handles UPLOAD_INFECTED with explicit virus messaging', () => {
    const err = makeAxiosError({ error_code: 'UPLOAD_INFECTED' });
    const toast = mapErrorToToast(err);
    expect(toast.title).toMatch(/virus/i);
  });

  it('handles CONCURRENCY_CONFLICT with refresh-and-retry guidance', () => {
    const err = makeAxiosError({ error_code: 'CONCURRENCY_CONFLICT' });
    const toast = mapErrorToToast(err);
    expect(toast.description).toMatch(/Refresh and try again/i);
  });

  it('handles CLOSED_PERIOD with reversal hint', () => {
    const err = makeAxiosError({ error_code: 'CLOSED_PERIOD' });
    const toast = mapErrorToToast(err);
    expect(toast.description).toMatch(/Reversals go to the next open period/);
  });
});

describe('mapErrorToToast — fallback behaviour', () => {
  it('falls back to the backend message when the code is unknown', () => {
    const err = makeAxiosError({
      error_code: 'SOMETHING_NEW',
      message: 'A brand new error type',
      correlation_id: 'xxyyzz00-0000-0000-0000-000000000000',
    });
    const toast = mapErrorToToast(err);
    expect(toast.title).toBe('Something went wrong');
    expect(toast.description).toMatch(/^A brand new error type/);
    expect(toast.description).toMatch(/\(ref: xxyyzz00\)$/);
  });

  it('uses the error.message when no envelope is available', () => {
    const err = new Error('Network unreachable');
    const toast = mapErrorToToast(err);
    expect(toast.description).toBe('Network unreachable');
  });

  it('uses a generic fallback when nothing else is available', () => {
    const toast = mapErrorToToast({});
    expect(toast.description).toBe('An unexpected error occurred.');
  });

  it('always sets variant=destructive', () => {
    expect(mapErrorToToast(new Error('x')).variant).toBe('destructive');
    expect(mapErrorToToast(makeAxiosError({ error_code: 'MAKER_EQUALS_CHECKER' })).variant).toBe(
      'destructive',
    );
  });
});

describe('showErrorToast', () => {
  it('forwards the mapped payload to the toast function', () => {
    const toast = vi.fn();
    const err = makeAxiosError({ error_code: 'MAKER_EQUALS_CHECKER' });
    showErrorToast(err, toast);
    expect(toast).toHaveBeenCalledTimes(1);
    const payload = toast.mock.calls[0][0];
    expect(payload.title).toBe('Approval blocked — maker-checker');
    expect(payload.variant).toBe('destructive');
  });
});
