import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { canAccessAdminPath } from '@/lib/moduleAccess';
import { useAuthStore } from '@/stores/authStore';

interface RequireModuleAccessProps {
  children: ReactNode;
}

export function RequireModuleAccess({ children }: RequireModuleAccessProps) {
  const location = useLocation();
  const permissions = useAuthStore((state) => state.permissions);

  if (!canAccessAdminPath(location.pathname, permissions)) {
    return <Navigate to="/admin" replace />;
  }

  return <>{children}</>;
}
