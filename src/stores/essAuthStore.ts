import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ESSSessionUser {
  id?: string;
  employee_id?: string;
  employee_code?: string;
  employee_name?: string;
  name?: string;
  mobile?: string;
  email?: string | null;
}

interface ESSAuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: ESSSessionUser | null;
  setSession: (accessToken: string, refreshToken: string, user?: ESSSessionUser | null) => void;
  clear: () => void;
}

export const useEssAuthStore = create<ESSAuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setSession: (accessToken, refreshToken, user = null) =>
        set({ accessToken, refreshToken, user }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: 'smfc-ess-auth',
    },
  ),
);

export const selectIsESSAuthenticated = (state: ESSAuthState): boolean =>
  Boolean(state.accessToken);
