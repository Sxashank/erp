export type AppThemeId = 'ledger' | 'sage' | 'dusk';

export interface AppThemeDefinition {
  id: AppThemeId;
  label: string;
  description: string;
  swatches: [string, string, string];
}

export const DEFAULT_APP_THEME: AppThemeId = 'ledger';

export const APP_THEMES: AppThemeDefinition[] = [
  {
    id: 'ledger',
    label: 'Ledger Blue',
    description: 'Deep blue navigation with a clean porcelain workspace.',
    swatches: ['#1e3a5f', '#3f76c7', '#f6f8fc'],
  },
  {
    id: 'sage',
    label: 'Sage Stone',
    description: 'Muted green slate with a calm off-white working area.',
    swatches: ['#1f3a38', '#6a9c8f', '#f5f5ef'],
  },
  {
    id: 'dusk',
    label: 'Dusk Copper',
    description: 'Charcoal shell with restrained copper and ivory highlights.',
    swatches: ['#2b2430', '#b37a4c', '#f7f2ea'],
  },
];

export function isAppThemeId(value: string): value is AppThemeId {
  return APP_THEMES.some((theme) => theme.id === value);
}
