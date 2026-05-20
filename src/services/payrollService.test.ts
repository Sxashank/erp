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
        componentCode: 'HRA',
        componentName: 'House Rent Allowance',
        componentType: 'EARNING',
        category: 'ALLOWANCE',
        calculationType: 'PERCENTAGE_OF_BASIC',
        defaultValue: 40,
        isTaxable: true,
        isProRated: true,
        affectsPf: false,
        affectsEsi: false,
        affectsPt: false,
        displayOrder: 1,
        isActive: true,
        createdAt: '2026-04-01T00:00:00Z',
      },
    });

    const result = await payrollService.createComponent({
      componentCode: 'HRA',
      componentName: 'House Rent Allowance',
      componentType: 'EARNING',
      category: 'ALLOWANCE',
      calculationType: 'PERCENTAGE',
      percentageOf: 'BASIC',
      percentageValue: 40,
    });

    expect(api.post).toHaveBeenCalledWith(
      '/payroll/components',
      expect.objectContaining({
        calculationType: 'PERCENTAGE_OF_BASIC',
        defaultValue: 40,
        percentageOf: undefined,
        percentageValue: undefined,
      }),
    );
    expect(result).toMatchObject({
      calculationType: 'PERCENTAGE',
      percentageOf: 'BASIC',
      percentageValue: 40,
    });
  });

  it('maps salary structure component values to the backend structure contract', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        id: 'structure-1',
        structureCode: 'STD',
        structureName: 'Standard Structure',
        effectiveFrom: '2026-04-01',
        paymentMode: 'BANK',
        payFrequency: 'MONTHLY',
        isActive: true,
        createdAt: '2026-04-01T00:00:00Z',
        components: [
          {
            id: 'line-1',
            componentId: 'component-1',
            calculationType: 'PERCENTAGE_OF_BASIC',
            value: 50,
            isMandatory: true,
          },
        ],
      },
    });

    const result = await payrollService.createStructure({
      structureCode: 'STD',
      structureName: 'Standard Structure',
      effectiveFrom: '2026-04-01',
      paymentMode: 'BANK',
      payFrequency: 'MONTHLY',
      isActive: true,
      components: [
        {
          componentId: 'component-1',
          calculationType: 'PERCENTAGE',
          percentageOf: 'BASIC',
          percentageValue: 50,
          isMandatory: true,
        },
      ],
    });

    expect(api.post).toHaveBeenCalledWith(
      '/payroll/structures',
      expect.objectContaining({
        effectiveFrom: '2026-04-01',
        components: [
          expect.objectContaining({
            componentId: 'component-1',
            calculationType: 'PERCENTAGE_OF_BASIC',
            value: 50,
          }),
        ],
      }),
    );
    expect(result.components?.[0]).toMatchObject({
      calculationType: 'PERCENTAGE',
      percentageOf: 'BASIC',
      percentageValue: 50,
      defaultValue: 50,
    });
  });

  it('maps PF statutory setup aliases to backend statutory fields', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        id: 'setup-1',
        statutoryType: 'PF',
        pfEmployerRate: 12,
        pfEmployeeRate: 12,
        pfAdminChargeRate: 0.5,
        pfWageCeiling: 15000,
        effectiveFrom: '2026-04-01',
        isActive: true,
        createdAt: '2026-04-01T00:00:00Z',
      },
    });

    const result = await payrollService.createStatutorySetup({
      statutoryType: 'PF',
      employerContributionPct: 12,
      employeeContributionPct: 12,
      adminChargesPct: 0.5,
      wageCeiling: 15000,
      effectiveFrom: '2026-04-01',
      isApplicable: true,
    });

    expect(api.post).toHaveBeenCalledWith(
      '/payroll/statutory-setup',
      expect.objectContaining({
        statutoryType: 'PF',
        pfEmployerRate: 12,
        pfEmployeeRate: 12,
        pfAdminChargeRate: 0.5,
        pfWageCeiling: 15000,
        isActive: true,
      }),
    );
    expect(result).toMatchObject({
      employerContributionPct: 12,
      employeeContributionPct: 12,
      adminChargesPct: 0.5,
      wageCeiling: 15000,
      isApplicable: true,
    });
  });
});
