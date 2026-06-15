import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import {
  APP_THEMES,
  DEFAULT_APP_THEME,
  type AppThemeDefinition,
  type AppThemeId,
} from '@/lib/appThemes';

interface AppThemeContextValue {
  theme: AppThemeId;
  setTheme: (theme: AppThemeId) => void;
  themes: AppThemeDefinition[];
}

const AppThemeContext = createContext<AppThemeContextValue | null>(null);

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<AppThemeId>(DEFAULT_APP_THEME);

  useEffect(() => {
    document.documentElement.dataset.appTheme = theme;
  }, [theme]);

  const value = useMemo(
    () => ({
      theme,
      setTheme,
      themes: APP_THEMES,
    }),
    [theme],
  );

  return <AppThemeContext.Provider value={value}>{children}</AppThemeContext.Provider>;
}

export function useAppTheme() {
  const context = useContext(AppThemeContext);
  if (!context) {
    throw new Error('useAppTheme must be used within AppThemeProvider');
  }
  return context;
}
