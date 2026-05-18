import { describe, expect, it } from 'vitest';

import {
  ERP_MODULES,
  canAccessAdminPath,
  filterNavItemsByAccess,
  getAccessRuleForAdminPath,
} from './moduleAccess';

describe('moduleAccess', () => {
  it('lists the full ERP module scope, not only lending', () => {
    expect(ERP_MODULES.map((module) => module.key)).toEqual([
      'dashboard',
      'masters',
      'users_acl',
      'finance',
      'gst',
      'tds_tcs',
      'ap_ar',
      'lending',
      'treasury_alm',
      'regulatory_reports',
      'fixed_assets',
      'fixed_deposits',
      'hris_payroll',
      'inventory_procurement',
      'compliance_legal_dms',
      'notifications_settings_portals',
    ]);
  });

  it('allows super admins to reach every mapped and future admin path', () => {
    const permissions = new Set(['SUPER_ADMIN']);

    expect(canAccessAdminPath('/admin/gst/rates', permissions)).toBe(true);
    expect(canAccessAdminPath('/admin/future-module/new', permissions)).toBe(true);
  });

  it('keeps module access permission scoped', () => {
    const permissions = new Set(['FIN_VOUCHER_VIEW']);

    expect(canAccessAdminPath('/admin/finance/vouchers', permissions)).toBe(true);
    expect(canAccessAdminPath('/admin/lending/applications', permissions)).toBe(false);
    expect(canAccessAdminPath('/admin/hris/employees', permissions)).toBe(false);
  });

  it('filters sidebar children by the same access rules', () => {
    const items = [
      {
        label: 'Finance',
        children: [
          { label: 'Vouchers', href: '/admin/finance/vouchers' },
          { label: 'Financial Years', href: '/admin/finance/financial-years' },
        ],
      },
      {
        label: 'Lending',
        children: [
          { label: 'Applications', href: '/admin/lending/applications' },
          { label: 'Loan Accounts', href: '/admin/lending/accounts' },
        ],
      },
    ];

    expect(filterNavItemsByAccess(items, new Set(['FIN_VOUCHER_VIEW']))).toEqual([
      {
        label: 'Finance',
        children: [{ label: 'Vouchers', href: '/admin/finance/vouchers' }],
      },
    ]);
  });

  it('returns null for unmapped admin paths unless the user is super admin', () => {
    expect(getAccessRuleForAdminPath('/admin/unknown')).toBeNull();
    expect(canAccessAdminPath('/admin/unknown', new Set(['FIN_REPORT_VIEW']))).toBe(false);
  });
});
