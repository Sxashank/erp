import { beforeEach, describe, expect, it, vi } from 'vitest';

import api from './api';
import payrollService from './payrollService';

vi.mock('./api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('payrollService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps percentage salary components to backend calculation fields', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        id: 'component-1',
        organization_id: 'org-1',
        component_code: 'HRA',
        component_name: 'House Rent Allowance',
        component_type: 'EARNING',
        category: 'ALLOWANCE',
        calculation_type: 'PERCENTAGE_OF_BASIC',
        default_value: 40,
        is_taxable: true,
        is_pro_rated: true,
        affects_pf: false,
        affects_esi: false,
        affects_pt: false,
        display_order: 1,
        is_active: true,
        created_at: '2026-04-01T00:00:00Z',
      },
    });

    const result = await payrollService.createComponent({
      organization_id: 'org-1',
      component_code: 'HRA',
      component_name: 'House Rent Allowance',
      component_type: 'EARNING',
      category: 'ALLOWANCE',
      calculation_type: 'PERCENTAGE',
      percentage_of: 'BASIC',
      percentage_value: 40,
    });

    expect(api.post).toHaveBeenCalledWith(
      '/payroll/components',
      expect.objectContaining({
        calculation_type: 'PERCENTAGE_OF_BASIC',
        default_value: 40,
        percentage_of: undefined,
        percentage_value: undefined,
      }),
    );
    expect(result).toMatchObject({
      calculation_type: 'PERCENTAGE',
      percentage_of: 'BASIC',
      percentage_value: 40,
    });
  });

  it('maps salary structure component values to the backend structure contract', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        id: 'structure-1',
        organization_id: 'org-1',
        structure_code: 'STD',
        structure_name: 'Standard Structure',
        effective_from: '2026-04-01',
        payment_mode: 'BANK',
        pay_frequency: 'MONTHLY',
        is_active: true,
        created_at: '2026-04-01T00:00:00Z',
        components: [
          {
            id: 'line-1',
            component_id: 'component-1',
            calculation_type: 'PERCENTAGE_OF_BASIC',
            value: 50,
            is_mandatory: true,
          },
        ],
      },
    });

    const result = await payrollService.createStructure({
      organization_id: 'org-1',
      structure_code: 'STD',
      structure_name: 'Standard Structure',
      effective_from: '2026-04-01',
      payment_mode: 'BANK',
      pay_frequency: 'MONTHLY',
      is_active: true,
      components: [
        {
          component_id: 'component-1',
          calculation_type: 'PERCENTAGE',
          percentage_of: 'BASIC',
          percentage_value: 50,
          is_mandatory: true,
        },
      ],
    });

    expect(api.post).toHaveBeenCalledWith(
      '/payroll/structures',
      expect.objectContaining({
        effective_from: '2026-04-01',
        components: [
          expect.objectContaining({
            component_id: 'component-1',
            calculation_type: 'PERCENTAGE_OF_BASIC',
            value: 50,
          }),
        ],
      }),
    );
    expect(result.components?.[0]).toMatchObject({
      calculation_type: 'PERCENTAGE',
      percentage_of: 'BASIC',
      percentage_value: 50,
      default_value: 50,
    });
  });

  it('maps PF statutory setup aliases to backend statutory fields', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        id: 'setup-1',
        organization_id: 'org-1',
        statutory_type: 'PF',
        pf_employer_rate: 12,
        pf_employee_rate: 12,
        pf_admin_charge_rate: 0.5,
        pf_wage_ceiling: 15000,
        effective_from: '2026-04-01',
        is_active: true,
        created_at: '2026-04-01T00:00:00Z',
      },
    });

    const result = await payrollService.createStatutorySetup({
      organization_id: 'org-1',
      statutory_type: 'PF',
      employer_contribution_pct: 12,
      employee_contribution_pct: 12,
      admin_charges_pct: 0.5,
      wage_ceiling: 15000,
      effective_from: '2026-04-01',
      is_applicable: true,
    });

    expect(api.post).toHaveBeenCalledWith(
      '/payroll/statutory-setup',
      expect.objectContaining({
        statutory_type: 'PF',
        pf_employer_rate: 12,
        pf_employee_rate: 12,
        pf_admin_charge_rate: 0.5,
        pf_wage_ceiling: 15000,
        is_active: true,
      }),
    );
    expect(result).toMatchObject({
      employer_contribution_pct: 12,
      employee_contribution_pct: 12,
      admin_charges_pct: 0.5,
      wage_ceiling: 15000,
      is_applicable: true,
    });
  });
});
