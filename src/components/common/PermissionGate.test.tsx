import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { useAuthStore } from '@/stores/authStore';

import { PermissionGate } from './PermissionGate';

function seed(perms: string[]): void {
  useAuthStore.setState({
    accessToken: 'x',
    refreshToken: 'y',
    user: {
      id: 'u1',
      username: 'alice',
      email: 'a@b.com',
      fullName: 'Alice',
      organizationId: 'o1',
      defaultUnitId: null,
      mfaEnabled: false,
      roles: [],
    },
    permissions: new Set(perms),
    isBootstrapping: false,
  });
}

describe('PermissionGate', () => {
  it('renders children when single permission is granted', () => {
    seed(['voucher.post']);
    render(
      <PermissionGate permission="voucher.post">
        <span>allowed</span>
      </PermissionGate>,
    );
    expect(screen.getByText('allowed')).toBeInTheDocument();
  });

  it('renders fallback when single permission is missing', () => {
    seed([]);
    render(
      <PermissionGate permission="voucher.post" fallback={<span>denied</span>}>
        <span>allowed</span>
      </PermissionGate>,
    );
    expect(screen.getByText('denied')).toBeInTheDocument();
    expect(screen.queryByText('allowed')).toBeNull();
  });

  it('anyOf passes if user has at least one permission', () => {
    seed(['loan_application.approve']);
    render(
      <PermissionGate anyOf={['voucher.post', 'loan_application.approve']}>
        <span>ok</span>
      </PermissionGate>,
    );
    expect(screen.getByText('ok')).toBeInTheDocument();
  });

  it('allOf requires every permission', () => {
    seed(['voucher.post']);
    render(
      <PermissionGate allOf={['voucher.post', 'voucher.reverse']} fallback={<span>no</span>}>
        <span>yes</span>
      </PermissionGate>,
    );
    expect(screen.getByText('no')).toBeInTheDocument();
  });
});
