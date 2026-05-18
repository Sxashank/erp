/**
 * Tests for MakerCheckerGate — the FE half of §8.4 maker-checker.
 *
 * The component reads the current user via `useAuth()`; we mock the hook
 * directly so we don't need to stand up the Zustand store.
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { MakerCheckerGate } from './MakerCheckerGate';

vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/hooks/useAuth';

const mockedUseAuth = vi.mocked(useAuth);

function setUser(id: string | null): void {
  if (id === null) {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isBootstrapping: false,
      accessToken: null,
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
      reloadProfile: vi.fn(),
    });
  } else {
    mockedUseAuth.mockReturnValue({
      user: {
        id,
        username: 'u',
        email: 'u@x',
        fullName: 'Test User',
        organizationId: 'org-1',
        defaultUnitId: null,
        mfaEnabled: false,
        roles: [],
      },
      isAuthenticated: true,
      isBootstrapping: false,
      accessToken: 'tok',
      login: vi.fn(),
      logout: vi.fn(),
      refresh: vi.fn(),
      reloadProfile: vi.fn(),
    });
  }
}

describe('MakerCheckerGate', () => {
  it('shows children when current user is NOT the maker', () => {
    setUser('approver-id');
    render(
      <MakerCheckerGate makerId="maker-id">
        <button>Approve</button>
      </MakerCheckerGate>,
    );
    expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument();
  });

  it('hides children when current user IS the maker', () => {
    setUser('maker-id');
    render(
      <MakerCheckerGate makerId="maker-id">
        <button>Approve</button>
      </MakerCheckerGate>,
    );
    expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument();
  });

  it('shows the fallback when current user is the maker', () => {
    setUser('maker-id');
    render(
      <MakerCheckerGate
        makerId="maker-id"
        fallback={<span>You submitted this; ask a different approver.</span>}
      >
        <button>Approve</button>
      </MakerCheckerGate>,
    );
    expect(screen.getByText(/ask a different approver/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument();
  });

  it('shows children when makerId is nullish (legacy row)', () => {
    setUser('approver-id');
    render(
      <MakerCheckerGate makerId={null}>
        <button>Approve</button>
      </MakerCheckerGate>,
    );
    // Legacy rows: we defer to the backend guard rather than forever-hiding.
    expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument();
  });

  it('shows children when makerId is undefined', () => {
    setUser('approver-id');
    render(
      <MakerCheckerGate makerId={undefined}>
        <button>Approve</button>
      </MakerCheckerGate>,
    );
    expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument();
  });

  it('hides children when there is no authenticated user', () => {
    setUser(null);
    render(
      <MakerCheckerGate makerId="maker-id">
        <button>Approve</button>
      </MakerCheckerGate>,
    );
    // Defensive: no user → no approve UI. The auth layer should have
    // redirected, but a flash of an approve button during a race is bad.
    expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument();
  });

  it('compares ids as strings (handles numeric vs string IDs)', () => {
    setUser('42');
    render(
      <MakerCheckerGate makerId={42 as unknown as string}>
        <button>Approve</button>
      </MakerCheckerGate>,
    );
    // Same logical id, different JS types → still treated as self-approval.
    expect(screen.queryByRole('button', { name: 'Approve' })).not.toBeInTheDocument();
  });
});
